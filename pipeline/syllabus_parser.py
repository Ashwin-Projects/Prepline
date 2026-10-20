"""
Syllabus Parser Module (Phase 7)

Parses text-selectable VIT syllabus PDFs using pdfplumber:
- Detects pages without a text layer (scanned/image pages; OCR excluded from MVP scope) and
  rejects PDFs that have no extractable text at all.
- Splits the text into courses (course code + title + L-T-P-[J-]C), then modules within each course.
- Keeps only allowlisted core CS courses (config syllabus.core_courses) and reports kept/dropped
  courses and allowlisted courses with no readable syllabus.
- Maps each module through the full Phase 4-6 taxonomy pipeline (taxonomy_mapper.map_source_to_taxonomy)
  preserving taxonomy_version, with per-module depth signals.
"""

import re
import os
from typing import Dict, Any, Iterable, List, Optional, Tuple
import pdfplumber

from pipeline.config import load_scoring_config
from pipeline.keyword_abstraction import DEFAULT_TAXONOMY_VERSION
from pipeline.taxonomy_mapper import map_source_to_taxonomy

# Minimum text threshold to detect scanned / non-text PDFs and pages
MIN_TEXT_LENGTH_THRESHOLD = 50

_CODE = r"[A-Z]{3,4}\d{3,4}[A-Z]?"

# VIT tabular header: "BECE102L Digital Systems Design 3 0 0 3" or
# "BMAT205L Discrete Mathematics and Graph Theory L T P C" with the numbers on the next line.
# Anchored at line start, so catalogue rows ("5 BMAT205L ... 1.0 3 1 0 0 4.0") never match.
_VIT_HEADER = re.compile(
    rf"^(?P<code>{_CODE})[ \t]+(?P<title>.+?)[ \t]+"
    r"(?:(?P<inline>\d+(?:[ \t]+\d+){3,4})|L[ \t]+T[ \t]+P[ \t]+(?:J[ \t]+)?C)[ \t]*$",
    re.MULTILINE,
)
# Numbers on the next line, optionally after one wrapped title line ("... VULNERABILITY L T P C" / "ANALYSIS" / "2 0 0 2").
_NEXT_LINE_NUMBERS = re.compile(
    r"[ \t]*\r?\n(?:[ \t]*(?P<cont>[^\d\s][^\r\n]*?)[ \t]*\r?\n)?[ \t]*(?P<nums>\d+(?:[ \t]+\d+){3,4})[ \t]*$",
    re.MULTILINE,
)
# Bare header without the L T P C marker, numbers directly on the next line ("BCSE399J Summer Industrial Internship" / "0 0 0 1").
_VIT_BARE_HEADER = re.compile(rf"^(?P<code>{_CODE})[ \t]+(?P<title>[^\r\n]+?)[ \t]*$", re.MULTILINE)
_BARE_NEXT_LINE_NUMBERS = re.compile(r"[ \t]*\r?\n[ \t]*(?P<nums>\d+(?:[ \t]+\d+){3,4})[ \t]*$", re.MULTILINE)

# Labelled header: "Course Code: CSE2001" / "Course Title: ..." / "L T P J C : 3 0 2 0 4"
_LABELLED_HEADER = re.compile(rf"^[ \t]*Course[ \t]+Code[ \t]*[:\-][ \t]*(?P<code>{_CODE})[ \t]*$", re.MULTILINE)
_LABELLED_TITLE = re.compile(r"(?:Course Title|Course Name)\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE)
_LABELLED_LTPJC = re.compile(r"\bL\s*T\s*P\s*(?:J\s*)?C\s*[:\-\s]+\s*(\d+(?:\s+\d+){3,4})", re.IGNORECASE)

# Catalogue rows: "<sl.no> <code> <title> ..." (used only to tell scanned syllabi from absent ones)
_CATALOGUE_ROW = re.compile(rf"^[ \t]*\d+[ \t]+(?P<code>{_CODE})[ \t]+", re.MULTILINE)

_MODULE_HEADER = re.compile(
    r"^[ \t]*(?:Module|Unit)[ \t]*[:\-]?[ \t]*(\d+)[ \t]*[:\-]?[ \t]*([^\n\r]*)", re.IGNORECASE | re.MULTILINE
)
_MODULE_TERMINATOR = re.compile(
    r"^[ \t]*(?:Total[ \t]+Lecture[ \t]+hours|Total[ \t]+Laboratory[ \t]+Hours|Total[ \t]+Tutorial[ \t]+hours|"
    r"Text[ \t]+Book|Reference[ \t]+Book|Mode[ \t]+of[ \t]+(?:Evaluation|assessment)|Recommended[ \t]+by|Approved[ \t]+by)",
    re.IGNORECASE | re.MULTILINE,
)
# Lab block of an embedded (theory + lab) course, placed after the theory terminators.
_LAB_BLOCK_HEADER = re.compile(
    r"^[ \t]*(?:Indicative[ \t]+Experiments|List[ \t]+of[ \t]+Experiments)\b[^\r\n]*$", re.IGNORECASE | re.MULTILINE
)
_TRAILING_HOURS = re.compile(r"[ \t]*\(?[ \t]*\d+[ \t]*(?:hours|hrs|hour|hr)[ \t]*\)?[ \t]*$", re.IGNORECASE)

_METADATA_KEYS = ("course_code", "course_title", "lecture_hours", "tutorial_hours",
                  "practical_hours", "project_hours", "credits")


class UnsupportedPDFError(ValueError):
    """Raised when a PDF is scanned, lacks extractable text, or has no course headers."""
    pass


class NoCoreCoursesError(ValueError):
    """Raised when a syllabus PDF contains no allowlisted core CS course."""
    pass


def page_has_text_layer(page_text: Optional[str]) -> bool:
    """A page has a usable text layer when its stripped text reaches MIN_TEXT_LENGTH_THRESHOLD."""
    return len((page_text or "").strip()) >= MIN_TEXT_LENGTH_THRESHOLD


def is_scanned_pdf(pdf_path: str) -> bool:
    """
    Checks if a PDF is scanned (contains no text or text below threshold).
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")

    total_text_length = 0
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            return True
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            total_text_length += len(page_text.strip())

    return total_text_length < MIN_TEXT_LENGTH_THRESHOLD


def _ltpjc(numbers: str) -> Dict[str, Optional[int]]:
    """Maps 4 numbers (L T P C) or 5 numbers (L T P J C) to hour/credit fields."""
    values = [int(n) for n in numbers.split()]
    if len(values) == 4:
        lecture, tutorial, practical, credits = values
        project = None
    else:
        lecture, tutorial, practical, project, credits = values[:5]
    return {
        "lecture_hours": lecture,
        "tutorial_hours": tutorial,
        "practical_hours": practical,
        "project_hours": project,
        "credits": credits,
    }


def _empty_metadata() -> Dict[str, Any]:
    return {
        "course_code": "UNKNOWN",
        "course_title": "UNKNOWN",
        "lecture_hours": None,
        "tutorial_hours": None,
        "practical_hours": None,
        "project_hours": None,
        "credits": None,
    }


def _find_headers(full_text: str) -> List[Tuple[int, Dict[str, Any]]]:
    """Returns (start offset, metadata) for every course header, in document order."""
    headers: List[Tuple[int, Dict[str, Any]]] = []

    for m in _VIT_HEADER.finditer(full_text):
        numbers = m.group("inline")
        title = m.group("title").strip()
        if numbers is None:
            nxt = _NEXT_LINE_NUMBERS.match(full_text, m.end())
            if nxt is None:
                continue
            numbers = nxt.group("nums")
            if nxt.group("cont"):
                title = f"{title} {nxt.group('cont').strip()}"
        meta = {"course_code": m.group("code"), "course_title": title}
        meta.update(_ltpjc(numbers))
        headers.append((m.start(), meta))

    found_at = {start for start, _ in headers}
    for m in _VIT_BARE_HEADER.finditer(full_text):
        if m.start() in found_at:
            continue
        nxt = _BARE_NEXT_LINE_NUMBERS.match(full_text, m.end())
        if nxt is None:
            continue
        meta = {"course_code": m.group("code"), "course_title": m.group("title").strip()}
        meta.update(_ltpjc(nxt.group("nums")))
        headers.append((m.start(), meta))

    labelled = list(_LABELLED_HEADER.finditer(full_text))
    for i, m in enumerate(labelled):
        end = labelled[i + 1].start() if i + 1 < len(labelled) else len(full_text)
        block = full_text[m.end():end]
        meta = _empty_metadata()
        meta["course_code"] = m.group("code")
        title = _LABELLED_TITLE.search(block)
        if title:
            meta["course_title"] = title.group(1).strip()
        numbers = _LABELLED_LTPJC.search(block)
        if numbers:
            meta.update(_ltpjc(numbers.group(1)))
        headers.append((m.start(), meta))

    headers.sort(key=lambda h: h[0])
    return headers


def segment_courses(full_text: str) -> List[Dict[str, Any]]:
    """
    Splits syllabus text into courses. Each course carries its header metadata
    (course_code, course_title, lecture/tutorial/practical/project hours, credits)
    and `text`, the span from its header to the next course header.
    """
    headers = _find_headers(full_text)
    courses = []
    for i, (start, meta) in enumerate(headers):
        end = headers[i + 1][0] if i + 1 < len(headers) else len(full_text)
        courses.append({**meta, "text": full_text[start:end]})
    return courses


def course_metadata_of(course: Dict[str, Any]) -> Dict[str, Any]:
    return {k: course.get(k) for k in _METADATA_KEYS}


def extract_course_metadata(full_text: str) -> Dict[str, Any]:
    """
    Extracts course code, title and L-T-P-[J-]C credits of the first course found in the text.
    """
    courses = segment_courses(full_text)
    return course_metadata_of(courses[0]) if courses else _empty_metadata()


def filter_core_courses(
    courses: List[Dict[str, Any]], allowlist: Iterable[str]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Keeps allowlisted courses (first occurrence of each code). Dropped courses carry
    drop_reason "not_in_allowlist" or "duplicate".
    """
    allowed = set(allowlist)
    kept: List[Dict[str, Any]] = []
    dropped: List[Dict[str, Any]] = []
    seen = set()
    for course in courses:
        code = course["course_code"]
        if code not in allowed:
            dropped.append({**course, "drop_reason": "not_in_allowlist"})
        elif code in seen:
            dropped.append({**course, "drop_reason": "duplicate"})
        else:
            seen.add(code)
            kept.append(course)
    return kept, dropped


def find_missing_allowlisted(
    full_text: str, courses: List[Dict[str, Any]], allowlist: Iterable[str]
) -> Tuple[List[str], List[str]]:
    """
    Returns (allowlisted_missing, scanned_courses): allowlisted codes with no detectable syllabus
    header, and the subset the PDF's course catalogue lists (their syllabus pages carry no text layer).
    """
    detected = {c["course_code"] for c in courses}
    catalogue = {m.group("code") for m in _CATALOGUE_ROW.finditer(full_text)}
    missing = [code for code in allowlist if code not in detected]
    scanned = [code for code in missing if code in catalogue]
    return missing, scanned


def extract_depth_signals(
    unit_text: str, course_metadata: Dict[str, Any], module_count: int = 1
) -> Dict[str, Optional[float]]:
    """
    Extracts depth signals available from a syllabus unit:
    - unit_hours: read from the module header line only (the first non-empty line)
    - slide_count
    - lab_hours: the course's practical hours (P per week * semester_weeks) spread evenly
      across the course's module_count modules
    - lab_count
    - assignment_count
    """
    depth_signals = {
        "unit_hours": None,
        "slide_count": None,
        "lab_hours": None,
        "lab_count": None,
        "assignment_count": None
    }

    # Extract unit_hours from the module header line (e.g., "Module:1 Digital Logic 8 hours", "... 6hours")
    header_line = next((line for line in unit_text.splitlines() if line.strip()), "")
    hours_match = re.search(r'\b(\d+)\s*(?:hours|hrs|hour|hr)\b', header_line, re.IGNORECASE)
    if hours_match:
        depth_signals["unit_hours"] = int(hours_match.group(1))

    # Extract slide_count if explicitly mentioned
    slides_match = re.search(r'\b(\d+)\s*(?:slides|slide)\b', unit_text, re.IGNORECASE)
    if slides_match:
        depth_signals["slide_count"] = int(slides_match.group(1))

    # Extract lab_count (e.g., "Experiment 1", "Lab exercise 3", "10 lab experiments")
    lab_exp_matches = re.findall(r'\b(?:experiment|lab exercise|practical task)\s*\d+', unit_text, re.IGNORECASE)
    if lab_exp_matches:
        depth_signals["lab_count"] = len(lab_exp_matches)

    # Course practical hours (P periods/week * semester weeks), spread across the course's modules
    if course_metadata.get("practical_hours"):
        semester_weeks = load_scoring_config()["semester_weeks"]
        depth_signals["lab_hours"] = course_metadata["practical_hours"] * semester_weeks / max(module_count, 1)

    # Extract assignment_count (e.g., "Assignment 1", "Assessment 2")
    assignment_matches = re.findall(r'\b(?:assignment|assessment|project task)\s*\d+', unit_text, re.IGNORECASE)
    if assignment_matches:
        depth_signals["assignment_count"] = len(assignment_matches)

    return depth_signals


def parse_course_modules(course: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Splits one course into modules. A module runs from its "Module:N" header to the next module
    header or the first terminator line (Total Lecture hours, Text Book, Reference Books, Mode of
    Evaluation, Recommended by, Approved by, ...). A course without module headers (e.g. a lab
    course) yields one unit, module_number 0, bounded by the first terminator.
    """
    text = course["text"]
    metadata = course_metadata_of(course)
    headers = list(_MODULE_HEADER.finditer(text))
    modules = []

    def bounded_end(start: int, hard_end: int) -> int:
        terminator = _MODULE_TERMINATOR.search(text, start, hard_end)
        return terminator.start() if terminator else hard_end

    if headers:
        # An embedded course's lab block ("Indicative Experiments") follows the theory terminators;
        # it becomes one extra unit (module_number 0) so its experiments are mapped too.
        lab_block = _LAB_BLOCK_HEADER.search(text, headers[-1].end())
        unit_count = len(headers) + (1 if lab_block else 0)
        for i, match in enumerate(headers):
            module_num = int(match.group(1))
            module_title = _TRAILING_HOURS.sub("", match.group(2)).strip()
            next_start = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            unit_text = text[match.start():bounded_end(match.end(), next_start)].strip()
            modules.append({
                "course_code": course["course_code"],
                "module_number": module_num,
                "module_title": module_title or f"Module {module_num}",
                "unit_text": unit_text,
                "depth_signals": extract_depth_signals(unit_text, metadata, module_count=unit_count),
            })
        if lab_block:
            unit_text = text[lab_block.start():bounded_end(lab_block.end(), len(text))].strip()
            modules.append({
                "course_code": course["course_code"],
                "module_number": 0,
                "module_title": f"{course.get('course_title') or course['course_code']} - Indicative Experiments",
                "unit_text": unit_text,
                "depth_signals": extract_depth_signals(unit_text, metadata, module_count=unit_count),
            })
    else:
        unit_text = text[:bounded_end(0, len(text))].strip()
        modules.append({
            "course_code": course["course_code"],
            "module_number": 0,
            "module_title": course.get("course_title") or "Full Syllabus",
            "unit_text": unit_text,
            "depth_signals": extract_depth_signals(unit_text, metadata),
        })

    return modules


def parse_syllabus_pdf(
    pdf_path: str,
    taxonomy_version: str = DEFAULT_TAXONOMY_VERSION,
    core_courses: Optional[Iterable[str]] = None
) -> Dict[str, Any]:
    """
    Parses a text-selectable VIT syllabus PDF:
    1. Extracts each page's text once; records pages without a text layer. A PDF with no
       extractable text raises UnsupportedPDFError.
    2. Splits the text into courses, then modules. No course header -> UnsupportedPDFError.
    3. Keeps only allowlisted core courses (core_courses, default config syllabus.core_courses);
       none kept -> NoCoreCoursesError.
    4. Maps each module to taxonomy topics via map_source_to_taxonomy preserving taxonomy_version.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        pages_text = [page.extract_text() or "" for page in pdf.pages]

    if sum(len(t.strip()) for t in pages_text) < MIN_TEXT_LENGTH_THRESHOLD:
        raise UnsupportedPDFError(
            f"Unsupported PDF '{os.path.basename(pdf_path)}': Document is a scanned image or contains no extractable text. "
            "OCR processing is excluded from MVP scope."
        )

    full_text = "\n".join(t for t in pages_text if t)
    courses = segment_courses(full_text)
    if not courses:
        raise UnsupportedPDFError(
            f"Unsupported PDF '{os.path.basename(pdf_path)}': no course headers found "
            "(expected a course code, title and L-T-P-C line per course)."
        )

    if core_courses is None:
        core_courses = load_scoring_config()["syllabus"]["core_courses"]
    allowlist = list(core_courses)
    kept, dropped = filter_core_courses(courses, allowlist)
    allowlisted_missing, scanned_courses = find_missing_allowlisted(full_text, courses, allowlist)
    if not kept:
        found = ", ".join(c["course_code"] for c in courses)
        raise NoCoreCoursesError(f"No allowlisted core CS course found in the syllabus. Courses found: {found}.")

    two_pass_mappings = []
    for course in kept:
        for mod in parse_course_modules(course):
            source_id = f"{mod['course_code']}_mod_{mod['module_number']}"
            mapping = map_source_to_taxonomy(
                source_id=source_id,
                raw_text=mod["unit_text"],
                source_type="syllabus",
                taxonomy_version=taxonomy_version
            )
            # Attach depth signals to the mapping output for Phase 8 consumption
            mapping["depth_signals"] = mod["depth_signals"]
            mapping["course_code"] = mod["course_code"]
            mapping["module_number"] = mod["module_number"]
            mapping["module_title"] = mod["module_title"]
            two_pass_mappings.append(mapping)

    return {
        "syllabus_id": os.path.basename(pdf_path),
        "source_type": "syllabus",
        "taxonomy_version": taxonomy_version,
        "course_metadata": course_metadata_of(kept[0]),
        "courses": [course_metadata_of(c) for c in kept],
        "course_filter": {
            "kept": [c["course_code"] for c in kept],
            "dropped": [
                {"course_code": d["course_code"], "course_title": d["course_title"], "drop_reason": d["drop_reason"]}
                for d in dropped
            ],
            "allowlisted_missing": allowlisted_missing,
        },
        "text_layer": {
            "page_count": len(pages_text),
            "pages_without_text": [i + 1 for i, t in enumerate(pages_text) if not page_has_text_layer(t)],
            "scanned_courses": scanned_courses,
        },
        "units_count": len(two_pass_mappings),
        "two_pass_mappings": two_pass_mappings
    }

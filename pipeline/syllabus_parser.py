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

# Course and module headers are short lines, so they are parsed line by line with plain token
# logic (no backtracking regexes) and only on lines up to MAX_HEADER_LINE characters. That keeps
# parsing linear on adversarial text such as tens of thousands of spaces after "L T P C".
MAX_HEADER_LINE = 300
# VIT tabular header line: "BECE102L Digital Systems Design 3 0 0 3", or "... Graph Theory L T P C" with
# the numbers on the next line (optionally after one wrapped title line), or a bare "CODE Title" line
# followed by a numbers line. Must start at the line start, so catalogue rows ("5 BMAT205L ...") never match.
_HEADER_START = re.compile(rf"(?P<code>{_CODE})[ \t]")
_LTPC_MARKERS = (("L", "T", "P", "C"), ("L", "T", "P", "J", "C"))

# Labelled header: "Course Code: CSE2001" / "Course Title: ..." / "L T P J C : 3 0 2 0 4"
_LABELLED_HEADER = re.compile(rf"^[ \t]*Course[ \t]+Code[ \t]*[:\-][ \t]*(?P<code>{_CODE})[ \t]*$", re.MULTILINE)
_LABELLED_TITLE = re.compile(r"(?:Course Title|Course Name)\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE)
# L-T-P-[J-]C marker; the numbers are read from a bounded window right after it, with disjoint classes.
_LTPJC_MARKER = re.compile(r"\bL\s*T\s*P\s*(?:J\s*)?C\b", re.IGNORECASE)
_LTPJC_WINDOW = 120
_LTPJC_NUMBERS = re.compile(r"[\s:\-]*(\d+(?:[ \t\r\n]+\d+){3,4})")

# Catalogue rows: "<sl.no> <code> <title> ..." (used only to tell scanned syllabi from absent ones)
_CATALOGUE_ROW = re.compile(rf"^[ \t]*\d+[ \t]+(?P<code>{_CODE})[ \t]+", re.MULTILINE)

_MODULE_KEYWORD = re.compile(r"[ \t]*(?:Module|Unit)", re.IGNORECASE)
_MODULE_TERMINATOR = re.compile(
    r"^[ \t]*(?:Total[ \t]+Lecture[ \t]+hours|Total[ \t]+Laboratory[ \t]+Hours|Total[ \t]+Tutorial[ \t]+hours|"
    r"Text[ \t]+Book|Reference[ \t]+Book|Mode[ \t]+of[ \t]+(?:Evaluation|assessment)|Recommended[ \t]+by|Approved[ \t]+by)",
    re.IGNORECASE | re.MULTILINE,
)
# Lab block of an embedded (theory + lab) course, placed after the theory terminators.
_LAB_BLOCK_HEADER = re.compile(
    r"^[ \t]*(?:Indicative[ \t]+Experiments|List[ \t]+of[ \t]+Experiments)\b[^\r\n]*$", re.IGNORECASE | re.MULTILINE
)
_TRAILING_HOURS = re.compile(r"\(?\d+[ \t]*(?:hours|hrs|hour|hr)\)?$", re.IGNORECASE)

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


def _lines_with_offsets(text: str) -> List[Tuple[int, str]]:
    """(start offset, line without its line break) for every line of text."""
    lines, pos = [], 0
    for raw in text.splitlines(keepends=True):
        lines.append((pos, raw.rstrip("\r\n")))
        pos += len(raw)
    return lines


def _is_int(token: str) -> bool:
    return token.isascii() and token.isdigit()


def _numbers_line(line: Optional[str]) -> Optional[str]:
    """The line's 4-5 integers ("3 1 0 4"), or None when it is anything else."""
    if line is None or len(line) > MAX_HEADER_LINE:
        return None
    tokens = line.split()
    if 4 <= len(tokens) <= 5 and all(_is_int(t) for t in tokens):
        return " ".join(tokens)
    return None


def _vit_header(lines: List[Tuple[int, str]], i: int) -> Optional[Tuple[str, str, str]]:
    """(code, title, numbers) when line i opens a VIT-format course, else None."""
    line = lines[i][1]
    if len(line) > MAX_HEADER_LINE:
        return None
    m = _HEADER_START.match(line)
    if m is None:
        return None
    tokens = line[m.end():].split()
    if not tokens:
        return None
    nxt = lines[i + 1][1] if i + 1 < len(lines) else None

    # Inline numbers: the shortest non-empty title followed by 4-5 integers (5 preferred).
    trailing = 0
    for token in reversed(tokens):
        if not _is_int(token):
            break
        trailing += 1
    for k in (5, 4):
        if trailing >= k and len(tokens) > k:
            return m.group("code"), " ".join(tokens[:-k]), " ".join(tokens[-k:])

    # "L T P C" marker: numbers on the next line, or after one wrapped title line.
    for marker in _LTPC_MARKERS:
        n = len(marker)
        if len(tokens) > n and tuple(tokens[-n:]) == marker:
            title = " ".join(tokens[:-n])
            numbers = _numbers_line(nxt)
            if numbers:
                return m.group("code"), title, numbers
            cont = (nxt or "").strip()
            if cont and len(cont) <= MAX_HEADER_LINE and not cont[0].isdigit():
                numbers = _numbers_line(lines[i + 2][1] if i + 2 < len(lines) else None)
                if numbers:
                    return m.group("code"), f"{title} {cont}", numbers
            return None

    # Bare "CODE Title" line with the numbers directly on the next line.
    numbers = _numbers_line(nxt)
    if numbers:
        return m.group("code"), " ".join(tokens), numbers
    return None


def _labelled_ltpjc(block: str) -> Optional[str]:
    """Numbers after an "L T P [J] C" marker, read from a bounded window after the marker."""
    marker = _LTPJC_MARKER.search(block)
    if marker is None:
        return None
    numbers = _LTPJC_NUMBERS.match(block[marker.end():marker.end() + _LTPJC_WINDOW])
    return numbers.group(1) if numbers else None


def _find_headers(full_text: str) -> List[Tuple[int, Dict[str, Any]]]:
    """Returns (start offset, metadata) for every course header, in document order."""
    headers: List[Tuple[int, Dict[str, Any]]] = []

    lines = _lines_with_offsets(full_text)
    for i, (start, _) in enumerate(lines):
        found = _vit_header(lines, i)
        if found:
            code, title, numbers = found
            meta = {"course_code": code, "course_title": title}
            meta.update(_ltpjc(numbers))
            headers.append((start, meta))

    vit_starts = sorted(start for start, _ in headers)
    labelled = list(_LABELLED_HEADER.finditer(full_text))
    for i, m in enumerate(labelled):
        # the block ends at the next header of any kind, so a course never reads its neighbour's numbers
        ends = [s for s in vit_starts if s > m.start()][:1]
        ends += [labelled[i + 1].start()] if i + 1 < len(labelled) else []
        end = min(ends) if ends else len(full_text)
        block = full_text[m.end():end]
        meta = _empty_metadata()
        meta["course_code"] = m.group("code")
        title = _LABELLED_TITLE.search(block)
        if title:
            meta["course_title"] = title.group(1).strip()
        numbers = _labelled_ltpjc(block)
        if numbers:
            meta.update(_ltpjc(numbers))
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


def _strip_separator(text: str) -> str:
    text = text.lstrip(" \t")
    if text[:1] in (":", "-"):
        text = text[1:].lstrip(" \t")
    return text


def _module_header(line: str) -> Optional[Tuple[int, str]]:
    """(module number, title) for a "Module:N Title" / "Unit N - Title" line, else None (token logic, no backtracking)."""
    if len(line) > MAX_HEADER_LINE:
        return None
    keyword = _MODULE_KEYWORD.match(line)
    if keyword is None:
        return None
    rest = _strip_separator(line[keyword.end():])
    digits = len(rest) - len(rest.lstrip("0123456789"))
    if digits == 0:
        return None
    title = _strip_separator(rest[digits:]).rstrip()
    trailing_hours = _TRAILING_HOURS.search(title)
    if trailing_hours:
        title = title[:trailing_hours.start()].rstrip()
    return int(rest[:digits]), title


def _module_headers(text: str) -> List[Tuple[int, int, int, str]]:
    """(line start, line end, module number, title) for every module header line in text."""
    found = []
    for start, line in _lines_with_offsets(text):
        header = _module_header(line)
        if header:
            found.append((start, start + len(line), header[0], header[1]))
    return found


def parse_course_modules(course: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Splits one course into modules. A module runs from its "Module:N" header to the next module
    header or the first terminator line (Total Lecture hours, Text Book, Reference Books, Mode of
    Evaluation, Recommended by, Approved by, ...). A course without module headers (e.g. a lab
    course) yields one unit, module_number 0, bounded by the first terminator.
    """
    text = course["text"]
    metadata = course_metadata_of(course)
    headers = _module_headers(text)
    modules = []

    def bounded_end(start: int, hard_end: int) -> int:
        terminator = _MODULE_TERMINATOR.search(text, start, hard_end)
        return terminator.start() if terminator else hard_end

    if headers:
        # An embedded course's lab block ("Indicative Experiments") follows the theory terminators;
        # it becomes one extra unit (module_number 0) so its experiments are mapped too.
        lab_block = _LAB_BLOCK_HEADER.search(text, headers[-1][1])
        unit_count = len(headers) + (1 if lab_block else 0)
        for i, (line_start, line_end, module_num, module_title) in enumerate(headers):
            next_start = headers[i + 1][0] if i + 1 < len(headers) else len(text)
            unit_text = text[line_start:bounded_end(line_end, next_start)].strip()
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
    core_courses: Optional[Iterable[str]] = None,
    max_pages: Optional[int] = None
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
        if max_pages is not None and len(pdf.pages) > max_pages:
            raise UnsupportedPDFError(
                f"Unsupported PDF '{os.path.basename(pdf_path)}': it has {len(pdf.pages)} pages; "
                f"the limit is {max_pages} pages."
            )
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

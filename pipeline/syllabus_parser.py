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

import glob
import re
import os
from typing import Dict, Any, Iterable, List, Optional, Tuple
import pdfplumber

from pipeline.config import load_scoring_config
from pipeline.keyword_abstraction import DEFAULT_TAXONOMY_VERSION
from pipeline.taxonomy_mapper import map_source_to_taxonomy

# Minimum text threshold to detect scanned / non-text PDFs and pages
MIN_TEXT_LENGTH_THRESHOLD = 50
# Words in the VIT course PDFs sit ~2pt apart; pdfplumber's default x_tolerance (3) glues them together.
EXTRACT_X_TOLERANCE = 1.5

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
_TOTAL_LAB_HOURS = re.compile(r"^[ \t]*Total[ \t]+Laboratory[ \t]+Hours[ \t:]*(\d+)", re.IGNORECASE | re.MULTILINE)

# VIT running page lines: "Agenda Item 65/39 - Annexure - 35" (header) and
# "Proceedings of the 65th Academic Council (17.03.2022) 973" (footer).
_RUNNING_LINES = (("Agenda Item", "Annexure"), ("Proceedings of the", "Academic Council"))

_METADATA_KEYS = ("course_code", "course_title", "lecture_hours", "tutorial_hours",
                  "practical_hours", "project_hours", "credits", "ltpc_status")


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


def extract_pages_text(pdf_path: str, max_pages: Optional[int] = None) -> List[str]:
    """Each page's text (EXTRACT_X_TOLERANCE word spacing); "" for a page without a text layer."""
    with pdfplumber.open(pdf_path) as pdf:
        if max_pages is not None and len(pdf.pages) > max_pages:
            raise UnsupportedPDFError(
                f"Unsupported PDF '{os.path.basename(pdf_path)}': it has {len(pdf.pages)} pages; "
                f"the limit is {max_pages} pages."
            )
        return [page.extract_text(x_tolerance=EXTRACT_X_TOLERANCE) or "" for page in pdf.pages]


def strip_running_lines(text: str) -> str:
    """Drops VIT page header/footer lines, which otherwise land inside modules that cross a page break."""
    kept = []
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if any(stripped.startswith(start) and marker in stripped for start, marker in _RUNNING_LINES):
            continue
        kept.append(line)
    return "".join(kept)


def _ltpjc(numbers: Optional[str]) -> Dict[str, Any]:
    """Maps 4 numbers (L T P C) or 5 numbers (L T P J C) to hour/credit fields; None -> all None, "incomplete"."""
    if numbers is None:
        return {"lecture_hours": None, "tutorial_hours": None, "practical_hours": None,
                "project_hours": None, "credits": None, "ltpc_status": "incomplete"}
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
        "ltpc_status": "complete",
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
        "ltpc_status": "incomplete",
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


def _partial_numbers_line(line: Optional[str]) -> bool:
    """True for a line of only 1-3 integers: an L-T-P-C row whose other digits are missing from the text layer."""
    if line is None or len(line) > MAX_HEADER_LINE:
        return False
    tokens = line.split()
    return 1 <= len(tokens) <= 3 and all(_is_int(t) for t in tokens)


def _vit_header(lines: List[Tuple[int, str]], i: int) -> Optional[Tuple[str, str, Optional[str]]]:
    """(code, title, numbers) when line i opens a VIT-format course, else None. numbers is None when the
    "L T P C" row is incomplete (its columns cannot be told apart, so no value is guessed)."""
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
            if _partial_numbers_line(nxt):
                return m.group("code"), title, None
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
        meta.update(_ltpjc(_labelled_ltpjc(block)))
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


def split_experiments(text: str) -> List[str]:
    """
    Splits an "Indicative Experiments" list into one string per experiment. Items are numbered
    1, 2, 3, ... followed by ".", ")" or whitespace; a line that does not carry the next number in the
    sequence (e.g. a wrapped "8 bit and 16 bit variants") continues the previous item.
    """
    # Each item collects its lines and is joined once at the end (appending to a growing string is quadratic).
    items: List[List[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        digits = len(stripped) - len(stripped.lstrip("0123456789"))
        rest = stripped[digits:]
        if 0 < digits <= 2 and int(stripped[:digits]) == len(items) + 1 and rest[:1] in (".", ")", " ", "\t"):
            title = rest[1:].strip() if rest[:1] in (".", ")") else rest.strip()
            if title:
                items.append([title])
                continue
        if items:
            items[-1].append(stripped)
    return [" ".join(parts) for parts in items]


def course_group_of(course_code: str) -> str:
    """The course a theory/lab component belongs to: BCSE202L and BCSE202P -> BCSE202."""
    return course_code[:-1] if course_code[-1:].isalpha() else course_code


def _total_lab_hours(text: str, metadata: Dict[str, Any]) -> Optional[float]:
    """The course's "Total Laboratory Hours", else practical periods/week * semester weeks, else None."""
    stated = _TOTAL_LAB_HOURS.search(text)
    if stated:
        return float(stated.group(1))
    if metadata.get("practical_hours"):
        return float(metadata["practical_hours"] * load_scoring_config()["semester_weeks"])
    return None


def parse_course_modules(course: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Splits one course into units, each tagged with source_id, course_group, component (theory|lab) and
    empty (True when the module has no body text; callers do not map those).
    - Theory modules run from their "Module:N" header to the next module header or the first terminator
      line (Total Lecture hours, Text Book, Reference Books, Mode of Evaluation, Recommended by, ...).
    - A lab-only course (no module headers) becomes one unit per "Indicative Experiments" item:
      lab_hours = the course's lab hours spread across its experiments, and the experiment count is a
      course-level signal (course_signals.lab_count) that scoring counts once per (topic, course).
      Without a readable experiment list it yields one unit bounded by the first terminator.
    - An embedded (theory + lab) course keeps its lab block as one extra unit, module_number 0.
    """
    text = course["text"]
    code = course["course_code"]
    metadata = course_metadata_of(course)
    headers = _module_headers(text)
    group = course_group_of(code)
    modules = []

    def bounded_end(start: int, hard_end: int) -> int:
        terminator = _MODULE_TERMINATOR.search(text, start, hard_end)
        return terminator.start() if terminator else hard_end

    def unit(source_id, number, title, unit_text, component, depth_signals, empty=False, course_signals=None):
        return {
            "source_id": source_id,
            "course_code": code,
            "course_group": group,
            "component": component,
            "module_number": number,
            "module_title": title,
            "unit_text": unit_text,
            "empty": empty,
            "depth_signals": depth_signals,
            "course_signals": course_signals,
        }

    if headers:
        # An embedded course's lab block ("Indicative Experiments") follows the theory terminators;
        # it becomes one extra unit (module_number 0) so its experiments are mapped too.
        lab_block = _LAB_BLOCK_HEADER.search(text, headers[-1][1])
        spans = []
        for i, (line_start, line_end, module_num, module_title) in enumerate(headers):
            next_start = headers[i + 1][0] if i + 1 < len(headers) else len(text)
            end = bounded_end(line_end, next_start)
            spans.append((line_start, end, module_num, module_title, not text[line_end:end].strip()))
        unit_count = sum(1 for span in spans if not span[4]) + (1 if lab_block else 0)
        for line_start, end, module_num, module_title, empty in spans:
            unit_text = text[line_start:end].strip()
            modules.append(unit(
                f"{code}_mod_{module_num}", module_num, module_title or f"Module {module_num}", unit_text, "theory",
                extract_depth_signals(unit_text, metadata, module_count=unit_count), empty=empty,
            ))
        if lab_block:
            unit_text = text[lab_block.start():bounded_end(lab_block.end(), len(text))].strip()
            modules.append(unit(
                f"{code}_mod_0", 0, f"{course.get('course_title') or code} - Indicative Experiments", unit_text, "lab",
                extract_depth_signals(unit_text, metadata, module_count=unit_count),
            ))
        return modules

    lab_block = _LAB_BLOCK_HEADER.search(text)
    experiments = split_experiments(text[lab_block.end():bounded_end(lab_block.end(), len(text))]) if lab_block else []
    if experiments:
        lab_hours = _total_lab_hours(text, metadata)
        per_experiment = lab_hours / len(experiments) if lab_hours is not None else None
        for n, experiment in enumerate(experiments, start=1):
            signals = {"unit_hours": None, "slide_count": None, "lab_hours": per_experiment,
                       "lab_count": None, "assignment_count": None}
            modules.append(unit(f"{code}_exp_{n}", n, experiment, experiment, "lab", signals,
                                course_signals={"lab_count": len(experiments)}))
        return modules

    unit_text = text[:bounded_end(0, len(text))].strip()
    component = "lab" if metadata.get("practical_hours") and not metadata.get("lecture_hours") else "theory"
    modules.append(unit(f"{code}_mod_0", 0, course.get("course_title") or "Full Syllabus", unit_text, component,
                        extract_depth_signals(unit_text, metadata)))
    return modules


def collect_syllabus_pdfs(folder: str, pattern: str = "BCSE*.pdf") -> List[str]:
    """Sorted paths of the PDFs in folder whose names match pattern (default: VIT course syllabi only)."""
    return sorted(glob.glob(os.path.join(glob.escape(folder), pattern)))


def _transcription_for(pdf_path: str, transcriptions_dir: Optional[str]) -> Optional[str]:
    """
    The manual transcription <transcriptions_dir>/<CODE>.txt of a course PDF named "<CODE>_...pdf", without its
    "#" comment lines (provenance notes); None when there is none.
    """
    code = os.path.basename(pdf_path).split("_")[0]
    if not transcriptions_dir or not code.isalnum():
        return None
    path = os.path.join(transcriptions_dir, f"{code}.txt")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return "".join(line for line in f if not line.lstrip().startswith("#"))


def _read_courses(
    pdf_path: str, max_pages: Optional[int], transcription: Optional[str] = None
) -> Tuple[List[str], str, List[Dict[str, Any]], str]:
    """
    (pages_text, full_text, courses, text_source) of one PDF; UnsupportedPDFError when it has no text or no course
    header. A PDF without a text layer is read from its manual transcription when one is given
    (text_source "manual_transcription"; never used for a PDF that has text).
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")
    pages_text = extract_pages_text(pdf_path, max_pages)
    if sum(len(t.strip()) for t in pages_text) >= MIN_TEXT_LENGTH_THRESHOLD:
        text, text_source = "\n".join(t for t in pages_text if t), "pdf"
    elif transcription is not None:
        text, text_source = transcription, "manual_transcription"
    else:
        raise UnsupportedPDFError(
            f"Unsupported PDF '{os.path.basename(pdf_path)}': Document is a scanned image or contains no extractable text. "
            "OCR processing is excluded from MVP scope."
        )
    full_text = strip_running_lines(text)
    courses = segment_courses(full_text)
    if not courses:
        raise UnsupportedPDFError(
            f"Unsupported PDF '{os.path.basename(pdf_path)}': no course headers found "
            "(expected a course code, title and L-T-P-C line per course)."
        )
    return pages_text, full_text, courses, text_source


def _pages_without_text(pages_text: List[str]) -> List[int]:
    return [i + 1 for i, t in enumerate(pages_text) if not page_has_text_layer(t)]


def _allowlist(core_courses: Optional[Iterable[str]]) -> List[str]:
    if core_courses is None:
        core_courses = load_scoring_config()["syllabus"]["core_courses"]
    return list(core_courses)


def _filter_or_raise(
    courses: List[Dict[str, Any]], full_text: str, allowlist: List[str]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[str]]:
    """(kept courses, course_filter report, scanned_courses); NoCoreCoursesError when nothing is kept."""
    kept, dropped = filter_core_courses(courses, allowlist)
    allowlisted_missing, scanned_courses = find_missing_allowlisted(full_text, courses, allowlist)
    if not kept:
        found = ", ".join(c["course_code"] for c in courses)
        raise NoCoreCoursesError(f"No allowlisted core CS course found in the syllabus. Courses found: {found}.")
    course_filter = {
        "kept": [c["course_code"] for c in kept],
        "dropped": [
            {"course_code": d["course_code"], "course_title": d["course_title"], "drop_reason": d["drop_reason"]}
            for d in dropped
        ],
        "allowlisted_missing": allowlisted_missing,
    }
    return kept, course_filter, scanned_courses


def _course_component(units: List[Dict[str, Any]]) -> str:
    components = {u["component"] for u in units}
    return components.pop() if len(components) == 1 else "embedded"


def _map_courses(kept: List[Dict[str, Any]], taxonomy_version: str):
    """
    Maps every non-empty unit of the kept courses to taxonomy topics via map_source_to_taxonomy
    (preserving taxonomy_version). Returns (mappings, skipped_modules, course records).
    """
    mappings, skipped, records = [], [], []
    for course in kept:
        source_file = course.get("source_file")
        units = parse_course_modules(course)
        for mod in units:
            if mod["empty"]:
                skipped.append({"course_code": mod["course_code"], "module_number": mod["module_number"],
                                "module_title": mod["module_title"], "source_file": source_file, "reason": "no_body"})
                continue
            mapping = map_source_to_taxonomy(
                source_id=mod["source_id"],
                raw_text=mod["unit_text"],
                source_type="syllabus",
                taxonomy_version=taxonomy_version
            )
            # Attach depth signals and unit tags to the mapping output for Phase 8 consumption
            for key in ("depth_signals", "course_signals", "course_code", "course_group", "component",
                        "module_number", "module_title"):
                mapping[key] = mod[key]
            mapping["source_file"] = source_file
            mappings.append(mapping)
        mapped = [u for u in units if not u["empty"]]
        lab_hours = [u["depth_signals"]["lab_hours"] for u in mapped if u["depth_signals"]["lab_hours"] is not None]
        experiments = [u for u in mapped if u["source_id"].startswith(f"{course['course_code']}_exp_")]
        records.append({
            **course_metadata_of(course),
            "course_group": course_group_of(course["course_code"]),
            "component": _course_component(units),
            "source_file": source_file,
            "text_source": course.get("text_source", "pdf"),
            "experiment_count": len(experiments) or None,
            "lab_hours_total": round(sum(lab_hours), 4) if lab_hours else None,
        })
    return mappings, skipped, records


def _course_groups(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """One entry per course group, pairing its theory (or embedded) and lab components."""
    by_code = {r["course_code"]: r for r in records}
    groups: Dict[str, Dict[str, Any]] = {}
    for record in records:
        group = groups.setdefault(record["course_group"], {
            "course_group": record["course_group"], "course_title": None, "theory": None, "lab": None})
        slot = "lab" if record["component"] == "lab" else "theory"
        group[slot] = group[slot] or record["course_code"]
    for group in groups.values():
        if group["theory"]:
            group["course_title"] = by_code[group["theory"]]["course_title"]
        else:
            title = by_code[group["lab"]]["course_title"]
            group["course_title"] = title[:-4] if title.endswith(" Lab") else title
    return list(groups.values())


def _result(syllabus_id, taxonomy_version, kept, course_filter, records, mappings, skipped, text_layer):
    return {
        "syllabus_id": syllabus_id,
        "source_type": "syllabus",
        "taxonomy_version": taxonomy_version,
        "course_metadata": course_metadata_of(kept[0]),
        "courses": records,
        "course_groups": _course_groups(records),
        "course_filter": course_filter,
        "text_layer": text_layer,
        "skipped_modules": skipped,
        "units_count": len(mappings),
        "two_pass_mappings": mappings
    }


def parse_syllabus_pdf(
    pdf_path: str,
    taxonomy_version: str = DEFAULT_TAXONOMY_VERSION,
    core_courses: Optional[Iterable[str]] = None,
    max_pages: Optional[int] = None
) -> Dict[str, Any]:
    """
    Parses one text-selectable VIT syllabus PDF:
    1. Extracts each page's text once; records pages without a text layer. A PDF with no
       extractable text raises UnsupportedPDFError.
    2. Drops running page lines, splits the text into courses, then units. No course header -> UnsupportedPDFError.
    3. Keeps only allowlisted core courses (core_courses, default config syllabus.core_courses);
       none kept -> NoCoreCoursesError.
    4. Maps each non-empty unit to taxonomy topics via map_source_to_taxonomy preserving taxonomy_version;
       body-less modules are listed in skipped_modules.
    """
    pages_text, full_text, courses, _ = _read_courses(pdf_path, max_pages)
    kept, course_filter, scanned_courses = _filter_or_raise(courses, full_text, _allowlist(core_courses))
    mappings, skipped, records = _map_courses(kept, taxonomy_version)
    text_layer = {
        "page_count": len(pages_text),
        "pages_without_text": _pages_without_text(pages_text),
        "scanned_courses": scanned_courses,
    }
    return _result(os.path.basename(pdf_path), taxonomy_version, kept, course_filter, records, mappings, skipped,
                   text_layer)


def parse_syllabus_pdfs(
    pdf_paths: Iterable[str],
    syllabus_id: str,
    taxonomy_version: str = DEFAULT_TAXONOMY_VERSION,
    core_courses: Optional[Iterable[str]] = None,
    max_pages: Optional[int] = None,
    transcriptions_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Builds ONE combined syllabus from several course PDFs (e.g. a theory BCSE202L and its lab BCSE202P).
    Each file is read and segmented on its own; the courses are merged and the allowlist/duplicate filter
    runs once over all of them. A file without text or course headers is recorded in file_errors and the
    others are still scored; no readable file -> UnsupportedPDFError, no core course -> NoCoreCoursesError.
    A PDF without a text layer is read from transcriptions_dir/<CODE>.txt when that manual transcription exists.
    Same schema as parse_syllabus_pdf plus source_files, file_errors and per-file text_layer.files.
    """
    paths = list(pdf_paths)
    courses, texts, files, file_errors = [], [], [], []
    for path in paths:
        name = os.path.basename(path)
        try:
            pages_text, full_text, file_courses, text_source = _read_courses(
                path, max_pages, _transcription_for(path, transcriptions_dir))
        except UnsupportedPDFError as err:
            file_errors.append({"file": name, "error": str(err)})
            continue
        for course in file_courses:
            course["source_file"] = name
            course["text_source"] = text_source
        courses.extend(file_courses)
        texts.append(full_text)
        files.append({"file": name, "page_count": len(pages_text), "pages_without_text": _pages_without_text(pages_text),
                      "text_source": text_source})
    if not courses:
        raise UnsupportedPDFError(
            "No readable course syllabus in: " + ", ".join(os.path.basename(p) for p in paths) + ". "
            + " ".join(e["error"] for e in file_errors)
        )

    kept, course_filter, scanned_courses = _filter_or_raise(courses, "\n".join(texts), _allowlist(core_courses))
    mappings, skipped, records = _map_courses(kept, taxonomy_version)
    text_layer = {
        "page_count": sum(f["page_count"] for f in files),
        "pages_without_text": [f"{f['file']} p{n}" for f in files for n in f["pages_without_text"]],
        "scanned_courses": scanned_courses,
        "files": files,
    }
    result = _result(syllabus_id, taxonomy_version, kept, course_filter, records, mappings, skipped, text_layer)
    result["source_files"] = [os.path.basename(p) for p in paths]
    result["file_errors"] = file_errors
    return result

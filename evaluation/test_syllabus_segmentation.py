"""
Item 1: split a syllabus PDF into courses (code + title + L-T-P-[J-]C), then modules
within each course, and keep only allowlisted core CS courses.

Fixture texts follow the layout of the real VIT B.Tech CSE 2024-25 PDF. Tests pass
their own allowlist; the real one lives in config/scoring_v1.0.json.
"""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

import backend.routes as routes
from backend.app import app
from pipeline.syllabus_parser import (
    NoCoreCoursesError,
    UnsupportedPDFError,
    filter_core_courses,
    find_missing_allowlisted,
    page_has_text_layer,
    parse_course_modules,
    parse_syllabus_pdf,
    segment_courses,
)

VIT_TWO_COURSES = """Course Code Course Title L T P C
BCSE202L Data Structures and Algorithms 3 0 0 3
Pre-requisite NIL Syllabus version
1.0
Course Objectives
1. Learn the objectives text that must not be mapped.
Module:1 Introduction to Data Structures 7 hours
Arrays, linked lists and stacks.
Module:2 Trees 8hours
Binary search trees and AVL trees.
Total Lecture hours: 45 hours
Text Book(s)
1. Cormen, Introduction to Algorithms
Recommended by Board of Studies 03.07.2021
Approved by Academic Council No. 63 Date 23.09.2021
BMAT205L Discrete Mathematics and Graph Theory L T P C
3 1 0 4
Pre-requisite NIL Syllabus Version
Module:1 Mathematical Logic 7 hours
Statements and connectives.
Total Lecture hours: 45 hours
"""

CATALOGUE_PAGE = """Discipline Core
sl.no Course Code Course Title Course Type Ver L T P J Credits
1 BCSE202L Data Structures and Algorithms Theory Only 1.0 3 0 0 0 3.0
2 BCSE202P Data Structures and Algorithms Lab Lab Only 1.0 0 0 2 0 1.0
5 BMAT205L Discrete Mathematics and Graph Theory Theory Only 1.0 3 1 0 0 4.0
"""

LAB_COURSE = """BCSE202P Data Structures and Algorithms Lab L T P C
0 0 2 1
Indicative Experiments
1. Implement a stack using arrays 2 hours
2. Implement a queue using linked lists 2 hours
Total Laboratory Hours 30 hours
Mode of assessment: Continuous assessment
"""


def _by_code(courses):
    return {c["course_code"]: c for c in courses}


def test_segments_inline_and_nextline_ltpc():
    courses = _by_code(segment_courses(VIT_TWO_COURSES))
    assert list(courses) == ["BCSE202L", "BMAT205L"]
    dsa = courses["BCSE202L"]
    assert dsa["course_title"] == "Data Structures and Algorithms"
    assert (dsa["lecture_hours"], dsa["tutorial_hours"], dsa["practical_hours"], dsa["credits"]) == (3, 0, 0, 3)
    assert dsa["project_hours"] is None
    dm = courses["BMAT205L"]
    assert dm["course_title"] == "Discrete Mathematics and Graph Theory"
    assert (dm["lecture_hours"], dm["tutorial_hours"], dm["practical_hours"], dm["credits"]) == (3, 1, 0, 4)
    assert "Statements and connectives" in dm["text"]
    assert "Statements and connectives" not in dsa["text"]


def test_ltpjc_five_numbers():
    course = segment_courses("BCSE101E Computer Programming: Python 1 0 4 0 3\nModule:1 Basics 4 hours\nx\n")[0]
    assert course["course_title"] == "Computer Programming: Python"
    assert (course["lecture_hours"], course["tutorial_hours"], course["practical_hours"],
            course["project_hours"], course["credits"]) == (1, 0, 4, 0, 3)


def test_wrapped_title_header():
    text = ("BCSE319L PENETRATION TESTING AND VULNERABILITY L T P C\nANALYSIS\n2 0 0 2\n"
            "Pre-requisite NIL Syllabus version\nModule:1 Introduction 4 hours\nScanning tools.\n")
    course = segment_courses(text)[0]
    assert course["course_title"] == "PENETRATION TESTING AND VULNERABILITY ANALYSIS"
    assert (course["lecture_hours"], course["tutorial_hours"], course["practical_hours"], course["credits"]) == (2, 0, 0, 2)


def test_bare_title_with_numbers_on_next_line():
    text = "BCSE399J Summer Industrial Internship\n0 0 0 1\nPre-requisite NIL Syllabus version\n1.0\n"
    course = segment_courses(text)[0]
    assert course["course_code"] == "BCSE399J"
    assert course["course_title"] == "Summer Industrial Internship"
    assert course["credits"] == 1


def test_catalogue_rows_not_courses():
    assert segment_courses(CATALOGUE_PAGE) == []


def test_labelled_header_format():
    text = """
    Course Code: CSE2001
    Course Title: Data Structures and Algorithms
    L T P J C : 3 0 2 0 4
    Module: 1 Stacks and Queues (6 hours)
    Stack operations.
    """
    course = segment_courses(text)[0]
    assert course["course_code"] == "CSE2001"
    assert course["course_title"] == "Data Structures and Algorithms"
    assert (course["lecture_hours"], course["practical_hours"], course["project_hours"], course["credits"]) == (3, 2, 0, 4)


def test_module_bounded_by_terminators():
    dsa = _by_code(segment_courses(VIT_TWO_COURSES))["BCSE202L"]
    modules = parse_course_modules(dsa)
    assert [m["module_number"] for m in modules] == [1, 2]
    assert [m["module_title"] for m in modules] == ["Introduction to Data Structures", "Trees"]
    assert all(m["course_code"] == "BCSE202L" for m in modules)
    assert "Learn the objectives" not in modules[0]["unit_text"]
    last = modules[1]["unit_text"]
    assert "AVL trees" in last
    for boilerplate in ("Total Lecture hours", "Text Book", "Cormen", "Approved by Academic Council"):
        assert boilerplate not in last


def test_lab_course_without_modules_single_unit():
    lab = segment_courses(LAB_COURSE)[0]
    modules = parse_course_modules(lab)
    assert len(modules) == 1
    assert modules[0]["module_number"] == 0
    assert modules[0]["module_title"] == "Data Structures and Algorithms Lab"
    assert "Implement a stack" in modules[0]["unit_text"]
    assert "Mode of assessment" not in modules[0]["unit_text"]


def test_filter_core_courses():
    courses = segment_courses(VIT_TWO_COURSES)
    kept, dropped = filter_core_courses(courses, ["BCSE202L"])
    assert [c["course_code"] for c in kept] == ["BCSE202L"]
    assert [(d["course_code"], d["drop_reason"]) for d in dropped] == [("BMAT205L", "not_in_allowlist")]


def test_duplicate_course_dropped():
    courses = segment_courses(VIT_TWO_COURSES + VIT_TWO_COURSES)
    kept, dropped = filter_core_courses(courses, ["BCSE202L", "BMAT205L"])
    assert [c["course_code"] for c in kept] == ["BCSE202L", "BMAT205L"]
    assert [(d["course_code"], d["drop_reason"]) for d in dropped] == [
        ("BCSE202L", "duplicate"), ("BMAT205L", "duplicate")
    ]


def test_allowlisted_missing_reported():
    full_text = CATALOGUE_PAGE + VIT_TWO_COURSES
    courses = segment_courses(full_text)
    missing, scanned = find_missing_allowlisted(full_text, courses, ["BCSE202L", "BCSE202P", "BCSE999L"])
    assert missing == ["BCSE202P", "BCSE999L"]
    # only courses the catalogue lists but whose syllabus never appears count as scanned
    assert scanned == ["BCSE202P"]


def test_page_has_text_layer():
    assert page_has_text_layer("x" * 60)
    assert not page_has_text_layer("   Fountation Core   ")
    assert not page_has_text_layer("")


# --- PDF-level behaviour ---------------------------------------------------

@pytest.fixture
def tmpdir_path():
    with tempfile.TemporaryDirectory() as d:
        yield d


def _course_page(c, code, title, module_title, body, y=750):
    c.drawString(100, y, f"Course Code: {code}")
    c.drawString(100, y - 15, f"Course Title: {title}")
    c.drawString(100, y - 30, "L T P J C : 3 0 2 0 4")
    c.drawString(100, y - 60, f"Module: 1 {module_title} (6 hours)")
    c.drawString(100, y - 75, body)


def test_two_course_pdf_keeps_allowlisted_only(tmpdir_path):
    path = os.path.join(tmpdir_path, "two_courses.pdf")
    c = canvas.Canvas(path)
    _course_page(c, "CSE2001", "Data Structures and Algorithms", "Stacks and Queues", "Stack and queue operations.")
    c.showPage()
    _course_page(c, "CSE3001", "Software Engineering", "Process Models", "Waterfall and agile process models.")
    c.save()

    result = parse_syllabus_pdf(path, core_courses=["CSE2001"])
    assert {m["source_id"] for m in result["two_pass_mappings"]} == {"CSE2001_mod_1"}
    assert result["course_filter"]["kept"] == ["CSE2001"]
    assert result["course_filter"]["dropped"] == [
        {"course_code": "CSE3001", "course_title": "Software Engineering", "drop_reason": "not_in_allowlist"}
    ]
    assert result["course_metadata"]["course_code"] == "CSE2001"
    assert [c["course_code"] for c in result["courses"]] == ["CSE2001"]


def test_text_layer_detection_per_page(tmpdir_path):
    path = os.path.join(tmpdir_path, "with_blank_page.pdf")
    c = canvas.Canvas(path)
    _course_page(c, "CSE2001", "Data Structures and Algorithms", "Stacks and Queues", "Stack and queue operations.")
    c.showPage()
    c.showPage()  # page 2: no text layer (stands in for a scanned page)
    c.save()

    result = parse_syllabus_pdf(path, core_courses=["CSE2001", "CSE2002"])
    assert result["text_layer"]["page_count"] == 2
    assert result["text_layer"]["pages_without_text"] == [2]
    assert result["course_filter"]["allowlisted_missing"] == ["CSE2002"]


def test_no_headers_raises_unsupported(tmpdir_path):
    path = os.path.join(tmpdir_path, "no_headers.pdf")
    c = canvas.Canvas(path)
    c.drawString(100, 750, "This document has plenty of selectable text but no course header at all.")
    c.save()
    with pytest.raises(UnsupportedPDFError, match="no course headers"):
        parse_syllabus_pdf(path, core_courses=["CSE2001"])


def test_nothing_kept_raises(tmpdir_path):
    path = os.path.join(tmpdir_path, "one_course.pdf")
    c = canvas.Canvas(path)
    _course_page(c, "CSE2001", "Data Structures and Algorithms", "Stacks and Queues", "Stack and queue operations.")
    c.save()
    with pytest.raises(NoCoreCoursesError, match="CSE2001"):
        parse_syllabus_pdf(path, core_courses=["XYZ999"])


def test_api_returns_400_when_no_core_courses(tmpdir_path):
    path = os.path.join(tmpdir_path, "one_course.pdf")
    c = canvas.Canvas(path)
    _course_page(c, "CSE2001", "Data Structures and Algorithms", "Stacks and Queues", "Stack and queue operations.")
    c.save()
    app.dependency_overrides[routes.get_core_courses] = lambda: ["XYZ999"]
    try:
        with open(path, "rb") as f:
            response = TestClient(app).post(
                "/api/v1/syllabi/upload", files={"file": ("one_course.pdf", f, "application/pdf")}
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 400
    assert "CSE2001" in response.json()["detail"]

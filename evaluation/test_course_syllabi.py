"""
Course-syllabi run: individual VIT course PDFs (BCSE<code>L = theory, BCSE<code>P = lab) scored as one
combined syllabus (docs/superpowers/specs/2026-10-21-course-syllabi-design.md).

Fixture texts follow the layout of the real 2024-25 course PDFs in data/raw/syllabi/.
"""
import pytest
from reportlab.pdfgen import canvas

from pipeline.syllabus_parser import (
    extract_pages_text,
    parse_course_modules,
    segment_courses,
    split_experiments,
    strip_running_lines,
)

THEORY = """BCSE202L Data Structures and Algorithms L T P C
3 0 0 3
Pre-requisite NIL Syllabus version
1.0
Course Objectives
1. To impart basic concepts of data structures and algorithms.
Module:1 Algorithm Analysis 8 hours
Space and time complexity of an algorithm.
Module:2 Linear Data Structures 7 hours
Arrays, stacks, queues and linked lists.
Module:3 Contemporary Issues 2 hours
Total Lecture hours: 45 hours
Text Book
1. Mark A. Weiss, Data Structures & Algorithm Analysis in C++
"""

LAB = """BCSE202P Data Structures and Algorithms Lab L T P C
0 0 2 1
Pre-requisite NIL Syllabus version
1.0
Course Objectives
1. To impart basic concepts of data structures and algorithms.
Course Outcomes
1. Apply appropriate data structures to find solutions to practical problems.
Indicative Experiments
1. Implementation of stack data structure and its applications
2. Implementation of queue data structure and its applications
3. Graph Traversal - Depth First Search and Breadth First Search algorithm
4. Single Source Shortest Path Algorithm - Dijkstra's algorithm
Total Laboratory Hours 30 hours
Text Book
1. Mark A. Weiss, Data Structures & Algorithm Analysis in C++, 2013, 4th Edition,
Mode of assessment: Continuous assessments and FAT.
"""

# BCSE204P: items 6-11 have no period after the number; item 2 wraps onto a second line.
DAA_EXPERIMENTS = """1. Greedy Strategy : Activity Selection & Huffman coding
2. Dynamic Programming : ALS, Matrix Chain Multiplication , Longest Common
Subsequence, 0-1 Knapsack
3. Divide and Conquer : Maximum Subarray and Karatsuba faster integer multiplication
algorithm
4. Backtracking: N-queens
5. Branch and Bound: Job selection
6 String matching algorithms : Naive, KMP and Rabin Karp,suffix trees
7 MST and all pair shortest path algorithms
8 Network Flows : Ford -Fulkerson and Edmond -Karp
9 Intersection of line segments &Finding Convexhull, Finding closest pair of points
10 Polynomial time algorithm for verification of NPC problems
11 Approximation and Randomized algorithms
"""


# --- running page lines -----------------------------------------------------

def test_strip_running_lines_removes_vit_page_header_and_footer():
    text = ("Agenda Item 65/39 - Annexure - 35\n"
            "Module:8 Contemporary Issues 2 hours\n"
            "Proceedings of the 65th Academic Council (17.03.2022) 992\n"
            "Agenda Item 65/39 - Annexure - 35\n"
            "Total Lecture hours: 45 hours\n"
            "Approved by Academic Council No. 65 Date 17-03-2022\n")
    assert strip_running_lines(text) == ("Module:8 Contemporary Issues 2 hours\n"
                                         "Total Lecture hours: 45 hours\n"
                                         "Approved by Academic Council No. 65 Date 17-03-2022\n")


# --- headers ----------------------------------------------------------------

def test_complete_ltpc_header_status():
    course = segment_courses(THEORY)[0]
    assert (course["lecture_hours"], course["tutorial_hours"], course["practical_hours"], course["credits"]) == (3, 0, 0, 3)
    assert course["ltpc_status"] == "complete"


def test_incomplete_ltpc_header_recognised_without_guessing():
    # BCSE205L: the PDF's text layer holds only "3" (under L) and "0" (under P).
    text = ("BCSE205L Computer Architecture and Organization L T P C\n3 0\n"
            "Pre-requisite NIL Syllabus Version\nModule:1 Introduction 5 Hours\nVon Neumann architecture.\n")
    course = segment_courses(text)[0]
    assert course["course_code"] == "BCSE205L"
    assert course["course_title"] == "Computer Architecture and Organization"
    assert course["ltpc_status"] == "incomplete"
    for key in ("lecture_hours", "tutorial_hours", "practical_hours", "project_hours", "credits"):
        assert course[key] is None, key


# --- experiments ------------------------------------------------------------

def test_split_experiments_mixed_numbering():
    experiments = split_experiments(DAA_EXPERIMENTS)
    assert len(experiments) == 11
    assert experiments[1] == ("Dynamic Programming : ALS, Matrix Chain Multiplication , Longest Common "
                              "Subsequence, 0-1 Knapsack")
    assert experiments[5].startswith("String matching algorithms")
    assert experiments[10] == "Approximation and Randomized algorithms"


def test_wrapped_line_starting_with_a_number_is_not_a_new_experiment():
    experiments = split_experiments("1. Implement adders\n8 bit and 16 bit variants\n2. Implement an ALU\n")
    assert experiments == ["Implement adders 8 bit and 16 bit variants", "Implement an ALU"]


def test_lab_course_becomes_one_unit_per_experiment():
    units = parse_course_modules(segment_courses(LAB)[0])
    assert [u["source_id"] for u in units] == [f"BCSE202P_exp_{n}" for n in (1, 2, 3, 4)]
    assert [u["module_number"] for u in units] == [1, 2, 3, 4]
    assert {u["component"] for u in units} == {"lab"}
    assert {u["course_group"] for u in units} == {"BCSE202"}
    assert "Dijkstra" in units[3]["unit_text"]
    for unit in units:
        for excluded in ("Course Objectives", "Apply appropriate", "Total Laboratory", "Weiss"):
            assert excluded not in unit["unit_text"]


def test_lab_hours_spread_across_experiments_and_lab_count_once_per_course():
    units = parse_course_modules(segment_courses(LAB)[0])
    assert [u["depth_signals"]["lab_hours"] for u in units] == [7.5] * 4  # Total Laboratory Hours 30 / 4
    assert sum(u["depth_signals"]["lab_hours"] for u in units) == 30
    assert all(u["depth_signals"]["lab_count"] is None for u in units)
    assert all(u["course_signals"] == {"lab_count": 4} for u in units)


def test_lab_hours_fall_back_to_practical_periods_times_weeks():
    units = parse_course_modules(segment_courses(LAB.replace("Total Laboratory Hours 30 hours\n", ""))[0])
    assert [u["depth_signals"]["lab_hours"] for u in units] == [2 * 15 / 4] * 4


# --- theory modules ---------------------------------------------------------

def test_theory_modules_tagged_and_empty_module_flagged():
    units = parse_course_modules(segment_courses(THEORY)[0])
    assert [u["source_id"] for u in units] == ["BCSE202L_mod_1", "BCSE202L_mod_2", "BCSE202L_mod_3"]
    assert {u["component"] for u in units} == {"theory"}
    assert {u["course_group"] for u in units} == {"BCSE202"}
    assert [u["empty"] for u in units] == [False, False, True]
    assert [u["depth_signals"]["unit_hours"] for u in units] == [8, 7, 2]
    assert all(u["depth_signals"]["lab_hours"] is None for u in units)
    assert all(u.get("course_signals") is None for u in units)


# --- extraction ---------------------------------------------------------------

def test_extraction_separates_closely_spaced_words(tmp_path):
    # The real PDFs place words ~2pt apart, which pdfplumber's default x_tolerance (3) glues together.
    path = str(tmp_path / "tight.pdf")
    c = canvas.Canvas(path)
    x = 100.0
    for word in ("Data", "Structures", "and", "Algorithms"):
        c.drawString(x, 750, word)
        x += c.stringWidth(word, "Helvetica", 12) + 2.0
    c.save()
    assert extract_pages_text(path)[0].strip() == "Data Structures and Algorithms"


# --- scoring: course-level signals -------------------------------------------

NODES = [{"topic_id": "t", "name": "T", "type": "high_level_concept"}]


def _experiment(course_code, n, lab_count):
    return {"source_id": f"{course_code}_exp_{n}", "course_code": course_code, "matched_topic_ids": ["t"],
            "depth_signals": {"unit_hours": None, "slide_count": None, "lab_hours": 3.0, "lab_count": None,
                              "assignment_count": None},
            "course_signals": {"lab_count": lab_count}}


def _topic(mappings):
    from pipeline.scoring import calculate_syllabus_coverage
    result = calculate_syllabus_coverage({"two_pass_mappings": mappings}, taxonomy_nodes=NODES)
    return result["topic_coverage"][0]


def test_lab_count_counted_once_per_course():
    # three experiments of one lab match t: three lab_hours signals, one lab_count signal
    topic = _topic([_experiment("BCSE202P", n, 10) for n in (1, 2, 3)])
    assert topic["depth_signal_count"] == 4
    # N: lab_hours 3/10 = 0.3 (x3), lab_count min(10/5, 1) = 1.0 -> D_norm 0.475 -> D = 1 + 4 * 0.475
    assert topic["depth"] == pytest.approx(2.9)


def test_lab_count_counted_again_for_another_course():
    topic = _topic([_experiment("BCSE202P", 1, 10), _experiment("BCSE202P", 2, 10), _experiment("BCSE204P", 1, 11)])
    assert topic["depth_signal_count"] == 5


def test_api_cache_keeps_course_signals():
    import backend.routes as routes
    parsed = {"syllabus_id": "s", "two_pass_mappings": [_experiment("BCSE202P", 1, 10)]}
    routes._cache_syllabus("test_course_signals", parsed)
    try:
        cached = routes.SYLLABUS_CACHE["test_course_signals"]["two_pass_mappings"][0]
        assert cached["course_signals"] == {"lab_count": 10}
    finally:
        routes.SYLLABUS_CACHE.pop("test_course_signals", None)

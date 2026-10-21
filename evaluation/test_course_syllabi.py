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


# --- combined syllabus from several PDFs ---------------------------------------

from pipeline.syllabus_parser import (  # noqa: E402
    NoCoreCoursesError,
    UnsupportedPDFError,
    collect_syllabus_pdfs,
    parse_syllabus_pdf,
    parse_syllabus_pdfs,
)

CORE = ["BCSE202L", "BCSE202P"]


def _write_pdf(path, pages):
    c = canvas.Canvas(str(path))
    for lines in pages:
        for i, line in enumerate(lines):
            c.drawString(72, 780 - 14 * i, line)
        c.showPage()
    c.save()
    return str(path)


def _theory_pdf(tmp_path, name="BCSE202L_DSA_TH.pdf"):
    # Module 3 has no body: only the page footer and the next page's header follow it.
    page1 = THEORY.split("Total Lecture hours")[0].splitlines() + [
        "Proceedings of the 65th Academic Council (17.03.2022) 973"]
    page2 = ["Agenda Item 65/39 - Annexure - 35", "Total Lecture hours: 45 hours", "Text Book",
             "1. Mark A. Weiss, Data Structures & Algorithm Analysis in C++"]
    return _write_pdf(tmp_path / name, [["Agenda Item 65/39 - Annexure - 35"] + page1, page2])


def _lab_pdf(tmp_path, name="BCSE202P_DSA_LAB.pdf"):
    return _write_pdf(tmp_path / name, [["Agenda Item 65/39 - Annexure - 35"] + LAB.splitlines()])


def test_parse_syllabus_pdfs_builds_one_combined_syllabus(tmp_path):
    theory, lab = _theory_pdf(tmp_path), _lab_pdf(tmp_path)
    result = parse_syllabus_pdfs([theory, lab], syllabus_id="VIT_CSE_2024_25_courses", core_courses=CORE)

    assert result["syllabus_id"] == "VIT_CSE_2024_25_courses"
    assert result["source_files"] == ["BCSE202L_DSA_TH.pdf", "BCSE202P_DSA_LAB.pdf"]
    assert result["file_errors"] == []
    mappings = result["two_pass_mappings"]
    assert [m["source_id"] for m in mappings] == [
        "BCSE202L_mod_1", "BCSE202L_mod_2", "BCSE202P_exp_1", "BCSE202P_exp_2", "BCSE202P_exp_3", "BCSE202P_exp_4"]
    assert result["units_count"] == 6
    assert {m["course_group"] for m in mappings} == {"BCSE202"}
    assert [m["component"] for m in mappings] == ["theory"] * 2 + ["lab"] * 4
    assert {m["source_file"] for m in mappings if m["component"] == "lab"} == {"BCSE202P_DSA_LAB.pdf"}
    assert all(m["course_signals"] == {"lab_count": 4} for m in mappings if m["component"] == "lab")
    assert all(m["course_signals"] is None for m in mappings if m["component"] == "theory")
    assert result["skipped_modules"] == [{"course_code": "BCSE202L", "module_number": 3,
                                          "module_title": "Contemporary Issues", "source_file": "BCSE202L_DSA_TH.pdf",
                                          "reason": "no_body"}]
    assert result["course_groups"] == [{"course_group": "BCSE202", "course_title": "Data Structures and Algorithms",
                                        "theory": "BCSE202L", "lab": "BCSE202P"}]
    lab_course = next(c for c in result["courses"] if c["course_code"] == "BCSE202P")
    assert (lab_course["experiment_count"], lab_course["lab_hours_total"]) == (4, 30.0)
    assert result["text_layer"]["page_count"] == 3
    assert [f["file"] for f in result["text_layer"]["files"]] == result["source_files"]
    assert result["course_filter"]["allowlisted_missing"] == []


def test_unreadable_file_is_recorded_and_the_rest_scored(tmp_path):
    blank = _write_pdf(tmp_path / "BCSE999L_scanned.pdf", [[]])
    result = parse_syllabus_pdfs([blank, _lab_pdf(tmp_path)], syllabus_id="s", core_courses=CORE)
    assert [e["file"] for e in result["file_errors"]] == ["BCSE999L_scanned.pdf"]
    assert "no extractable text" in result["file_errors"][0]["error"]
    assert result["course_filter"]["kept"] == ["BCSE202P"]
    assert result["course_filter"]["allowlisted_missing"] == ["BCSE202L"]


def test_duplicate_file_keeps_source_ids_unique(tmp_path):
    lab, copy = _lab_pdf(tmp_path), _lab_pdf(tmp_path, "BCSE202P_DSA_LAB (1).pdf")
    result = parse_syllabus_pdfs([lab, copy], syllabus_id="s", core_courses=CORE)
    ids = [m["source_id"] for m in result["two_pass_mappings"]]
    assert len(ids) == len(set(ids)) == 4
    assert result["course_filter"]["dropped"] == [
        {"course_code": "BCSE202P", "course_title": "Data Structures and Algorithms Lab", "drop_reason": "duplicate"}]


def test_no_core_course_in_any_file_raises(tmp_path):
    with pytest.raises(NoCoreCoursesError, match="BCSE202P"):
        parse_syllabus_pdfs([_lab_pdf(tmp_path)], syllabus_id="s", core_courses=["XYZ999"])


def test_all_files_unreadable_raises(tmp_path):
    blank = _write_pdf(tmp_path / "blank.pdf", [[]])
    with pytest.raises(UnsupportedPDFError, match="blank.pdf"):
        parse_syllabus_pdfs([blank], syllabus_id="s", core_courses=CORE)


def test_single_pdf_parse_skips_empty_modules_and_tags_units(tmp_path):
    result = parse_syllabus_pdf(_theory_pdf(tmp_path), core_courses=CORE)
    assert result["syllabus_id"] == "BCSE202L_DSA_TH.pdf"
    assert [m["source_id"] for m in result["two_pass_mappings"]] == ["BCSE202L_mod_1", "BCSE202L_mod_2"]
    assert [s["module_number"] for s in result["skipped_modules"]] == [3]
    assert result["text_layer"]["pages_without_text"] == []


def test_collect_syllabus_pdfs_matches_glob_only(tmp_path):
    for name in ("BCSE202P_lab.pdf", "BCSE202L_th.pdf", "B.Tech_CSE_2024_2025.pdf", "BCSE_notes.txt"):
        (tmp_path / name).write_bytes(b"%PDF-1.4")
    assert collect_syllabus_pdfs(str(tmp_path)) == [str(tmp_path / "BCSE202L_th.pdf"), str(tmp_path / "BCSE202P_lab.pdf")]
    assert collect_syllabus_pdfs(str(tmp_path), pattern="B.Tech*.pdf") == [str(tmp_path / "B.Tech_CSE_2024_2025.pdf")]


# --- manifest -------------------------------------------------------------------

def test_manifest_has_one_row_per_core_course_file():
    import csv
    import os

    from pipeline.config import ROOT, load_scoring_config

    with open(os.path.join(ROOT, "data", "raw", "syllabi", "vit_syllabus_manifest.csv"), encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    course_rows = [r for r in rows if r["component"] in ("theory", "lab")]
    # every core course has at least one row, in allowlist order (embedded E courses have a theory and a lab file)
    assert list(dict.fromkeys(r["course_code"] for r in course_rows)) == load_scoring_config()["syllabus"]["core_courses"]
    for row in course_rows:
        assert row["course_group"] == row["course_code"][:-1]
        assert row["official_source_url"] == ""
        if row["text_layer"] == "missing":  # file not supplied
            assert row["expected_local_filename"] == "" and row["used_in_course_run"] == "no"
            continue
        assert row["expected_local_filename"].startswith(row["course_code"] + "_"), row
        assert row["source"].startswith("VIT official course syllabus PDF, downloaded by user 2026-10-2")
        assert row["used_in_course_run"] == ("yes" if row["text_layer"] == "yes" else "no"), row
    by_code = {}
    for r in course_rows:
        by_code.setdefault(r["course_code"], []).append(r)
    assert by_code["BCSE205L"][0]["ltpc_status"] == "incomplete"
    assert [r["component"] for r in by_code["BCSE101E"]] == ["theory", "lab"]
    assert {r["text_layer"] for r in by_code["BCSE102L"]} == {"no"}
    assert by_code["BCSE203E"][0]["text_layer"] == "missing"
    programme = [r for r in rows if r["component"] == "programme"]
    assert len(programme) == 1 and programme[0]["used_in_course_run"] == "no"


# --- manual transcriptions for PDFs without a text layer (2026-10-22) ----------------

TRANSCRIBED_THEORY = """# Manual transcription of BCSE102L (vector-outline PDF, no text layer).
BCSE102L Structured and Object-Oriented Programming L T P C
2 0 0 2
Module:1 C Programming Fundamentals 2 hours
Variables - Data Types - Operators - Branching and Looping.
Module:2 Arrays and Functions 4 hours
One Dimensional array - Recursive functions.
Total Lecture hours: 30 hours
"""


def _transcribed_dir(tmp_path, code, text):
    folder = tmp_path / "transcribed"
    folder.mkdir(exist_ok=True)
    (folder / f"{code}.txt").write_text(text, encoding="utf-8")
    return str(folder)


def test_transcription_used_when_pdf_has_no_text_layer(tmp_path):
    blank = _write_pdf(tmp_path / "BCSE102L_SOOP_TH_63 ACP.pdf", [[], []])
    folder = _transcribed_dir(tmp_path, "BCSE102L", TRANSCRIBED_THEORY)
    result = parse_syllabus_pdfs([blank], syllabus_id="s", core_courses=["BCSE102L"], transcriptions_dir=folder)
    assert result["file_errors"] == []
    assert [m["source_id"] for m in result["two_pass_mappings"]] == ["BCSE102L_mod_1", "BCSE102L_mod_2"]
    assert all("Manual transcription" not in m["raw_text"] for m in result["two_pass_mappings"])
    assert result["text_layer"]["files"] == [{"file": "BCSE102L_SOOP_TH_63 ACP.pdf", "page_count": 2,
                                              "pages_without_text": [1, 2], "text_source": "manual_transcription"}]
    course = result["courses"][0]
    assert (course["course_code"], course["lecture_hours"], course["text_source"]) == ("BCSE102L", 2, "manual_transcription")


def test_transcription_ignored_when_pdf_has_text(tmp_path):
    lab = _lab_pdf(tmp_path)
    folder = _transcribed_dir(tmp_path, "BCSE202P", TRANSCRIBED_THEORY.replace("BCSE102L", "BCSE202P"))
    result = parse_syllabus_pdfs([lab], syllabus_id="s", core_courses=CORE, transcriptions_dir=folder)
    assert result["text_layer"]["files"][0]["text_source"] == "pdf"
    assert result["courses"][0]["text_source"] == "pdf"
    assert [m["source_id"] for m in result["two_pass_mappings"]][:1] == ["BCSE202P_exp_1"]


def test_no_text_and_no_transcription_is_still_a_file_error(tmp_path):
    blank = _write_pdf(tmp_path / "BCSE999L_scanned.pdf", [[]])
    folder = _transcribed_dir(tmp_path, "BCSE102L", TRANSCRIBED_THEORY)
    result = parse_syllabus_pdfs([blank, _lab_pdf(tmp_path)], syllabus_id="s", core_courses=CORE, transcriptions_dir=folder)
    assert [e["file"] for e in result["file_errors"]] == ["BCSE999L_scanned.pdf"]

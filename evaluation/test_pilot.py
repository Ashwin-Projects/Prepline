"""
Phase 16 pilot kit: form spec, form export template and the pre-registered descriptive analysis (M1-M3).
All response data here is SYNTHETIC (improvement answers start "SYNTHETIC"), built in the test, and never written to
results/.
"""
import csv
import json

import pytest
from fastapi.testclient import TestClient

from evaluation.pilot import analyze_pilot as ap
from evaluation.pilot import form_spec as fs

AMAZON, MICROSOFT, FLIPKART = "Amazon", "Microsoft", "Flipkart"

Q4_OPTIONS = [
    "Arrays and strings", "Two pointers / sliding window", "Hashing", "Linked lists", "Stacks and queues",
    "Trees and binary search trees", "Heaps / priority queues", "Graphs (BFS/DFS)", "Shortest paths",
    "Dynamic programming", "Greedy algorithms", "Backtracking / recursion", "Sorting and searching", "DBMS / SQL",
    "Operating systems", "Computer networks", "OOP / object-oriented design", "System design", "Other", "Cannot recall",
]


def test_form_text_is_the_owners_exact_wording():
    assert fs.FORM_TITLE == "PREPLINE Pilot — Curriculum vs Interview Topic Gaps"
    assert fs.CONSENT_YES == "I agree to take part."
    assert fs.DESCRIPTION.endswith("Anonymous: no names or emails are collected. Answers are used only for this "
                                   "academic project.")
    assert fs.COMPANY == "Which company's interview preparation would you like to evaluate?"
    assert fs.Q2 == "How well do the identified topic gaps match your own weak areas?"
    assert fs.GAP_SCALE == ["1 Not at all", "2 Slightly", "3 Moderately", "4 Very well", "5 Exactly matches my weak areas"]
    assert fs.Q3 == "Have you taken an online assessment or interview with this company?"
    assert fs.Q4 == "Which technical topics did you encounter in that assessment or interview?"
    assert fs.TOPIC_OPTIONS == Q4_OPTIONS
    assert fs.Q5 == "Please rate PREPLINE."
    assert fs.RATE_SCALE == ["1 Strongly disagree", "2 Disagree", "3 Neither agree nor disagree", "4 Agree",
                             "5 Strongly agree"]
    assert fs.RATE_ITEMS == [
        "The identified topic gaps were easy to understand.",
        "The gaps were relevant to preparing for my selected company.",
        "The confidence labels helped me judge how much to trust the results.",
        "PREPLINE helps me decide what to study next.",
    ]
    assert fs.Q6 == "What is the one most important improvement you would suggest?"


def test_profiles_have_top10_gaps_for_q2_and_top10_importance_for_m1():
    p = {x["company"]: x for x in fs.profiles()}
    assert list(p) == [AMAZON, MICROSOFT, FLIPKART]
    assert [len(p[c]["gaps"]) for c in p] == [9, 10, 10]  # Amazon's scoring universe has only 9 positive gaps
    assert p[AMAZON]["gaps"][0] == "Linked List Manipulation & Cycle Detection"
    assert [len(p[c]["top_important_ids"]) for c in p] == [9, 10, 10]
    # by importance, not by gap: Microsoft's 10th is Semaphores (Sliding Window is 11th) ...
    assert "os.process_synchronization.semaphores_mutex" in p[MICROSOFT]["top_important_ids"]
    assert "dsa.arrays.sliding_window" not in p[MICROSOFT]["top_important_ids"]
    # ... and Flipkart's routing gap is not among its 10 most important topics
    assert "cn.network_layer.routing_protocols" in p[FLIPKART]["gap_ids"]
    assert "cn.network_layer.routing_protocols" not in p[FLIPKART]["top_important_ids"]


def test_q4_mapping_unmapped_and_cannot_recall():
    assert set(fs.UNMAPPED) == {"Hashing", "Greedy algorithms", "OOP / object-oriented design", fs.OTHER}
    assert fs.CANNOT_RECALL == "Cannot recall"
    mapped = [o for o in Q4_OPTIONS if o not in fs.UNMAPPED and o != fs.CANNOT_RECALL]
    assert set(fs.OPTION_TOPICS) == set(mapped)
    granular = {n["topic_id"] for n in fs.taxonomy_nodes() if n["type"] == "granular_skill"}
    assert all(ids and set(ids) <= granular for ids in fs.OPTION_TOPICS.values())
    reachable = {i for ids in fs.OPTION_TOPICS.values() for i in ids}
    assert {i for x in fs.profiles() for i in x["top_important_ids"]} <= reachable


def test_columns_follow_google_forms_export_with_repeated_grid_titles():
    cols = fs.columns()
    assert cols[:3] == ["Timestamp", fs.CONSENT, fs.COMPANY]
    q2 = [c for c in cols if c.startswith(fs.Q2 + " [")]
    assert len(q2) == 29 and q2.count(f"{fs.Q2} [Linked List Manipulation & Cycle Detection]") == 3
    assert [c for c in cols if c.startswith(fs.Q5 + " [")] == [f"{fs.Q5} [{s}]" for s in fs.RATE_ITEMS]
    assert cols[-1] == fs.Q6


def test_shipped_template_form_and_protocol_are_in_sync():
    with open(fs.TEMPLATE_PATH, encoding="utf-8") as f:
        assert next(csv.reader(f)) == fs.columns()
    form = open(fs.FORM_PATH, encoding="utf-8").read()
    for text in (fs.FORM_TITLE, fs.DESCRIPTION, fs.CONSENT_YES, fs.COMPANY, fs.Q2, fs.Q3, fs.Q4, fs.Q5, fs.Q6,
                 *fs.RATE_ITEMS, *fs.GAP_SCALE, *fs.RATE_SCALE, *fs.TOPIC_OPTIONS):
        assert text in form, text
    for profile in fs.profiles():
        assert all(gap in form for gap in profile["gaps"])
    protocol = open(fs.PROTOCOL_PATH, encoding="utf-8").read()
    assert "importance" in protocol and "OOP / object-oriented design" in protocol and "Cannot recall" in protocol
    assert "top-10 most important topics" in protocol


def test_parse_topics_handles_other_free_text_and_cannot_recall():
    assert fs.parse_topics("Two pointers / sliding window, Hashing, Graphs (BFS/DFS)") == {
        "Two pointers / sliding window", "Hashing", "Graphs (BFS/DFS)"}
    assert fs.parse_topics("Linked lists, tries and segment trees") == {"Linked lists", fs.OTHER}
    assert fs.parse_topics(fs.CANNOT_RECALL) == {fs.CANNOT_RECALL}
    assert fs.parse_topics("") == set()


def _row(company, track, ratings, topics="", rate=(4, 4, 4, 4), consent=True, improve="SYNTHETIC test row"):
    """One SYNTHETIC response as a list aligned with the (duplicate-titled) export header."""
    profiles = fs.profiles()
    profile = {p["company"]: p for p in profiles}[company]
    out, seen = [], {}
    for col in fs.columns():
        value = ""
        if col == "Timestamp":
            value = "2026/11/01 10:00:00"
        elif col == fs.CONSENT:
            value = fs.CONSENT_YES if consent else ""
        elif col == fs.COMPANY:
            value = company
        elif col.startswith(fs.Q2 + " ["):
            gap = col[len(fs.Q2) + 2:-1]
            seen[gap] = seen.get(gap, 0) + 1
            section = [p["company"] for p in profiles if gap in p["gaps"]][seen[gap] - 1]
            if section == company:
                r = ratings(profile["gaps"].index(gap))
                value = fs.GAP_SCALE[r - 1] if r else ""
        elif col == fs.Q3:
            value = "Yes" if track == "A" else "No"
        elif col == fs.Q4:
            value = topics if track == "A" else ""
        elif col.startswith(fs.Q5 + " ["):
            value = fs.RATE_SCALE[rate[fs.RATE_ITEMS.index(col[len(fs.Q5) + 2:-1])] - 1] if rate else ""
        elif col == fs.Q6:
            value = improve
        out.append(value)
    return out


def _write(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return str(path)


@pytest.fixture
def synthetic_csv(tmp_path):
    """
    SYNTHETIC responses; M1 is hand-computed against each company's saved top-10 topics by importance I(t):
      Amazon: Linked List, Monotonic Stack, LCA, Shortest Path, Grid DP, Top-K, BST, Binary Search, Tree Traversals.
      Microsoft: ... Semaphores is 10th (an OS topic); Sliding Window is 11th (a miss).
      Flipkart: String DP, LCA, Shortest Path, Tree Traversals, B-Trees, Sliding Window, Subsets, Knapsack, Top-K,
      Linked List: no networks topic (Routing is a priority gap but not top-10 by importance).
    """
    rows = [
        # A1 Amazon: Linked lists (hit), DBMS / SQL (miss), Dynamic programming (hit: Grid DP) -> 2/3; Hashing unmapped
        _row(AMAZON, "A", lambda i: 4, "Linked lists, DBMS / SQL, Dynamic programming, Hashing", (4, 4, 4, 4)),
        # A2 Amazon: Shortest paths (hit) + free-text Other -> 1/1
        _row(AMAZON, "A", lambda i: 2, "Shortest paths, bit manipulation", (5, 5, 5, 5)),
        # A3 Microsoft: Two pointers / sliding window (miss: 11th), Operating systems (hit: Semaphores) -> 1/2; OOP
        # unmapped; ratings 3 on the first 5 gaps, rest blank -> 3.0
        _row(MICROSOFT, "A", lambda i: 3 if i < 5 else None,
             "Two pointers / sliding window, Operating systems, OOP / object-oriented design", (3, 3, 3, 3)),
        # A4 Flipkart: Computer networks (miss), Dynamic programming (hit), Greedy (unmapped) -> 1/2
        _row(FLIPKART, "A", lambda i: 5, "Computer networks, Greedy algorithms, Dynamic programming", (2, 2, 2, 2)),
        # A5 Microsoft: Cannot recall only -> no M1
        _row(MICROSOFT, "A", lambda i: 3, fs.CANNOT_RECALL, (3, 3, 3, 3)),
        # no consent: excluded
        _row(AMAZON, "A", lambda i: 1, "Sorting and searching", (1, 1, 1, 1), consent=False),
        # Track B
        _row(AMAZON, "B", lambda i: 4, rate=(3, 3, 3, 3)),
        _row(AMAZON, "B", lambda i: 2, rate=(4, 4, 4, 4)),
        _row(FLIPKART, "B", lambda i: 5, rate=None),
    ]
    return _write(tmp_path / "SYNTHETIC_pilot_responses.csv", fs.columns(), rows)


def test_load_responses_merges_duplicate_grid_columns(synthetic_csv):
    responses = ap.load_responses(synthetic_csv)
    assert len(responses) == 9
    assert responses[0][f"{fs.Q2} [Linked List Manipulation & Cycle Detection]"] == ["4 Very well", "", ""]


def test_track_a_metrics_per_company_and_overall(synthetic_csv):
    r = ap.analyze(ap.load_responses(synthetic_csv))
    assert r["n_responses"] == 9 and r["n_excluded_no_consent"] == 1 and r["n_excluded_incomplete"] == 0
    a = r["tracks"]["A"]
    c = a["by_company"]
    assert a["overall"]["n"] == 5 and c[AMAZON]["n"] == 2 and c[MICROSOFT]["n"] == 2
    assert c[AMAZON]["M1_topic_hit_rate"] == pytest.approx((2 / 3 + 1) / 2)
    assert c[AMAZON]["M2_gap_relevance"] == pytest.approx(3.0)
    assert c[AMAZON]["M3_usefulness"] == pytest.approx(4.5)
    assert c[MICROSOFT]["M1_topic_hit_rate"] == pytest.approx(0.5) and c[MICROSOFT]["M1_topic_hit_rate_n"] == 1
    assert c[MICROSOFT]["M2_gap_relevance"] == pytest.approx(3.0)  # blank rows are skipped
    assert c[FLIPKART]["M1_topic_hit_rate"] == pytest.approx(0.5)
    o = a["overall"]
    assert o["M1_topic_hit_rate"] == pytest.approx((2 / 3 + 1 + 0.5 + 0.5) / 4)
    assert o["M2_gap_relevance"] == pytest.approx((4 + 2 + 3 + 5 + 3) / 5)
    assert o["M3_usefulness"] == pytest.approx((4 + 5 + 3 + 2 + 3) / 5)


def test_unmapped_and_cannot_recall_reported_separately(synthetic_csv):
    u = ap.analyze(ap.load_responses(synthetic_csv))["q4_unmapped"]
    assert u["n_track_a"] == 5
    assert u["selected"] == {"Hashing": 1, "Greedy algorithms": 1, "OOP / object-oriented design": 1, fs.OTHER: 1}
    assert u["cannot_recall"] == 1


def test_track_b_metrics_and_combined_rating(synthetic_csv):
    r = ap.analyze(ap.load_responses(synthetic_csv))
    b = r["tracks"]["B"]
    assert b["overall"]["n"] == 3 and b["by_company"][AMAZON]["n"] == 2
    assert b["by_company"][AMAZON]["M2_gap_relevance"] == pytest.approx(3.0)
    assert b["by_company"][AMAZON]["M3_usefulness"] == pytest.approx(3.5)
    assert b["by_company"][FLIPKART]["M3_usefulness"] is None
    assert "M1_topic_hit_rate" not in b["overall"]
    assert b["overall"]["M2_gap_relevance"] == pytest.approx(11 / 3)
    assert r["M3_all_participants"]["M3_usefulness_n"] == 7
    assert r["M3_all_participants"]["M3_usefulness"] == pytest.approx((17 + 7) / 7)


def test_consent_is_found_by_its_answer_whatever_the_question_title(tmp_path):
    header = [("Do you agree?" if c == fs.CONSENT else c) for c in fs.columns()]
    rows = [_row(AMAZON, "B", lambda i: 4), _row(AMAZON, "B", lambda i: 4, consent=False)]
    r = ap.analyze(ap.load_responses(_write(tmp_path / "x.csv", header, rows)))
    assert r["n_excluded_no_consent"] == 1 and r["tracks"]["B"]["overall"]["n"] == 1
    assert fs.CONSENT not in ap.missing_columns(str(tmp_path / "x.csv"))


def test_report_writes_md_json_chart_and_never_overwrites(synthetic_csv, tmp_path):
    out = tmp_path / "pilot"
    ap.run(synthetic_csv, str(out))
    md = (out / "PILOT_RESULTS.md").read_text(encoding="utf-8")
    assert "descriptive only" in md and "no inferential statistics" in md.lower()
    assert "## Track A" in md and "## Track B" in md and "OOP / object-oriented design" in md and "Cannot recall" in md
    assert "top-10 most important topics" in md and "| Amazon | 2 |" in md
    data = json.loads((out / "pilot_results.json").read_text(encoding="utf-8"))
    assert data["tracks"]["A"]["overall"]["n"] == 5 and data["tracks"]["B"]["overall"]["n"] == 3
    assert data["synthetic"] is True
    assert (out / "pilot_m1_topic_hit_rate.png").stat().st_size > 0
    with pytest.raises(FileExistsError):
        ap.run(synthetic_csv, str(out))
    ap.run(synthetic_csv, str(out), replace=True)


def test_synthetic_data_never_goes_to_results(synthetic_csv):
    with pytest.raises(ValueError, match="SYNTHETIC"):
        ap.run(synthetic_csv, ap.DEFAULT_OUT_DIR)


def test_missing_columns_are_named(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("Timestamp,Consent\n", encoding="utf-8")
    missing = ap.missing_columns(str(path))
    assert fs.Q3 in missing and f"{fs.Q5} [{fs.RATE_ITEMS[0]}]" in missing


def test_pilot_api_in_progress_then_results(tmp_path, monkeypatch):
    import backend.dashboard as dashboard
    from backend.app import app
    client = TestClient(app)
    monkeypatch.setattr(dashboard, "PILOT_RESULTS", str(tmp_path / "pilot_results.json"))
    data = client.get("/api/v1/pilot").json()
    assert data == {"status": "in_progress", "results": None}
    (tmp_path / "pilot_results.json").write_text(json.dumps({"overall": {"n": 12}}), encoding="utf-8")
    data = client.get("/api/v1/pilot").json()
    assert data["status"] == "results_available" and data["results"]["overall"]["n"] == 12

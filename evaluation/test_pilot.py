"""
Phase 16 pilot kit: form spec, form export template and the pre-registered descriptive analysis (M1-M3).
All response data here is SYNTHETIC (participant ids SYN..), built in the test, and never written to results/.
"""
import csv
import json

import pytest
from fastapi.testclient import TestClient

from evaluation.pilot import analyze_pilot as ap
from evaluation.pilot import form_spec as fs

AMAZON, MICROSOFT, FLIPKART, GOOGLE = "Amazon SDE-1", "Microsoft SDE-1", "Flipkart SDE-1", "Google SWE-L3"


def test_profiles_from_saved_results():
    p = {x["label"]: x for x in fs.profiles()}
    assert list(p) == [AMAZON, MICROSOFT, GOOGLE, FLIPKART]
    assert len(p[AMAZON]["top_important"]) == 9 and p[AMAZON]["top_important"][0] == "Linked List Manipulation & Cycle Detection"
    assert len(p[MICROSOFT]["top_important"]) == 10 and "Semaphores, Mutexes, and Monitors" in p[MICROSOFT]["top_important"]
    assert "Sliding Window Technique" not in p[MICROSOFT]["top_important"]  # 11th by importance
    assert [len(p[x]["gaps"]) for x in (AMAZON, MICROSOFT, FLIPKART)] == [9, 10, 10]
    assert p[GOOGLE]["top_important"] == [] and p[GOOGLE]["gaps"] == [] and p[GOOGLE]["status"] == "INSUFFICIENT_DATA"


def test_columns_match_the_form():
    cols = fs.columns()
    assert cols[:8] == ["Timestamp", fs.CONSENT, fs.PARTICIPANT, fs.TRACK, fs.COMPANY, fs.ROLE, fs.ROUNDS, fs.TOPICS]
    assert fs.COMPANY_B in cols and fs.PERCEIVED in cols and cols.index(fs.PERCEIVED) > cols.index(fs.COMPANY_B)
    assert sum(c.startswith(f"{fs.GAP_PREFIX} {AMAZON} [") for c in cols) == 9
    assert sum(c.startswith(f"{fs.GAP_PREFIX} {MICROSOFT} [") for c in cols) == 10
    assert sum(c.startswith(f"{fs.GAP_PREFIX} {GOOGLE} [") for c in cols) == 0
    assert sum(c.startswith(f"{fs.USEFULNESS} [") for c in cols) == 5
    assert cols[-1] == fs.COMMENTS
    assert len(fs.topic_options()) == 46


def test_shipped_template_and_form_are_in_sync():
    with open(fs.TEMPLATE_PATH, encoding="utf-8") as f:
        assert next(csv.reader(f)) == fs.columns()
    form = open(fs.FORM_PATH, encoding="utf-8").read()
    for profile in fs.profiles():
        for gap in profile["gaps"]:
            assert gap in form
    assert fs.CONSENT in form and "Do not collect email addresses" in form
    assert fs.TRACK_A in form and fs.TRACK_B in form and "create_form.gs" in form
    script = open(fs.SCRIPT_PATH, encoding="utf-8").read()
    for title in [fs.CONSENT, fs.PARTICIPANT, fs.TRACK, fs.COMPANY, fs.TOPICS, fs.COMPANY_B, fs.PERCEIVED, fs.USEFULNESS]:
        assert json.dumps(title) in script
    for profile in fs.profiles():
        for gap in profile["gaps"]:
            assert json.dumps(f"{fs.gap_row(profile['gaps'].index(gap) + 1, gap)}") in script
    assert "DO_NOT_COLLECT" in script and "setRequired(true)" in script and "setGoToPage" in script
    assert all(topic in form for topic in fs.topic_options())


def test_parse_multiselect_with_commas_in_names():
    cell = "Cache Invalidation & Eviction Strategies, Semaphores, Mutexes, and Monitors, Sliding Window Technique"
    assert fs.parse_topics(cell) == {"Cache Invalidation & Eviction Strategies", "Semaphores, Mutexes, and Monitors",
                                     "Sliding Window Technique"}
    assert fs.parse_topics("None of these") == set()


def _row(pid, company, topics, gap_rating, usefulness, consent=None):
    """Track A (took an OA/interview)."""
    row = {c: "" for c in fs.columns()}
    row.update({"Timestamp": "2026/11/01 10:00:00", fs.CONSENT: fs.CONSENT_YES if consent is None else consent,
                fs.PARTICIPANT: pid, fs.TRACK: fs.TRACK_A, fs.COMPANY: company, fs.ROLE: "SDE-1",
                fs.ROUNDS: "Online assessment, Technical interview", fs.TOPICS: ", ".join(topics),
                fs.COMMENTS: "SYNTHETIC test row"})
    for i, col in enumerate(c for c in fs.columns() if c.startswith(f"{fs.GAP_PREFIX} {company} [")):
        row[col] = gap_rating(i)
    for i, col in enumerate(c for c in fs.columns() if c.startswith(f"{fs.USEFULNESS} [")):
        row[col] = str(usefulness[i])
    return row


def _row_b(pid, company, perceived, usefulness):
    """Track B (any CSE student, used the dashboard for 5 minutes)."""
    row = {c: "" for c in fs.columns()}
    row.update({"Timestamp": "2026/11/02 10:00:00", fs.CONSENT: fs.CONSENT_YES, fs.PARTICIPANT: pid,
                fs.TRACK: fs.TRACK_B, fs.COMPANY_B: company, fs.PERCEIVED: str(perceived),
                fs.COMMENTS: "SYNTHETIC test row"})
    for i, col in enumerate(c for c in fs.columns() if c.startswith(f"{fs.USEFULNESS} [")):
        row[col] = str(usefulness[i])
    return row


@pytest.fixture
def synthetic_csv(tmp_path):
    """SYNTHETIC responses; expected values below are hand-computed from the saved top-10 lists."""
    rows = [
        _row("SYN01", AMAZON, ["Linked List Manipulation & Cycle Detection", "Top K Elements and K-Way Merge", "SQL Joins"],
             lambda i: "4", [4, 4, 4, 4, 4]),
        _row("SYN02", AMAZON, ["Binary Search Trees"], lambda i: "2", [5, 5, 5, 5, 5]),
        _row("SYN03", MICROSOFT, ["Cache Invalidation & Eviction Strategies", "Semaphores, Mutexes, and Monitors",
                                  "Sliding Window Technique"], lambda i: "3" if i < 5 else "N/A", [3, 3, 3, 3, 3]),
        _row("SYN04", FLIPKART, ["String and Subsequence DP", "Knapsack and Subset DP", "Routing Algorithms and Protocols",
                                 "Tree Traversals"], lambda i: "5", [2, 2, 2, 2, 2]),
        _row("SYN05", GOOGLE, ["Shortest Path Algorithms"], lambda i: "", [4, 4, 4, 4, 5]),
        _row("SYN06", AMAZON, ["Binary Search"], lambda i: "1", [1, 1, 1, 1, 1], consent=""),
        _row_b("SYN07", AMAZON, 4, [3, 3, 3, 3, 3]),
        _row_b("SYN08", AMAZON, 2, [4, 4, 4, 4, 4]),
        _row_b("SYN09", FLIPKART, 5, [5, 5, 5, 5, 5]),
    ]
    path = tmp_path / "SYNTHETIC_pilot_responses.csv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fs.columns())
        w.writeheader()
        w.writerows(rows)
    return str(path)


def test_track_a_metrics_per_company_and_overall(synthetic_csv):
    r = ap.analyze(ap.load_responses(synthetic_csv))
    assert r["n_responses"] == 9 and r["n_excluded_no_consent"] == 1
    a = r["tracks"]["A"]
    c = a["by_company"]
    assert a["overall"]["n"] == 5 and c[AMAZON]["n"] == 2
    assert c[AMAZON]["M1_topic_hit_rate"] == pytest.approx((2 / 3 + 1) / 2)
    assert c[AMAZON]["M2_gap_relevance"] == pytest.approx(3.0)
    assert c[AMAZON]["M3_usefulness"] == pytest.approx(4.5)
    assert c[MICROSOFT]["M1_topic_hit_rate"] == pytest.approx(2 / 3)  # Sliding Window is 11th: a miss
    assert c[MICROSOFT]["M2_gap_relevance"] == pytest.approx(3.0)  # N/A ratings are skipped
    assert c[FLIPKART]["M1_topic_hit_rate"] == pytest.approx(0.75)
    assert c[GOOGLE]["M1_topic_hit_rate"] is None and c[GOOGLE]["M2_gap_relevance"] is None
    assert c[GOOGLE]["M3_usefulness"] == pytest.approx(4.2)
    o = a["overall"]
    assert o["M1_topic_hit_rate"] == pytest.approx((2 / 3 + 1 + 2 / 3 + 0.75) / 4)
    assert o["M2_gap_relevance"] == pytest.approx(3.5)
    assert o["M3_usefulness"] == pytest.approx((4 + 5 + 3 + 2 + 4.2) / 5)


def test_track_b_metrics_and_combined_usefulness(synthetic_csv):
    r = ap.analyze(ap.load_responses(synthetic_csv))
    b = r["tracks"]["B"]
    assert b["overall"]["n"] == 3 and b["by_company"][AMAZON]["n"] == 2
    assert b["by_company"][AMAZON]["M2b_perceived_match"] == pytest.approx(3.0)
    assert b["by_company"][AMAZON]["M3_usefulness"] == pytest.approx(3.5)
    assert b["by_company"][FLIPKART]["M2b_perceived_match"] == pytest.approx(5.0)
    assert b["overall"]["M2b_perceived_match"] == pytest.approx(11 / 3)
    assert "M1_topic_hit_rate" not in b["overall"]
    assert r["M3_all_participants"]["n"] == 8
    assert r["M3_all_participants"]["M3_usefulness"] == pytest.approx((18.2 + 12) / 8)


def test_report_writes_md_json_chart_and_never_overwrites(synthetic_csv, tmp_path):
    out = tmp_path / "pilot"
    ap.run(synthetic_csv, str(out))
    md = (out / "PILOT_RESULTS.md").read_text(encoding="utf-8")
    assert "descriptive only" in md and "no inferential statistics" in md.lower()
    assert "## Track A" in md and "## Track B" in md
    assert "| Amazon SDE-1 | 2 |" in md
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

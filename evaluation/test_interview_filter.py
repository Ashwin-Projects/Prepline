"""
Item 3: interview question filtering before scoring.

Excluded: round_type == behavioral, needs_review true, or no question_text.
Report count = reports with >= 1 included question; it drives both the
density gate and the I(t) denominator.
"""
import csv
import os

import pytest
from fastapi.testclient import TestClient

import backend.routes as routes
from backend.app import app
from pipeline import scoring
from pipeline.interview_parser import count_reports, filter_questions, write_excluded_questions

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_QUESTIONS = os.path.join(ROOT, "data", "processed", "questions.csv")


def _row(report_id="R1", round_type="technical", question_text="Two Sum", needs_review="False", **extra):
    row = {"report_id": report_id, "round_type": round_type, "question_text": question_text,
           "topic": "", "needs_review": needs_review}
    row.update(extra)
    return row


def test_behavioral_excluded():
    included, excluded = filter_questions([_row(round_type="behavioral"), _row()])
    assert len(included) == 1
    assert excluded[0]["exclusion_reason"] == "behavioral_round"


@pytest.mark.parametrize("flag", ["True", "true", True, "1", "yes"])
def test_needs_review_string_and_bool(flag):
    included, excluded = filter_questions([_row(needs_review=flag)])
    assert included == []
    assert excluded[0]["exclusion_reason"] == "needs_review"


@pytest.mark.parametrize("text", ["nan", "NaN", "", "   ", None])
def test_nan_question_text_excluded(text):
    included, excluded = filter_questions([_row(question_text=text)])
    assert included == []
    assert excluded[0]["exclusion_reason"] == "no_question_text"


def test_multiple_reasons_joined():
    _, excluded = filter_questions([_row(round_type="behavioral", needs_review="True", question_text="nan")])
    assert excluded[0]["exclusion_reason"] == "behavioral_round;needs_review;no_question_text"


def test_missing_columns_included():
    included, excluded = filter_questions([{"report_id": "R1", "question_text": "Two Sum"}])
    assert len(included) == 1 and excluded == []


def test_filter_does_not_mutate_input_rows():
    row = _row(round_type="behavioral")
    filter_questions([row])
    assert "exclusion_reason" not in row


def test_write_excluded_questions(tmp_path):
    _, excluded = filter_questions([_row(round_type="behavioral")])
    out = tmp_path / "excluded.csv"
    write_excluded_questions(excluded, str(out))
    with open(out, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert reader.fieldnames[-1] == "exclusion_reason"
    assert rows[0]["report_id"] == "R1"
    assert rows[0]["exclusion_reason"] == "behavioral_round"


def test_count_reports_distinct_non_empty():
    assert count_reports([_row("R1"), _row("R1"), _row("R2"), _row("")]) == 2


def test_real_dataset_counts():
    with open(REAL_QUESTIONS, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    included, excluded = filter_questions(rows)
    assert len(included) == 46
    assert len(excluded) == 52
    assert count_reports(included) == 18


def test_importance_denominator_defaults_to_included_reports():
    rows = [_row("R1", question_text="Deadlock Detection and Prevention"),
            _row("R2", round_type="behavioral", question_text="Tell me about yourself")]
    res = scoring.calculate_topic_importance(rows)
    assert res["total_reports_count"] == 1
    assert res["questions_included"] == 1
    assert res["questions_excluded"] == 1


def test_topic_only_rows_contribute_nothing():
    rows = [_row("R1", question_text="nan", topic="Dynamic Programming")]
    with pytest.raises(ValueError):
        # no included questions -> no reports -> no valid denominator
        scoring.calculate_topic_importance(rows)
    res = scoring.calculate_topic_importance(rows, total_reports_count=1)
    assert all(item["importance"] == 0.0 for item in res["interview_importance"])


def test_no_hardcoded_21_default():
    import inspect
    default = inspect.signature(scoring.calculate_topic_importance).parameters["total_reports_count"].default
    assert default is None


@pytest.fixture
def fourteen_report_csv(tmp_path):
    path = tmp_path / "questions.csv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["report_id", "round", "round_type", "question_text",
                                               "topic", "needs_review", "review_reason"])
        writer.writeheader()
        for i in range(1, 17):
            writer.writerow({"report_id": f"R{i:02d}", "round": "R1",
                             "round_type": "behavioral" if i > 14 else "technical",
                             "question_text": "Two Sum", "topic": "", "needs_review": "False",
                             "review_reason": ""})
    return str(path)


def test_density_gate_below_15_after_filtering(fourteen_report_csv, monkeypatch):
    monkeypatch.setattr(routes, "QUESTIONS_CSV_PATH", fourteen_report_csv)
    client = TestClient(app)
    data = client.post("/api/v1/validate-target", json={"company": "Amazon", "role": "SDE-1"}).json()
    assert data["report_count"] == 14
    assert data["status"] == "INSUFFICIENT_DATA"

    routes.SYLLABUS_CACHE["syl_gate_test"] = {"taxonomy_version": "v1.0", "two_pass_mappings": []}
    try:
        run = client.post("/api/v1/pipeline/run", json={"syllabus_id": "syl_gate_test"}).json()
    finally:
        routes.SYLLABUS_CACHE.pop("syl_gate_test", None)
    assert run["status"] == "INSUFFICIENT_DATA"
    assert run["report_count"] == 14
    assert run["S_comp"] is None

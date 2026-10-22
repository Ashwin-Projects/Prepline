"""
Retrospective validation (not the participant pilot): leave-one-report-out top-10 hit rate vs a random top-10.
Fold logic is tested with injected importance/topic functions (no embeddings); the run uses the real v1.2 scoring.
"""
import json
from collections import Counter

import pytest
from fastapi.testclient import TestClient

import evaluation.retro_validation as rv


def _rows(spec):
    """spec: {report_id: [topics]} -> question rows carrying their topic in 'topic' (test-only shortcut)."""
    return [{"report_id": r, "question_text": t, "topic": t} for r, topics in spec.items() for t in topics] + \
        [{"report_id": r, "question_text": "", "topic": ""} for r, topics in spec.items() if not topics]


def fake_importance(rows, n_reports):
    """I(t) = share of training reports mentioning t."""
    per_report = {}
    for row in rows:
        if row["topic"]:
            per_report.setdefault(row["report_id"], set()).add(row["topic"])
    counts = Counter(t for topics in per_report.values() for t in topics)
    return {t: c / n_reports for t, c in counts.items()}


def fake_held(rows):
    return {row["topic"] for row in rows if row["topic"]}


SPEC = {"R1": ["a", "b"], "R2": ["a", "c"], "R3": ["a", "b", "d"], "R4": []}


def test_leave_one_report_out_folds():
    folds = rv.loo_folds(_rows(SPEC), fake_importance, fake_held, k=2)
    by_id = {f["report_id"]: f for f in folds}
    # R1 held out: train R2,R3,R4 -> a, then b/c/d tie -> b by id; held {a,b} -> 2/2
    assert by_id["R1"]["top"] == ["a", "b"] and by_id["R1"]["hit_rate"] == 1.0
    assert by_id["R2"]["hit_rate"] == 0.5  # train R1,R3 -> a, b; held {a,c}
    assert by_id["R3"]["hit_rate"] == pytest.approx(2 / 3)  # train R1,R2 -> a, then b/c tie -> b; held {a,b,d}
    assert by_id["R4"]["hit_rate"] is None  # no mapped topics: listed but not scored
    s = rv.summarize(folds)
    assert s["n_reports"] == 4 and s["n_folds_scored"] == 3 and s["n_folds_skipped"] == 1
    assert s["hit_rate"] == pytest.approx((1 + 0.5 + 2 / 3) / 3)


def test_top_list_only_has_positive_importance():
    folds = rv.loo_folds(_rows({"R1": ["a"], "R2": ["a"]}), fake_importance, fake_held, k=10)
    assert folds[0]["top"] == ["a"]  # one topic in the training universe, not padded to 10


def test_random_baseline_is_seeded_and_size_matched():
    folds = rv.loo_folds(_rows({"R1": ["a"], "R2": ["a"], "R3": ["a"]}), fake_importance, fake_held, k=10)
    pool = [f"t{i}" for i in range(9)] + ["a"]
    base1 = rv.random_baseline(folds, pool, draws=2000, seed=7)
    assert base1 == rv.random_baseline(folds, pool, draws=2000, seed=7)
    # each fold draws 1 topic (the size of PREPLINE's top list) from 10: expected hit rate 0.1
    assert base1["mean"] == pytest.approx(0.1, abs=0.02)
    assert 0 <= base1["p2_5"] <= base1["mean"] <= base1["p97_5"] <= 1
    assert base1["draws"] == 2000 and base1["seed"] == 7


def test_report_outputs_are_labelled_and_never_overwritten(tmp_path):
    folds = rv.loo_folds(_rows(SPEC), fake_importance, fake_held, k=2)
    company = {"target_id": "acme", "label": "Acme SDE-1", **rv.summarize(folds),
               "baseline": rv.random_baseline(folds, list("abcdefgh"), draws=200, seed=1), "folds": folds}
    result = rv.assemble([company], seed=1, draws=200, k=2)
    rv.write_outputs(result, str(tmp_path))
    md = (tmp_path / "RETRO_VALIDATION.md").read_text(encoding="utf-8")
    assert "Retrospective validation — not the participant pilot" in md and "| Acme SDE-1 |" in md
    data = json.loads((tmp_path / "retro_validation.json").read_text(encoding="utf-8"))
    assert data["label"].startswith("Retrospective validation") and data["companies"][0]["n_folds_scored"] == 3
    assert (tmp_path / "retro_validation_hit_rate.png").stat().st_size > 0
    with pytest.raises(FileExistsError):
        rv.write_outputs(result, str(tmp_path))


def test_validation_api(tmp_path, monkeypatch):
    import backend.dashboard as dashboard
    from backend.app import app
    client = TestClient(app)
    monkeypatch.setattr(dashboard, "RETRO_VALIDATION", str(tmp_path / "retro_validation.json"))
    assert client.get("/api/v1/validation").json() == {"available": False, "results": None}
    (tmp_path / "retro_validation.json").write_text(json.dumps({"label": "x", "companies": []}), encoding="utf-8")
    assert client.get("/api/v1/validation").json()["available"] is True

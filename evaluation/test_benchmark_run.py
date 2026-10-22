"""
Phase 13 part 2: matcher benchmark harness (evaluation/benchmark/run_benchmark.py).
Thresholds are chosen on dev only; val confirms; test is scored once with the chosen thresholds.
"""
import json

import pytest

from evaluation.benchmark import run_benchmark as rb

NODES = [
    {"topic_id": "dsa.trees", "name": "Trees and Binary Trees", "type": "high_level_concept",
     "description": "Hierarchical node data structures and tree traversals."},
    {"topic_id": "dsa.trees.bst", "name": "Binary Search Trees", "type": "granular_skill",
     "description": "Ordered binary search trees, insertion, deletion."},
    {"topic_id": "dsa.graphs", "name": "Graphs and Network Topologies", "type": "high_level_concept",
     "description": "Vertices, edges and graph algorithms."},
]


def test_thresholds_grid():
    assert rb.THRESHOLDS == [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]


def test_predict_top1_or_none():
    assert rb.predict({"dsa.trees": 0.6, "dsa.graphs": 0.4}, 0.5) == "dsa.trees"
    assert rb.predict({"dsa.trees": 0.45, "dsa.graphs": 0.4}, 0.5) == "none"
    assert rb.predict({"dsa.trees": 0.6, "dsa.graphs": 0.6}, 0.5) == "dsa.graphs"  # ties alphabetical, as in production
    assert rb.predict({}, 0.3) == "none"


def test_keyword_scores_respect_node_type():
    scores = rb.keyword_scores("Binary search tree insertion and deletion", NODES, "granular_skill")
    assert scores == {"dsa.trees.bst": 1.0}
    syllabus = rb.keyword_scores("Binary trees and graphs", NODES, "high_level_concept")
    assert set(syllabus) == {"dsa.trees", "dsa.graphs"}
    assert syllabus["dsa.trees"] == 1.0  # trees, binary (and/stop words ignored, plural folded)
    assert syllabus["dsa.graphs"] == pytest.approx(1 / 3)


def test_tfidf_scores_respect_node_type():
    scores = rb.tfidf_scores(["graph algorithms on vertices and edges"], NODES, ["high_level_concept"])[0]
    assert set(scores) == {"dsa.trees", "dsa.graphs"}
    assert scores["dsa.graphs"] > scores["dsa.trees"]


def test_metrics_include_none():
    m = rb.metrics(["a", "b", "none", "none"], ["a", "none", "none", "b"])
    assert m["n"] == 4 and m["correct"] == 2 and m["accuracy"] == 0.5
    # per class: a P1 R1 F1; b P0 R0 F0; none P.5 R.5 F.5 -> macro F1 0.5
    assert m["macro_f1"] == pytest.approx(0.5)
    assert m["macro_precision"] == pytest.approx(0.5) and m["macro_recall"] == pytest.approx(0.5)


def test_choose_threshold_dev_only():
    gold = ["dsa.trees", "none"]
    scores = [{"dsa.trees": 0.62}, {"dsa.trees": 0.41}]
    sweep = rb.sweep(scores, gold)
    assert [row["threshold"] for row in sweep] == rb.THRESHOLDS
    chosen = rb.choose_threshold(sweep)
    assert chosen == 0.50  # 0.45..0.60 all perfect; tie -> closest to the production 0.50, then lower
    assert rb.choose_threshold([{"threshold": 0.4, "macro_f1": 0.8, "accuracy": 0.7},
                                {"threshold": 0.6, "macro_f1": 0.8, "accuracy": 0.9}]) == 0.6


def test_evaluate_uses_dev_threshold_for_test():
    split = {"d1": "dev", "d2": "dev", "t1": "test", "v1": "val"}
    gold = {"d1": "dsa.trees", "d2": "none", "t1": "dsa.trees", "v1": "none"}
    meta = {k: {"source_type": "syllabus", "domain": "dsa" if gold[k] != "none" else "none"} for k in gold}
    scores = {"d1": {"dsa.trees": 0.62}, "d2": {"dsa.trees": 0.41}, "t1": {"dsa.trees": 0.35}, "v1": {"dsa.trees": 0.2}}
    result = rb.evaluate_method(scores, gold, split, meta)
    assert result["threshold"] == 0.50
    assert result["test"]["overall"]["accuracy"] == 0.0  # 0.35 < 0.50 although 0.30 would have been right on test
    assert result["val"]["overall"]["accuracy"] == 1.0
    assert set(result["test"]["by_source_type"]) == {"syllabus"}
    assert set(result["test"]["by_domain"]) == {"dsa"}


def test_results_never_overwritten(tmp_path):
    out = tmp_path / "benchmark.json"
    rb.write_json({"a": 1}, str(out))
    assert json.loads(out.read_text(encoding="utf-8")) == {"a": 1}
    with pytest.raises(FileExistsError):
        rb.write_json({"a": 2}, str(out))


def _result(val, test, dev):
    return {"methods": {name: {"threshold": 0.5, "dev": {"overall": {"macro_f1": dev[i]}},
                               "val": {"overall": {"macro_f1": val[i]}}, "test": {"overall": {"macro_f1": test[i]}}}
                        for i, name in enumerate(rb.METHODS)}}


def test_recommendation_follows_val_not_test():
    # production (c) best on val -> keep it, even though (d) is best on dev and test
    text = rb.recommendation(_result(val=[0.1, 0.1, 0.3, 0.2], test=[0.1, 0.1, 0.2, 0.4], dev=[0.1, 0.1, 0.2, 0.4]))
    assert text.startswith("Keep the production matcher")
    assert "minilm_name_desc" in text
    text = rb.recommendation(_result(val=[0.1, 0.1, 0.2, 0.3], test=[0.1, 0.1, 0.2, 0.4], dev=[0.1, 0.1, 0.2, 0.4]))
    assert text.startswith("Recommend evaluating minilm_name_desc")


def test_main_refuses_before_scoring_when_results_exist(tmp_path, monkeypatch):
    existing = tmp_path / "benchmark.json"
    existing.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(rb, "OUT_JSON", str(existing))
    monkeypatch.setattr(rb, "keyword_scores", lambda *a, **k: pytest.fail("scored although results exist"))
    monkeypatch.setattr(rb.sys, "argv", ["run_benchmark.py"])
    with pytest.raises(SystemExit, match="--render"):
        rb.main()

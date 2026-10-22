"""
Phase 15 data: per-target topic tables (importance, coverage, depth, coverage source) for the dashboard, exported
alongside the saved results without changing them. The exporter refuses to write a table whose recomputed S_comp
differs from the saved result.
"""
import json

import pytest

import evaluation.export_topic_tables as ett
from evaluation.test_run_all_targets import FAKE_SYLLABUS, _two_targets
from evaluation import run_all_targets as rat


def test_topic_table_rows():
    coverage = {"topic_coverage": [
        {"topic_id": "dsa.trees", "topic_name": "Trees", "presence": 1, "depth": 3.0, "coverage": 0.8,
         "depth_status": "measured", "coverage_source": "direct", "inherited_from": None},
        {"topic_id": "dsa.trees.bst", "topic_name": "BST", "presence": 1, "depth": 3.0, "coverage": 0.8,
         "depth_status": "measured", "coverage_source": "inherited", "inherited_from": "dsa.trees"}]}
    importance = {"interview_importance": [{"topic_id": "dsa.trees.bst", "importance": 0.5}]}
    nodes = [{"topic_id": "dsa.trees", "domain": "dsa", "type": "high_level_concept"},
             {"topic_id": "dsa.trees.bst", "domain": "dsa", "type": "granular_skill"}]
    rows = ett.topic_table(coverage, importance, nodes)
    bst = next(r for r in rows if r["topic_id"] == "dsa.trees.bst")
    assert bst == {"topic_id": "dsa.trees.bst", "topic_name": "BST", "domain": "dsa", "type": "granular_skill",
                   "importance": 0.5, "coverage": 0.8, "priority_gap": 0.1, "depth": 3.0, "depth_status": "measured",
                   "presence": 1, "coverage_source": "inherited", "inherited_from": "dsa.trees"}
    trees = next(r for r in rows if r["topic_id"] == "dsa.trees")
    assert trees["importance"] == 0.0 and trees["priority_gap"] == 0.0
    no_importance = ett.topic_table(coverage, None, nodes)
    assert all(r["importance"] is None and r["priority_gap"] is None for r in no_importance)


def test_export_checks_s_comp_and_never_overwrites(tmp_path):
    targets = _two_targets(tmp_path)
    results_dir = tmp_path / "results"
    rat.run_all(targets, str(results_dir), parse=lambda: FAKE_SYLLABUS)
    out_dir = tmp_path / "topics"
    written = ett.export(targets, str(results_dir), str(out_dir), parse=lambda: FAKE_SYLLABUS)
    assert [w["target_id"] for w in written] == ["acme_sde1", "beta_sde1"]
    beta = json.loads((out_dir / "beta_sde1_v1.2_topics.json").read_text(encoding="utf-8"))
    assert beta["S_comp_recomputed"] == beta["S_comp_saved"] and len(beta["topics"]) == 83
    acme = json.loads((out_dir / "acme_sde1_v1.2_topics.json").read_text(encoding="utf-8"))
    assert acme["status"] == "INSUFFICIENT_DATA" and all(t["importance"] is None for t in acme["topics"])
    with pytest.raises(FileExistsError):
        ett.export(targets, str(results_dir), str(out_dir), parse=lambda: FAKE_SYLLABUS)


def test_export_rejects_s_comp_mismatch(tmp_path):
    targets = _two_targets(tmp_path)
    results_dir = tmp_path / "results"
    rat.run_all(targets, str(results_dir), parse=lambda: FAKE_SYLLABUS)
    beta_file = results_dir / "beta_sde1_v1.2_course_syllabi.json"
    saved = json.loads(beta_file.read_text(encoding="utf-8"))
    beta_file.write_text(json.dumps(dict(saved, S_comp=99.0)), encoding="utf-8")
    with pytest.raises(ValueError, match="S_comp"):
        ett.export(targets, str(results_dir), str(tmp_path / "topics"), parse=lambda: FAKE_SYLLABUS)

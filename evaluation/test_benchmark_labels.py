"""
Phase 13 part 1: the labelling sheet validator (evaluation/benchmark/validate_labels.py).

Labels are pinned to taxonomy v1.0: syllabus rows take high_level_concept ids, interview rows granular_skill ids,
"none" is a valid label, and an empty expected_primary means "not labelled yet".
"""
import csv
import os

import pytest

from evaluation.benchmark import validate_labels as vl

NODE_TYPES = {
    "dsa": "high_level_concept",
    "dsa.trees": "high_level_concept",
    "dsa.graphs": "high_level_concept",
    "dsa.trees.bst": "granular_skill",
    "dsa.graphs.shortest_path": "granular_skill",
}


def _row(item_id, source_type="syllabus", primary="", secondary="", course="BCSE202L"):
    return {"item_id": item_id, "source_type": source_type, "course_or_report": course, "raw_text": "text",
            "expected_primary": primary, "expected_secondary": secondary, "label_notes": ""}


def _errors(rows):
    return [(e["item_id"], e["field"]) for e in vl.validate_rows(rows, NODE_TYPES)["errors"]]


def test_unlabelled_rows_are_valid_and_counted():
    report = vl.validate_rows([_row("a"), _row("b", "interview", course="AMZ001")], NODE_TYPES)
    assert report["errors"] == []
    assert report["total"] == 2
    assert report["labelled"] == 0
    assert report["by_source_type"] == {"syllabus": {"total": 1, "labelled": 0}, "interview": {"total": 1, "labelled": 0}}


def test_valid_labels_counted_per_source_type():
    rows = [_row("a", primary="dsa.trees", secondary="dsa.graphs ; dsa"),
            _row("b", primary="none"),
            _row("c", "interview", primary="dsa.trees.bst", course="AMZ001"),
            _row("d", "interview", course="AMZ002")]
    report = vl.validate_rows(rows, NODE_TYPES)
    assert report["errors"] == []
    assert report["labelled"] == 3
    assert report["by_source_type"]["syllabus"] == {"total": 2, "labelled": 2}
    assert report["by_source_type"]["interview"] == {"total": 2, "labelled": 1}


def test_unknown_id_rejected():
    assert _errors([_row("a", primary="dsa.heapz")]) == [("a", "expected_primary")]
    assert _errors([_row("b", primary="dsa.trees", secondary="dsa.tries")]) == [("b", "expected_secondary")]


def test_node_type_must_match_source_type():
    rows = [_row("a", primary="dsa.trees.bst"),  # syllabus row with a granular_skill
            _row("b", "interview", primary="dsa.trees", course="AMZ001"),  # interview row with a high_level_concept
            _row("c", primary="dsa.trees", secondary="dsa.graphs.shortest_path")]
    assert _errors(rows) == [("a", "expected_primary"), ("b", "expected_primary"), ("c", "expected_secondary")]
    message = vl.validate_rows(rows[:1], NODE_TYPES)["errors"][0]["message"]
    assert "granular_skill" in message and "high_level_concept" in message


def test_secondary_rules():
    assert _errors([_row("a", primary="none", secondary="dsa.trees")]) == [("a", "expected_secondary")]
    assert _errors([_row("b", secondary="dsa.trees")]) == [("b", "expected_secondary")]  # secondary without primary
    assert _errors([_row("c", primary="dsa.trees", secondary="dsa.trees")]) == [("c", "expected_secondary")]
    assert _errors([_row("d", primary="dsa.trees", secondary="dsa.graphs;dsa.graphs")]) == [("d", "expected_secondary")]
    assert _errors([_row("e", primary="dsa.trees", secondary="none")]) == [("e", "expected_secondary")]


def test_sheet_level_errors():
    rows = [_row("a"), _row("a"), _row("b", source_type="lecture")]
    assert _errors(rows) == [("a", "item_id"), ("b", "source_type")]


def test_missing_columns_rejected(tmp_path):
    path = tmp_path / "labels.csv"
    path.write_text("item_id,source_type\nx,syllabus\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected_primary"):
        vl.load_labels(str(path))


def test_main_exit_code(tmp_path, capsys):
    path = tmp_path / "labels.csv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=vl.COLUMNS)
        w.writeheader()
        w.writerow(_row("a", primary="dsa.trees"))
    assert vl.main([str(path)]) == 0
    assert "labelled 1 / 1" in capsys.readouterr().out
    with open(path, "a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=vl.COLUMNS).writerow(_row("b", primary="dsa.heapz"))
    assert vl.main([str(path)]) == 1
    assert "dsa.heapz" in capsys.readouterr().out


def test_shipped_sheet_is_valid_and_unlabelled():
    rows = vl.load_labels(vl.DEFAULT_LABELS)
    report = vl.validate_rows(rows, vl.load_node_types())
    assert report["errors"] == []
    assert report["by_source_type"] == {"syllabus": {"total": 162, "labelled": 0},
                                        "interview": {"total": 46, "labelled": 0}}
    assert len(vl.load_node_types()) == 83
    assert os.path.basename(vl.DEFAULT_LABELS) == "labels_v1.0.csv"

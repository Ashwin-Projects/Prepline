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


def _drafted(item_id, confidence="high", reviewed="False", **kw):
    return dict(_row(item_id, **kw), label_source="llm_draft", draft_confidence=confidence, reviewed=reviewed)


def test_review_counts():
    rows = [_drafted("a", primary="dsa.trees"),
            _drafted("b", "low", primary="none"),
            _drafted("c", "medium", "True", primary="dsa.graphs"),
            _row("d")]
    report = vl.validate_rows(rows, NODE_TYPES)
    assert report["errors"] == []
    assert report["review"] == {"reviewed": 1, "drafted": 2, "by_confidence": {"high": 1, "medium": 1, "low": 1},
                                "adjudicated_by_rule": {}, "human_adjudicated": 0}


def test_draft_columns_validated():
    rows = [_drafted("a", "unsure", primary="dsa.trees"), _drafted("b", reviewed="yes", primary="dsa.trees"),
            _drafted("c", "", primary="dsa.trees")]
    assert _errors(rows) == [("a", "draft_confidence"), ("b", "reviewed"), ("c", "draft_confidence")]


def _checked(item_id, primary, second, agreement, notes="", confidence="high", secondary="", second_secondary="",
             source="llm_cross_checked", **kw):
    return dict(_drafted(item_id, confidence, primary=primary, secondary=secondary, **kw), label_source=source,
                second_primary=second, second_secondary=second_secondary, agreement=agreement, review_notes=notes)


def test_classify_agreement():
    assert vl.classify_agreement("dsa.trees", "", "dsa.trees", "dsa.graphs") == "agree"
    assert vl.classify_agreement("dsa.trees", "dsa.graphs", "dsa.graphs", "") == "partial"  # primary in other's secondary
    assert vl.classify_agreement("dsa", "", "dsa.graphs", "") == "partial"  # ancestor / descendant
    assert vl.classify_agreement("dsa.trees", "", "dsa.graphs", "") == "disagree"
    assert vl.classify_agreement("none", "", "dsa.graphs", "") == "disagree"
    assert vl.classify_agreement("none", "", "none", "") == "agree"


def test_cohens_kappa():
    assert vl.cohens_kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
    # observed 0.5, expected 0.5 -> 0
    assert vl.cohens_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"]) == 0.0
    assert round(vl.cohens_kappa(["a", "a", "a", "b"], ["a", "a", "b", "b"]), 4) == 0.5


def test_second_labeller_columns_validated():
    rows = [_checked("a", "dsa.trees", "dsa.heapz", "disagree", "x", source="llm_draft"),
            _checked("b", "dsa.trees", "dsa.trees.bst", "partial", "x", source="llm_draft"),
            _checked("c", "dsa.trees", "dsa.trees", "maybe"),
            _checked("d", "dsa.trees", "none", "disagree", "x", second_secondary="dsa.graphs", source="llm_draft"),
            _checked("e", "dsa.trees", "dsa.graphs", "agree"),  # agreement must match the labels
            _checked("f", "dsa.trees", "dsa.graphs", "disagree", "", source="llm_draft"),  # needs review -> notes
            _checked("g", "dsa.trees", "dsa.graphs", "disagree", "x"),  # only agree rows are cross-checked
            _checked("h", "dsa.trees", "dsa.trees", "agree", source="llm_draft")]
    assert _errors(rows) == [("a", "second_primary"), ("b", "second_primary"), ("c", "agreement"),
                             ("d", "second_secondary"), ("e", "agreement"), ("f", "review_notes"),
                             ("g", "label_source"), ("h", "label_source")]


def test_low_confidence_agree_needs_notes():
    assert _errors([_checked("a", "dsa.trees", "dsa.trees", "agree", confidence="low")]) == [("a", "review_notes")]
    assert _errors([_checked("b", "dsa.trees", "dsa.trees", "agree", "both low", confidence="low")]) == []


def test_agreement_summary():
    rows = [_checked("a", "dsa.trees", "dsa.trees", "agree"),
            _checked("b", "dsa.trees", "dsa.trees", "agree", "second labeller low confidence"),
            _checked("c", "dsa", "dsa.trees", "partial", "x", source="llm_draft"),
            _checked("d", "none", "dsa.trees", "disagree", "x", source="llm_draft")]
    report = vl.validate_rows(rows, NODE_TYPES)
    assert report["errors"] == []
    assert report["agreement"] == {"agree": 2, "partial": 1, "disagree": 1, "needs_review": 3, "kappa": report["agreement"]["kappa"]}


def test_review_order_disagree_partial_low_agree_rest():
    rows = [_checked("ok1", "dsa.trees", "dsa.trees", "agree"),
            _checked("p1", "dsa", "dsa.trees", "partial", "x", source="llm_draft"),
            _checked("lo1", "dsa.trees", "dsa.trees", "agree", "low", confidence="low"),
            _checked("d1", "none", "dsa.trees", "disagree", "x", source="llm_draft"),
            _checked("ok2", "dsa.graphs", "dsa.graphs", "agree"),
            _checked("d2", "none", "dsa.graphs", "disagree", "x", source="llm_draft")]
    assert [r["item_id"] for r in vl.review_order(rows)] == ["d1", "d2", "p1", "lo1", "ok1", "ok2"]


def test_main_reports_review_counts(tmp_path, capsys):
    path = tmp_path / "labels.csv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=vl.COLUMNS + vl.DRAFT_COLUMNS)
        w.writeheader()
        w.writerow(_drafted("a", primary="dsa.trees"))
        w.writerow(_drafted("b", "low", "True", primary="none"))
    assert vl.main([str(path)]) == 0
    assert "reviewed 1 / drafted (not yet reviewed) 1" in capsys.readouterr().out


def _adjudicated(item_id, primary, second, agreement, notes="R1: gap: hashing", reviewed="True", **kw):
    return dict(_checked(item_id, primary, second, agreement, notes, source="human_rule_adjudicated", **kw),
                reviewed=reviewed)


def test_human_adjudicated_rows():
    # final label may differ from both LLM labels; agreement keeps the LLM comparison it was adjudicated from
    rows = [_adjudicated("a", "none", "dsa.trees", "disagree"),
            _adjudicated("b", "dsa.trees", "dsa.trees", "agree", "R5"),
            _adjudicated("c", "none", "dsa.trees", "disagree", reviewed="False"),
            _adjudicated("d", "none", "dsa.trees", "disagree", "adjudicated by rule"),
            _adjudicated("e", "none", "dsa.trees", "maybe")]
    assert _errors(rows) == [("c", "reviewed"), ("d", "review_notes"), ("e", "agreement")]


def test_adjudicated_rows_leave_the_review_queue():
    rows = [_adjudicated("a1", "none", "dsa.trees", "disagree"),
            _checked("d1", "none", "dsa.trees", "disagree", "x", source="llm_draft"),
            _checked("ok1", "dsa.trees", "dsa.trees", "agree")]
    report = vl.validate_rows(rows, NODE_TYPES)
    assert report["errors"] == []
    assert report["agreement"]["needs_review"] == 1
    assert report["review"]["reviewed"] == 1 and report["review"]["adjudicated_by_rule"] == {"R1": 1}
    assert [r["item_id"] for r in vl.review_order(rows)] == ["d1", "ok1", "a1"]


def test_human_adjudicated_rows():
    rows = [dict(_adjudicated("a", "dsa.trees", "dsa.graphs", "disagree", "human: keep"), label_source="human_adjudicated"),
            dict(_adjudicated("b", "dsa.trees", "dsa.graphs", "disagree", "kept"), label_source="human_adjudicated"),
            dict(_adjudicated("c", "dsa.trees", "dsa.graphs", "disagree", "human", reviewed="False"),
                 label_source="human_adjudicated")]
    assert _errors(rows) == [("b", "review_notes"), ("c", "reviewed")]
    report = vl.validate_rows(rows[:1], NODE_TYPES)
    assert report["agreement"]["needs_review"] == 0 and report["review"]["human_adjudicated"] == 1


def test_shipped_sheet_is_gold_v1_0():
    rows = vl.load_labels(vl.DEFAULT_LABELS)
    report = vl.validate_rows(rows, vl.load_node_types())
    assert report["errors"] == []
    assert report["by_source_type"] == {"syllabus": {"total": 201, "labelled": 201},
                                        "interview": {"total": 46, "labelled": 46}}
    adjudicated = [r for r in rows if r["label_source"] == "human_rule_adjudicated"]
    assert len(adjudicated) == 48 and all(r["reviewed"] == "True" for r in adjudicated)
    assert report["review"]["reviewed"] == 56  # the owner's rule-adjudicated (48) and individually decided (8) rows
    assert report["review"]["human_adjudicated"] == 8
    assert sum(report["review"]["adjudicated_by_rule"].values()) == 48
    assert report["agreement"]["needs_review"] == 0
    assert all(r["second_primary"] for r in rows)
    assert [r["item_id"] for r in rows][:2] == ["BCSE202L_mod_1", "BCSE202L_mod_2"]  # sheet order kept
    assert len(vl.load_node_types()) == 83


def test_shipped_review_order_matches_sheet():
    shipped = vl.load_labels(vl.DEFAULT_REVIEW_ORDER)
    assert shipped == vl.review_order(vl.load_labels(vl.DEFAULT_LABELS))

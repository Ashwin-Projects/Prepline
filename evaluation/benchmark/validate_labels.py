"""
Phase 13 part 1: validates the benchmark labelling sheet (labels_v1.0.csv) against taxonomy v1.0.

Rules (LABELLING_GUIDE.md): syllabus rows take high_level_concept ids, interview rows granular_skill ids;
expected_primary is one id, "none", or empty (= not labelled yet); expected_secondary is an optional
";"-separated list of other ids of the same type, only alongside a real primary. Reports labelled rows per
source type and every invalid row; exits with code 1 if any row is invalid.

Draft columns (optional): label_source (e.g. "llm_draft"), draft_confidence (high/medium/low) and reviewed
(True/False). The report counts reviewed rows and drafted rows not yet reviewed. REVIEW_ORDER.csv holds the same
rows in review order, so the doubtful drafts are reviewed first.

Second-labeller columns (optional): second_primary, second_secondary (an independent labeller's labels, same rules),
agreement (agree = same primary; partial = one primary is the other's ancestor or in its secondaries; disagree) and
review_notes. Only agreeing rows may be label_source=llm_cross_checked; partial and disagree rows, and agreeing rows
with low confidence, need review_notes. REVIEW_ORDER.csv: disagree -> partial -> agree with review notes -> rest.
reviewed=True is set only by the human reviewer. Rows settled by the reviewer's adjudication rules are
label_source=human_rule_adjudicated with reviewed=True and the rule id (R1-R5, ADJUDICATION.md) in review_notes; their
agreement column keeps the LLM comparison they were adjudicated from, and they leave the review queue.

Usage:
    python evaluation/benchmark/validate_labels.py [path/to/labels.csv]
    python evaluation/benchmark/validate_labels.py --write-review-order   # regenerate REVIEW_ORDER.csv
"""
import csv
import json
import os
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_LABELS = os.path.join(ROOT, "evaluation", "benchmark", "labels_v1.0.csv")
DEFAULT_REVIEW_ORDER = os.path.join(ROOT, "evaluation", "benchmark", "REVIEW_ORDER.csv")
# Labels are pinned to taxonomy v1.0, independent of the scoring config's current taxonomy.
TAXONOMY_PATH = os.path.join(ROOT, "data", "taxonomy", "taxonomy_v1.0.json")

COLUMNS = ["item_id", "source_type", "course_or_report", "raw_text", "expected_primary", "expected_secondary",
           "label_notes"]
DRAFT_COLUMNS = ["label_source", "draft_confidence", "reviewed"]
CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}
SECOND_COLUMNS = ["second_primary", "second_secondary", "agreement", "review_notes"]
AGREEMENT_LEVELS = ("agree", "partial", "disagree")
CROSS_CHECKED = "llm_cross_checked"
ADJUDICATED = "human_rule_adjudicated"
HUMAN_ADJUDICATED = "human_adjudicated"  # decided row by row by the reviewer; review_notes say "human"
RULE_ID = re.compile(r"\bR[1-5]\b")
NONE_LABEL = "none"
ALLOWED_TYPE = {"syllabus": "high_level_concept", "interview": "granular_skill"}


def load_node_types(path: str = TAXONOMY_PATH) -> Dict[str, str]:
    """{topic_id: node type} for every node of the taxonomy."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    nodes = data["nodes"] if isinstance(data, dict) and "nodes" in data else data
    return {n["topic_id"]: n["type"] for n in nodes}


def load_labels(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing columns {', '.join(missing)}")
        return [{k: (v or "").strip() for k, v in row.items() if k is not None} for row in reader]


def _id_problem(topic_id: str, source_type: str, node_types: Dict[str, str]) -> Optional[str]:
    if topic_id not in node_types:
        return f"unknown topic_id '{topic_id}' (not in taxonomy v1.0)"
    allowed = ALLOWED_TYPE[source_type]
    if node_types[topic_id] != allowed:
        return f"'{topic_id}' is a {node_types[topic_id]}; {source_type} rows take {allowed} ids"
    return None


def _secondary_problems(primary: str, secondary: List[str], source_type: str, node_types: Dict[str, str]) -> List[str]:
    if not primary:
        return ["secondary labels without a primary"]
    if primary == NONE_LABEL:
        return ["secondary labels with primary 'none'"]
    problems, seen = [], set()
    for topic_id in secondary:
        if topic_id == NONE_LABEL:
            problems.append("'none' is not a secondary label")
        elif topic_id == primary:
            problems.append(f"'{topic_id}' repeats the primary")
        elif topic_id in seen:
            problems.append(f"'{topic_id}' listed twice")
        else:
            problem = _id_problem(topic_id, source_type, node_types)
            if problem:
                problems.append(problem)
        seen.add(topic_id)
    return problems


def _split(ids: str) -> List[str]:
    return [s.strip() for s in (ids or "").split(";") if s.strip()]


def _is_ancestor(a: str, b: str) -> bool:
    return b.startswith(a + ".")


def classify_agreement(primary: str, secondary: str, second_primary: str, second_secondary: str) -> str:
    """agree: same primary; partial: one primary is the other's ancestor or listed in its secondaries; else disagree."""
    if primary == second_primary:
        return "agree"
    if NONE_LABEL in (primary, second_primary):
        return "disagree"
    if (primary in _split(second_secondary) or second_primary in _split(secondary)
            or _is_ancestor(primary, second_primary) or _is_ancestor(second_primary, primary)):
        return "partial"
    return "disagree"


def cohens_kappa(a: List[str], b: List[str]) -> float:
    """Cohen's kappa for two labellers' categorical labels over the same items."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    expected = sum((a.count(c) / n) * (b.count(c) / n) for c in set(a) | set(b))
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def needs_review(row: Dict[str, str]) -> bool:
    if row.get("reviewed") == "True":
        return False
    return row.get("agreement") in ("partial", "disagree") or bool(row.get("review_notes"))


def _second_labeller_errors(row: Dict[str, str], source_type: str, node_types: Dict[str, str], error) -> None:
    item_id, second = row.get("item_id", ""), row.get("second_primary", "")
    second_secondary = _split(row.get("second_secondary", ""))
    problem = None if second == NONE_LABEL else _id_problem(second, source_type, node_types)
    if problem:
        error(item_id, "second_primary", problem)
    if second_secondary:
        problems = _secondary_problems(second, second_secondary, source_type, node_types)
        if problems:
            error(item_id, "second_secondary", "; ".join(problems))
    agreement = row.get("agreement", "")
    expected = classify_agreement(row.get("expected_primary", ""), row.get("expected_secondary", ""),
                                  second, row.get("second_secondary", ""))
    if agreement not in AGREEMENT_LEVELS:
        error(item_id, "agreement", f"agreement '{agreement}' is not one of {', '.join(AGREEMENT_LEVELS)}")
        return
    if row.get("label_source") in (ADJUDICATED, HUMAN_ADJUDICATED):
        if row.get("reviewed") != "True":
            error(item_id, "reviewed", "adjudicated rows are reviewed=True")
        if row["label_source"] == ADJUDICATED and not RULE_ID.search(row.get("review_notes", "")):
            error(item_id, "review_notes", "rule-adjudicated rows name their rule (R1-R5) in review_notes")
        if row["label_source"] == HUMAN_ADJUDICATED and "human" not in row.get("review_notes", "").lower():
            error(item_id, "review_notes", "human-adjudicated rows say 'human' in review_notes")
        return
    if agreement != expected:
        error(item_id, "agreement", f"agreement '{agreement}' does not match the labels ('{expected}')")
        return
    if (agreement == "agree") != (row.get("label_source") == CROSS_CHECKED):
        error(item_id, "label_source", f"label_source must be '{CROSS_CHECKED}' exactly when the primaries agree")
    if not row.get("review_notes") and (agreement != "agree" or row.get("draft_confidence") == "low"):
        error(item_id, "review_notes", "partial/disagree and low-confidence rows need review_notes")


def validate_rows(rows: List[Dict[str, str]], node_types: Dict[str, str]) -> Dict[str, Any]:
    """
    {"total", "labelled", "by_source_type": {type: {"total", "labelled"}}, "errors": [{item_id, field, message}],
     "review": {"reviewed", "drafted", "by_confidence": {level: count}}}; "drafted" = drafted, not yet reviewed.
    """
    errors: List[Dict[str, str]] = []
    review = {"reviewed": 0, "drafted": 0, "by_confidence": {level: 0 for level in CONFIDENCE_ORDER},
              "adjudicated_by_rule": {}, "human_adjudicated": 0}
    rules: Counter = Counter()
    agreement = {level: 0 for level in AGREEMENT_LEVELS}
    agreement["needs_review"] = 0
    primaries, second_primaries = [], []
    by_source_type = {source_type: {"total": 0, "labelled": 0} for source_type in ALLOWED_TYPE}
    seen_ids = set()

    def error(item_id: str, field: str, message: str) -> None:
        errors.append({"item_id": item_id, "field": field, "message": message})

    for row in rows:
        item_id, source_type = row.get("item_id", ""), row.get("source_type", "")
        primary = row.get("expected_primary", "")
        secondary = [s.strip() for s in row.get("expected_secondary", "").split(";") if s.strip()]
        if not item_id or item_id in seen_ids:
            error(item_id, "item_id", "missing item_id" if not item_id else "duplicate item_id")
        seen_ids.add(item_id)
        if row.get("label_source"):
            confidence, reviewed = row.get("draft_confidence", ""), row.get("reviewed", "")
            if confidence not in CONFIDENCE_ORDER:
                error(item_id, "draft_confidence", f"draft_confidence '{confidence}' is not one of high, medium, low")
            else:
                review["by_confidence"][confidence] += 1
            if reviewed not in ("True", "False"):
                error(item_id, "reviewed", f"reviewed '{reviewed}' is not True or False")
            else:
                review["reviewed" if reviewed == "True" else "drafted"] += 1
            match = RULE_ID.search(row.get("review_notes", "")) if row["label_source"] == ADJUDICATED else None
            if match:
                rules[match.group(0)] += 1
            review["human_adjudicated"] += row["label_source"] == HUMAN_ADJUDICATED
        if source_type not in ALLOWED_TYPE:
            error(item_id, "source_type", f"source_type '{source_type}' is not one of {', '.join(ALLOWED_TYPE)}")
            continue
        by_source_type[source_type]["total"] += 1
        if primary:
            by_source_type[source_type]["labelled"] += 1
            problem = None if primary == NONE_LABEL else _id_problem(primary, source_type, node_types)
            if problem:
                error(item_id, "expected_primary", problem)
        if secondary:
            problems = _secondary_problems(primary, secondary, source_type, node_types)
            if problems:
                error(item_id, "expected_secondary", "; ".join(problems))
        if row.get("second_primary"):
            _second_labeller_errors(row, source_type, node_types, error)
            if row.get("agreement") in AGREEMENT_LEVELS:
                agreement[row["agreement"]] += 1
            agreement["needs_review"] += needs_review(row)
            primaries.append(primary)
            second_primaries.append(row["second_primary"])

    return {
        "total": sum(c["total"] for c in by_source_type.values()),
        "labelled": sum(c["labelled"] for c in by_source_type.values()),
        "by_source_type": by_source_type,
        "errors": errors,
        "review": dict(review, adjudicated_by_rule=dict(sorted(rules.items()))),
        "agreement": dict(agreement, kappa=cohens_kappa(primaries, second_primaries) if primaries else None),
    }


def review_order(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Cross-checked sheets: disagree -> partial -> agree with review notes (low confidence) -> rest.
    Draft-only sheets: low -> medium -> high draft_confidence. Sheet order is kept within a group.
    """
    if any(row.get("agreement") for row in rows):
        def group(row):
            if row.get("reviewed") == "True":
                return 4
            if row.get("agreement") == "disagree":
                return 0
            if row.get("agreement") == "partial":
                return 1
            return 2 if row.get("review_notes") else 3
        return sorted(rows, key=group)
    return sorted(rows, key=lambda row: CONFIDENCE_ORDER.get(row.get("draft_confidence", ""), len(CONFIDENCE_ORDER)))


def write_review_order(labels_path: str = DEFAULT_LABELS, out_path: str = DEFAULT_REVIEW_ORDER) -> None:
    rows = load_labels(labels_path)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(review_order(rows))


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["--write-review-order"]:
        write_review_order()
        print(f"Wrote {DEFAULT_REVIEW_ORDER}")
        return 0
    path = argv[0] if argv else DEFAULT_LABELS
    report = validate_rows(load_labels(path), load_node_types())
    per_type = ", ".join(f"{t} {c['labelled']}/{c['total']}" for t, c in report["by_source_type"].items())
    print(f"{os.path.basename(path)}: labelled {report['labelled']} / {report['total']} ({per_type})")
    review = report["review"]
    if review["reviewed"] or review["drafted"]:
        by_confidence = ", ".join(f"{level} {n}" for level, n in review["by_confidence"].items())
        print(f"  reviewed {review['reviewed']} / drafted (not yet reviewed) {review['drafted']}; "
              f"draft confidence: {by_confidence}")
    agreement = report["agreement"]
    if agreement["kappa"] is not None:
        print(f"  second labeller: agree {agreement['agree']}, partial {agreement['partial']}, "
              f"disagree {agreement['disagree']}; Cohen's kappa (current primary vs second labeller) {agreement['kappa']:.3f}; "
              f"rows needing review {agreement['needs_review']}")
    if review["adjudicated_by_rule"]:
        print(f"  adjudicated by reviewer rules: {review['adjudicated_by_rule']}; "
              f"decided individually by the reviewer: {review['human_adjudicated']}")
    for e in report["errors"]:
        print(f"  INVALID {e['item_id']} {e['field']}: {e['message']}")
    print(f"{len(report['errors'])} invalid row field(s)" if report["errors"] else "No invalid rows.")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())

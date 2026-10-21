"""
Phase 13 part 1: validates the benchmark labelling sheet (labels_v1.0.csv) against taxonomy v1.0.

Rules (LABELLING_GUIDE.md): syllabus rows take high_level_concept ids, interview rows granular_skill ids;
expected_primary is one id, "none", or empty (= not labelled yet); expected_secondary is an optional
";"-separated list of other ids of the same type, only alongside a real primary. Reports labelled rows per
source type and every invalid row; exits with code 1 if any row is invalid.

Usage:
    python evaluation/benchmark/validate_labels.py [path/to/labels.csv]
"""
import csv
import json
import os
import sys
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_LABELS = os.path.join(ROOT, "evaluation", "benchmark", "labels_v1.0.csv")
# Labels are pinned to taxonomy v1.0, independent of the scoring config's current taxonomy.
TAXONOMY_PATH = os.path.join(ROOT, "data", "taxonomy", "taxonomy_v1.0.json")

COLUMNS = ["item_id", "source_type", "course_or_report", "raw_text", "expected_primary", "expected_secondary",
           "label_notes"]
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


def validate_rows(rows: List[Dict[str, str]], node_types: Dict[str, str]) -> Dict[str, Any]:
    """{"total", "labelled", "by_source_type": {type: {"total", "labelled"}}, "errors": [{item_id, field, message}]}."""
    errors: List[Dict[str, str]] = []
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

    return {
        "total": sum(c["total"] for c in by_source_type.values()),
        "labelled": sum(c["labelled"] for c in by_source_type.values()),
        "by_source_type": by_source_type,
        "errors": errors,
    }


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    path = argv[0] if argv else DEFAULT_LABELS
    report = validate_rows(load_labels(path), load_node_types())
    per_type = ", ".join(f"{t} {c['labelled']}/{c['total']}" for t, c in report["by_source_type"].items())
    print(f"{os.path.basename(path)}: labelled {report['labelled']} / {report['total']} ({per_type})")
    for e in report["errors"]:
        print(f"  INVALID {e['item_id']} {e['field']}: {e['message']}")
    print(f"{len(report['errors'])} invalid row field(s)" if report["errors"] else "No invalid rows.")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())

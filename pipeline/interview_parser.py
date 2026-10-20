"""
Interview Parser Module (Phase 2)

Filters processed interview question rows before scoring (rules in
config/scoring_v1.1.json -> interview_filter):
- round_type in exclude_round_types (behavioral)  -> "behavioral_round"
- needs_review is true                            -> "needs_review"
- no question_text (empty / "nan")                -> "no_question_text"

The report count used for the density gate and the I(t) denominator is the
number of distinct reports with at least one included question.
"""
import csv
import os
from typing import Any, Dict, List, Tuple

from pipeline.config import load_scoring_config

EXCLUSION_REASON_FIELD = "exclusion_reason"
_TRUE_VALUES = {"true", "1", "yes"}


def _is_empty(value: Any) -> bool:
    return value is None or str(value).strip().lower() in ("", "nan")


def _is_true(value: Any) -> bool:
    return value is True or str(value).strip().lower() in _TRUE_VALUES


def _exclusion_reasons(row: Dict[str, Any], rules: Dict[str, Any]) -> List[str]:
    reasons = []
    round_type = str(row.get("round_type") or "").strip().lower()
    if round_type in {t.lower() for t in rules["exclude_round_types"]}:
        reasons.append("behavioral_round")
    if rules["exclude_needs_review"] and _is_true(row.get("needs_review")):
        reasons.append("needs_review")
    if rules["require_question_text"] and _is_empty(row.get("question_text")):
        reasons.append("no_question_text")
    return reasons


def filter_questions(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Splits question rows into (included, excluded); excluded rows are copies carrying exclusion_reason."""
    rules = load_scoring_config()["interview_filter"]
    included: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []
    for row in rows:
        reasons = _exclusion_reasons(row, rules)
        if reasons:
            excluded.append({**row, EXCLUSION_REASON_FIELD: ";".join(reasons)})
        else:
            included.append(row)
    return included, excluded


def count_reports(rows: List[Dict[str, Any]]) -> int:
    """Number of distinct non-empty report_ids among the given rows."""
    return len({str(r.get("report_id") or "").strip() for r in rows} - {""})


def load_questions_csv(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_excluded_questions(excluded: List[Dict[str, Any]], path: str) -> None:
    """Writes excluded rows with their original columns plus exclusion_reason."""
    fieldnames: List[str] = []
    for row in excluded:
        for key in row:
            if key != EXCLUSION_REASON_FIELD and key not in fieldnames:
                fieldnames.append(key)
    fieldnames.append(EXCLUSION_REASON_FIELD)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(excluded)

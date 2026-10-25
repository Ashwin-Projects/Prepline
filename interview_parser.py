"""Load reviewed interview-report indexes while preserving review metadata."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "data/raw/interviews/amazon_sde1_interview_experiences_phase2.csv"


def load_interview_index(path: str | Path = DEFAULT_INDEX, eligible_only: bool = False) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    required = {"report_id", "company", "role", "question_topic_summary", "source_url",
                "deduplication_status", "source_review_status", "legal_review_status"}
    if rows and not required.issubset(rows[0]):
        raise ValueError(f"Interview index is missing columns: {sorted(required - set(rows[0]))}")
    ids = [row["report_id"].strip() for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Interview report IDs must be unique")
    if not eligible_only:
        return rows
    return [row for row in rows if
            row.get("deduplication_status", "").strip().casefold() in {"unique", "confirmed unique", "verified unique"}
            and row.get("source_review_status", "").strip().casefold() in {"reviewed", "approved", "verified"}
            and row.get("legal_review_status", "").strip().casefold() in {"approved", "permitted", "cleared"}
            and row.get("permission_basis", "").strip()
            and row.get("deduplication_evidence", "").strip()
            and row.get("reviewer", "").strip()
            and row.get("review_date", "").strip()]

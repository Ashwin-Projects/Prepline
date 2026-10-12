"""
Phase 12.1 - Unmapped Terms Logging

Appends below-threshold intermediate concepts to an append-only JSON
Lines log whenever Phase 5 matching finds no taxonomy node for a term.
This module ONLY writes.
"""
import json
import os
from datetime import datetime, timezone
from typing import List, Optional

LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "processed",
    "unmapped_terms.log"
)


def log_unmapped_terms(
    terms: List[str],
    source_type: str,
    taxonomy_version: str,
    source_id: Optional[str] = None,
    log_path: Optional[str] = None,
) -> None:
    """
    Append one JSON line per unmapped term/occurrence.
    `source_type` is "interview" or "syllabus" (Phase 12.1: "term,
    frequency, source type, taxonomy version" - frequency is derived
    at review time by counting distinct sources, not stored here).
    `source_id` lets the review step count each source once, so rerunning
    the pipeline over the same data does not inflate frequency.
    """
    if not terms:
        return
    log_path = log_path or LOG_PATH
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logged_at = datetime.now(timezone.utc).isoformat()
    with open(log_path, "a", encoding="utf-8") as f:
        for term in terms:
            entry = {
                "term": term,
                "source_id": source_id,
                "source_type": source_type,
                "taxonomy_version": taxonomy_version,
                "logged_at": logged_at,
            }
            f.write(json.dumps(entry) + "\n")

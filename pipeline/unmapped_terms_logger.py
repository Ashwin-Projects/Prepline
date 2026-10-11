"""
Phase 12.1 - Unmapped Terms Logging

Appends below-threshold intermediate concepts to an append-only JSON
Lines log whenever Phase 5 matching finds no taxonomy node for a term.
This module ONLY writes. 
"""
import json
import os
from datetime import datetime, timezone
from typing import List

LOG_PATH = os.path.join("data", "processed", "unmapped_terms.log")


def log_unmapped_terms(terms: List[str],source_type: str,
    taxonomy_version: str,log_path: str = LOG_PATH,) -> None:
    """
    Append one JSON line per unmapped term/occurrence.
    `source_type` is "interview" or "syllabus" (Phase 12.1: "term,
    frequency, source type, taxonomy version" - frequency is derived
    at review time by counting lines, not stored here).
    """
    if not terms:
        return
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as f:
        for term in terms:
            entry = {
                "term": term,
                "source_type": source_type,
                "taxonomy_version": taxonomy_version,
                "logged_at": datetime.now(timezone.utc).isoformat(),
            }
            f.write(json.dumps(entry) + "\n")
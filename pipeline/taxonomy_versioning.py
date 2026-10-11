"""
Phase 12.3-12.5 - Taxonomy Versioning Governance

Does NOT automate migration or recalculation (12.5 forbids that).
Gives the human reviewer a structured, auditable way to record a version change and find which 
(company, role) pairs need a manual rerun.
"""
import json
import os
from datetime import datetime, timezone
from typing import List, Literal

CHANGELOG_PATH = os.path.join("data", "taxonomy", "taxonomy_changelog.json")

ChangeType = Literal["additive", "structural"]


def _load_changelog(path: str = CHANGELOG_PATH) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def _save_changelog(entries: list[dict], path: str = CHANGELOG_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)


def record_taxonomy_version_change(
    change_type: ChangeType,
    old_version: str,
    new_version: str,
    affected_topic_ids: List[str],
    reason: str,
    reviewed_by: str,
) -> dict:
    """
    - "additive": new leaf/node added. Only company/role pairs touching affected_topic_ids need a manual rerun; 
      everything else stays under old_version.
    - "structural": rename/merge/split/restructure. ALL mappings that touched affected_topic_ids under old_version 
      are incompatible with new_version and must be manually rerun; old results are preserved, never silently compared 
      across versions.
    """
    entry = {
        "change_type": change_type,
        "old_version": old_version,
        "new_version": new_version,
        "affected_topic_ids": affected_topic_ids,
        "reason": reason,
        "reviewed_by": reviewed_by,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    entries = _load_changelog()
    entries.append(entry)
    _save_changelog(entries)
    return entry


def find_affected_company_role_pairs(
    affected_topic_ids: List[str],
    stored_mappings: List[dict],) -> List[tuple[str, str]]:
    """
    Read-only: tells you what to rerun, does not rerun it.
    `stored_mappings` is whatever Sprint 5 persists - just needs
    "company", "role", "matched_topic_ids" keys per record.
    """
    affected = set(affected_topic_ids)
    pairs = set()
    for record in stored_mappings:
        if affected.intersection(record.get("matched_topic_ids", [])):
            pairs.add((record["company"], record["role"]))
    return sorted(pairs)


def get_changelog(path: str = CHANGELOG_PATH) -> list[dict]:
    return _load_changelog(path)
"""
Phase 12.3-12.5 - Taxonomy Versioning Governance

Does NOT automate migration or recalculation (12.5 forbids that).
Gives the human reviewer a structured, auditable way to record a version change and find which
mappings / (company, role) pairs need a manual rerun.
"""
import json
import os
from datetime import datetime, timezone
from typing import List, Literal, Optional, Tuple

CHANGELOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "taxonomy",
    "taxonomy_changelog.json"
)

ChangeType = Literal["additive", "structural"]
VALID_CHANGE_TYPES = ("additive", "structural")


def _load_changelog(path: Optional[str] = None) -> List[dict]:
    path = path or CHANGELOG_PATH
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_changelog(entries: List[dict], path: Optional[str] = None) -> None:
    path = path or CHANGELOG_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def record_taxonomy_version_change(
    change_type: ChangeType,
    old_version: str,
    new_version: str,
    affected_topic_ids: List[str],
    reason: str,
    reviewed_by: str,
    changelog_path: Optional[str] = None,
) -> dict:
    """
    - "additive": new leaf/node added. Only company/role pairs touching affected_topic_ids need a manual rerun;
      everything else stays under old_version.
    - "structural": rename/merge/split/restructure/redefinition. ALL mappings that touched affected_topic_ids under
      old_version are incompatible with new_version and must be manually rerun; old results are preserved, never
      silently compared across versions.
    """
    if change_type not in VALID_CHANGE_TYPES:
        raise ValueError(f"change_type must be one of {VALID_CHANGE_TYPES}, got {change_type!r}")
    if not old_version or not new_version or old_version == new_version:
        raise ValueError("new_version must be a non-empty version string different from old_version.")
    if not affected_topic_ids:
        raise ValueError("affected_topic_ids must list at least one topic_id.")

    entries = _load_changelog(changelog_path)
    if any(e["new_version"] == new_version for e in entries):
        raise ValueError(f"Taxonomy version {new_version!r} is already recorded in the changelog.")

    entry = {
        "change_type": change_type,
        "old_version": old_version,
        "new_version": new_version,
        "affected_topic_ids": sorted(set(affected_topic_ids)),
        "reason": reason,
        "reviewed_by": reviewed_by,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    entries.append(entry)
    _save_changelog(entries, changelog_path)
    return entry


def _record_topic_ids(record: dict) -> set:
    """Topic IDs a stored record touched - per-question mappings use matched_topic_ids, scored results use credit/topic_id."""
    topic_ids = set(record.get("matched_topic_ids", []))
    topic_ids.update(record.get("credit", {}).keys())
    if "topic_id" in record:
        topic_ids.add(record["topic_id"])
    return topic_ids


def find_affected_mappings(
    affected_topic_ids: List[str],
    stored_mappings: List[dict],
    old_version: Optional[str] = None,
) -> List[dict]:
    """
    Read-only (Phase 12.4): every stored mapping, interview or syllabus, that touched an affected topic.
    If old_version is given, only records stored under that taxonomy_version are returned - results under
    other versions are not part of this change.
    """
    affected = set(affected_topic_ids)
    return [
        record for record in stored_mappings
        if (old_version is None or record.get("taxonomy_version") == old_version)
        and affected.intersection(_record_topic_ids(record))
    ]


def find_affected_company_role_pairs(
    affected_topic_ids: List[str],
    stored_mappings: List[dict],
    old_version: Optional[str] = None,
) -> List[Tuple[str, str]]:
    """
    Read-only (Phase 12.3): tells you what to rerun, does not rerun it.
    Records without "company" / "role" keys (e.g. syllabus mappings) are skipped here;
    use find_affected_mappings() to see those.
    """
    pairs = set()
    for record in find_affected_mappings(affected_topic_ids, stored_mappings, old_version):
        if record.get("company") and record.get("role"):
            pairs.add((record["company"], record["role"]))
    return sorted(pairs)


def get_changelog(path: Optional[str] = None) -> List[dict]:
    return _load_changelog(path)

#!/usr/bin/env python3
"""Validate Prepline dataset schemas and taxonomy references; never auto-approve labels."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = ROOT / "data/taxonomy/taxonomy_v1.1.json"
CANDIDATE_FILES = [
    ROOT / "evaluation/source_backed_mappings_for_review.csv",
    ROOT / "evaluation/codeprep_mappings_for_review.csv",
]
GROUND_TRUTH = ROOT / "evaluation/ground_truth.csv"
INTERVIEWS = ROOT / "data/raw/interviews/amazon_sde1_interview_experiences_phase2.csv"
REQUIRED_MAPPING = {
    "raw_text", "expected_topic_id", "taxonomy_version", "source_id",
    "source_type", "source_url", "review_status", "reviewer", "review_date", "notes"
}
REQUIRED_INTERVIEW = {
    "report_id", "company", "role", "rounds", "question_topic_summary",
    "source_url", "source_date_or_page_date", "source_platform",
    "deduplication_status", "source_review_status", "legal_review_status",
    "deduplication_evidence", "permission_basis", "reviewer", "review_date"
}


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return set(reader.fieldnames or []), list(reader)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict-accepted", action="store_true",
                        help="Fail if Phase 2 or Phase 13 acceptance gates are not met.")
    args = parser.parse_args()
    errors, warnings = [], []
    taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    version = taxonomy.get("taxonomy_version")
    topics = {topic["topic_id"] for topic in taxonomy.get("topics", [])}

    all_candidates = []
    for path in CANDIDATE_FILES:
        if not path.exists():
            warnings.append(f"Candidate file missing: {path.relative_to(ROOT)}")
            continue
        fields, rows = read_rows(path)
        missing = REQUIRED_MAPPING - fields
        if missing:
            errors.append(f"{path.relative_to(ROOT)} missing columns: {sorted(missing)}")
        for line, row in enumerate(rows, start=2):
            if not row.get("raw_text", "").strip():
                errors.append(f"{path.relative_to(ROOT)}:{line}: empty raw_text")
            if row.get("expected_topic_id") not in topics:
                errors.append(f"{path.relative_to(ROOT)}:{line}: unknown topic ID {row.get('expected_topic_id')!r}")
            if row.get("taxonomy_version") != version:
                errors.append(f"{path.relative_to(ROOT)}:{line}: taxonomy version does not match {version}")
        all_candidates.extend(rows)
        print(f"PASS schema/reference check: {path.relative_to(ROOT)} ({len(rows)} rows)")

    pair_keys = [(r.get("raw_text", "").strip().casefold(), r.get("expected_topic_id", "").strip()) for r in all_candidates]
    if len(pair_keys) != len(set(pair_keys)):
        errors.append("Candidate files contain duplicate raw_text/topic pairs across files.")
    print(f"Candidate pool: {len(all_candidates)} rows, {len(set(pair_keys))} unique pairs; none counted as accepted labels.")

    if GROUND_TRUTH.exists():
        fields, rows = read_rows(GROUND_TRUTH)
        missing = REQUIRED_MAPPING - fields
        if missing:
            errors.append(f"ground_truth.csv missing columns: {sorted(missing)}")
        accepted = [r for r in rows if r.get("review_status", "").strip().lower() in {"verified", "approved"}]
        for line, row in enumerate(accepted, start=2):
            for key in ("raw_text", "source_id", "source_type", "source_url", "reviewer", "review_date"):
                if not row.get(key, "").strip():
                    errors.append(f"ground_truth.csv:{line}: accepted row missing {key}")
            if not row.get("source_url", "").strip().startswith(("https://", "http://")):
                errors.append(f"ground_truth.csv:{line}: accepted row source_url must be HTTP(S)")
            if row.get("expected_topic_id") not in topics:
                errors.append(f"ground_truth.csv:{line}: accepted row has unknown topic ID")
            if row.get("taxonomy_version") != version:
                errors.append(f"ground_truth.csv:{line}: accepted row taxonomy version mismatch")
        accepted_pairs = [(r.get("raw_text", "").strip().casefold(), r.get("expected_topic_id", "").strip()) for r in accepted]
        if len(accepted_pairs) != len(set(accepted_pairs)):
            errors.append("ground_truth.csv contains duplicate accepted text/topic pairs.")
        print(f"Ground truth: {len(rows)} rows; {len(accepted)} rows marked accepted (review fields validated, not independently authenticated).")
        if args.strict_accepted and len(set(accepted_pairs)) < 200:
            errors.append("Fewer than 200 distinct accepted Phase 13 mappings.")
    else:
        warnings.append("ground_truth.csv missing")
        if args.strict_accepted:
            errors.append("ground_truth.csv is required for strict acceptance.")

    if INTERVIEWS.exists():
        fields, rows = read_rows(INTERVIEWS)
        missing = REQUIRED_INTERVIEW - fields
        if missing:
            errors.append(f"Phase 2 interview index missing columns: {sorted(missing)}")
        ready = [r for r in rows if r.get("deduplication_status", "").strip().lower() in {"unique", "confirmed unique", "verified unique"}
                 and r.get("source_review_status", "").strip().lower() in {"reviewed", "approved", "verified"}
                 and r.get("legal_review_status", "").strip().lower() in {"approved", "permitted", "cleared"}]
        ready_ids = {r.get("report_id", "").strip() for r in ready if r.get("report_id", "").strip()}
        print(f"Phase 2 interview index: {len(rows)} candidates; {len(ready_ids)} satisfy review-status fields.")
        if args.strict_accepted and len(ready_ids) < 15:
            errors.append("Fewer than 15 reports satisfy Phase 2 review-status fields.")
    else:
        warnings.append("Phase 2 interview index missing")
        if args.strict_accepted:
            errors.append("Phase 2 interview index is required for strict acceptance.")

    for warning in warnings:
        print("WARNING:", warning)
    for error in errors:
        print("ERROR:", error)
    if errors:
        print(f"FAILED: {len(errors)} error(s).")
        return 1
    print("PASS: structural validation succeeded. This does not certify legal permission or the truth of human-review records.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

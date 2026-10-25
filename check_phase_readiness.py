"""Check Phase 2 and Phase 13 completion gates without treating candidates as verified.

Run from repository root:
    python scripts/check_phase_readiness.py

This checks recorded evidence fields; it cannot independently prove consent, license
compliance, reviewer identity, or the quality of a human decision.
"""
from pathlib import Path
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
INTERVIEWS = ROOT / "data/raw/interviews/amazon_sde1_interview_experiences_phase2.csv"
GROUND_TRUTH = ROOT / "evaluation/ground_truth.csv"
CANDIDATE_FILES = [
    ROOT / "evaluation/source_backed_mappings_for_review.csv",
    ROOT / "evaluation/codeprep_mappings_for_review.csv",
]
TAXONOMY = ROOT / "data/taxonomy/taxonomy_v1.1.json"
SYLLABUS = ROOT / "data/raw/syllabi/VIT_CSE_2024_2025.pdf"


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def nonempty(row, key):
    return bool(str(row.get(key, "") or "").strip())


def main():
    failures = []
    interview_rows = read_csv(INTERVIEWS) if INTERVIEWS.exists() else []
    required_phase2 = (
        "report_id", "source_url", "deduplication_evidence", "permission_basis",
        "reviewer", "review_date",
    )
    eligible = [
        row for row in interview_rows
        if all(nonempty(row, key) for key in required_phase2)
        and row.get("deduplication_status", "").strip().lower() in {"unique", "confirmed unique", "verified unique"}
        and row.get("source_review_status", "").strip().lower() in {"reviewed", "approved", "verified"}
        and row.get("legal_review_status", "").strip().lower() in {"approved", "permitted", "cleared"}
    ]
    unique_ids = {row.get("report_id", "").strip() for row in eligible}
    print(f"Phase 2: {len(unique_ids)} reports satisfy recorded source, permission, reviewer, and deduplication fields (minimum 15).")
    if len(unique_ids) < 15:
        failures.append("Phase 2: fewer than 15 independent reports have documented permission, review, and deduplication evidence.")
    if not SYLLABUS.exists():
        failures.append("Phase 2: official syllabus PDF is not present at data/raw/syllabi/VIT_CSE_2024_2025.pdf.")
    elif SYLLABUS.stat().st_size < 100_000:
        failures.append("Phase 2: syllabus PDF exists but is unexpectedly small; validate the download.")

    if not TAXONOMY.exists():
        failures.append("Phase 13: taxonomy v1.1 file is missing.")
        valid_topic_ids = set()
    else:
        taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
        valid_topic_ids = {topic["topic_id"] for topic in taxonomy.get("topics", [])}

    candidates = []
    for path in CANDIDATE_FILES:
        if path.exists():
            candidates.extend(read_csv(path))
    candidate_pairs = {
        (row.get("raw_text", "").strip().casefold(), row.get("expected_topic_id", "").strip())
        for row in candidates
        if nonempty(row, "raw_text") and row.get("expected_topic_id", "").strip() in valid_topic_ids
    }
    print(f"Phase 13 candidate pool: {len(candidates)} rows; {len(candidate_pairs)} unique valid text/topic pairs. Candidates are not accepted labels.")

    labels = read_csv(GROUND_TRUTH) if GROUND_TRUTH.exists() else []
    accepted = []
    required_label_fields = ("source_id", "source_type", "source_url", "reviewer", "review_date", "raw_text")
    for row in labels:
        if (
            all(nonempty(row, key) for key in required_label_fields)
            and row.get("source_url", "").strip().lower().startswith(("https://", "http://"))
            and row.get("review_status", "").strip().lower() in {"verified", "approved"}
            and row.get("expected_topic_id", "").strip() in valid_topic_ids
            and row.get("taxonomy_version", "").strip() == "v1.1"
        ):
            accepted.append(row)
    accepted_keys = {
        (row["raw_text"].strip().casefold(), row["expected_topic_id"].strip())
        for row in accepted
    }
    print(f"Phase 13: {len(accepted_keys)} unique source-backed labels satisfy the recorded approval fields (minimum 200).")
    if len(accepted_keys) < 200:
        failures.append("Phase 13: fewer than 200 unique mappings have complete provenance and explicit human-review fields.")
    if len(accepted) != len(accepted_keys):
        failures.append("Phase 13: duplicate approved text/topic pairs exist in ground_truth.csv.")

    if failures:
        print("\nNOT READY:")
        for failure in failures:
            print(f"- {failure}")
        print("\nDo not report final benchmark metrics until every gate is satisfied.")
        return 1
    print("\nReadiness fields pass. Independently confirm reviewer work and run the evaluation on the frozen dataset.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

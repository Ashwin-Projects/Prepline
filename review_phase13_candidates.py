#!/usr/bin/env python3
"""Human-in-the-loop review for Prepline Phase 13 mapping candidates.

Run from repository root:
    python scripts/review_phase13_candidates.py
Approved rows are written to ground_truth.csv; all decisions are recorded separately.
No candidate is auto-approved.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = [
    ROOT / "evaluation/codeprep_mappings_for_review.csv",
    ROOT / "evaluation/source_backed_mappings_for_review.csv",
]
DEFAULT_OUTPUT = ROOT / "evaluation/ground_truth.csv"
DEFAULT_LEDGER = ROOT / "evaluation/review_decisions.csv"
FIELDS = [
    "raw_text", "expected_topic_id", "taxonomy_version", "source_id",
    "source_type", "source_url", "review_status", "reviewer", "review_date", "notes"
]


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def pair(row: dict[str, str]) -> tuple[str, str]:
    return (row.get("raw_text", "").strip().casefold(), row.get("expected_topic_id", "").strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="*", default=[str(p) for p in DEFAULT_INPUTS])
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--taxonomy", default=str(ROOT / "data/taxonomy/taxonomy_v1.1.json"))
    parser.add_argument("--reviewer", default="")
    args = parser.parse_args()

    reviewer = args.reviewer.strip() or input("Reviewer name/identifier: ").strip()
    if not reviewer:
        parser.error("A reviewer identifier is required.")
    taxonomy = json.loads(Path(args.taxonomy).read_text(encoding="utf-8"))
    version = taxonomy.get("taxonomy_version", "unknown")
    topics = {t["topic_id"]: t for t in taxonomy.get("topics", [])}
    candidates = []
    for source in args.inputs:
        path = Path(source)
        if path.exists():
            candidates.extend(load_csv(path))
        else:
            print(f"Skipping missing input: {path}")

    output = Path(args.output)
    ledger_path = Path(args.ledger)
    accepted = load_csv(output)
    ledger = load_csv(ledger_path)
    seen = {pair(row) for row in accepted} | {pair(row) for row in ledger}
    pending = []
    candidate_seen = set()
    for row in candidates:
        key = pair(row)
        if not key[0] or key[1] not in topics or key in seen or key in candidate_seen:
            continue
        candidate_seen.add(key)
        pending.append(row)

    print(f"Taxonomy {version}: {len(topics)} topics; {len(pending)} new candidates; {len(accepted)} approved labels already in ground_truth.csv.")
    print("Before approving, inspect the original source, permission/license, and taxonomy fit.")
    for index, row in enumerate(pending, start=1):
        topic_id = row.get("expected_topic_id", "").strip()
        print("\n" + "=" * 78)
        print(f"[{index}/{len(pending)}] {row.get('source_id','')} | {topic_id} — {topics[topic_id].get('name','')}")
        print("Prompt:", row.get("raw_text", ""))
        print("Source:", row.get("source_url", ""))
        print("Notes:", row.get("notes", ""))
        choice = input("[a]pprove / [r]eject / [s]kip / [q]uit: ").strip().lower()
        if choice == "q":
            break
        if choice not in {"a", "r"}:
            continue
        review_note = input("Review note (optional): ").strip()
        record = {key: str(row.get(key, "") or "") for key in FIELDS}
        record["taxonomy_version"] = version
        record["review_status"] = "verified" if choice == "a" else "rejected"
        record["reviewer"] = reviewer
        record["review_date"] = date.today().isoformat()
        record["notes"] = (record.get("notes", "") + (" | " if record.get("notes") else "") + f"Human review: {review_note}").strip()
        ledger.append(record)
        if choice == "a":
            accepted.append(record)
            write_csv(output, accepted)
        write_csv(ledger_path, ledger)
        seen.add(pair(record))
        print(f"Saved {record['review_status']} decision to {ledger_path}")
        if choice == "a":
            print(f"Approved mapping added to {output}")
    print(f"\\nApproved unique labels in ground_truth.csv: {len({pair(row) for row in accepted})}")
    print("Do not claim the benchmark is complete until 200+ distinct labels and source eligibility have been independently confirmed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Phase 12.2 - Manual Review of Unmapped Terms

Reads data/processed/unmapped_terms.log and produces a frequency-sorted
report for a human to review on a set schedule. READ-ONLY - never
writes to the taxonomy or triggers a rerun.

Usage:
    python3 evaluation/review_unmapped_terms.py
    python3 evaluation/review_unmapped_terms.py --taxonomy-version v1.0
    python3 evaluation/review_unmapped_terms.py --min-count 2 --export data/processed/unmapped_review.csv
"""
import argparse
import csv
import json
import os
from collections import defaultdict

LOG_PATH = os.path.join("data", "processed", "unmapped_terms.log")


def load_log(log_path: str = LOG_PATH) -> list[dict]:
    if not os.path.exists(log_path):
        return []
    entries = []
    with open(log_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def aggregate(entries: list[dict], taxonomy_version: str | None = None) -> list[dict]:
    counts = defaultdict(int)
    first_seen = {}
    last_seen = {}
    for e in entries:
        if taxonomy_version and e["taxonomy_version"] != taxonomy_version:
            continue
        key = (e["term"], e["taxonomy_version"], e["source_type"])
        counts[key] += 1
        ts = e["logged_at"]
        if key not in first_seen or ts < first_seen[key]:
            first_seen[key] = ts
        if key not in last_seen or ts > last_seen[key]:
            last_seen[key] = ts

    rows = [
        {
            "term": term,
            "taxonomy_version": tv,
            "source_type": st,
            "frequency": count,
            "first_seen": first_seen[(term, tv, st)],
            "last_seen": last_seen[(term, tv, st)],
        }
        for (term, tv, st), count in counts.items()
    ]
    rows.sort(key=lambda r: -r["frequency"])
    return rows


def main():
    parser = argparse.ArgumentParser(description="Review unmapped terms, sorted by frequency.")
    parser.add_argument("--taxonomy-version", default=None)
    parser.add_argument("--min-count", type=int, default=1)
    parser.add_argument("--export", default=None)
    args = parser.parse_args()

    entries = load_log()
    if not entries:
        print(f"No unmapped terms logged yet at {LOG_PATH}.")
        return

    rows = aggregate(entries, taxonomy_version=args.taxonomy_version)
    rows = [r for r in rows if r["frequency"] >= args.min_count]

    if not rows:
        print("No unmapped terms match the given filters.")
        return

    print(f"{'FREQ':>5}  {'TAXONOMY':<10}  {'SOURCE':<10}  TERM")
    print("-" * 70)
    for r in rows:
        print(f"{r['frequency']:>5}  {r['taxonomy_version']:<10}  {r['source_type']:<10}  {r['term']}")

    print(f"\n{len(rows)} distinct unmapped terms shown. Review these manually and decide, per term:")
    print("  - add as a new taxonomy leaf/node (Phase 12.3, additive)")
    print("  - fold into an existing node's description (no taxonomy version bump needed)")
    print("  - ignore (noise / not a real curriculum topic)")

    if args.export:
        os.makedirs(os.path.dirname(args.export) or ".", exist_ok=True)
        with open(args.export, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["term", "taxonomy_version", "source_type", "frequency", "first_seen", "last_seen"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nExported to {args.export}")


if __name__ == "__main__":
    main()
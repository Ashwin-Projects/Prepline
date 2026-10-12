"""
Phase 12.2 - Manual Review of Unmapped Terms

Reads data/processed/unmapped_terms.log and produces a frequency-sorted
report for a human to review on a set schedule. READ-ONLY - never
writes to the taxonomy or triggers a rerun.

Frequency = number of distinct sources (source_id) in which the term was
unmapped. The API reruns the interview pipeline on every request, so raw
log lines repeat; counting distinct sources keeps frequency stable.
Entries logged without a source_id are counted once per line.

Usage:
    python evaluation/review_unmapped_terms.py
    python evaluation/review_unmapped_terms.py --taxonomy-version v1.0
    python evaluation/review_unmapped_terms.py --min-count 2 --export data/processed/unmapped_review.csv
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from typing import List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from pipeline.unmapped_terms_logger import LOG_PATH

FIELDNAMES = ["term", "taxonomy_version", "source_type", "frequency", "occurrences", "first_seen", "last_seen"]


def load_log(log_path: Optional[str] = None) -> List[dict]:
    log_path = log_path or LOG_PATH
    if not os.path.exists(log_path):
        return []
    entries = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Skipping malformed log line {line_no}", file=sys.stderr)
    return entries


def aggregate(entries: List[dict], taxonomy_version: Optional[str] = None) -> List[dict]:
    sources = defaultdict(set)
    occurrences = defaultdict(int)
    first_seen = {}
    last_seen = {}
    for i, e in enumerate(entries):
        if taxonomy_version and e.get("taxonomy_version") != taxonomy_version:
            continue
        key = (e["term"], e.get("taxonomy_version"), e.get("source_type"))
        sources[key].add(e.get("source_id") or f"__line_{i}")
        occurrences[key] += 1
        ts = e.get("logged_at", "")
        if key not in first_seen or ts < first_seen[key]:
            first_seen[key] = ts
        if key not in last_seen or ts > last_seen[key]:
            last_seen[key] = ts

    rows = [
        {
            "term": term,
            "taxonomy_version": tv,
            "source_type": st,
            "frequency": len(sources[(term, tv, st)]),
            "occurrences": occurrences[(term, tv, st)],
            "first_seen": first_seen[(term, tv, st)],
            "last_seen": last_seen[(term, tv, st)],
        }
        for (term, tv, st) in sources
    ]
    rows.sort(key=lambda r: (-r["frequency"], r["term"]))
    return rows


def main():
    parser = argparse.ArgumentParser(description="Review unmapped terms, sorted by frequency.")
    parser.add_argument("--taxonomy-version", default=None)
    parser.add_argument("--min-count", type=int, default=1)
    parser.add_argument("--export", default=None)
    parser.add_argument("--log-path", default=None)
    args = parser.parse_args()

    log_path = args.log_path or LOG_PATH
    entries = load_log(log_path)
    if not entries:
        print(f"No unmapped terms logged yet at {log_path}.")
        return

    rows = aggregate(entries, taxonomy_version=args.taxonomy_version)
    rows = [r for r in rows if r["frequency"] >= args.min_count]

    if not rows:
        print("No unmapped terms match the given filters.")
        return

    print(f"{'FREQ':>5}  {'TAXONOMY':<10}  {'SOURCE':<10}  TERM")
    print("-" * 70)
    for r in rows:
        print(f"{r['frequency']:>5}  {str(r['taxonomy_version']):<10}  {str(r['source_type']):<10}  {r['term']}")

    print(f"\n{len(rows)} distinct unmapped terms shown. Review these manually and decide, per term:")
    print("  - add as a new taxonomy leaf/node (Phase 12.3, additive -> new taxonomy version)")
    print("  - fold into an existing node's description (changes matching -> also a new taxonomy version)")
    print("  - ignore (noise / not a real curriculum topic)")

    if args.export:
        os.makedirs(os.path.dirname(args.export) or ".", exist_ok=True)
        with open(args.export, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nExported to {args.export}")


if __name__ == "__main__":
    main()

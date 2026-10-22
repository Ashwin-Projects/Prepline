"""
Phase 13 part 2: grouped dev/val/test split of the benchmark labels (SPLIT_PLAN.md).

Each source_type is split separately. Groups (a course's theory + lab files, or one interview report) are sorted by key,
shuffled with random.Random(SEED), and assigned in that order, each to the split furthest below its target row count
(70 / 15 / 15 %); ties go to test, then val, then dev. The split file is versioned and never overwritten.

Usage:
    python evaluation/benchmark/build_splits.py
"""
import csv
import os
import random
import sys
from collections import Counter, defaultdict
from typing import Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from evaluation.benchmark.validate_labels import DEFAULT_LABELS, load_labels

SEED = 20261022
TARGETS = {"dev": 0.70, "val": 0.15, "test": 0.15}
TIE_ORDER = ["test", "val", "dev"]
DEFAULT_SPLITS = os.path.join(ROOT, "evaluation", "benchmark", "splits_v1.0.csv")
COLUMNS = ["item_id", "source_type", "group", "split"]


def group_key(row: Dict[str, str]) -> str:
    """Syllabus: the course code without its trailing L/P/E (BCSE202L + BCSE202P -> BCSE202); interview: the report id."""
    key = row["course_or_report"]
    return key[:-1] if row["source_type"] == "syllabus" and key[-1:] in ("L", "P", "E") else key


def build_splits(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """One {item_id, source_type, group, split} per row, in sheet order."""
    split_of_group: Dict[tuple, str] = {}
    for source_type in sorted({r["source_type"] for r in rows}):
        members = [r for r in rows if r["source_type"] == source_type]
        sizes = Counter(group_key(r) for r in members)
        groups = sorted(sizes)
        random.Random(SEED).shuffle(groups)
        targets = {split: share * len(members) for split, share in TARGETS.items()}
        filled = defaultdict(int)
        for group in groups:
            split = max(TIE_ORDER, key=lambda s: (targets[s] - filled[s], -TIE_ORDER.index(s)))
            split_of_group[(source_type, group)] = split
            filled[split] += sizes[group]
    return [{"item_id": r["item_id"], "source_type": r["source_type"], "group": group_key(r),
             "split": split_of_group[(r["source_type"], group_key(r))]} for r in rows]


def write_splits(splits: List[Dict[str, str]], path: str = DEFAULT_SPLITS) -> None:
    if os.path.exists(path):
        raise FileExistsError(f"{path} exists; splits are versioned and never overwritten")
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(splits)


def summary(splits: List[Dict[str, str]]) -> List[str]:
    lines = []
    for source_type in sorted({s["source_type"] for s in splits}):
        for split in TARGETS:
            members = [s for s in splits if s["source_type"] == source_type and s["split"] == split]
            groups = sorted({s["group"] for s in members})
            lines.append(f"{source_type:<9} {split:<4} {len(members):>3} rows, {len(groups):>2} groups: {', '.join(groups)}")
    return lines


def main() -> None:
    splits = build_splits(load_labels(DEFAULT_LABELS))
    print("\n".join(summary(splits)))
    write_splits(splits)
    print(f"Wrote {DEFAULT_SPLITS}")


if __name__ == "__main__":
    main()

"""
Builds the Markdown change log between two versioned PREPLINE results files, with a
sequential per-item attribution table (each step = one full pipeline run after one change).

Usage:
    python evaluation/compare_results.py --old results/amazon_sde1_v1.0.json --new results/amazon_sde1_v1.1.json \
        --step "Item 3 - interview filtering=runs/run_A.json" ... --notes-file notes.md --out results/CHANGES_v1.1.md
"""
import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

TOP_N = 10


def _fmt(value) -> str:
    if value is None:
        return "–"
    if isinstance(value, (int, float)):
        return str(round(value, 4))
    return str(value)


def _delta(new, old) -> str:
    if new is None or old is None:
        return "–"
    return _fmt(round(new - old, 4))


def _gap_label(gap: Optional[dict]) -> str:
    return f"{gap['topic_name']} (`{gap['topic_id']}`)" if gap else "–"


def _top_ids(result: dict) -> List[str]:
    return [g["topic_id"] for g in result.get("top_priority_gaps", [])[:TOP_N]]


def _ids_list(ids: Sequence[str]) -> str:
    return ", ".join(f"`{i}`" for i in ids) if ids else "–"


def build_changes(old: dict, new: dict, steps: List[Tuple[str, dict]], notes: Sequence[str] = (),
                  title: str = "PREPLINE results v1.0 → v1.1") -> str:
    lines: List[str] = [f"# {title}", ""]

    if notes:
        lines += ["## Read this first", ""] + [f"- {n}" for n in notes] + [""]

    lines += [
        "## Headline numbers",
        "",
        "| Metric | v1.0 | v1.1 | Change |",
        "|---|---|---|---|",
        f"| S_comp | {_fmt(old.get('S_comp'))} | {_fmt(new.get('S_comp'))} | {_delta(new.get('S_comp'), old.get('S_comp'))} |",
        f"| Report count | {_fmt(old.get('report_count'))} | {_fmt(new.get('report_count'))} | {_delta(new.get('report_count'), old.get('report_count'))} |",
        f"| Scoring universe (topics with I(t) > 0) | {_fmt(old.get('scoring_universe_size'))} | {_fmt(new.get('scoring_universe_size'))} | {_delta(new.get('scoring_universe_size'), old.get('scoring_universe_size'))} |",
        f"| Runtime (s) | {_fmt(old.get('runtime_seconds'))} | {_fmt(new.get('runtime_seconds'))} | {_delta(new.get('runtime_seconds'), old.get('runtime_seconds'))} |",
        "",
        "## Top-10 priority gaps, side by side",
        "",
        "| Rank | v1.0 topic | v1.0 gap | v1.1 topic | v1.1 gap |",
        "|---|---|---|---|---|",
    ]
    old_gaps = old.get("top_priority_gaps", [])[:TOP_N]
    new_gaps = new.get("top_priority_gaps", [])[:TOP_N]
    for i in range(max(len(old_gaps), len(new_gaps))):
        o = old_gaps[i] if i < len(old_gaps) else None
        n = new_gaps[i] if i < len(new_gaps) else None
        lines.append(
            f"| {i + 1} | {_gap_label(o)} | {_fmt(o['priority_gap']) if o else '–'} "
            f"| {_gap_label(n)} | {_fmt(n['priority_gap']) if n else '–'} |"
        )

    lines += [
        "",
        "## What caused each change (sequential attribution)",
        "",
        "Each row is a full pipeline run after one more item was applied, in this order; the deltas are relative "
        "to the row above, so an item's effect is measured on top of the items before it.",
        "",
        "| Step | S_comp | Δ S_comp | Scoring universe | Entered top 10 | Left top 10 | Runtime (s) |",
        "|---|---|---|---|---|---|---|",
        f"| v1.0 baseline | {_fmt(old.get('S_comp'))} | – | {_fmt(old.get('scoring_universe_size'))} | – | – | {_fmt(old.get('runtime_seconds'))} |",
    ]
    previous = old
    for label, result in steps:
        before, after = _top_ids(previous), _top_ids(result)
        entered = [t for t in after if t not in before]
        left = [t for t in before if t not in after]
        lines.append(
            f"| {label} | {_fmt(result.get('S_comp'))} | {_delta(result.get('S_comp'), previous.get('S_comp'))} "
            f"| {_fmt(result.get('scoring_universe_size'))} | {_ids_list(entered)} | {_ids_list(left)} "
            f"| {_fmt(result.get('runtime_seconds'))} |"
        )
        previous = result

    return "\n".join(lines) + "\n"


def _load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Build the change log between two PREPLINE results files.")
    parser.add_argument("--old", required=True)
    parser.add_argument("--new", required=True)
    parser.add_argument("--step", action="append", default=[], help='"LABEL=path/to/run.json", in application order')
    parser.add_argument("--notes-file", help="Markdown bullet lines (one per line) shown under 'Read this first'")
    parser.add_argument("--extra-file", help="Markdown appended verbatim after the tables")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    if os.path.exists(args.out):
        sys.exit(f"Refusing to overwrite existing file: {args.out}")

    steps: List[Tuple[str, Dict]] = []
    for spec in args.step:
        label, _, path = spec.partition("=")
        steps.append((label.strip(), _load(path.strip())))
    notes: List[str] = []
    if args.notes_file:
        with open(args.notes_file, "r", encoding="utf-8") as f:
            notes = [line.strip()[2:] if line.strip().startswith("- ") else line.strip() for line in f if line.strip()]

    md = build_changes(_load(args.old), _load(args.new), steps, notes)
    if args.extra_file:
        with open(args.extra_file, "r", encoding="utf-8") as f:
            md += "\n" + f.read()
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"Saved to {args.out}")


if __name__ == "__main__":
    main()

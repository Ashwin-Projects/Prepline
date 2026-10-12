"""
Full Phase 7-12 pipeline run for one company/role + one syllabus PDF, saved as a versioned result file.

Mirrors the backend /api/v1 flow (density gate -> coverage -> importance -> S_comp -> priority gaps) and adds
the run's top unmapped terms (Phase 12). Unmapped terms are logged to a run-specific log so the summary
reflects this run only, not the shared data/processed/unmapped_terms.log.

Usage:
    python evaluation/run_full_pipeline.py --pdf "path/to/VIT_CSE_2024_2025.pdf"
    python evaluation/run_full_pipeline.py --pdf syllabus.pdf --out results/amazon_sde1_v1.0.json
"""
import argparse
import json
import os
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pipeline.unmapped_terms_logger as unmapped_terms_logger
from pipeline.embeddings import SIMILARITY_THRESHOLD
from pipeline.syllabus_parser import parse_syllabus_pdf
from pipeline.scoring import (
    calculate_syllabus_coverage,
    calculate_topic_importance,
    calculate_composite_score,
    rank_priority_gaps,
    GAMMA_DEFAULT,
    MVP_REFERENCE_VALUES,
)
from evaluation.review_unmapped_terms import load_log, aggregate

COMPANY = "Amazon"
ROLE = "SDE-1"
MIN_REPORTS = 15
# No scoring config module exists yet; the backend hard-codes this same value (backend/routes.py).
SCORING_CONFIG_VERSION = "v1.0"
TOP_N = 10

DEFAULT_QUESTIONS = os.path.join(ROOT, "data", "processed", "questions.csv")
DEFAULT_REPORTS = os.path.join(ROOT, "data", "processed", "reports.csv")
DEFAULT_OUT = os.path.join(ROOT, "results", "amazon_sde1_v1.0.json")


def count_reports(reports_csv: str) -> int:
    import csv
    with open(reports_csv, "r", encoding="utf-8") as f:
        return len({row["report_id"].strip() for row in csv.DictReader(f) if row.get("report_id")})


def run(pdf_path: str, questions_csv: str, reports_csv: str) -> dict:
    report_count = count_reports(reports_csv)
    result = {
        "company": COMPANY,
        "role": ROLE,
        "report_count": report_count,
        "syllabus_file": os.path.basename(pdf_path),
        "taxonomy_version": None,
        "scoring_config_version": SCORING_CONFIG_VERSION,
        "scoring_config": {
            "gamma": GAMMA_DEFAULT,
            "similarity_threshold": SIMILARITY_THRESHOLD,
            "depth_reference_values": MVP_REFERENCE_VALUES,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if report_count < MIN_REPORTS:
        result.update(status="INSUFFICIENT_DATA", S_comp=None)
        return result

    run_log = os.path.join(tempfile.mkdtemp(prefix="prepline_run_"), "unmapped_terms.log")
    unmapped_terms_logger.LOG_PATH = run_log

    t0 = time.time()
    print("Parsing syllabus PDF (slow on scanned pages)...", flush=True)
    syllabus = parse_syllabus_pdf(pdf_path)
    print(f"  {syllabus['units_count']} units in {time.time() - t0:.0f}s", flush=True)

    coverage = calculate_syllabus_coverage(syllabus)
    print("Scoring interview questions...", flush=True)
    importance = calculate_topic_importance(questions_csv, total_reports_count=report_count)
    composite = calculate_composite_score(importance, coverage)
    gaps = rank_priority_gaps(importance, coverage)

    topics = coverage["topic_coverage"]
    present = [t for t in topics if t["presence"] == 1]
    unmapped_rows = aggregate(load_log(run_log))
    unmapped_rows.sort(key=lambda r: (-r["occurrences"], r["term"]))

    result.update(
        status="SUCCESS",
        taxonomy_version=composite["taxonomy_version"],
        S_comp=composite["S_comp"],
        scoring_universe_size=composite["scoring_universe_size"],
        syllabus_units=syllabus["units_count"],
        units_with_matches=sum(1 for m in syllabus["two_pass_mappings"] if m["matched_topic_ids"]),
        topics_present=len(present),
        topics_in_taxonomy=len(topics),
        depth_counts={
            "all_topics": dict(Counter(t["depth_status"] for t in topics)),
            "present_topics": dict(Counter(t["depth_status"] for t in present)),
        },
        top_priority_gaps=gaps[:TOP_N],
        unmapped_terms_summary={
            "distinct_terms": len({r["term"] for r in unmapped_rows}),
            "distinct_terms_by_source_type": dict(Counter(r["source_type"] for r in unmapped_rows)),
            "total_occurrences": sum(r["occurrences"] for r in unmapped_rows),
        },
        top_unmapped_terms=[
            {k: r[k] for k in ("term", "source_type", "occurrences", "frequency")}
            for r in unmapped_rows[:TOP_N]
        ],
        runtime_seconds=round(time.time() - t0, 1),
    )
    return result


def print_summary(r: dict) -> None:
    print("\n" + "=" * 70)
    print(f"PREPLINE - {r['company']} {r['role']}  ({r['syllabus_file']})")
    print("=" * 70)
    print(f"Status:                 {r['status']}")
    print(f"Report count:           {r['report_count']}")
    print(f"Taxonomy version:       {r['taxonomy_version']}")
    print(f"Scoring config version: {r['scoring_config_version']}")
    if r["status"] != "SUCCESS":
        return
    print(f"S_comp:                 {r['S_comp']:.2f} / 100")
    print(f"Syllabus units:         {r['syllabus_units']} ({r['units_with_matches']} matched >=1 topic)")
    print(f"Topics present:         {r['topics_present']} / {r['topics_in_taxonomy']}")
    print(f"Depth (present topics): {r['depth_counts']['present_topics']}")
    print(f"Depth (all topics):     {r['depth_counts']['all_topics']}")
    print("\nTop priority gaps:")
    print(f"  {'#':>2}  {'GAP':>6}  {'I(t)':>6}  {'COV':>6}  TOPIC")
    for g in r["top_priority_gaps"]:
        print(f"  {g['rank']:>2}  {g['priority_gap']:>6.3f}  {g['importance']:>6.3f}  {g['coverage']:>6.3f}  {g['topic_name']} ({g['topic_id']})")
    u = r["unmapped_terms_summary"]
    print(f"\nUnmapped terms: {u['distinct_terms']} distinct, {u['total_occurrences']} occurrences {u['distinct_terms_by_source_type']}")
    print("Top unmapped terms (occurrences):")
    for u in r["top_unmapped_terms"]:
        print(f"  {u['occurrences']:>4}  {u['source_type']:<10}  {u['term']}")


def main():
    parser = argparse.ArgumentParser(description="Run the full Prepline pipeline and save a versioned result.")
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--questions", default=DEFAULT_QUESTIONS)
    parser.add_argument("--reports", default=DEFAULT_REPORTS)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        sys.exit(f"Syllabus PDF not found: {args.pdf}")

    result = run(args.pdf, args.questions, args.reports)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print_summary(result)
    print(f"\nSaved to {args.out}")


if __name__ == "__main__":
    main()

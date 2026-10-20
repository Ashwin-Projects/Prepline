"""
Full Phase 7-12 pipeline run for one company/role + one syllabus PDF, saved as a versioned result file.

Mirrors the backend /api/v1 flow (density gate -> coverage -> importance -> S_comp -> priority gaps) and adds
the run's top unmapped terms (Phase 12). Unmapped terms are logged to a run-specific log so the summary
reflects this run only, not the shared data/processed/unmapped_terms.log.

Usage:
    python evaluation/run_full_pipeline.py --pdf "path/to/VIT_CSE_2024_2025.pdf"
    python evaluation/run_full_pipeline.py --pdf syllabus.pdf --out results/amazon_sde1_<version>.json
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
from pipeline.config import load_scoring_config
from pipeline.embeddings import SIMILARITY_THRESHOLD
from pipeline.interview_parser import (
    count_reports,
    filter_questions,
    load_questions_csv,
    write_excluded_questions,
)
from pipeline.syllabus_parser import parse_syllabus_pdf
from pipeline.taxonomy_tree import find_granular_without_high_level_ancestor
from pipeline.scoring import (
    calculate_syllabus_coverage,
    calculate_topic_importance,
    calculate_composite_score,
    rank_priority_gaps,
    load_taxonomy_nodes,
    DEFAULT_TAXONOMY_PATH,
    GAMMA_DEFAULT,
    MVP_REFERENCE_VALUES,
)
from evaluation.review_unmapped_terms import load_log, aggregate

COMPANY = "Amazon"
ROLE = "SDE-1"
CONFIG = load_scoring_config()
MIN_REPORTS = CONFIG["min_reports"]
SCORING_CONFIG_VERSION = CONFIG["config_version"]
TOP_N = 10

DEFAULT_QUESTIONS = os.path.join(ROOT, "data", "processed", "questions.csv")
DEFAULT_EXCLUDED = os.path.join(ROOT, "data", "processed", "excluded_questions.csv")
DEFAULT_OUT = os.path.join(ROOT, "results", f"amazon_sde1_{CONFIG['taxonomy_version']}.json")


def run(pdf_path: str, questions_csv: str, excluded_out: str) -> dict:
    included, excluded = filter_questions(load_questions_csv(questions_csv))
    write_excluded_questions(excluded, excluded_out)
    report_count = count_reports(included)
    excluded_by_reason = dict(sorted(Counter(
        reason for row in excluded for reason in row["exclusion_reason"].split(";")
    ).items()))
    print(
        f"Interview questions: {len(included)} included, {len(excluded)} excluded {excluded_by_reason}; "
        f"{report_count} reports with >=1 included question",
        flush=True,
    )
    orphans = find_granular_without_high_level_ancestor(load_taxonomy_nodes(DEFAULT_TAXONOMY_PATH))
    print(f"Granular nodes without a high-level ancestor: {len(orphans)} {orphans}", flush=True)
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
        "granular_without_high_level_ancestor": orphans,
        "interview_filter": {
            "questions_total": len(included) + len(excluded),
            "questions_included": len(included),
            "questions_excluded": len(excluded),
            "excluded_by_reason": excluded_by_reason,
            "excluded_questions_file": os.path.relpath(excluded_out, ROOT).replace(os.sep, "/"),
        },
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
    print_course_filter(syllabus["course_filter"], syllabus["courses"], syllabus["text_layer"])

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
        courses_kept=syllabus["courses"],
        course_filter=syllabus["course_filter"],
        text_layer=syllabus["text_layer"],
        syllabus_units=syllabus["units_count"],
        modules_with_depth_signals=sum(
            1 for m in syllabus["two_pass_mappings"] if any(v is not None for v in m["depth_signals"].values())
        ),
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


def print_course_filter(course_filter: dict, kept_courses: list, text_layer: dict) -> None:
    print(f"Core courses kept ({len(kept_courses)}):", flush=True)
    for c in kept_courses:
        print(f"  KEEP  {c['course_code']:<9} {c['course_title']}")
    print(f"Courses dropped ({len(course_filter['dropped'])}):")
    for d in course_filter["dropped"]:
        print(f"  DROP  {d['course_code']:<9} {d['course_title']}  [{d['drop_reason']}]")
    missing = course_filter["allowlisted_missing"]
    print(f"Allowlisted core courses with no readable syllabus ({len(missing)}): {', '.join(missing) or '-'}")
    print(f"Pages without a text layer: {len(text_layer['pages_without_text'])} of {text_layer['page_count']} "
          f"{text_layer['pages_without_text']}; scanned core courses: {', '.join(text_layer['scanned_courses']) or '-'}",
          flush=True)


def print_summary(r: dict) -> None:
    print("\n" + "=" * 70)
    print(f"PREPLINE - {r['company']} {r['role']}  ({r['syllabus_file']})")
    print("=" * 70)
    print(f"Status:                 {r['status']}")
    print(f"Report count:           {r['report_count']} (reports with >=1 included question)")
    f = r["interview_filter"]
    print(f"Questions:              {f['questions_included']} included / {f['questions_excluded']} excluded {f['excluded_by_reason']}")
    print(f"Taxonomy version:       {r['taxonomy_version']}")
    print(f"Scoring config version: {r['scoring_config_version']}")
    if r["status"] != "SUCCESS":
        return
    print(f"S_comp:                 {r['S_comp']:.2f} / 100")
    print(f"Syllabus units:         {r['syllabus_units']} ({r['units_with_matches']} matched >=1 topic)")
    print(f"Topics present:         {r['topics_present']} / {r['topics_in_taxonomy']}")
    print(f"Depth (present topics): {r['depth_counts']['present_topics']}")
    print(f"Depth (all topics):     {r['depth_counts']['all_topics']}")
    print(f"Modules with >=1 depth signal: {r['modules_with_depth_signals']} / {r['syllabus_units']}")
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
    parser.add_argument("--excluded-out", default=DEFAULT_EXCLUDED)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        sys.exit(f"Syllabus PDF not found: {args.pdf}")

    result = run(args.pdf, args.questions, args.excluded_out)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print_summary(result)
    print(f"\nSaved to {args.out}")


if __name__ == "__main__":
    main()

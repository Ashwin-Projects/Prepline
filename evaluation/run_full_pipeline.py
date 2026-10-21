"""
Full Phase 7-12 pipeline run for one company/role + one syllabus, saved as a versioned result file.

The syllabus is one PDF, or several course PDFs combined into one syllabus (--pdf repeated, or --pdf-dir with
--glob; e.g. theory BCSE202L + lab BCSE202P). Mirrors the backend /api/v1 flow (density gate -> coverage ->
importance -> S_comp -> priority gaps) and adds the run's top unmapped terms (Phase 12). Unmapped terms are
logged to a run-specific log so the summary reflects this run only, not the shared data/processed/unmapped_terms.log.

Usage:
    python evaluation/run_full_pipeline.py --pdf "path/to/VIT_CSE_2024_2025.pdf"
    python evaluation/run_full_pipeline.py --pdf-dir data/raw/syllabi --glob "BCSE*.pdf" \\
        --syllabus-id VIT_CSE_2024_25_courses --out results/amazon_sde1_<version>_course_syllabi.json
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
from pipeline.config import CONFIG_PATH, load_scoring_config
from pipeline.embeddings import SIMILARITY_THRESHOLD
from pipeline.interview_parser import (
    count_reports,
    filter_questions,
    load_questions_csv,
    write_excluded_questions,
)
from pipeline.syllabus_parser import collect_syllabus_pdfs, parse_syllabus_pdf, parse_syllabus_pdfs
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
# Results files are versioned and never overwritten (Deprecation & Migration): v1.1 = scoring-correctness fixes,
# v1.2 = core allowlist from the owner's course syllabi + course-PDF parsing.
RESULTS_VERSION = "v1.2"
DEFAULT_OUT = os.path.join(ROOT, "results", f"amazon_sde1_{RESULTS_VERSION}.json")
DEFAULT_GLOB = "BCSE*.pdf"


def resolve_pdf_paths(pdfs: list, pdf_dir: str = None, pattern: str = DEFAULT_GLOB) -> list:
    """Explicit --pdf files first, then the --pdf-dir files matching pattern; each path once."""
    paths = list(pdfs) + (collect_syllabus_pdfs(pdf_dir, pattern) if pdf_dir else [])
    return list(dict.fromkeys(paths))


def run(pdf_paths, questions_csv: str, excluded_out: str, syllabus_id: str = None) -> dict:
    """pdf_paths: one path, or a list. Several paths (or a syllabus_id) build one combined syllabus."""
    if isinstance(pdf_paths, str):
        pdf_paths = [pdf_paths]
    combined = len(pdf_paths) > 1 or syllabus_id is not None
    included, excluded = filter_questions(load_questions_csv(questions_csv))
    write_excluded_questions(excluded, excluded_out)
    report_count = count_reports(included)
    excluded_by_reason = dict(sorted(Counter(
        reason for row in excluded for reason in row["exclusion_reason"].split(";")
    ).items()))
    print(
        f"Interview questions: {len(included)} included, {len(excluded)} excluded "
        f"(rows per reason, a row can have several: {excluded_by_reason}); "
        f"{report_count} reports with >=1 included question",
        flush=True,
    )
    orphans = find_granular_without_high_level_ancestor(load_taxonomy_nodes(DEFAULT_TAXONOMY_PATH))
    print(f"Granular nodes without a high-level ancestor: {len(orphans)} {orphans}", flush=True)
    result = {
        "results_version": RESULTS_VERSION,
        "company": COMPANY,
        "role": ROLE,
        "report_count": report_count,
        "syllabus_file": None if combined else os.path.basename(pdf_paths[0]),
        "syllabus_id": syllabus_id if combined else os.path.basename(pdf_paths[0]),
        "syllabus_files": [os.path.basename(p) for p in pdf_paths],
        "core_courses": CONFIG["syllabus"]["core_courses"],
        "taxonomy_version": None,
        "scoring_config_version": SCORING_CONFIG_VERSION,
        "scoring_config": {
            "config_file": os.path.relpath(CONFIG_PATH, ROOT).replace(os.sep, "/"),
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
    print(f"Parsing {len(pdf_paths)} syllabus PDF(s) (slow on scanned pages)...", flush=True)
    if combined:
        syllabus = parse_syllabus_pdfs(pdf_paths, syllabus_id=syllabus_id or "combined_syllabus")
    else:
        syllabus = parse_syllabus_pdf(pdf_paths[0])
    print(f"  {syllabus['units_count']} units in {time.time() - t0:.0f}s", flush=True)
    print_course_filter(syllabus["course_filter"], syllabus["courses"], syllabus["text_layer"])
    print_units(syllabus)

    t_parse = time.time() - t0

    t = time.time()
    coverage = calculate_syllabus_coverage(syllabus)
    t_coverage = time.time() - t
    print("Scoring interview questions...", flush=True)
    t = time.time()
    importance = calculate_topic_importance(questions_csv, total_reports_count=report_count)
    t_importance = time.time() - t
    t = time.time()
    composite = calculate_composite_score(importance, coverage)
    gaps = rank_priority_gaps(importance, coverage)
    t_scoring = time.time() - t
    stage_timings = {
        "parse": round(t_parse, 1),
        "coverage": round(t_coverage, 1),
        "importance": round(t_importance, 1),
        "scoring": round(t_scoring, 1),
    }
    print(f"Stage timings (s): {stage_timings}", flush=True)

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
        course_groups=syllabus["course_groups"],
        course_filter=syllabus["course_filter"],
        text_layer=syllabus["text_layer"],
        file_errors=syllabus.get("file_errors", []),
        skipped_modules=syllabus["skipped_modules"],
        syllabus_units=syllabus["units_count"],
        units_by_component=dict(Counter(m["component"] for m in syllabus["two_pass_mappings"])),
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
        stage_timings_seconds=stage_timings,
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


def print_units(syllabus: dict) -> None:
    """Per-course unit counts (theory modules, lab experiments, lab hours), skipped modules and file errors."""
    units = Counter(m["course_code"] for m in syllabus["two_pass_mappings"])
    print("Units per course:")
    for c in syllabus["courses"]:
        extra = f", {c['experiment_count']} experiments, lab hours {c['lab_hours_total']}" if c["experiment_count"] else ""
        print(f"  {c['course_code']:<9} {c['component']:<8} {units[c['course_code']]:>3} units{extra}"
              f"  [L-T-P-C {c['ltpc_status']}]")
    skipped = [f"{s['course_code']} M{s['module_number']}" for s in syllabus["skipped_modules"]]
    print(f"Skipped body-less modules ({len(skipped)}): {', '.join(skipped) or '-'}")
    for e in syllabus.get("file_errors", []):
        print(f"  FILE ERROR {e['file']}: {e['error']}")
    sys.stdout.flush()


def print_summary(r: dict) -> None:
    print("\n" + "=" * 70)
    print(f"PREPLINE - {r['company']} {r['role']}  ({r['syllabus_id']}, {len(r['syllabus_files'])} file(s))")
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
    parser.add_argument("--pdf", action="append", default=[], help="a syllabus PDF; repeat to combine several")
    parser.add_argument("--pdf-dir", help="folder of course syllabus PDFs, combined into one syllabus")
    parser.add_argument("--glob", default=DEFAULT_GLOB, help=f"file pattern inside --pdf-dir (default {DEFAULT_GLOB})")
    parser.add_argument("--syllabus-id", help="id of the combined syllabus, e.g. VIT_CSE_2024_25_courses")
    parser.add_argument("--questions", default=DEFAULT_QUESTIONS)
    parser.add_argument("--excluded-out", default=DEFAULT_EXCLUDED)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    if os.path.exists(args.out):
        sys.exit(f"Refusing to overwrite existing results file: {args.out} (results are versioned; choose a new --out)")
    pdf_paths = resolve_pdf_paths(args.pdf, args.pdf_dir, args.glob)
    if not pdf_paths:
        sys.exit(f"No syllabus PDFs given (--pdf) or found in --pdf-dir matching '{args.glob}'")
    missing = [p for p in pdf_paths if not os.path.exists(p)]
    if missing:
        sys.exit(f"Syllabus PDF not found: {', '.join(missing)}")

    result = run(pdf_paths, args.questions, args.excluded_out, syllabus_id=args.syllabus_id)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print_summary(result)
    print(f"\nSaved to {args.out}")


if __name__ == "__main__":
    main()

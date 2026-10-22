"""
Phase 15 data: per-target topic tables for the dashboard (Topic explorer, coverage by domain).

The saved results files keep only the top priority gaps. This recomputes, for every target with a saved results file,
the full per-topic table (importance, coverage, depth, depth status, coverage source) from the same syllabus and the
target's questions, and writes results/topics/<target>_<version>_topics.json. It never changes a results file, never
overwrites a topic table, and refuses to write if the recomputed S_comp differs from the saved one.

Usage:
    python evaluation/export_topic_tables.py
"""
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import evaluation.run_all_targets as rat
import evaluation.run_full_pipeline as rfp
import pipeline.unmapped_terms_logger as unmapped_terms_logger
from pipeline.config import load_targets
from pipeline.scoring import (
    DEFAULT_TAXONOMY_PATH,
    calculate_composite_score,
    calculate_syllabus_coverage,
    calculate_topic_importance,
    load_taxonomy_nodes,
)
from pipeline.syllabus_parser import parse_syllabus_pdfs

DEFAULT_OUT_DIR = os.path.join(ROOT, "results", "topics")


def topics_path(out_dir: str, target_id: str) -> str:
    return os.path.join(out_dir, f"{target_id}_{rfp.RESULTS_VERSION}_topics.json")


def topic_table(coverage: Dict[str, Any], importance: Dict[str, Any] = None, nodes: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """One row per taxonomy topic; importance and priority_gap are None when the target was not scored."""
    node_by_id = {n["topic_id"]: n for n in nodes or []}
    imp = {i["topic_id"]: i["importance"] for i in importance["interview_importance"]} if importance else None
    rows = []
    for c in coverage["topic_coverage"]:
        node = node_by_id.get(c["topic_id"], {})
        value = imp.get(c["topic_id"], 0.0) if imp is not None else None
        rows.append({
            "topic_id": c["topic_id"],
            "topic_name": c["topic_name"],
            "domain": node.get("domain", c["topic_id"].split(".")[0]),
            "type": node.get("type"),
            "importance": value,
            "coverage": c["coverage"],
            "priority_gap": round(value * (1 - c["coverage"]), 4) if value is not None else None,
            "depth": c["depth"],
            "depth_status": c["depth_status"],
            "presence": c["presence"],
            "coverage_source": c["coverage_source"],
            "inherited_from": c["inherited_from"],
        })
    return rows


def export(targets: List[Dict[str, Any]], results_dir: str, out_dir: str, parse) -> List[Dict[str, Any]]:
    """parse: zero-argument function returning the parsed syllabus the saved results were scored against."""
    jobs = [(t, rat.results_path(results_dir, t["id"])) for t in targets]
    jobs = [(t, path) for t, path in jobs if os.path.exists(path)]
    for t, _ in jobs:
        if os.path.exists(topics_path(out_dir, t["id"])):
            raise FileExistsError(f"{topics_path(out_dir, t['id'])} exists; topic tables are never overwritten")

    nodes = load_taxonomy_nodes(DEFAULT_TAXONOMY_PATH)
    t0 = time.time()
    coverage = calculate_syllabus_coverage(parse())
    print(f"Coverage computed for {len(coverage['topic_coverage'])} topics in {time.time() - t0:.0f}s", flush=True)
    unmapped_terms_logger.LOG_PATH = os.path.join(tempfile.mkdtemp(prefix="prepline_topics_"), "unmapped_terms.log")

    tables = []
    for target, path in jobs:
        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        importance, recomputed = None, None
        if saved["status"] == "SUCCESS":
            importance = calculate_topic_importance(target["questions_csv"], total_reports_count=saved["report_count"])
            recomputed = calculate_composite_score(importance, coverage)["S_comp"]
            if recomputed != saved["S_comp"]:
                raise ValueError(f"{target['id']}: recomputed S_comp {recomputed} != saved S_comp {saved['S_comp']}")
        tables.append({
            "target_id": target["id"],
            "results_file": os.path.basename(path),
            "status": saved["status"],
            "S_comp_saved": saved["S_comp"],
            "S_comp_recomputed": recomputed,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "topics": topic_table(coverage, importance, nodes),
        })
        print(f"[{target['id']}] {saved['status']}: S_comp saved {saved['S_comp']}, recomputed {recomputed}", flush=True)

    os.makedirs(out_dir, exist_ok=True)
    for table in tables:
        with open(topics_path(out_dir, table["target_id"]), "w", encoding="utf-8") as f:
            json.dump(table, f, indent=2)
    return tables


def main() -> None:
    pdf_paths = rfp.resolve_pdf_paths([], rat.DEFAULT_PDF_DIR, rat.DEFAULT_GLOB)
    if not pdf_paths:
        sys.exit(f"No syllabus PDFs found in {rat.DEFAULT_PDF_DIR}")
    transcriptions = rfp.default_transcriptions_dir(rat.DEFAULT_PDF_DIR)
    export(load_targets(), rat.DEFAULT_OUT_DIR, DEFAULT_OUT_DIR,
           parse=lambda: parse_syllabus_pdfs(pdf_paths, syllabus_id=rat.DEFAULT_SYLLABUS_ID,
                                             transcriptions_dir=transcriptions))
    print(f"Wrote topic tables to {DEFAULT_OUT_DIR}")


if __name__ == "__main__":
    main()

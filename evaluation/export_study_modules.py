"""
Dashboard data for 'What to study next': for every granular taxonomy topic, the VIT core course modules to revise.

A granular topic's coverage is inherited from its nearest high-level ancestor (pipeline/scoring.py), so the modules
listed are the syllabus units mapped to the topic itself ("direct") or to that ancestor ("parent topic"). A topic with
no such unit is not covered in the core curriculum. Parses the same syllabus as the saved v1.2 results and writes
results/study/study_modules_v1.2.json once; it never overwrites and never changes a score.

Usage:
    python evaluation/export_study_modules.py
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pipeline.taxonomy_tree import GRANULAR, nearest_high_level_ancestor

RESULTS_VERSION = "v1.2"
DEFAULT_OUT = os.path.join(ROOT, "results", "study", f"study_modules_{RESULTS_VERSION}.json")


def modules_by_topic(parsed: Dict[str, Any], nodes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """granular topic_id -> syllabus units that match it or its nearest high-level ancestor, in syllabus order."""
    nodes_by_id = {n["topic_id"]: n for n in nodes}
    titles = {c["course_code"]: c.get("course_title") for c in parsed.get("courses", [])}
    out = {}
    for node in nodes:
        if node.get("type") != GRANULAR:
            continue
        topic_id, parent = node["topic_id"], nearest_high_level_ancestor(node["topic_id"], nodes_by_id)
        units = []
        for m in parsed.get("two_pass_mappings", []):
            matched = set(m.get("matched_topic_ids") or [])
            if topic_id in matched or (parent and parent in matched):
                via = topic_id if topic_id in matched else parent
                units.append({
                    "course_code": m["course_code"],
                    "course_title": titles.get(m["course_code"]),
                    "module_number": m.get("module_number"),
                    "module_title": m.get("module_title"),
                    "component": m.get("component"),
                    "match": "direct" if via == topic_id else "parent topic",
                    "similarity": (m.get("similarity_scores") or {}).get(via),
                })
        # Strongest evidence first: direct matches, then by similarity (stable, so syllabus order breaks ties).
        out[topic_id] = sorted(units, key=lambda u: (u["match"] != "direct", -(u["similarity"] or 0.0)))
    return out


def export(parse: Callable[[], Dict[str, Any]], out_path: str = DEFAULT_OUT) -> Dict[str, Any]:
    if os.path.exists(out_path):
        raise FileExistsError(f"{out_path} exists; study module tables are never overwritten")
    from pipeline.scoring import DEFAULT_TAXONOMY_PATH, load_taxonomy_nodes

    t0 = time.time()
    parsed = parse()
    modules = modules_by_topic(parsed, load_taxonomy_nodes(DEFAULT_TAXONOMY_PATH))
    data = {
        "results_version": RESULTS_VERSION,
        "syllabus_id": parsed.get("syllabus_id"),
        "taxonomy_version": parsed.get("taxonomy_version"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "Units mapped to the topic (direct) or to its nearest high-level ancestor (parent topic), "
                "whose coverage the topic inherits.",
        "modules": modules,
    }
    print(f"{sum(1 for v in modules.values() if v)} of {len(modules)} granular topics have >=1 module "
          f"({len(parsed.get('two_pass_mappings', []))} units) in {time.time() - t0:.0f}s", flush=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


def main() -> None:
    import evaluation.run_all_targets as rat
    import evaluation.run_full_pipeline as rfp
    from pipeline.syllabus_parser import parse_syllabus_pdfs

    pdf_paths = rfp.resolve_pdf_paths([], rat.DEFAULT_PDF_DIR, rat.DEFAULT_GLOB)
    if not pdf_paths:
        sys.exit(f"No syllabus PDFs found in {rat.DEFAULT_PDF_DIR}")
    transcriptions = rfp.default_transcriptions_dir(rat.DEFAULT_PDF_DIR)
    export(lambda: parse_syllabus_pdfs(pdf_paths, syllabus_id=rat.DEFAULT_SYLLABUS_ID, transcriptions_dir=transcriptions))
    print(f"Wrote {DEFAULT_OUT}")


if __name__ == "__main__":
    main()

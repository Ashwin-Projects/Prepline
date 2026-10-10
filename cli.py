"""Command-line entry points for the Prepline prototype.

Examples (run from the repository root):
  python -m pipeline.cli map "Implement BFS on a graph"
  python -m pipeline.cli courses "Operating Systems"
  python -m pipeline.cli coverage --syllabus-topic-ids dsa.arrays,dsa.graphs --interview-topic-ids dsa.arrays,dbms.normalization
  python -m pipeline.cli readiness
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from pipeline.scoring import topic_coverage, weighted_coverage
from pipeline.syllabus_parser import load_course_catalog, search_course_catalog
from pipeline.taxonomy_mapper import load_taxonomy, map_text

ROOT = Path(__file__).resolve().parents[1]


def _csv_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prepline",
        description="Explore taxonomy mappings and syllabus/interview topic overlap.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    mapping = sub.add_parser("map", help="Map a text snippet to taxonomy topics")
    mapping.add_argument("text", help="Text to map, in quotation marks if it contains spaces")
    mapping.add_argument("--methods", default="keyword,tfidf", help="Comma-separated: keyword,tfidf,embedding")
    mapping.add_argument("--top-k", type=int, default=5)
    mapping.add_argument("--taxonomy", default=str(ROOT / "data/taxonomy/taxonomy_v1.1.json"))

    courses = sub.add_parser("courses", help="Search the extracted VIT course catalog")
    courses.add_argument("query")
    courses.add_argument("--catalog", default=str(ROOT / "data/raw/syllabi/vit_cse_2024_2025_discipline_core_catalog.csv"))

    coverage = sub.add_parser("coverage", help="Calculate topic overlap from explicit topic IDs")
    coverage.add_argument("--syllabus-topic-ids", required=True, help="Comma-separated taxonomy IDs mapped from syllabus text")
    coverage.add_argument("--interview-topic-ids", help="Comma-separated topic IDs from eligible interview data (required unless --weights is used)")
    coverage.add_argument("--weights", help="Optional JSON object mapping topic IDs to numeric weights")

    sub.add_parser("readiness", help="Run the fail-closed Phase 2/13 readiness check")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "map":
        methods = [item.strip() for item in args.methods.split(",") if item.strip()]
        if args.top_k < 0:
            raise SystemExit("--top-k must be non-negative")
        taxonomy = load_taxonomy(args.taxonomy)
        result = map_text(args.text, taxonomy, methods=methods)
        if "tfidf" in result:
            result["tfidf"] = result["tfidf"][:args.top_k]
        if "embedding" in result:
            result["embedding"] = result["embedding"][:args.top_k]
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "courses":
        rows = search_course_catalog(args.query, load_course_catalog(args.catalog))
        print(json.dumps(rows, indent=2))
        return 0 if rows else 1

    if args.command == "coverage":
        syllabus_ids = _csv_ids(args.syllabus_topic_ids)
        interview_ids = _csv_ids(args.interview_topic_ids or "")
        if args.weights:
            weights = json.loads(Path(args.weights).read_text(encoding="utf-8"))
            if not isinstance(weights, dict):
                raise SystemExit("--weights must point to a JSON object of topic_id: weight")
            result = weighted_coverage(syllabus_ids, weights)
        else:
            if not args.interview_topic_ids:
                raise SystemExit("--interview-topic-ids is required unless --weights is used")
            result = topic_coverage(syllabus_ids, interview_ids)
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "readiness":
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_phase_readiness.py")],
            cwd=ROOT,
            check=False,
        )
        return result.returncode

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""
Phase 15: read-only dashboard endpoints over the saved results.

GET /api/v1/targets                configured targets with their saved status and S_comp
GET /api/v1/results/{target_id}    saved results file + per-topic table (results/topics) + raw report count
GET /api/v1/comparison             one summary row per target (counts, density gate, S_comp, gaps, confidence)
GET /api/v1/benchmark              benchmark results (without per-item predictions) + label agreement + limitations
GET /api/v1/pilot                  Phase 16 pilot status, and its results once results/pilot/pilot_results.json exists
GET /api/v1/validation             retrospective leave-one-report-out validation (not the participant pilot)

Files are located only from config (config/api.json "dashboard", config/targets.json); a target_id that is not
configured is a 404 and never becomes part of a path.
"""
import csv
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status

from pipeline.config import load_api_config, load_scoring_config, load_targets, resolve_path

router = APIRouter(prefix="/api/v1", tags=["PREPLINE Dashboard"])

DASHBOARD = load_api_config()["dashboard"]
MIN_REPORTS = load_scoring_config()["min_reports"]
# Written by evaluation/pilot/analyze_pilot.py once real pilot responses are analysed (Phase 16).
PILOT_RESULTS = resolve_path(DASHBOARD["pilot_results"])
# Written by evaluation/retro_validation.py (leave-one-report-out; not the participant pilot).
RETRO_VALIDATION = resolve_path(DASHBOARD["retro_validation"])
# Draft vs independent second labeller, before human adjudication (evaluation/benchmark/ADJUDICATION.md).
LABEL_AGREEMENT = {"kappa_draft_vs_second_labeller": 0.812, "agree": 211, "partial": 8, "disagree": 28,
                   "rule_adjudicated": 48, "human_adjudicated": 8, "llm_cross_checked_only": 191,
                   "labellers": "Claude draft vs a fresh Claude subagent (two independent LLM labellers)",
                   "source": "evaluation/benchmark/ADJUDICATION.md"}


def _target(target_id: str) -> Dict[str, Any]:
    for t in load_targets():
        if t["id"] == target_id:
            return t
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown target '{target_id}'.")


def _read_json(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _results_path(target_id: str) -> str:
    name = f"{target_id}_{DASHBOARD['results_version']}_{DASHBOARD['results_suffix']}.json"
    return os.path.join(resolve_path(DASHBOARD["results_dir"]), name)


def _topics_path(target_id: str) -> str:
    return os.path.join(resolve_path(DASHBOARD["topics_dir"]), f"{target_id}_{DASHBOARD['results_version']}_topics.json")


def _raw_report_count(target: Dict[str, Any]) -> int:
    with open(target["reports_csv"], encoding="utf-8") as f:
        return sum(1 for row in csv.DictReader(f) if (row.get("report_id") or "").strip())


def _summary(target: Dict[str, Any], result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    result = result or {}
    report_count = result.get("report_count")
    depth = result.get("depth_counts", {}).get("all_topics", {})
    unmapped = result.get("unmapped_terms_summary", {})
    return {
        "target_id": target["id"],
        "company": target["company"],
        "role": target["role"],
        "results_available": bool(result),
        "status": result.get("status"),
        "S_comp": result.get("S_comp"),
        "raw_report_count": _raw_report_count(target),
        "report_count": report_count,
        "min_reports": MIN_REPORTS,
        "density_gate_passed": report_count is not None and report_count >= MIN_REPORTS,
        "scoring_universe_size": result.get("scoring_universe_size"),
        "fallback_topics": depth.get("fallback"),
        "topics_in_taxonomy": result.get("topics_in_taxonomy"),
        "unmapped_distinct_terms": unmapped.get("distinct_terms"),
        "top_priority_gaps": result.get("top_priority_gaps", []),
        "generated_at": result.get("generated_at"),
    }


@router.get("/targets")
def list_targets() -> Dict[str, Any]:
    targets = []
    for t in load_targets():
        s = _summary(t, _read_json(_results_path(t["id"])))
        targets.append({"id": t["id"], "company": t["company"], "role": t["role"],
                        "results_available": s["results_available"], "status": s["status"], "S_comp": s["S_comp"]})
    return {"targets": targets}


@router.get("/results/{target_id}")
def get_results(target_id: str) -> Dict[str, Any]:
    target = _target(target_id)
    result = _read_json(_results_path(target["id"]))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No saved results for '{target_id}'.")
    topics = _read_json(_topics_path(target["id"]))
    return {
        "target": {"id": target["id"], "company": target["company"], "role": target["role"]},
        "result": result,
        "raw_report_count": _raw_report_count(target),
        "min_reports": MIN_REPORTS,
        "topics": topics["topics"] if topics else [],
    }


@router.get("/comparison")
def get_comparison() -> Dict[str, Any]:
    return {"min_reports": MIN_REPORTS,
            "targets": [_summary(t, _read_json(_results_path(t["id"]))) for t in load_targets()]}


@router.get("/benchmark")
def get_benchmark() -> Dict[str, Any]:
    from evaluation.benchmark.run_benchmark import LIMITATIONS, METHODS, recommendation

    data = _read_json(resolve_path(DASHBOARD["benchmark_file"]))
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No saved benchmark results.")
    for method in data["methods"].values():
        for split in ("dev", "val", "test"):
            method[split].pop("predictions", None)
    data["method_labels"] = METHODS
    data["label_agreement"] = LABEL_AGREEMENT
    data["limitations"] = LIMITATIONS
    data["recommendation"] = recommendation(data)
    return data


@router.get("/pilot")
def get_pilot() -> Dict[str, Any]:
    results = _read_json(PILOT_RESULTS)
    return {"status": "results_available" if results else "in_progress", "results": results}


@router.get("/validation")
def get_validation() -> Dict[str, Any]:
    results = _read_json(RETRO_VALIDATION)
    return {"available": results is not None, "results": results}

"""
Dashboard 'What to study next' (read-only): per top priority gap of a target, the VIT core course modules to revise
and two practice links.

GET /api/v1/study/{target_id}

Modules come from results/study/study_modules_v1.2.json (evaluation/export_study_modules.py); links from
config/practice_links.json (each URL checked with WebFetch). Gaps come from the saved results file, unchanged.
"""
import json
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status

from backend.dashboard import DASHBOARD, _read_json, _results_path, _target
from pipeline.config import resolve_path

router = APIRouter(prefix="/api/v1", tags=["PREPLINE Dashboard"])

STUDY_MODULES = resolve_path(DASHBOARD["study_modules"])
PRACTICE_LINKS = resolve_path(DASHBOARD["practice_links"])
TOP_N = 10
NOT_COVERED = "Not covered in core curriculum"


def _links_file() -> Dict[str, Any]:
    with open(PRACTICE_LINKS, encoding="utf-8") as f:
        return json.load(f)


def load_links() -> Dict[str, List[Dict[str, str]]]:
    return _links_file()["links"]


def study_items(gaps: List[Dict[str, Any]], modules: Dict[str, List[Dict[str, Any]]],
                links: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, Any]]:
    items = []
    for g in gaps:
        found = modules.get(g["topic_id"], [])
        items.append({
            "rank": g["rank"],
            "topic_id": g["topic_id"],
            "topic_name": g["topic_name"],
            "coverage": g.get("coverage"),
            "priority_gap": g.get("priority_gap"),
            "in_core_curriculum": bool(found),
            "modules": found,
            "note": None if found else NOT_COVERED,
            "practice": links.get(g["topic_id"], [])[:2],
        })
    return items


def study_for(target_id: str) -> Dict[str, Any]:
    target = _target(target_id)
    result = _read_json(_results_path(target["id"]))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No saved results for '{target_id}'.")
    modules = (_read_json(STUDY_MODULES) or {}).get("modules", {})
    links = _links_file()
    gaps = result.get("top_priority_gaps", [])[:TOP_N] if result.get("status") == "SUCCESS" else []
    return {
        "target": {"id": target["id"], "company": target["company"], "role": target["role"]},
        "status": result.get("status"),
        "links_verified_on": links["verified_on"],
        "items": study_items(gaps, modules, links["links"]),
    }


@router.get("/study/{target_id}")
def get_study(target_id: str) -> Dict[str, Any]:
    return study_for(target_id)

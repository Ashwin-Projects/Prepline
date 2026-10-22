"""
Central scoring configuration.

Every frozen scoring constant (tau, gamma, depth reference values, MIN_REPORTS,
taxonomy version, embedding model + revision) lives in config/scoring_v1.2.json (config/scoring_v1.1.json and config/scoring_v1.0.json are kept as records).
The file is read once per path; later calls return the same dict.
"""
import json
import os
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config", "scoring_v1.2.json")
API_CONFIG_PATH = os.path.join(ROOT, "config", "api.json")
TARGETS_CONFIG_PATH = os.path.join(ROOT, "config", "targets.json")

_cache: Dict[str, Dict[str, Any]] = {}


def load_scoring_config(path: Optional[str] = None) -> Dict[str, Any]:
    path = os.path.abspath(path or CONFIG_PATH)
    if path not in _cache:
        with open(path, "r", encoding="utf-8") as f:
            _cache[path] = json.load(f)
    return _cache[path]


def load_api_config(path: Optional[str] = None) -> Dict[str, Any]:
    """API safety limits (upload size, page count, cache size, ...) from config/api.json, read once."""
    return load_scoring_config(path or API_CONFIG_PATH)


def resolve_path(relative_path: str) -> str:
    """Resolves a repo-relative path from the config (e.g. taxonomy_path) to an absolute path."""
    return os.path.join(ROOT, *relative_path.split("/"))


def load_targets(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Company/role targets from config/targets.json, in config order. Each target gets absolute paths to its data
    folder files: reports.csv and questions.csv (inputs) and excluded_questions.csv (written by the runner).
    """
    targets = []
    for entry in load_scoring_config(path or TARGETS_CONFIG_PATH)["targets"]:
        if entry["id"] in {t["id"] for t in targets}:
            raise ValueError(f"duplicate target id in targets config: {entry['id']}")
        data_dir = entry["data_dir"] if os.path.isabs(entry["data_dir"]) else resolve_path(entry["data_dir"])
        targets.append({
            **entry,
            "data_dir": data_dir,
            "reports_csv": os.path.join(data_dir, "reports.csv"),
            "questions_csv": os.path.join(data_dir, "questions.csv"),
            "excluded_csv": os.path.join(data_dir, "excluded_questions.csv"),
        })
    return targets


def find_target(company: str, role: str, targets: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """The configured target for company/role (case-insensitive), or None."""
    for target in load_targets() if targets is None else targets:
        if target["company"].lower() == company.lower() and target["role"].lower() == role.lower():
            return target
    return None

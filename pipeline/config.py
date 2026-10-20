"""
Central scoring configuration.

Every frozen scoring constant (tau, gamma, depth reference values, MIN_REPORTS,
taxonomy version, embedding model + revision) lives in config/scoring_v1.0.json.
The file is read once per path; later calls return the same dict.
"""
import json
import os
from typing import Any, Dict, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config", "scoring_v1.0.json")

_cache: Dict[str, Dict[str, Any]] = {}


def load_scoring_config(path: Optional[str] = None) -> Dict[str, Any]:
    path = os.path.abspath(path or CONFIG_PATH)
    if path not in _cache:
        with open(path, "r", encoding="utf-8") as f:
            _cache[path] = json.load(f)
    return _cache[path]


def resolve_path(relative_path: str) -> str:
    """Resolves a repo-relative path from the config (e.g. taxonomy_path) to an absolute path."""
    return os.path.join(ROOT, *relative_path.split("/"))

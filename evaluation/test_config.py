"""
Central scoring config (config/scoring_v1.0.json).

The frozen values below are the Constraint-Driven Development guard: tau, gamma,
the depth reference values, MIN_REPORTS and the taxonomy version must not change
unless the project owner explicitly says so.
"""
import os
import re

from pipeline.config import load_scoring_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FROZEN_REFERENCE_VALUES = {
    "unit_hours": 10.0,
    "slide_count": 20.0,
    "slides": 20.0,
    "lab_hours": 10.0,
    "lab_count": 5.0,
    "assignment_count": 5.0,
    "assignments": 5.0,
}


def test_frozen_values():
    cfg = load_scoring_config()
    assert cfg["similarity_threshold"] == 0.50
    assert cfg["gamma"] == 0.5
    assert cfg["min_reports"] == 15
    assert cfg["taxonomy_version"] == "v1.0"
    assert cfg["semester_weeks"] == 15
    assert cfg["depth_reference_values"] == FROZEN_REFERENCE_VALUES


def test_model_pinned():
    model = load_scoring_config()["embedding_model"]
    assert model["name"] == "all-MiniLM-L6-v2"
    assert model["revision"] == "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def test_loaded_once():
    assert load_scoring_config() is load_scoring_config()


def test_module_constants_come_from_config():
    from pipeline import embeddings, keyword_abstraction, scoring

    cfg = load_scoring_config()
    assert scoring.GAMMA_DEFAULT == cfg["gamma"]
    assert scoring.MVP_REFERENCE_VALUES == cfg["depth_reference_values"]
    assert scoring.MIN_REPORTS == cfg["min_reports"]
    assert scoring.DEFAULT_TAXONOMY_VERSION == cfg["taxonomy_version"]
    assert embeddings.SIMILARITY_THRESHOLD == cfg["similarity_threshold"]
    assert keyword_abstraction.DEFAULT_TAXONOMY_VERSION == cfg["taxonomy_version"]


def test_no_hardcoded_versions():
    for rel in ("backend/routes.py", "evaluation/run_full_pipeline.py", "pipeline/scoring.py"):
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            source = f.read()
        assert not re.search(r"v1\.0", source), f"hard-coded version string in {rel}"

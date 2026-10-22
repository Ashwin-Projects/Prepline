"""
Config-driven company/role targets (config/targets.json): each target is one config entry plus one data folder
(data/processed/<target_id>/ with reports.csv and questions.csv). Nothing in the API or the runner names a company.
"""
import csv
import json
import os

import pytest
from fastapi.testclient import TestClient

import backend.routes as routes
from backend.app import app
from pipeline.config import ROOT, find_target, load_targets

client = TestClient(app)


def write_target(tmp_path, target_id="acme_sde1", company="Acme", role="SDE-1", reports=16):
    """A data folder with `reports` technical reports, and a targets config listing it."""
    data_dir = tmp_path / target_id
    data_dir.mkdir()
    with open(data_dir / "reports.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["report_id", "company", "role"])
        writer.writeheader()
        for i in range(1, reports + 1):
            writer.writerow({"report_id": f"R{i:02d}", "company": company, "role": role})
    with open(data_dir / "questions.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["report_id", "round", "round_type", "question_text", "topic",
                                               "needs_review", "review_reason"])
        writer.writeheader()
        for i in range(1, reports + 1):
            writer.writerow({"report_id": f"R{i:02d}", "round": "R1", "round_type": "technical",
                             "question_text": "Deadlock Detection and Prevention", "topic": "", "needs_review": "False", "review_reason": ""})
    config = tmp_path / "targets.json"
    config.write_text(json.dumps({"targets": [
        {"id": target_id, "company": company, "role": role, "data_dir": str(data_dir)}
    ]}), encoding="utf-8")
    return str(config)


def test_configured_targets():
    targets = load_targets()
    assert [(t["id"], t["company"], t["role"]) for t in targets] == [
        ("amazon_sde1", "Amazon", "SDE-1"),
        ("microsoft_sde1", "Microsoft", "SDE-1"),
    ]


def test_target_paths_live_in_its_data_folder():
    amazon = load_targets()[0]
    folder = os.path.join(ROOT, "data", "processed", "amazon_sde1")
    assert amazon["data_dir"] == folder
    assert amazon["questions_csv"] == os.path.join(folder, "questions.csv")
    assert amazon["reports_csv"] == os.path.join(folder, "reports.csv")
    assert amazon["excluded_csv"] == os.path.join(folder, "excluded_questions.csv")
    for target in load_targets():
        assert os.path.exists(target["questions_csv"]) and os.path.exists(target["reports_csv"])


def test_amazon_data_moved_out_of_processed_root():
    for name in ("reports.csv", "questions.csv", "excluded_questions.csv"):
        assert not os.path.exists(os.path.join(ROOT, "data", "processed", name))


def test_find_target_is_case_insensitive():
    assert find_target("microsoft", "sde-1")["id"] == "microsoft_sde1"
    assert find_target("Google", "L3") is None


def test_targets_config_rejects_duplicate_ids(tmp_path):
    config = tmp_path / "targets.json"
    entry = {"id": "x", "company": "X", "role": "R", "data_dir": str(tmp_path)}
    config.write_text(json.dumps({"targets": [entry, dict(entry, company="Y")]}), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_targets(str(config))


@pytest.mark.parametrize("path", ["backend/routes.py", "evaluation/run_full_pipeline.py"])
def test_no_hardcoded_company(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        assert "amazon" not in f.read().lower()


def test_api_lists_configured_targets():
    data = client.get("/api/v1/supported-targets").json()
    assert [(t["company"], t["role"]) for t in data["supported_targets"]] == [
        ("Amazon", "SDE-1"), ("Microsoft", "SDE-1"),
    ]


def test_api_validates_microsoft_from_its_own_data():
    data = client.post("/api/v1/validate-target", json={"company": "Microsoft", "role": "SDE-1"}).json()
    assert data["company"] == "Microsoft"
    assert data["report_count"] == 15
    assert data["status"] == "ELIGIBLE"


def test_new_target_needs_only_data_folder_and_config_entry(tmp_path, monkeypatch):
    monkeypatch.setattr(routes, "TARGETS", load_targets(write_target(tmp_path, reports=14)))
    data = client.post("/api/v1/validate-target", json={"company": "Acme", "role": "SDE-1"}).json()
    assert (data["company"], data["report_count"], data["status"]) == ("Acme", 14, "INSUFFICIENT_DATA")
    amazon = client.post("/api/v1/validate-target", json={"company": "Amazon", "role": "SDE-1"}).json()
    assert amazon["status"] == "UNSUPPORTED_ROLE"


def test_app_names_no_company():
    from backend.app import app as api
    assert api.title == "PREPLINE — Curriculum-to-Interview Alignment"
    with open(os.path.join(ROOT, "backend", "app.py"), encoding="utf-8") as f:
        assert "amazon" not in f.read().lower()
    assert client.get("/").json()["scope"] == "Prototype: Amazon SDE-1, Microsoft SDE-1"

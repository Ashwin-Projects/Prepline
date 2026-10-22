"""
Phase 15: read-only dashboard endpoints over the saved results (backend/dashboard.py).
Only configured target ids are served; files are never located from user input.
"""
from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_targets_list():
    data = client.get("/api/v1/targets").json()
    assert [t["id"] for t in data["targets"]] == ["amazon_sde1", "microsoft_sde1", "google_swe_l3", "flipkart_sde1"]
    google = next(t for t in data["targets"] if t["id"] == "google_swe_l3")
    assert google["status"] == "INSUFFICIENT_DATA" and google["S_comp"] is None and google["results_available"]


def test_results_for_target():
    data = client.get("/api/v1/results/amazon_sde1").json()
    assert data["result"]["S_comp"] == 88.7653
    assert data["raw_report_count"] == 21 and data["min_reports"] == 15
    assert len(data["topics"]) == 83
    assert {"importance", "coverage", "depth", "depth_status", "coverage_source", "domain"} <= set(data["topics"][0])


def test_results_insufficient_target_is_not_an_error():
    response = client.get("/api/v1/results/google_swe_l3")
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["status"] == "INSUFFICIENT_DATA"
    assert data["result"]["report_count"] == 8 and data["raw_report_count"] == 16
    assert all(t["importance"] is None for t in data["topics"])


def test_results_unknown_target_404():
    assert client.get("/api/v1/results/nope").status_code == 404
    assert client.get("/api/v1/results/..%2Fconfig%2Fapi").status_code == 404


def test_comparison():
    data = client.get("/api/v1/comparison").json()
    rows = {r["target_id"]: r for r in data["targets"]}
    assert set(rows) == {"amazon_sde1", "microsoft_sde1", "google_swe_l3", "flipkart_sde1"}
    assert rows["google_swe_l3"]["density_gate_passed"] is False and rows["google_swe_l3"]["top_priority_gaps"] == []
    assert rows["flipkart_sde1"]["S_comp"] == 89.724 and rows["flipkart_sde1"]["raw_report_count"] == 20
    assert rows["amazon_sde1"]["fallback_topics"] == 3 and rows["amazon_sde1"]["unmapped_distinct_terms"] == 1305


def test_benchmark():
    data = client.get("/api/v1/benchmark").json()
    assert set(data["methods"]) == {"keyword", "tfidf", "minilm_desc", "minilm_name_desc"}
    assert data["methods"]["minilm_desc"]["test"]["overall"]["macro_f1"] == 0.2133
    assert "predictions" not in data["methods"]["minilm_desc"]["test"]
    assert data["label_agreement"]["kappa_draft_vs_second_labeller"] == 0.812
    assert data["limitations"]
    assert data["recommendation"].startswith("Keep the production matcher")


def test_cors_allows_vite_dev_server():
    response = client.options("/api/v1/targets", headers={"Origin": "http://localhost:5173",
                                                           "Access-Control-Request-Method": "GET"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

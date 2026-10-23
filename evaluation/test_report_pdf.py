"""
Dashboard 'Download report (PDF)': one PDF per company with the provisional score, confidence indicators, top gaps,
what to study next, versions and a disclaimer. Built from saved files only; scores are never recomputed.
"""
import io

import pdfplumber
import pytest
from fastapi.testclient import TestClient

from backend import report
from backend.app import app

client = TestClient(app)


def _result(reports, universe, fallback, status="SUCCESS"):
    return {"status": status, "report_count": reports, "scoring_universe_size": universe,
            "depth_counts": {"present_topics": {"fallback": fallback}}}


@pytest.mark.parametrize("result, level, n_reasons", [
    (_result(21, 12, 0), "High", 0),
    (_result(16, 12, 0), "Medium", 1),          # margin 1 above the 15-report gate
    (_result(16, 9, 2), "Low", 3),
    (_result(8, None, 0, "INSUFFICIENT_DATA"), "Insufficient data", 1),
])
def test_confidence_matches_the_dashboard_rules(result, level, n_reasons):
    c = report.confidence_of(result, 15)
    assert c["level"] == level and len(c["reasons"]) == n_reasons


def _text(pdf_bytes):
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def test_report_pdf_for_scored_company():
    response = client.get("/api/v1/report/amazon_sde1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == 'attachment; filename="prepline_amazon_sde1_v1.2.pdf"'
    assert response.content.startswith(b"%PDF")
    text = _text(response.content)
    assert "Amazon SDE-1" in text and "88.8" in text and "Provisional" in text
    expected = report.confidence_of(client.get("/api/v1/results/amazon_sde1").json()["result"], 15)
    assert f"{expected['level']} confidence" in text
    assert all(reason in text for reason in expected["reasons"])
    assert "Linked List Manipulation & Cycle Detection" in text and "Tree Traversals" in text
    assert "What to study next" in text and "BCSE202L" in text and "geeksforgeeks.org" in text
    assert "taxonomy v1.0" in text and "config v1.2" in text and "results v1.2" in text
    assert "not a ranking" in text and "Disclaimer" in text


def test_report_pdf_for_insufficient_company_has_no_score():
    response = client.get("/api/v1/report/google_swe_l3")
    assert response.status_code == 200
    text = _text(response.content)
    assert "Insufficient data" in text and "8 of 15" in text
    assert "What to study next" not in text


def test_report_unknown_target_404():
    assert client.get("/api/v1/report/nope").status_code == 404
    assert client.get("/api/v1/report/..%2Fconfig%2Fapi").status_code == 404

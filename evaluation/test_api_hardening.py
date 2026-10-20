"""
Security hardening of the API (manual review findings M1-M5, L1, L3).
Limits come from config/api.json; tests shrink them with monkeypatch where needed.
"""
import io
import json

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

import backend.routes as routes
from backend.app import app
from pipeline.config import load_api_config
from pipeline.syllabus_parser import UnsupportedPDFError, parse_syllabus_pdf

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def core_course_allowlist():
    app.dependency_overrides[routes.get_core_courses] = lambda: ["CSE2001"]
    yield
    app.dependency_overrides.clear()


def _pdf_bytes(pages: int = 1) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for page in range(pages):
        c.drawString(100, 750, "Course Code: CSE2001")
        c.drawString(100, 735, "Course Title: Data Structures and Algorithms")
        c.drawString(100, 720, "L T P J C : 3 0 2 0 4")
        c.drawString(100, 680, f"Module: {page + 1} Stacks and Queues (6 hours)")
        c.drawString(100, 665, "Stack operations, Queue implementations.")
        c.showPage()
    c.save()
    return buf.getvalue()


def _upload(content: bytes, name: str = "syllabus.pdf"):
    return client.post("/api/v1/syllabi/upload", files={"file": (name, content, "application/pdf")})


# --- M1: upload size, page count, cache size, no raw text in the cache ---------------------------

def test_api_limits_in_config():
    cfg = load_api_config()
    assert cfg["max_upload_bytes"] == 10 * 1024 * 1024
    assert cfg["max_pdf_pages"] == 300
    assert cfg["syllabus_cache_size"] > 0


def test_oversized_upload_rejected_with_413(monkeypatch):
    monkeypatch.setattr(routes, "MAX_UPLOAD_BYTES", 1000)
    response = _upload(b"%PDF-1.4\n" + b"0" * 2000)
    assert response.status_code == 413


def test_oversized_body_rejected_before_the_handler(monkeypatch):
    called = []
    monkeypatch.setattr(routes, "MAX_UPLOAD_BYTES", 1000)
    monkeypatch.setattr(routes, "parse_syllabus_pdf", lambda *a, **k: called.append(1))
    response = _upload(b"%PDF-1.4\n" + b"0" * 200_000)  # > limit + multipart overhead
    assert response.status_code == 413
    assert called == []


def test_too_many_pages_rejected_with_400(monkeypatch):
    monkeypatch.setattr(routes, "MAX_PDF_PAGES", 1)
    response = _upload(_pdf_bytes(pages=2))
    assert response.status_code == 400
    assert "pages" in response.json()["detail"]


def test_parser_enforces_page_limit(tmp_path):
    path = tmp_path / "two_pages.pdf"
    path.write_bytes(_pdf_bytes(pages=2))
    with pytest.raises(UnsupportedPDFError, match="pages"):
        parse_syllabus_pdf(str(path), core_courses=["CSE2001"], max_pages=1)


def test_syllabus_cache_is_capped(monkeypatch):
    monkeypatch.setattr(routes, "SYLLABUS_CACHE_SIZE", 2)
    routes.SYLLABUS_CACHE.clear()
    ids = [_upload(_pdf_bytes()).json()["syllabus_id"] for _ in range(3)]
    assert len(routes.SYLLABUS_CACHE) == 2
    assert ids[0] not in routes.SYLLABUS_CACHE  # oldest evicted
    run = client.post("/api/v1/pipeline/run", json={"syllabus_id": ids[0]})
    assert run.status_code == 404


def test_cache_stores_no_raw_text():
    routes.SYLLABUS_CACHE.clear()
    syllabus_id = _upload(_pdf_bytes()).json()["syllabus_id"]
    stored = json.dumps(routes.SYLLABUS_CACHE[syllabus_id])
    assert "raw_text" not in stored
    assert "intermediate_concepts" not in stored
    assert "Queue implementations" not in stored
    # what scoring needs is kept
    mapping = routes.SYLLABUS_CACHE[syllabus_id]["two_pass_mappings"][0]
    assert {"matched_topic_ids", "depth_signals"} <= set(mapping)

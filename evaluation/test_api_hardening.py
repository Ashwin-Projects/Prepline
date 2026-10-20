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


# --- M5: loopback-only dev server; unguessable syllabus ids --------------------------------------

def test_dev_server_binds_loopback_by_default(monkeypatch):
    import backend.app as app_module
    monkeypatch.delenv("PREPLINE_HOST", raising=False)
    assert app_module.dev_server_settings()["host"] == "127.0.0.1"
    monkeypatch.setenv("PREPLINE_HOST", "0.0.0.0")
    assert app_module.dev_server_settings()["host"] == "0.0.0.0"  # explicit opt-in only


def test_syllabus_ids_are_uuid4():
    import re
    import uuid
    first = _upload(_pdf_bytes(), name="my_syllabus.pdf").json()["syllabus_id"]
    second = _upload(_pdf_bytes(), name="my_syllabus.pdf").json()["syllabus_id"]
    for syllabus_id in (first, second):
        match = re.fullmatch(r"syl_([0-9a-f]{32})", syllabus_id)
        assert match, syllabus_id
        assert uuid.UUID(match.group(1)).version == 4
    assert first != second
    assert "my_syllabus" not in first


# --- M4: CORS allowlist from config, no credentials ----------------------------------------------

def _preflight(origin):
    return client.options("/api/v1/pipeline/run",
                          headers={"Origin": origin, "Access-Control-Request-Method": "POST"})


def test_cors_allowlist_in_config():
    assert load_api_config()["cors_allowed_origins"] == ["http://localhost:8501"]


def test_cors_rejects_unknown_origin():
    response = _preflight("https://evil.example")
    assert "access-control-allow-origin" not in response.headers
    simple = client.get("/api/v1/supported-targets", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in simple.headers


def test_cors_allows_dashboard_without_credentials():
    response = _preflight("http://localhost:8501")
    assert response.headers["access-control-allow-origin"] == "http://localhost:8501"
    assert "access-control-allow-credentials" not in response.headers


# --- M3: 500s are generic + request id; details only in the server log; long names are 400 -------

SECRET = r"boom at C:\Users\someone\AppData\Local\Temp\tmpabc\syllabus.pdf"


def _assert_generic_500(response):
    import re
    assert response.status_code == 500
    body = response.json()
    assert "Users" not in json.dumps(body) and "boom" not in json.dumps(body)
    assert re.fullmatch(r"[0-9a-f]{32}", body["request_id"])
    assert body["request_id"] in body["detail"]
    assert response.headers["x-request-id"] == body["request_id"]
    return body["request_id"]


def test_upload_500_is_generic_and_logged(monkeypatch, caplog):
    def broken(*args, **kwargs):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(routes, "parse_syllabus_pdf", broken)
    with caplog.at_level("ERROR"):
        request_id = _assert_generic_500(_upload(_pdf_bytes()))
    logged = [r for r in caplog.records if request_id in r.getMessage()]
    assert logged and SECRET in (logged[0].exc_text or "") + str(logged[0].exc_info)


def test_unhandled_500_is_generic_and_logged(monkeypatch, caplog):
    def broken(*args, **kwargs):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(routes, "calculate_syllabus_coverage", broken)
    routes._cache_syllabus("syl_err_test", {"syllabus_id": "x", "taxonomy_version": "v1.0", "two_pass_mappings": []})
    with caplog.at_level("ERROR"):
        request_id = _assert_generic_500(client.post("/api/v1/pipeline/run", json={"syllabus_id": "syl_err_test"}))
    assert any(request_id in r.getMessage() for r in caplog.records)


def test_overlong_filename_is_400():
    response = _upload(_pdf_bytes(), name="a" * 300 + ".pdf")
    assert response.status_code == 400
    assert "filename" in response.json()["detail"].lower()


# --- M2: handlers never block the event loop; parsing has a timeout ------------------------------

def _fake_parsed():
    return {"syllabus_id": "x.pdf", "taxonomy_version": "v1.0", "course_metadata": {},
            "units_count": 0, "two_pass_mappings": []}


def _time_quick_request_during(slow_request):
    """Runs slow_request(shared_client) in a thread, then times a quick request on the SAME event loop.
    (A TestClient used without `with` starts a new event loop per request, which would hide blocking.)"""
    import threading
    import time
    with TestClient(app, raise_server_exceptions=False) as shared:
        worker = threading.Thread(target=slow_request, args=(shared,))
        worker.start()
        time.sleep(0.3)  # the slow request is now in its handler
        start = time.perf_counter()
        quick = shared.get("/api/v1/supported-targets")
        elapsed = time.perf_counter() - start
        worker.join()
    return quick, elapsed


def test_slow_parse_does_not_block_other_requests(monkeypatch):
    import time

    def slow_parse(*args, **kwargs):
        time.sleep(2.0)
        return _fake_parsed()

    monkeypatch.setattr(routes, "parse_syllabus_pdf", slow_parse)
    quick, elapsed = _time_quick_request_during(
        lambda c: c.post("/api/v1/syllabi/upload", files={"file": ("s.pdf", _pdf_bytes(), "application/pdf")})
    )
    assert quick.status_code == 200
    assert elapsed < 1.0, f"event loop blocked for {elapsed:.2f}s"


def test_slow_pipeline_run_does_not_block_other_requests(monkeypatch):
    import time
    real = routes.calculate_syllabus_coverage

    def slow_coverage(*args, **kwargs):
        time.sleep(2.0)
        return real(*args, **kwargs)

    monkeypatch.setattr(routes, "calculate_syllabus_coverage", slow_coverage)
    routes._cache_syllabus("syl_block_test", _fake_parsed())
    quick, elapsed = _time_quick_request_during(
        lambda c: c.post("/api/v1/pipeline/run", json={"syllabus_id": "syl_block_test"})
    )
    assert quick.status_code == 200
    assert elapsed < 1.0, f"event loop blocked for {elapsed:.2f}s"


def test_parse_timeout_returns_504(monkeypatch):
    import time

    def stuck_parse(*args, **kwargs):
        time.sleep(3.0)
        return _fake_parsed()

    monkeypatch.setattr(routes, "parse_syllabus_pdf", stuck_parse)
    monkeypatch.setattr(routes, "PARSE_TIMEOUT_SECONDS", 0.5)
    start = time.perf_counter()
    response = _upload(_pdf_bytes())
    assert response.status_code == 504
    assert time.perf_counter() - start < 2.5


def test_parse_timeout_in_config():
    assert load_api_config()["parse_timeout_seconds"] > 0


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

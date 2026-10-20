"""
Item 7: uploaded syllabus filenames are sanitised before they touch the filesystem.
"""
import io
import os

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

import backend.routes as routes
from backend.app import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def core_course_allowlist():
    # The upload fixtures use course CSE2001; supply a test allowlist instead of the real config.
    app.dependency_overrides[routes.get_core_courses] = lambda: ["CSE2001"]
    yield
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("../../evil.pdf", "evil.pdf"),
        ("..\\..\\evil.pdf", "evil.pdf"),
        ("/etc/evil.pdf", "evil.pdf"),
        ("my syllabus (1).pdf", "my_syllabus__1_.pdf"),
        ("syllabus.PDF", "syllabus.PDF"),
        ("../.pdf", "upload.pdf"),
        ("..\\..\\", "upload.pdf"),
        ("", "upload.pdf"),
        (None, "upload.pdf"),
    ],
)
def test_safe_upload_filename(raw, expected):
    assert routes.safe_upload_filename(raw) == expected


def _pdf_bytes() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, "Course Code: CSE2001")
    c.drawString(100, 735, "Course Title: Data Structures and Algorithms")
    c.drawString(100, 720, "L T P J C : 3 0 2 0 4")
    c.drawString(100, 680, "Module: 1 Stacks and Queues (6 hours)")
    c.drawString(100, 665, "Stack operations, Queue implementations.")
    c.save()
    return buf.getvalue()


@pytest.mark.parametrize("raw_name", ["../../evil.pdf", "..\\..\\evil.pdf"])
def test_upload_with_traversal_filename_stays_in_tempdir(raw_name, monkeypatch):
    seen_paths = []
    real_parse = routes.parse_syllabus_pdf

    def spy(path, *args, **kwargs):
        seen_paths.append(path)
        return real_parse(path, *args, **kwargs)

    monkeypatch.setattr(routes, "parse_syllabus_pdf", spy)

    response = client.post(
        "/api/v1/syllabi/upload",
        files={"file": (raw_name, _pdf_bytes(), "application/pdf")},
    )

    assert response.status_code == 201, response.text
    assert len(seen_paths) == 1
    written = seen_paths[0]
    assert os.path.basename(written) == "evil.pdf"
    assert ".." not in written
    assert response.json()["filename"] == "evil.pdf"
    assert ".." not in response.json()["syllabus_id"]

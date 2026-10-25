"""Load structured syllabus catalogs and optionally extract text from a PDF."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "data/raw/syllabi/vit_cse_2024_2025_discipline_core_catalog.csv"


def load_course_catalog(path: str | Path = DEFAULT_CATALOG) -> list[dict[str, Any]]:
    """Load the extracted course catalog, preserving source/page provenance."""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    required = {"course_code", "course_title", "course_type", "credits", "curriculum_source", "source_page"}
    if rows and not required.issubset(rows[0]):
        raise ValueError(f"Course catalog is missing columns: {sorted(required - set(rows[0]))}")
    seen = set()
    for row in rows:
        key = row["course_code"].strip()
        if not key or key in seen:
            raise ValueError(f"Missing or duplicate course code: {key!r}")
        seen.add(key)
        row["credits"] = float(row["credits"]) if row.get("credits", "").strip() else None
    return rows


def extract_pdf_text(path: str | Path) -> list[dict[str, Any]]:
    """Extract page text from a local PDF; does not download or redistribute it."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf to extract PDF text: python -m pip install pypdf") from exc
    pdf_path = Path(path)
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)
    reader = PdfReader(str(pdf_path))
    return [{"page": index + 1, "text": page.extract_text() or ""} for index, page in enumerate(reader.pages)]


def search_course_catalog(query: str, courses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Case-insensitive course-code/title search."""
    needle = query.casefold().strip()
    if not needle:
        return courses
    return [row for row in courses if needle in row["course_code"].casefold()
            or needle in row["course_title"].casefold()]

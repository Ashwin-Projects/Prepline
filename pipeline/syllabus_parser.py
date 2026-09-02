"""
Syllabus Parser Module (Phase 7)

Parses text-selectable VIT syllabus PDFs using pdfplumber:
- Detects and flags scanned/image-based PDFs as unsupported (OCR excluded from MVP scope).
- Extracts course metadata, module units, and available depth signals.
- Passes extracted text to the two-pass abstraction pipeline preserving taxonomy_version.
"""

import re
import os
from typing import Dict, Any, List, Optional
import pdfplumber

from pipeline.keyword_abstraction import two_pass_abstract, DEFAULT_TAXONOMY_VERSION

# Minimum text threshold to detect scanned / non-text PDFs
MIN_TEXT_LENGTH_THRESHOLD = 50


class UnsupportedPDFError(ValueError):
    """Raised when a PDF is scanned or lacks extractable text (OCR unsupported in MVP)."""
    pass


def is_scanned_pdf(pdf_path: str) -> bool:
    """
    Checks if a PDF is scanned (contains no text or text below threshold).
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")

    total_text_length = 0
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            return True
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            total_text_length += len(page_text.strip())

    return total_text_length < MIN_TEXT_LENGTH_THRESHOLD


def extract_course_metadata(full_text: str) -> Dict[str, Any]:
    """
    Extracts VIT course code, course title, and L-T-P-J-C credits from full syllabus text.
    """
    metadata = {
        "course_code": "UNKNOWN",
        "course_title": "UNKNOWN",
        "lecture_hours": None,
        "tutorial_hours": None,
        "practical_hours": None,
        "project_hours": None,
        "credits": None
    }

    # Match Course Code (e.g., CSE2001, ECE1002, BIT3001)
    code_match = re.search(r'\b([A-Z]{3,4}\d{3,4}[L|P|J]?)\b', full_text)
    if code_match:
        metadata["course_code"] = code_match.group(1)

    # Match Course Title (e.g., Course Title: Data Structures and Algorithms)
    title_match = re.search(r'(?:Course Title|Course Name)\s*[:\-]\s*([^\n\r]+)', full_text, re.IGNORECASE)
    if title_match:
        metadata["course_title"] = title_match.group(1).strip()

    # Match L-T-P-J-C structure (e.g., L T P J C / 3 0 2 0 4 or L: 3 T: 0 P: 2 J: 0 C: 4)
    ltpjc_match = re.search(r'\bL\s*T\s*P\s*J\s*C\s*[\:\-\s]+\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', full_text, re.IGNORECASE)
    if ltpjc_match:
        metadata["lecture_hours"] = int(ltpjc_match.group(1))
        metadata["tutorial_hours"] = int(ltpjc_match.group(2))
        metadata["practical_hours"] = int(ltpjc_match.group(3))
        metadata["project_hours"] = int(ltpjc_match.group(4))
        metadata["credits"] = int(ltpjc_match.group(5))

    return metadata


def extract_depth_signals(unit_text: str, course_metadata: Dict[str, Any]) -> Dict[str, Optional[int]]:
    """
    Extracts depth signals available from a syllabus unit:
    - unit_hours
    - slide_count
    - lab_hours
    - lab_count
    - assignment_count
    """
    depth_signals = {
        "unit_hours": None,
        "slide_count": None,
        "lab_hours": None,
        "lab_count": None,
        "assignment_count": None
    }

    # Extract unit_hours (e.g., "6 hours", "8 Hours", "Duration: 5 hrs")
    hours_match = re.search(r'\b(\d+)\s*(?:hours|hrs|hour|hr)\b', unit_text, re.IGNORECASE)
    if hours_match:
        depth_signals["unit_hours"] = int(hours_match.group(1))

    # Extract slide_count if explicitly mentioned
    slides_match = re.search(r'\b(\d+)\s*(?:slides|slide)\b', unit_text, re.IGNORECASE)
    if slides_match:
        depth_signals["slide_count"] = int(slides_match.group(1))

    # Extract lab_count (e.g., "Experiment 1", "Lab exercise 3", "10 lab experiments")
    lab_exp_matches = re.findall(r'\b(?:experiment|lab exercise|practical task)\s*\d+', unit_text, re.IGNORECASE)
    if lab_exp_matches:
        depth_signals["lab_count"] = len(lab_exp_matches)

    # Extract lab_hours from course practical hours metadata if applicable
    if course_metadata.get("practical_hours"):
        depth_signals["lab_hours"] = course_metadata["practical_hours"] * 15  # standard semester hours conversion

    # Extract assignment_count (e.g., "Assignment 1", "Assessment 2")
    assignment_matches = re.findall(r'\b(?:assignment|assessment|project task)\s*\d+', unit_text, re.IGNORECASE)
    if assignment_matches:
        depth_signals["assignment_count"] = len(assignment_matches)

    return depth_signals


def parse_vit_modules(full_text: str, course_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Splits text into VIT syllabus modules/units and extracts text content and depth signals.
    """
    # Pattern for VIT module splits: e.g. "Module: 1", "Module 1", "Unit 1"
    module_pattern = r'(?i)(?:Module|Unit)\s*[:\-]?\s*(\d+)\s*[:\-]?\s*([^\n\r]*)'
    splits = list(re.finditer(module_pattern, full_text))

    modules = []

    if splits:
        for i, match in enumerate(splits):
            module_num = match.group(1)
            module_title = match.group(2).strip()
            
            start_idx = match.start()
            end_idx = splits[i + 1].start() if i + 1 < len(splits) else len(full_text)
            
            unit_content = full_text[start_idx:end_idx].strip()
            depth_signals = extract_depth_signals(unit_content, course_metadata)

            modules.append({
                "module_number": int(module_num),
                "module_title": module_title or f"Module {module_num}",
                "unit_text": unit_content,
                "depth_signals": depth_signals
            })
    else:
        # Fallback: treat whole text as a single syllabus unit if no explicit modules found
        depth_signals = extract_depth_signals(full_text, course_metadata)
        modules.append({
            "module_number": 1,
            "module_title": course_metadata.get("course_title", "Full Syllabus"),
            "unit_text": full_text.strip(),
            "depth_signals": depth_signals
        })

    return modules


def parse_syllabus_pdf(
    pdf_path: str,
    taxonomy_version: str = DEFAULT_TAXONOMY_VERSION
) -> Dict[str, Any]:
    """
    Parses a text-selectable VIT syllabus PDF:
    1. Detects scanned/image PDFs and raises UnsupportedPDFError.
    2. Extracts course metadata, modules, and depth signals.
    3. Passes extracted unit texts into two_pass_abstract preserving taxonomy_version.
    """
    if is_scanned_pdf(pdf_path):
        raise UnsupportedPDFError(
            f"Unsupported PDF '{os.path.basename(pdf_path)}': Document is a scanned image or contains no extractable text. "
            "OCR processing is excluded from MVP scope."
        )

    # Extract all text from pages
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

    full_text = "\n".join(pages_text)
    course_metadata = extract_course_metadata(full_text)
    modules = parse_vit_modules(full_text, course_metadata)

    # Map each module unit through two-pass abstraction pipeline
    two_pass_mappings = []
    course_code = course_metadata.get("course_code", "SYLLABUS")

    for mod in modules:
        source_id = f"{course_code}_mod_{mod['module_number']}"
        mapping = two_pass_abstract(
            source_id=source_id,
            raw_text=mod["unit_text"],
            source_type="syllabus",
            taxonomy_version=taxonomy_version
        )
        # Attach depth signals to the mapping output for Phase 8 consumption
        mapping["depth_signals"] = mod["depth_signals"]
        mapping["module_number"] = mod["module_number"]
        mapping["module_title"] = mod["module_title"]
        two_pass_mappings.append(mapping)

    return {
        "syllabus_id": os.path.basename(pdf_path),
        "source_type": "syllabus",
        "taxonomy_version": taxonomy_version,
        "course_metadata": course_metadata,
        "units_count": len(modules),
        "two_pass_mappings": two_pass_mappings
    }

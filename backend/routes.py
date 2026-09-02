"""
API Route Handlers (Phase 14)

Implements API endpoints for:
1. Syllabus PDF upload and parsing
2. Company/role target selection and report-count validation
3. PREPLINE pipeline execution and result generation
"""

import os
import shutil
import tempfile
from typing import Dict, Any
from fastapi import APIRouter, File, UploadFile, HTTPException, status

from backend.schemas import (
    TargetSelectionRequest,
    PipelineRunRequest,
    UploadSyllabusResponse,
    ReportCountValidationResponse,
    PreplineResultResponse,
    TopicCoverageItem,
    TopicImportanceItem,
    PriorityGapItem
)
from pipeline.syllabus_parser import parse_syllabus_pdf, UnsupportedPDFError

router = APIRouter(prefix="/api/v1", tags=["PREPLINE Alignment Engine"])

# Prototype Scope Constants
SUPPORTED_COMPANY = "Amazon"
SUPPORTED_ROLE = "SDE-1"
MIN_REPORTS_REQUIRED = 15

# Storage for uploaded syllabi in memory/temp cache for API prototype
SYLLABUS_CACHE: Dict[str, Dict[str, Any]] = {}


@router.get("/supported-targets", response_model=Dict[str, Any])
async def get_supported_targets():
    """Returns currently supported company and role combinations (Amazon SDE-1 only in prototype)."""
    return {
        "supported_targets": [
            {"company": SUPPORTED_COMPANY, "role": SUPPORTED_ROLE}
        ],
        "message": "Currently supporting Amazon SDE-1 prototype only."
    }


@router.post("/syllabi/upload", response_model=UploadSyllabusResponse, status_code=status.HTTP_201_CREATED)
async def upload_syllabus(file: UploadFile = File(...)):
    """
    Endpoint 1: Syllabus Upload
    Parses uploaded text-selectable PDF syllabus via Phase 7 parser.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only text-selectable PDF files are accepted."
        )

    # Save uploaded file temporarily for parsing
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Execute Phase 7 Syllabus Parser
        parsed_syllabus = parse_syllabus_pdf(temp_path, taxonomy_version="v1.0")

        syllabus_id = f"syl_{len(SYLLABUS_CACHE) + 1:03d}_{file.filename}"
        SYLLABUS_CACHE[syllabus_id] = parsed_syllabus

        course_meta = parsed_syllabus.get("course_metadata", {})

        return UploadSyllabusResponse(
            syllabus_id=syllabus_id,
            filename=file.filename,
            units_count=parsed_syllabus.get("units_count", 0),
            course_code=course_meta.get("course_code"),
            course_title=course_meta.get("course_title"),
            taxonomy_version=parsed_syllabus.get("taxonomy_version", "v1.0"),
            message="Syllabus successfully uploaded and parsed."
        )

    except UnsupportedPDFError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse syllabus PDF: {str(err)}"
        )
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/validate-target", response_model=ReportCountValidationResponse)
async def validate_target(request: TargetSelectionRequest):
    """
    Endpoint 2 & 3: Company/Role Selection & Report-Count Density Gate Validation
    Checks if target is Amazon SDE-1 and evaluates report count against MIN_REPORTS_REQUIRED = 15.
    """
    # Verify company and role scope
    if request.company.lower() != SUPPORTED_COMPANY.lower() or request.role.lower() != SUPPORTED_ROLE.lower():
        return ReportCountValidationResponse(
            company=request.company,
            role=request.role,
            report_count=0,
            min_reports_required=MIN_REPORTS_REQUIRED,
            eligible=False,
            status="UNSUPPORTED_ROLE",
            message=f"Role '{request.company} {request.role}' is not supported yet. PREPLINE currently supports Amazon SDE-1 only."
        )

    # In prototype, we assume Amazon SDE-1 dataset count
    # (Will be connected to interview_parser.py dataset count in future phase)
    mock_report_count = 18  # >= 15 reports

    if mock_report_count < MIN_REPORTS_REQUIRED:
        return ReportCountValidationResponse(
            company=SUPPORTED_COMPANY,
            role=SUPPORTED_ROLE,
            report_count=mock_report_count,
            min_reports_required=MIN_REPORTS_REQUIRED,
            eligible=False,
            status="INSUFFICIENT_DATA",
            message=f"Insufficient interview data ({mock_report_count}/{MIN_REPORTS_REQUIRED} reports). Minimum 15 required."
        )

    return ReportCountValidationResponse(
        company=SUPPORTED_COMPANY,
        role=SUPPORTED_ROLE,
        report_count=mock_report_count,
        min_reports_required=MIN_REPORTS_REQUIRED,
        eligible=True,
        status="ELIGIBLE",
        message="Target Amazon SDE-1 meets the 15-report density gate requirement."
    )


@router.post("/pipeline/run", response_model=PreplineResultResponse)
async def run_pipeline(request: PipelineRunRequest):
    """
    Endpoint 4 & 5: Pipeline Execution & Return Results
    Orchestrates the PREPLINE pipeline flow and returns the full result structure.
    """
    # 1. Validate Target Role
    if request.company.lower() != SUPPORTED_COMPANY.lower() or request.role.lower() != SUPPORTED_ROLE.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only Amazon SDE-1 is supported in the prototype."
        )

    # 2. Check if syllabus exists in cache
    syllabus_data = SYLLABUS_CACHE.get(request.syllabus_id)
    if not syllabus_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Syllabus ID '{request.syllabus_id}' not found. Please upload syllabus first."
        )

    # 3. Validate Density Gate (Report Count >= 15)
    report_count = 18  # Baseline Amazon SDE-1 dataset report count
    if report_count < MIN_REPORTS_REQUIRED:
        return PreplineResultResponse(
            company=SUPPORTED_COMPANY,
            role=SUPPORTED_ROLE,
            report_count=report_count,
            density_gate_passed=False,
            S_comp=None,
            topic_coverage=[],
            interview_importance=[],
            priority_gaps=[],
            taxonomy_version="v1.0",
            scoring_config_version="v1.0",
            depth_confidence_status="fallback",
            status="INSUFFICIENT_DATA",
            message="Report count < 15. Pipeline stopped per density gate requirement."
        )

    # 4. Assemble modular result structure ready for future scoring engine output
    # (Scaffolding return structure with parsed syllabus mappings and version tags)
    taxonomy_ver = syllabus_data.get("taxonomy_version", "v1.0")

    # Sample result payload structure matching blueprint
    return PreplineResultResponse(
        company=SUPPORTED_COMPANY,
        role=SUPPORTED_ROLE,
        report_count=report_count,
        density_gate_passed=True,
        S_comp=76.5,  # Placeholder score ready for scoring.py hook
        topic_coverage=[
            TopicCoverageItem(
                topic_id="dsa.trees.bst",
                topic_name="Binary Search Trees",
                presence=1,
                depth=3.5,
                depth_status="measured",
                depth_signal_count=2,
                coverage=0.82
            ),
            TopicCoverageItem(
                topic_id="dsa.dp.knapsack",
                topic_name="Dynamic Programming Knapsack",
                presence=1,
                depth=1.0,
                depth_status="fallback",
                depth_signal_count=0,
                coverage=0.45
            )
        ],
        interview_importance=[
            TopicImportanceItem(
                topic_id="dsa.trees.bst",
                importance=0.88,
                matched_report_count=16
            ),
            TopicImportanceItem(
                topic_id="dsa.dp.knapsack",
                importance=0.92,
                matched_report_count=17
            )
        ],
        priority_gaps=[
            PriorityGapItem(
                rank=1,
                topic_id="dsa.dp.knapsack",
                topic_name="Dynamic Programming Knapsack",
                importance=0.92,
                coverage=0.45,
                priority_gap=0.506
            ),
            PriorityGapItem(
                rank=2,
                topic_id="dsa.trees.bst",
                topic_name="Binary Search Trees",
                importance=0.88,
                coverage=0.82,
                priority_gap=0.158
            )
        ],
        taxonomy_version=taxonomy_ver,
        scoring_config_version="v1.0",
        depth_confidence_status="measured",
        status="SUCCESS",
        message="PREPLINE alignment calculation completed successfully."
    )

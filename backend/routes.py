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
from pipeline.scoring import (
    calculate_syllabus_coverage,
    calculate_topic_importance,
    calculate_composite_score,
    rank_priority_gaps
)

router = APIRouter(prefix="/api/v1", tags=["PREPLINE Alignment Engine"])

# Prototype Scope Constants
SUPPORTED_COMPANY = "Amazon"
SUPPORTED_ROLE = "SDE-1"
MIN_REPORTS_REQUIRED = 15

# Dataset Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")
REPORTS_CSV_PATH = os.path.join(DATA_DIR, "reports.csv")
QUESTIONS_CSV_PATH = os.path.join(DATA_DIR, "questions.csv")


def _get_report_count() -> int:
    """Reads unique report count from canonical processed reports.csv dataset."""
    if not os.path.exists(REPORTS_CSV_PATH):
        return 0
    import csv
    with open(REPORTS_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        report_ids = {row["report_id"].strip() for row in reader if row.get("report_id")}
        return len(report_ids)

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

    report_count = _get_report_count()

    if report_count < MIN_REPORTS_REQUIRED:
        return ReportCountValidationResponse(
            company=SUPPORTED_COMPANY,
            role=SUPPORTED_ROLE,
            report_count=report_count,
            min_reports_required=MIN_REPORTS_REQUIRED,
            eligible=False,
            status="INSUFFICIENT_DATA",
            message=f"Insufficient interview data ({report_count}/{MIN_REPORTS_REQUIRED} reports). Minimum 15 required."
        )

    return ReportCountValidationResponse(
        company=SUPPORTED_COMPANY,
        role=SUPPORTED_ROLE,
        report_count=report_count,
        min_reports_required=MIN_REPORTS_REQUIRED,
        eligible=True,
        status="ELIGIBLE",
        message="Target Amazon SDE-1 meets the 15-report density gate requirement."
    )


@router.post("/pipeline/run", response_model=PreplineResultResponse)
async def run_pipeline(request: PipelineRunRequest):
    """
    Endpoint 4 & 5: Pipeline Execution & Return Results
    Orchestrates the PREPLINE pipeline flow and returns real calculated scoring results.
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
    report_count = _get_report_count()
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

    # 4. Phase 8: Calculate Syllabus Coverage
    coverage_res = calculate_syllabus_coverage(syllabus_data)
    topic_coverage_list = coverage_res.get("topic_coverage", [])

    # 5. Phase 9: Calculate Topic Importance
    importance_res = calculate_topic_importance(
        questions_input=QUESTIONS_CSV_PATH,
        total_reports_count=report_count
    )
    importance_list = importance_res.get("interview_importance", [])

    # 6. Phase 10: Calculate Composite Score S_comp
    composite_res = calculate_composite_score(
        importance_dict=importance_res,
        coverage_dict=coverage_res
    )
    s_comp = composite_res.get("composite_score", 0.0)

    # 7. Phase 11: Rank Priority Gaps
    priority_gaps_list = rank_priority_gaps(
        importance_dict=importance_res,
        coverage_dict=coverage_res
    )

    # 8. Determine overall depth confidence status
    depth_statuses = {item.get("depth_status") for item in topic_coverage_list if item.get("depth_status")}
    if depth_statuses == {"measured"}:
        overall_depth_status = "measured"
    elif depth_statuses == {"fallback"}:
        overall_depth_status = "fallback"
    elif depth_statuses:
        overall_depth_status = "mixed"
    else:
        overall_depth_status = "fallback"

    taxonomy_ver = syllabus_data.get("taxonomy_version", "v1.0")

    return PreplineResultResponse(
        company=SUPPORTED_COMPANY,
        role=SUPPORTED_ROLE,
        report_count=report_count,
        density_gate_passed=True,
        S_comp=s_comp,
        topic_coverage=[TopicCoverageItem(**item) for item in topic_coverage_list],
        interview_importance=[TopicImportanceItem(**item) for item in importance_list],
        priority_gaps=[PriorityGapItem(**item) for item in priority_gaps_list],
        taxonomy_version=taxonomy_ver,
        scoring_config_version="v1.0",
        depth_confidence_status=overall_depth_status,
        status="SUCCESS",
        message="PREPLINE alignment calculation completed successfully."
    )


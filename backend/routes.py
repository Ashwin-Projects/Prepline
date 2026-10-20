"""
API Route Handlers (Phase 14)

Implements API endpoints for:
1. Syllabus PDF upload and parsing
2. Company/role target selection and report-count validation
3. PREPLINE pipeline execution and result generation
"""

import asyncio
import logging
import os
import re
import shutil
import tempfile
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse

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
from pipeline.config import load_api_config, load_scoring_config
from pipeline.interview_parser import count_reports, filter_questions, load_questions_csv
from pipeline.syllabus_parser import parse_syllabus_pdf, NoCoreCoursesError, UnsupportedPDFError
from pipeline.scoring import (
    calculate_syllabus_coverage,
    get_interview_importance,
    calculate_composite_score,
    rank_priority_gaps
)

router = APIRouter(prefix="/api/v1", tags=["PREPLINE Alignment Engine"])

# Prototype Scope Constants
SUPPORTED_COMPANY = "Amazon"
SUPPORTED_ROLE = "SDE-1"

CONFIG = load_scoring_config()
MIN_REPORTS_REQUIRED = CONFIG["min_reports"]
TAXONOMY_VERSION = CONFIG["taxonomy_version"]
SCORING_CONFIG_VERSION = CONFIG["config_version"]

# API safety limits (config/api.json)
API_CONFIG = load_api_config()
MAX_UPLOAD_BYTES = API_CONFIG["max_upload_bytes"]
MAX_PDF_PAGES = API_CONFIG["max_pdf_pages"]
SYLLABUS_CACHE_SIZE = API_CONFIG["syllabus_cache_size"]
PARSE_TIMEOUT_SECONDS = API_CONFIG["parse_timeout_seconds"]
MAX_FILENAME_LENGTH = API_CONFIG["max_filename_length"]

logger = logging.getLogger("prepline.api")


def internal_error_response(err: BaseException, context: str) -> JSONResponse:
    """
    Logs the full error server-side under a fresh request id and returns a generic 500: clients never
    see exception text, file paths or library internals - only the id to quote when reporting it.
    """
    request_id = uuid.uuid4().hex
    logger.error("%s failed [request_id=%s]", context, request_id, exc_info=(type(err), err, err.__traceback__))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error. Reference: {request_id}", "request_id": request_id},
        headers={"X-Request-ID": request_id},
    )

# PDF parsing is CPU-bound: it runs on a small dedicated pool, never on the event loop, so other
# requests keep being served and at most max_concurrent_parses parses run at once.
_PARSE_EXECUTOR = ThreadPoolExecutor(
    max_workers=API_CONFIG["max_concurrent_parses"], thread_name_prefix="syllabus-parse"
)

# Dataset Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")
QUESTIONS_CSV_PATH = os.path.join(DATA_DIR, "questions.csv")


def _get_report_count() -> int:
    """
    Reports with at least one included question (interview_parser.filter_questions).
    The same count is used for the density gate and as the I(t) denominator.
    """
    if not os.path.exists(QUESTIONS_CSV_PATH):
        return 0
    included, _ = filter_questions(load_questions_csv(QUESTIONS_CSV_PATH))
    return count_reports(included)

def get_core_courses() -> List[str]:
    """Core CS course allowlist for syllabus uploads (config syllabus.core_courses); tests override this dependency."""
    return list(CONFIG["syllabus"]["core_courses"])


_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def safe_upload_filename(name: Optional[str]) -> str:
    """
    Reduces a client-supplied upload name to a bare, filesystem-safe PDF filename:
    no directory components (either separator), only [A-Za-z0-9._-], no leading dots.
    Anything that ends up empty or without a .pdf extension becomes "upload.pdf".
    """
    base = os.path.basename((name or "").replace("\\", "/"))
    base = _UNSAFE_FILENAME_CHARS.sub("_", base).lstrip(".")
    if not base.lower().endswith(".pdf"):
        return "upload.pdf"
    return base


# Parsed syllabi kept in memory for /pipeline/run: at most SYLLABUS_CACHE_SIZE entries (oldest evicted),
# and only what scoring needs - never the syllabus text itself.
SYLLABUS_CACHE: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
_CACHED_MAPPING_FIELDS = ("source_id", "course_code", "module_number", "matched_topic_ids", "depth_signals")


def _cache_syllabus(syllabus_id: str, parsed: Dict[str, Any]) -> None:
    SYLLABUS_CACHE[syllabus_id] = {
        "syllabus_id": parsed.get("syllabus_id"),
        "taxonomy_version": parsed.get("taxonomy_version", TAXONOMY_VERSION),
        "two_pass_mappings": [
            {k: m[k] for k in _CACHED_MAPPING_FIELDS if k in m} for m in parsed.get("two_pass_mappings", [])
        ],
    }
    while len(SYLLABUS_CACHE) > SYLLABUS_CACHE_SIZE:
        SYLLABUS_CACHE.popitem(last=False)


def _parse_uploaded_file(temp_dir: str, temp_path: str, core_courses: List[str]) -> Dict[str, Any]:
    """Runs on _PARSE_EXECUTOR and always removes its temp dir, even after the request has timed out."""
    try:
        return parse_syllabus_pdf(
            temp_path, taxonomy_version=TAXONOMY_VERSION, core_courses=core_courses, max_pages=MAX_PDF_PAGES
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


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
async def upload_syllabus(file: UploadFile = File(...), core_courses: List[str] = Depends(get_core_courses)):
    """
    Endpoint 1: Syllabus Upload
    Parses uploaded text-selectable PDF syllabus via Phase 7 parser.
    """
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only text-selectable PDF files are accepted."
        )

    # Save uploaded file temporarily for parsing
    temp_dir = tempfile.mkdtemp()
    parse_owns_temp_dir = False
    filename = safe_upload_filename(file.filename)
    if len(filename) > MAX_FILENAME_LENGTH:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Filename too long (max {MAX_FILENAME_LENGTH} characters)."
        )
    temp_path = os.path.join(temp_dir, filename)

    try:
        contents = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"Upload exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit."
            )
        with open(temp_path, "wb") as buffer:
            buffer.write(contents)

        # Execute Phase 7 Syllabus Parser off the event loop, with a timeout
        future = asyncio.get_running_loop().run_in_executor(
            _PARSE_EXECUTOR, _parse_uploaded_file, temp_dir, temp_path, core_courses
        )
        parse_owns_temp_dir = True
        try:
            parsed_syllabus = await asyncio.wait_for(future, timeout=PARSE_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Syllabus parsing timed out after {PARSE_TIMEOUT_SECONDS:g} seconds."
            )

        syllabus_id = f"syl_{len(SYLLABUS_CACHE) + 1:03d}_{filename}"
        _cache_syllabus(syllabus_id, parsed_syllabus)

        course_meta = parsed_syllabus.get("course_metadata", {})

        return UploadSyllabusResponse(
            syllabus_id=syllabus_id,
            filename=filename,
            units_count=parsed_syllabus.get("units_count", 0),
            course_code=course_meta.get("course_code"),
            course_title=course_meta.get("course_title"),
            taxonomy_version=parsed_syllabus.get("taxonomy_version", TAXONOMY_VERSION),
            message="Syllabus successfully uploaded and parsed."
        )

    except HTTPException:
        raise
    except (UnsupportedPDFError, NoCoreCoursesError) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
    except Exception as err:
        return internal_error_response(err, "Syllabus upload")
    finally:
        if not parse_owns_temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/validate-target", response_model=ReportCountValidationResponse)
def validate_target(request: TargetSelectionRequest):
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
def run_pipeline(request: PipelineRunRequest):
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
            taxonomy_version=TAXONOMY_VERSION,
            scoring_config_version=SCORING_CONFIG_VERSION,
            depth_confidence_status="fallback",
            status="INSUFFICIENT_DATA",
            message="Report count < 15. Pipeline stopped per density gate requirement."
        )

    # 4. Phase 8: Calculate Syllabus Coverage
    coverage_res = calculate_syllabus_coverage(syllabus_data)
    topic_coverage_list = coverage_res.get("topic_coverage", [])

    # 5. Phase 9: Calculate Topic Importance
    importance_res = get_interview_importance(
        SUPPORTED_COMPANY,
        SUPPORTED_ROLE,
        QUESTIONS_CSV_PATH,
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

    taxonomy_ver = syllabus_data.get("taxonomy_version", TAXONOMY_VERSION)

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
        scoring_config_version=SCORING_CONFIG_VERSION,
        depth_confidence_status=overall_depth_status,
        status="SUCCESS",
        message="PREPLINE alignment calculation completed successfully."
    )


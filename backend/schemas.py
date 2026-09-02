"""
API Request and Response Schemas (Phase 14)

Defines Pydantic schemas for syllabus upload, company/role selection,
report-count density gate validation, pipeline execution, and PREPLINE alignment results.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# --- Request Schemas ---

class TargetSelectionRequest(BaseModel):
    company: str = Field(..., example="Amazon", description="Target company name")
    role: str = Field(..., example="SDE-1", description="Target role title")


class PipelineRunRequest(BaseModel):
    syllabus_id: str = Field(..., description="Uploaded syllabus identifier")
    company: str = Field(default="Amazon", description="Target company name")
    role: str = Field(default="SDE-1", description="Target role title")


# --- Response Sub-Models for PREPLINE Result ---

class TopicCoverageItem(BaseModel):
    topic_id: str
    topic_name: str
    presence: int = Field(..., ge=0, le=1, description="Presence bit C(t): 1 if present, 0 if absent")
    depth: float = Field(..., ge=1.0, le=5.0, description="Normalized depth scale D(t) [1.0 - 5.0]")
    depth_status: str = Field(..., example="measured", description="'measured' or 'fallback'")
    depth_signal_count: int = Field(default=0, ge=0)
    coverage: float = Field(..., ge=0.0, le=1.0, description="Normalized coverage Coverage(t) [0.0 - 1.0]")


class TopicImportanceItem(BaseModel):
    topic_id: str
    importance: float = Field(..., ge=0.0, le=1.0, description="Report-level importance I(t)")
    matched_report_count: int = Field(default=0)


class PriorityGapItem(BaseModel):
    rank: int
    topic_id: str
    topic_name: str
    importance: float
    coverage: float
    priority_gap: float = Field(..., description="PriorityGap(t) = I(t) * (1 - Coverage(t))")


# --- Main API Response Schemas ---

class UploadSyllabusResponse(BaseModel):
    syllabus_id: str
    filename: str
    units_count: int
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    taxonomy_version: str = "v1.0"
    message: str = "Syllabus successfully uploaded and parsed."


class ReportCountValidationResponse(BaseModel):
    company: str
    role: str
    report_count: int
    min_reports_required: int = 15
    eligible: bool
    status: str = Field(..., example="ELIGIBLE", description="'ELIGIBLE', 'INSUFFICIENT_DATA', or 'UNSUPPORTED_ROLE'")
    message: str


class PreplineResultResponse(BaseModel):
    """
    Standard PREPLINE result structure per Phase 14 blueprint.
    """
    company: str = "Amazon"
    role: str = "SDE-1"
    report_count: int
    density_gate_passed: bool
    S_comp: Optional[float] = Field(None, ge=0.0, le=100.0, description="Overall Composite Score (0 - 100)")
    topic_coverage: List[TopicCoverageItem] = []
    interview_importance: List[TopicImportanceItem] = []
    priority_gaps: List[PriorityGapItem] = []
    taxonomy_version: str = "v1.0"
    scoring_config_version: str = "v1.0"
    depth_confidence_status: str = Field(..., example="measured", description="'measured', 'fallback', or 'mixed'")
    status: str = Field(default="SUCCESS", description="'SUCCESS', 'INSUFFICIENT_DATA', or 'ERROR'")
    message: Optional[str] = None

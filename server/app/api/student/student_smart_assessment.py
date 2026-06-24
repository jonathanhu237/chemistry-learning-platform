from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from server.app.auth import AuthUser, require_roles
from server.app.domains.assessments.reports import create_smart_assessment_report
from server.app.domains.assessments.smart_assessment import (
    dismiss_student_smart_baseline_prompt,
    get_student_assessment_status,
    start_student_point_assessment,
    start_student_smart_assessment,
    submit_student_smart_assessment,
)
from server.app.student_smart_assessment_schemas import (
    StudentAssessmentStatusResponse,
    StudentPointAssessmentStartRequest,
    StudentSmartAssessmentResponse,
    StudentSmartAssessmentSubmitRequest,
    StudentSmartAssessmentSubmitResponse,
)


router = APIRouter(prefix="/api/student", tags=["student-smart-assessment"])
StudentUser = Annotated[AuthUser, Depends(require_roles("student"))]


@router.get("/assessment/status", response_model=StudentAssessmentStatusResponse)
async def assessment_status(user: StudentUser) -> StudentAssessmentStatusResponse:
    return get_student_assessment_status(user)


@router.post("/assessment/baseline-prompt-dismiss", response_model=StudentAssessmentStatusResponse)
async def dismiss_baseline_prompt(user: StudentUser) -> StudentAssessmentStatusResponse:
    return dismiss_student_smart_baseline_prompt(user)


@router.post("/smart-assessment/start", response_model=StudentSmartAssessmentResponse)
async def start_smart_assessment(user: StudentUser) -> StudentSmartAssessmentResponse:
    return start_student_smart_assessment(user)


@router.post("/point-assessment/start", response_model=StudentSmartAssessmentResponse)
async def start_point_assessment(
    payload: StudentPointAssessmentStartRequest,
    user: StudentUser,
) -> StudentSmartAssessmentResponse:
    return start_student_point_assessment(user, payload)


@router.post("/smart-assessment/submit", response_model=StudentSmartAssessmentSubmitResponse)
async def submit_smart_assessment(
    payload: StudentSmartAssessmentSubmitRequest,
    user: StudentUser,
) -> StudentSmartAssessmentSubmitResponse:
    response = submit_student_smart_assessment(user, payload)
    response.assessment_report = await create_smart_assessment_report(user, response.report)
    return response

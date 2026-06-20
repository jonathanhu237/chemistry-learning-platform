from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from server.app.auth import AuthUser, require_roles
from server.app.domains.assessments.smart_assessment import (
    start_student_smart_assessment,
    submit_student_smart_assessment,
)
from server.app.student_smart_assessment_schemas import (
    StudentSmartAssessmentResponse,
    StudentSmartAssessmentSubmitRequest,
    StudentSmartAssessmentSubmitResponse,
)


router = APIRouter(prefix="/api/student", tags=["student-smart-assessment"])
StudentUser = Annotated[AuthUser, Depends(require_roles("student"))]


@router.post("/smart-assessment/start", response_model=StudentSmartAssessmentResponse)
async def start_smart_assessment(user: StudentUser) -> StudentSmartAssessmentResponse:
    return start_student_smart_assessment(user)


@router.post("/smart-assessment/submit", response_model=StudentSmartAssessmentSubmitResponse)
async def submit_smart_assessment(
    payload: StudentSmartAssessmentSubmitRequest,
    user: StudentUser,
) -> StudentSmartAssessmentSubmitResponse:
    return submit_student_smart_assessment(user, payload)

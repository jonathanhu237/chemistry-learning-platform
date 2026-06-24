from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from server.app.auth import AuthUser, require_roles
from server.app.domains.assessments.reports import create_pretest_report
from server.app.domains.assessments.pretest import start_student_pretest, submit_student_pretest_stage
from server.app.student_pretest_schemas import StudentPretestResponse, StudentPretestSubmitRequest


router = APIRouter(prefix="/api/student", tags=["student-pretest"])
StudentUser = Annotated[AuthUser, Depends(require_roles("student"))]


@router.post("/pretest/start", response_model=StudentPretestResponse)
async def start_pretest(user: StudentUser) -> StudentPretestResponse:
    return start_student_pretest(user)


@router.post("/pretest/submit", response_model=StudentPretestResponse)
async def submit_pretest_stage(payload: StudentPretestSubmitRequest, user: StudentUser) -> StudentPretestResponse:
    response = submit_student_pretest_stage(user, payload)
    if response.status == "completed" and response.session_id:
        response.report = await create_pretest_report(user, response.session_id)
    return response

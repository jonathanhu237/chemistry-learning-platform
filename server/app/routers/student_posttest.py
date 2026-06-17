from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from server.app.auth import AuthUser, require_roles
from server.app.services.student_posttest_service import start_student_posttest, submit_student_posttest
from server.app.student_posttest_schemas import (
    StudentPosttestResponse,
    StudentPosttestSubmitRequest,
    StudentPosttestSubmitResponse,
)


router = APIRouter(prefix="/api/student", tags=["student-posttest"])
StudentUser = Annotated[AuthUser, Depends(require_roles("student"))]


@router.post("/posttest/start", response_model=StudentPosttestResponse)
async def start_posttest(user: StudentUser) -> StudentPosttestResponse:
    return start_student_posttest(user)


@router.post("/posttest/submit", response_model=StudentPosttestSubmitResponse)
async def submit_posttest(payload: StudentPosttestSubmitRequest, user: StudentUser) -> StudentPosttestSubmitResponse:
    return submit_student_posttest(user, payload)

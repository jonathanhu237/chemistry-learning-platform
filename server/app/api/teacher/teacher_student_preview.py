from __future__ import annotations

from fastapi import APIRouter, Depends

from server.app.auth import AuthUser, require_teacher_user
from server.app.domains.preview.student_device_preview import (
    TeacherStudentPreviewSessionResponse,
    create_teacher_preview_session,
)


router = APIRouter(prefix="/api/teacher", tags=["teacher-student-preview"])


@router.post("/student-preview/session", response_model=TeacherStudentPreviewSessionResponse)
async def teacher_create_student_preview_session(
    user: AuthUser = Depends(require_teacher_user),
) -> TeacherStudentPreviewSessionResponse:
    return create_teacher_preview_session(user)

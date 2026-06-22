from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from server.app.api.web_admin.auth import require_web_admin_token
from server.app.domains.preview.student_device_preview import (
    PreviewInfrastructureResponse,
    disable_preview_student,
    ensure_teacher_preview_student_by_teacher_id,
    list_preview_infrastructure,
    reset_preview_student,
    restore_preview_student,
)


router = APIRouter(prefix="/api/web-admin", tags=["web-admin-student-preview"])


@router.get("/student-preview/classes", response_model=list[PreviewInfrastructureResponse])
async def web_admin_list_student_preview_classes(
    _auth: None = Depends(require_web_admin_token),
) -> list[PreviewInfrastructureResponse]:
    return list_preview_infrastructure()


@router.post("/student-preview/classes/{teacher_user_id}/reset", response_model=PreviewInfrastructureResponse)
async def web_admin_reset_student_preview(
    teacher_user_id: str = Path(min_length=1),
    _auth: None = Depends(require_web_admin_token),
) -> PreviewInfrastructureResponse:
    return reset_preview_student(teacher_user_id)


@router.post("/student-preview/classes/{teacher_user_id}/ensure", response_model=PreviewInfrastructureResponse)
async def web_admin_ensure_student_preview(
    teacher_user_id: str = Path(min_length=1),
    _auth: None = Depends(require_web_admin_token),
) -> PreviewInfrastructureResponse:
    return ensure_teacher_preview_student_by_teacher_id(teacher_user_id)


@router.post("/student-preview/classes/{teacher_user_id}/disable", response_model=PreviewInfrastructureResponse)
async def web_admin_disable_student_preview(
    teacher_user_id: str = Path(min_length=1),
    _auth: None = Depends(require_web_admin_token),
) -> PreviewInfrastructureResponse:
    return disable_preview_student(teacher_user_id)


@router.post("/student-preview/classes/{teacher_user_id}/restore", response_model=PreviewInfrastructureResponse)
async def web_admin_restore_student_preview(
    teacher_user_id: str = Path(min_length=1),
    _auth: None = Depends(require_web_admin_token),
) -> PreviewInfrastructureResponse:
    return restore_preview_student(teacher_user_id)

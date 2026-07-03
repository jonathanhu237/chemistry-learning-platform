from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path, Response

from server.app.auth import AuthUser, require_teacher_user
from server.app.domains.analytics.read_models import (
    export_class_report_csv,
    get_class_dashboard,
    get_class_weak_points,
    get_student_report,
)


router = APIRouter(prefix="/api/teacher", tags=["experiment-teacher"])


@router.get("/analytics/classes/{class_id}/dashboard")
async def teacher_class_dashboard(
    class_id: str = Path(min_length=1),
    experiment_id: str | None = None,
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    return get_class_dashboard(class_id=class_id, experiment_id=experiment_id, user=user)


@router.get("/analytics/classes/{class_id}/students/{student_id}")
async def teacher_student_report(
    class_id: str = Path(min_length=1),
    student_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    return get_student_report(class_id=class_id, student_id=student_id, user=user)


@router.get("/analytics/classes/{class_id}/weak-points")
async def teacher_class_weak_points(
    class_id: str = Path(min_length=1),
    experiment_id: str | None = None,
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    return get_class_weak_points(class_id=class_id, experiment_id=experiment_id, user=user)


@router.get("/analytics/classes/{class_id}/export")
async def teacher_export_class_report(
    class_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> Response:
    csv_payload = export_class_report_csv(class_id=class_id, user=user)
    return Response(
        content=csv_payload.content,
        media_type=csv_payload.media_type,
        headers={"Content-Disposition": f'attachment; filename="{csv_payload.filename}"'},
    )

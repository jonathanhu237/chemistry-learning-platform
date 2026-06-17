from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import FileResponse

from server.app.auth import AuthUser, require_roles
from server.app.schemas import FeedbackListResponse, FeedbackSummaryResponse, FeedbackUpdateRequest
from server.app.services.feedback_service import (
    feedback_summary,
    get_feedback_attachment,
    get_feedback,
    list_feedback,
    update_feedback,
)


router = APIRouter(prefix="/api/admin", tags=["admin-feedback"])


@router.get("/feedback/summary", response_model=FeedbackSummaryResponse)
async def admin_feedback_summary(
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> FeedbackSummaryResponse:
    return feedback_summary(user)


@router.get("/feedback", response_model=FeedbackListResponse)
async def admin_list_feedback(
    status_filter: str | None = Query(default=None, alias="status"),
    feedback_type: str | None = None,
    class_id: str | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> FeedbackListResponse:
    return list_feedback(
        user,
        status_filter=status_filter,
        feedback_type=feedback_type,
        class_id=class_id,
        search=search,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.get("/feedback/{feedback_id}")
async def admin_get_feedback(
    feedback_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return get_feedback(feedback_id, user)


@router.get("/feedback/{feedback_id}/attachments/{attachment_id}", include_in_schema=False)
async def admin_get_feedback_attachment(
    feedback_id: str = Path(min_length=1),
    attachment_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> FileResponse:
    attachment = get_feedback_attachment(feedback_id, attachment_id, user)
    return FileResponse(
        attachment["absolute_path"],
        media_type=attachment["mime_type"],
        filename=attachment.get("original_file_name") or f"{attachment_id}.jpg",
    )


@router.patch("/feedback/{feedback_id}")
async def admin_update_feedback(
    payload: FeedbackUpdateRequest,
    feedback_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return update_feedback(payload, feedback_id, user)

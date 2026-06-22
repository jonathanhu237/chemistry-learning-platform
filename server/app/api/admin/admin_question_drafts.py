from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path

from server.app.auth import AuthUser, require_teacher_console_user
from server.app.experiment_admin_schemas import DraftUpdateRequest
from server.app.domains.questions.drafts import (
    list_question_drafts,
    publish_question_draft,
    reject_question_draft,
    update_question_draft,
)


router = APIRouter(prefix="/api/admin", tags=["experiment-admin"])


@router.get("/question-banks/drafts")
async def admin_list_question_drafts(
    generation_id: str | None = None,
    experiment_id: str | None = None,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return list_question_drafts(generation_id=generation_id, experiment_id=experiment_id)


@router.patch("/question-banks/drafts/{draft_id}")
async def admin_update_question_draft(
    payload: DraftUpdateRequest,
    draft_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return update_question_draft(payload=payload, draft_id=draft_id)


@router.post("/question-banks/drafts/{draft_id}/publish")
async def admin_publish_question_draft(
    draft_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return publish_question_draft(draft_id=draft_id, user=user)


@router.post("/question-banks/drafts/{draft_id}/reject")
async def admin_reject_question_draft(
    draft_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return reject_question_draft(draft_id=draft_id)

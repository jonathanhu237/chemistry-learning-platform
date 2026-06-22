from __future__ import annotations

from pathlib import Path as FilePath
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field

from server.app.auth import AuthUser, require_teacher_console_user
from server.app.curriculum import (
    archive_curriculum_version,
    create_curriculum_draft,
    get_curriculum_version,
    list_curriculum_versions,
    load_curriculum_artifact,
    publish_curriculum_version,
)
from server.app.review import apply_review_action, get_review_item, list_review_items


router = APIRouter(prefix="/api/admin", tags=["admin-curriculum-review"])


class CurriculumCreateRequest(BaseModel):
    artifact_path: str = Field(default="data/processed/reviewed_curriculum.json", min_length=1)


class ReviewActionRequest(BaseModel):
    action: str = Field(pattern="^(approve|reject|request_changes|publish|unpublish|archive)$")
    note: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


@router.get("/curriculum/versions")
async def admin_list_curriculum_versions(
    user: AuthUser = Depends(require_teacher_console_user),
) -> list[dict[str, Any]]:
    return list_curriculum_versions()


@router.post("/curriculum/versions")
async def admin_create_curriculum_version(
    payload: CurriculumCreateRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    curriculum = load_curriculum_artifact(FilePath(payload.artifact_path))
    return create_curriculum_draft(curriculum, actor_user_id=user.id)


@router.get("/curriculum/versions/{version_id}")
async def admin_get_curriculum_version(
    version_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    version = get_curriculum_version(version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum version not found")
    return version


@router.post("/curriculum/versions/{version_id}/publish")
async def admin_publish_curriculum_version(
    version_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return publish_curriculum_version(version_id, actor_user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/curriculum/versions/{version_id}/archive")
async def admin_archive_curriculum_version(
    version_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return archive_curriculum_version(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/review/items")
async def admin_list_review_items(
    item_type: str | None = None,
    status_filter: str | None = None,
    chapter_id: str | None = None,
    search: str | None = None,
    limit: int = 300,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return list_review_items(
        item_type=item_type,
        status=status_filter,
        chapter_id=chapter_id,
        search=search,
        limit=limit,
    )


@router.get("/review/items/{item_id}")
async def admin_get_review_item(
    item_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    item = get_review_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review item not found")
    return item


@router.post("/review/items/{item_id}/actions")
async def admin_apply_review_action(
    payload: ReviewActionRequest,
    item_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return apply_review_action(
            item_id=item_id,
            action=payload.action,
            actor_user_id=user.id,
            note=payload.note,
            payload=payload.payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

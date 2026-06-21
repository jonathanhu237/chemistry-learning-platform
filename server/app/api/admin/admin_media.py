from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

from server.app.auth import AuthUser, get_user_from_access_token, is_teacher_console_role, require_teacher_console_user
from server.app.infrastructure.settings import get_settings
from server.app.infrastructure.database import db_session
from server.app.domains.media.assets import (
    complete_resumable_upload,
    create_media_asset,
    decide_duplicate_candidate,
    list_media_assets,
    precheck_exact_duplicate,
)
from server.app.domains.media.bindings import (
    create_media_binding,
    delete_media_binding,
    publish_media_binding,
    unpublish_media_binding,
)
from server.app.domains.media.processing_queue import (
    active_media_processing_status,
    retry_media_processing,
)


router = APIRouter(prefix="/api/admin", tags=["admin-media"])


class MediaBindingRequest(BaseModel):
    media_asset_id: str = Field(min_length=1)
    target_type: str = Field(pattern="^(chapter|knowledge_unit|knowledge_point|experiment|learning_card)$")
    target_id: str = Field(min_length=1)
    title: str | None = None
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    metadata: dict[str, Any] = Field(default_factory=dict)


class MediaDuplicatePrecheckRequest(BaseModel):
    checksum_sha256: str = Field(min_length=64, max_length=128)
    file_size_bytes: int = Field(gt=0)


class MediaUploadCompleteRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    upload_id: str = Field(min_length=1, max_length=200)
    filename: str = Field(min_length=1, max_length=260)
    content_type: str | None = None
    checksum_sha256: str | None = Field(default=None, min_length=64, max_length=128)


class MediaDuplicateDecisionRequest(BaseModel):
    status: str = Field(pattern="^(kept|reused|ignored)$")


def _media_asset_file_response(asset_id: str) -> FileResponse:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT id,
                           COALESCE(playback_relative_path, relative_path) AS relative_path,
                           COALESCE(playback_mime_type, mime_type) AS mime_type,
                           original_file_name,
                           upload_status
                    FROM media_assets
                    WHERE id = CAST(:asset_id AS uuid)
                    """
                ),
                {"asset_id": asset_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    if row["upload_status"] != "ready":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Media asset is not ready for preview")
    root = get_settings().media_root.resolve()
    file_path = (root / row["relative_path"]).resolve()
    if root != file_path and root not in file_path.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found")
    return FileResponse(
        file_path,
        media_type=row.get("mime_type") or "application/octet-stream",
        filename=row.get("original_file_name") or file_path.name,
    )


@router.get("/media/assets")
async def admin_list_media_assets(
    upload_status: str | None = None,
    limit: int = 200,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return list_media_assets(upload_status=upload_status, limit=limit)


@router.post("/media/assets/precheck")
async def admin_precheck_media_asset(
    payload: MediaDuplicatePrecheckRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return precheck_exact_duplicate(
        checksum_sha256_value=payload.checksum_sha256,
        file_size_bytes=payload.file_size_bytes,
    )


@router.get("/media/assets/processing")
async def admin_media_processing_status(
    limit: int = Query(default=200, ge=1, le=1000),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return active_media_processing_status(limit=limit)


@router.post("/media/assets/complete-upload")
async def admin_complete_resumable_media_upload(
    payload: MediaUploadCompleteRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return complete_resumable_upload(
            title=payload.title,
            upload_id=payload.upload_id,
            filename=payload.filename,
            content_type=payload.content_type,
            uploaded_by=user.id,
            checksum_sha256_value=payload.checksum_sha256,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/media/assets/{asset_id}/file", include_in_schema=False)
async def admin_get_media_asset_file(
    asset_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> FileResponse:
    return _media_asset_file_response(asset_id)


@router.get("/media/assets/{asset_id}/stream", include_in_schema=False)
async def admin_stream_media_asset_file(
    asset_id: str = Path(min_length=1),
    access_token: str = Query(min_length=1),
) -> FileResponse:
    user = get_user_from_access_token(access_token)
    if not is_teacher_console_role(user.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return _media_asset_file_response(asset_id)


def _media_asset_thumbnail_response(asset_id: str) -> FileResponse:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT thumbnail_relative_path, original_file_name
                    FROM media_assets
                    WHERE id = CAST(:asset_id AS uuid)
                    """
                ),
                {"asset_id": asset_id},
            )
            .mappings()
            .first()
        )
    if not row or not row.get("thumbnail_relative_path"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media thumbnail not found")
    root = get_settings().media_root.resolve()
    file_path = (root / row["thumbnail_relative_path"]).resolve()
    if root != file_path and root not in file_path.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media thumbnail not found")
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media thumbnail not found")
    return FileResponse(file_path, media_type="image/jpeg", filename=f"{asset_id}.jpg")


@router.get("/media/assets/{asset_id}/thumbnail", include_in_schema=False)
async def admin_get_media_asset_thumbnail(
    asset_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> FileResponse:
    return _media_asset_thumbnail_response(asset_id)


@router.get("/media/assets/{asset_id}/thumbnail-stream", include_in_schema=False)
async def admin_stream_media_asset_thumbnail(
    asset_id: str = Path(min_length=1),
    access_token: str = Query(min_length=1),
) -> FileResponse:
    user = get_user_from_access_token(access_token)
    if not is_teacher_console_role(user.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return _media_asset_thumbnail_response(asset_id)


@router.post("/media/assets/{asset_id}/retry-processing")
async def admin_retry_media_asset_processing(
    asset_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return retry_media_processing(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/media/duplicate-candidates/{candidate_id}")
async def admin_decide_media_duplicate_candidate(
    payload: MediaDuplicateDecisionRequest,
    candidate_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return decide_duplicate_candidate(candidate_id, decision=payload.status, actor_user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/media/assets")
async def admin_upload_media_asset(
    title: str = Form(...),
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    content = await file.read()
    return create_media_asset(
        title=title,
        filename=file.filename or "upload.mp4",
        content=content,
        content_type=file.content_type,
        uploaded_by=user.id,
    )


@router.post("/media/assets/{asset_id}/replace")
async def admin_replace_media_asset(
    asset_id: str = Path(min_length=1),
    title: str = Form(...),
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    content = await file.read()
    return create_media_asset(
        title=title,
        filename=file.filename or "upload.mp4",
        content=content,
        content_type=file.content_type,
        uploaded_by=user.id,
        replace_asset_id=asset_id,
    )


@router.post("/media/bindings")
async def admin_create_media_binding(
    payload: MediaBindingRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return create_media_binding(
        media_asset_id=payload.media_asset_id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        title=payload.title,
        status=payload.status,
        metadata=payload.metadata,
    )


@router.post("/media/bindings/{binding_id}/publish")
async def admin_publish_media_binding(
    binding_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return publish_media_binding(binding_id, actor_user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/media/bindings/{binding_id}/unpublish")
async def admin_unpublish_media_binding(
    binding_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return unpublish_media_binding(binding_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/media/bindings/{binding_id}")
async def admin_delete_media_binding(
    binding_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return delete_media_binding(binding_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

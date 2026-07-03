from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

from server.app.auth import AuthUser, get_user_from_access_token, is_teacher_role, require_teacher_user
from server.app.infrastructure.settings import get_settings
from server.app.infrastructure.database import db_session
from server.app.domains.media.assets import (
    MediaUploadPolicyError,
    complete_resumable_upload,
    create_media_asset,
    decide_duplicate_candidate,
    list_media_assets,
    precheck_exact_duplicate,
)
from server.app.domains.media.files import media_upload_policy
from server.app.domains.media.subtitles import (
    SubtitleValidationError,
    create_subtitle_track,
    delete_subtitle_track,
    list_subtitle_tracks,
    retry_subtitle_track_normalization,
    subtitle_track_file,
    update_subtitle_track,
)
from server.app.domains.media.lifecycle import (
    archive_media_asset,
    delete_media_asset,
    media_asset_archive_plan,
    media_asset_delete_plan,
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


router = APIRouter(prefix="/api/teacher", tags=["teacher-media"])


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


class MediaAssetArchiveRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class MediaAssetDeleteRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class MediaSubtitleTrackUpdateRequest(BaseModel):
    language_code: str | None = Field(default=None, min_length=2, max_length=35)
    label: str | None = Field(default=None, min_length=1, max_length=80)
    kind: str | None = Field(default=None, pattern="^(subtitles|captions)$")
    is_default: bool | None = None


class MediaUploadPolicyResponse(BaseModel):
    max_media_upload_mb: int
    max_media_upload_bytes: int
    allowed_extensions: list[str]


def _media_upload_policy_error(exc: MediaUploadPolicyError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=exc.detail())



def _subtitle_error(exc: SubtitleValidationError) -> HTTPException:
    code = status.HTTP_404_NOT_FOUND if exc.reason in {"media_asset_not_found", "subtitle_track_not_found", "subtitle_file_not_found"} else status.HTTP_400_BAD_REQUEST
    if exc.reason == "subtitle_file_too_large":
        code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    return HTTPException(status_code=code, detail=exc.detail)

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
                           upload_status,
                           COALESCE(lifecycle_status, 'active') AS lifecycle_status
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
    if row.get("lifecycle_status") != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset is archived")
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
async def teacher_list_media_assets(
    upload_status: str | None = None,
    limit: int = 200,
    include_archived: bool = False,
    lifecycle_status: str | None = Query(default=None, pattern="^(active|archived|tombstoned)$"),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    return list_media_assets(
        upload_status=upload_status,
        limit=limit,
        include_archived=include_archived,
        lifecycle_status=lifecycle_status,
    )


@router.get("/media/upload-policy", response_model=MediaUploadPolicyResponse)
async def teacher_media_upload_policy(
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    return media_upload_policy()


@router.post("/media/assets/precheck")
async def teacher_precheck_media_asset(
    payload: MediaDuplicatePrecheckRequest,
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    return precheck_exact_duplicate(
        checksum_sha256_value=payload.checksum_sha256,
        file_size_bytes=payload.file_size_bytes,
    )


@router.get("/media/assets/processing")
async def teacher_media_processing_status(
    limit: int = Query(default=200, ge=1, le=1000),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    return active_media_processing_status(limit=limit)


@router.post("/media/assets/complete-upload")
async def teacher_complete_resumable_media_upload(
    payload: MediaUploadCompleteRequest,
    user: AuthUser = Depends(require_teacher_user),
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
    except MediaUploadPolicyError as exc:
        raise _media_upload_policy_error(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/media/assets/{asset_id}/file", include_in_schema=False)
async def teacher_get_media_asset_file(
    asset_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> FileResponse:
    return _media_asset_file_response(asset_id)


@router.get("/media/assets/{asset_id}/stream", include_in_schema=False)
async def teacher_stream_media_asset_file(
    asset_id: str = Path(min_length=1),
    access_token: str = Query(min_length=1),
) -> FileResponse:
    user = get_user_from_access_token(access_token)
    if not is_teacher_role(user.role):
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
                      AND COALESCE(lifecycle_status, 'active') = 'active'
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
async def teacher_get_media_asset_thumbnail(
    asset_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> FileResponse:
    return _media_asset_thumbnail_response(asset_id)


@router.get("/media/assets/{asset_id}/thumbnail-stream", include_in_schema=False)
async def teacher_stream_media_asset_thumbnail(
    asset_id: str = Path(min_length=1),
    access_token: str = Query(min_length=1),
) -> FileResponse:
    user = get_user_from_access_token(access_token)
    if not is_teacher_role(user.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return _media_asset_thumbnail_response(asset_id)



@router.get("/media/assets/{asset_id}/subtitle-tracks")
async def teacher_list_media_subtitle_tracks(
    asset_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    return {"items": list_subtitle_tracks(asset_id)}


@router.post("/media/assets/{asset_id}/subtitle-tracks")
async def teacher_create_media_subtitle_track(
    asset_id: str = Path(min_length=1),
    file: UploadFile = File(...),
    language_code: str = Form("und"),
    label: str | None = Form(default=None),
    kind: str = Form("subtitles"),
    is_default: bool = Form(False),
    client_link_id: str | None = Form(default=None),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    content = await file.read()
    try:
        return create_subtitle_track(
            asset_id=asset_id,
            filename=file.filename or "subtitle.vtt",
            content=content,
            content_type=file.content_type,
            language_code=language_code,
            label=label,
            kind=kind,
            is_default=is_default,
            uploaded_by=user.id,
            metadata={"client_link_id": client_link_id} if client_link_id else {},
        )
    except SubtitleValidationError as exc:
        raise _subtitle_error(exc) from exc


@router.patch("/media/assets/{asset_id}/subtitle-tracks/{track_id}")
async def teacher_update_media_subtitle_track(
    payload: MediaSubtitleTrackUpdateRequest,
    asset_id: str = Path(min_length=1),
    track_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    try:
        return update_subtitle_track(
            asset_id=asset_id,
            track_id=track_id,
            language_code=payload.language_code,
            label=payload.label,
            kind=payload.kind,
            is_default=payload.is_default,
        )
    except SubtitleValidationError as exc:
        raise _subtitle_error(exc) from exc


@router.delete("/media/assets/{asset_id}/subtitle-tracks/{track_id}")
async def teacher_delete_media_subtitle_track(
    asset_id: str = Path(min_length=1),
    track_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    try:
        return delete_subtitle_track(asset_id=asset_id, track_id=track_id)
    except SubtitleValidationError as exc:
        raise _subtitle_error(exc) from exc


@router.post("/media/assets/{asset_id}/subtitle-tracks/{track_id}/retry")
async def teacher_retry_media_subtitle_track(
    asset_id: str = Path(min_length=1),
    track_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    try:
        return retry_subtitle_track_normalization(asset_id=asset_id, track_id=track_id)
    except SubtitleValidationError as exc:
        raise _subtitle_error(exc) from exc


@router.get("/media/assets/{asset_id}/subtitle-tracks/{track_id}/stream", include_in_schema=False)
async def teacher_stream_media_subtitle_track(
    asset_id: str = Path(min_length=1),
    track_id: str = Path(min_length=1),
    access_token: str = Query(min_length=1),
) -> FileResponse:
    user = get_user_from_access_token(access_token)
    if not is_teacher_role(user.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    try:
        path, media_type, filename = subtitle_track_file(asset_id, track_id)
    except SubtitleValidationError as exc:
        raise _subtitle_error(exc) from exc
    return FileResponse(path, media_type=media_type, filename=filename)

@router.post("/media/assets/{asset_id}/retry-processing")
async def teacher_retry_media_asset_processing(
    asset_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    try:
        return retry_media_processing(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/media/assets/{asset_id}/archive-plan")
async def teacher_media_asset_archive_plan(
    asset_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    try:
        return media_asset_archive_plan(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/media/assets/{asset_id}/archive")
async def teacher_archive_media_asset(
    payload: MediaAssetArchiveRequest,
    asset_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    try:
        return archive_media_asset(asset_id=asset_id, actor_user_id=user.id, reason=payload.reason)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/media/assets/{asset_id}/delete-plan")
async def teacher_media_asset_delete_plan(
    asset_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    try:
        return media_asset_delete_plan(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/media/assets/{asset_id}/delete")
async def teacher_delete_media_asset(
    payload: MediaAssetDeleteRequest,
    asset_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    try:
        return delete_media_asset(asset_id=asset_id, actor_user_id=user.id, reason=payload.reason)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/media/duplicate-candidates/{candidate_id}")
async def teacher_decide_media_duplicate_candidate(
    payload: MediaDuplicateDecisionRequest,
    candidate_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    try:
        return decide_duplicate_candidate(candidate_id, decision=payload.status, actor_user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/media/assets")
async def teacher_upload_media_asset(
    title: str = Form(...),
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    content = await file.read()
    try:
        return create_media_asset(
            title=title,
            filename=file.filename or "upload.mp4",
            content=content,
            content_type=file.content_type,
            uploaded_by=user.id,
        )
    except MediaUploadPolicyError as exc:
        raise _media_upload_policy_error(exc) from exc


@router.post("/media/assets/{asset_id}/replace")
async def teacher_replace_media_asset(
    asset_id: str = Path(min_length=1),
    title: str = Form(...),
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    content = await file.read()
    try:
        return create_media_asset(
            title=title,
            filename=file.filename or "upload.mp4",
            content=content,
            content_type=file.content_type,
            uploaded_by=user.id,
            replace_asset_id=asset_id,
        )
    except MediaUploadPolicyError as exc:
        raise _media_upload_policy_error(exc) from exc


@router.post("/media/bindings")
async def teacher_create_media_binding(
    payload: MediaBindingRequest,
    user: AuthUser = Depends(require_teacher_user),
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
async def teacher_publish_media_binding(
    binding_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    try:
        return publish_media_binding(binding_id, actor_user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/media/bindings/{binding_id}/unpublish")
async def teacher_unpublish_media_binding(
    binding_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    try:
        return unpublish_media_binding(binding_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/media/bindings/{binding_id}")
async def teacher_delete_media_binding(
    binding_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    try:
        return delete_media_binding(binding_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

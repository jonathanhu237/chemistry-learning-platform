from __future__ import annotations

import secrets
import shutil
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import text

from server.app.domains.media.files import (
    checksum_sha256_file,
    json_param,
    resolve_media_relative,
    safe_media_path,
    source_media_path,
    validate_media_file,
)
from server.app.domains.media.processing_queue import enqueue_processing_job
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings


def asset_id() -> str:
    return str(uuid.uuid4())


def row_dict(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["lifecycle_status"] = item.get("lifecycle_status") or "active"
    for key in ("renditions", "duplicate_candidates", "processing_job"):
        if item.get(key) is None:
            item[key] = [] if key != "processing_job" else None
    return item


def media_file_status(kind: str, relative_path: str) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "kind": kind,
        "kinds": [kind],
        "relative_path": relative_path,
        "exists": False,
        "file_size_bytes": None,
        "error": None,
    }
    try:
        path = resolve_media_relative(relative_path)
    except ValueError as exc:
        entry["error"] = str(exc)
        return entry
    try:
        if path.is_file():
            entry["exists"] = True
            entry["file_size_bytes"] = path.stat().st_size
    except OSError as exc:
        entry["error"] = exc.__class__.__name__
    return entry


def asset_file_entries(asset: dict[str, Any]) -> list[dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}

    def add(kind: str, relative_path: Any) -> None:
        value = str(relative_path or "").strip()
        if not value:
            return
        if value in by_path:
            by_path[value]["kinds"].append(kind)
            return
        by_path[value] = media_file_status(kind, value)

    add("relative", asset.get("relative_path"))
    add("source", asset.get("source_relative_path"))
    add("playback", asset.get("playback_relative_path"))
    add("thumbnail", asset.get("thumbnail_relative_path"))
    for rendition in asset.get("renditions") or []:
        add(f"rendition:{rendition.get('kind') or 'unknown'}", rendition.get("relative_path"))
    return list(by_path.values())


def media_asset_file_summary(asset: dict[str, Any]) -> dict[str, Any]:
    files = asset_file_entries(asset)
    existing_count = sum(1 for item in files if item["exists"])
    missing_count = sum(1 for item in files if not item["exists"])
    primary_file_available = any(
        item["exists"] and any(kind in {"playback", "source", "relative"} for kind in item["kinds"])
        for item in files
    )
    if not files:
        file_state = "untracked"
    elif existing_count == len(files):
        file_state = "available"
    elif existing_count == 0:
        file_state = "missing"
    else:
        file_state = "partial"
    if asset.get("upload_status") in {"pending", "processing"} and existing_count == 0:
        file_state = "pending"
    return {
        "file_state": file_state,
        "primary_file_available": primary_file_available,
        "existing_file_count": existing_count,
        "missing_file_count": missing_count,
        "media_files": files,
    }


def row_with_file_summary(row: Any) -> dict[str, Any]:
    item = row_dict(row)
    item.update(media_asset_file_summary(item))
    return item


def find_exact_asset(checksum: str, file_size_bytes: int) -> dict[str, Any] | None:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT id, title, original_file_name, relative_path, source_relative_path,
                           thumbnail_relative_path, playback_relative_path, playback_mime_type,
                           checksum_sha256, mime_type, file_size_bytes, duration_seconds,
                           upload_status, lifecycle_status, processing_phase, processing_progress,
                           error_reason, created_at, updated_at
                    FROM media_assets
                    WHERE checksum_sha256 = :checksum
                      AND file_size_bytes = :file_size_bytes
                      AND upload_status <> 'failed'
                      AND upload_status <> 'replaced'
                      AND COALESCE(lifecycle_status, 'active') = 'active'
                    ORDER BY created_at ASC
                    LIMIT 1
                    """
                ),
                {"checksum": checksum, "file_size_bytes": file_size_bytes},
            )
            .mappings()
            .first()
        )
    return dict(row) if row else None


def precheck_exact_duplicate(*, checksum_sha256_value: str, file_size_bytes: int) -> dict[str, Any]:
    existing = find_exact_asset(checksum_sha256_value.lower(), file_size_bytes)
    return {"exists": bool(existing), "asset": existing}


def insert_failed_asset(
    *,
    title: str,
    filename: str,
    relative_path: str,
    mime_type: str,
    file_size_bytes: int,
    error_reason: str | None,
    uploaded_by: str | None,
) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    INSERT INTO media_assets (
                      title, original_file_name, relative_path, source_relative_path,
                      mime_type, file_size_bytes, upload_status, processing_phase,
                      processing_progress, error_reason, uploaded_by, metadata
                    )
                    VALUES (
                      :title, :original_file_name, :relative_path, :relative_path,
                      :mime_type, :file_size_bytes, 'failed', 'failed', 0,
                      :error_reason, CAST(:uploaded_by AS uuid), '{}'::jsonb
                    )
                    RETURNING id, title, original_file_name, relative_path, source_relative_path,
                              mime_type, file_size_bytes, upload_status, processing_phase,
                              processing_progress, error_reason, created_at, updated_at
                    """
                ),
                {
                    "title": title,
                    "original_file_name": filename,
                    "relative_path": relative_path,
                    "mime_type": mime_type,
                    "file_size_bytes": file_size_bytes,
                    "error_reason": error_reason,
                    "uploaded_by": uploaded_by,
                },
            )
            .mappings()
            .one()
        )
    return dict(row)


def create_media_asset_record_from_file(
    *,
    title: str,
    filename: str,
    source_path: Path,
    content_type: str | None,
    uploaded_by: str | None,
    replace_asset_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    file_size = source_path.stat().st_size if source_path.exists() else 0
    validation = validate_media_file(filename, b"x" * min(file_size, 1), content_type)
    if not validation.ok and validation.error != "file_too_large":
        return insert_failed_asset(
            title=title,
            filename=filename,
            relative_path=f"failed/{secrets.token_hex(16)}{Path(filename).suffix.lower()}",
            mime_type=validation.mime_type,
            file_size_bytes=file_size,
            error_reason=validation.error,
            uploaded_by=uploaded_by,
        )
    max_bytes = get_settings().max_media_upload_mb * 1024 * 1024
    if file_size > max_bytes:
        return insert_failed_asset(
            title=title,
            filename=filename,
            relative_path=f"failed/{secrets.token_hex(16)}{Path(filename).suffix.lower()}",
            mime_type=validation.mime_type,
            file_size_bytes=file_size,
            error_reason="file_too_large",
            uploaded_by=uploaded_by,
        )
    if file_size <= 0:
        return insert_failed_asset(
            title=title,
            filename=filename,
            relative_path=f"failed/{secrets.token_hex(16)}{Path(filename).suffix.lower()}",
            mime_type=validation.mime_type,
            file_size_bytes=file_size,
            error_reason="empty_file",
            uploaded_by=uploaded_by,
        )

    digest = checksum_sha256_file(source_path)
    existing = find_exact_asset(digest, file_size)
    if existing and not replace_asset_id:
        try:
            source_path.unlink(missing_ok=True)
        except OSError:
            pass
        existing["reused_existing"] = True
        existing["duplicate_type"] = "exact"
        return existing

    new_asset_id = asset_id()
    destination, relative_path = source_media_path(new_asset_id, filename)
    if source_path.resolve() != destination.resolve():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), destination)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    INSERT INTO media_assets (
                      id, title, original_file_name, relative_path, source_relative_path,
                      checksum_sha256, mime_type, file_size_bytes, upload_status,
                      processing_phase, processing_progress, uploaded_by, replaced_by, metadata
                    )
                    VALUES (
                      CAST(:id AS uuid), :title, :original_file_name, :relative_path, :source_relative_path,
                      :checksum_sha256, :mime_type, :file_size_bytes, 'processing',
                      'queued', 0, CAST(:uploaded_by AS uuid), CAST(:replaced_by AS uuid),
                      CAST(:metadata AS jsonb)
                    )
                    RETURNING id, title, original_file_name, relative_path, source_relative_path,
                              checksum_sha256, mime_type, file_size_bytes, upload_status,
                              processing_phase, processing_progress, error_reason,
                              created_at, updated_at
                    """
                ),
                {
                    "id": new_asset_id,
                    "title": title,
                    "original_file_name": filename,
                    "relative_path": relative_path,
                    "source_relative_path": relative_path,
                    "checksum_sha256": digest,
                    "mime_type": validation.mime_type,
                    "file_size_bytes": file_size,
                    "uploaded_by": uploaded_by,
                    "replaced_by": replace_asset_id,
                    "metadata": json_param(metadata or {}),
                },
            )
            .mappings()
            .one()
        )
        if replace_asset_id:
            session.execute(
                text(
                    """
                    UPDATE media_assets
                    SET upload_status = 'replaced',
                        replaced_by = CAST(:new_asset_id AS uuid),
                        updated_at = now()
                    WHERE id = CAST(:old_asset_id AS uuid)
                    """
                ),
                {"new_asset_id": row["id"], "old_asset_id": replace_asset_id},
            )
    enqueue_processing_job(str(row["id"]), metadata={"source": "upload"})
    return dict(row)


def create_media_asset(
    *,
    title: str,
    filename: str,
    content: bytes,
    content_type: str | None,
    uploaded_by: str | None,
    replace_asset_id: str | None = None,
) -> dict[str, Any]:
    validation = validate_media_file(filename, content, content_type)
    if not validation.ok:
        return insert_failed_asset(
            title=title,
            filename=filename,
            relative_path=f"failed/{secrets.token_hex(16)}{Path(filename).suffix.lower()}",
            mime_type=validation.mime_type,
            file_size_bytes=validation.file_size_bytes,
            error_reason=validation.error,
            uploaded_by=uploaded_by,
        )

    absolute_path, relative_path = safe_media_path(filename)
    absolute_path.write_bytes(content)
    return create_media_asset_record_from_file(
        title=title,
        filename=filename,
        source_path=absolute_path,
        content_type=content_type,
        uploaded_by=uploaded_by,
        replace_asset_id=replace_asset_id,
        metadata={"legacy_upload_path": relative_path},
    )


def complete_resumable_upload(
    *,
    title: str,
    upload_id: str,
    filename: str,
    content_type: str | None,
    uploaded_by: str | None,
    checksum_sha256_value: str | None = None,
) -> dict[str, Any]:
    if not upload_id or "/" in upload_id or "\\" in upload_id or upload_id in {".", ".."}:
        raise ValueError("Invalid upload id")
    settings = get_settings()
    upload_path = resolve_media_relative((Path(settings.tus_upload_dir) / upload_id).as_posix())
    if not upload_path.exists():
        raise FileNotFoundError("Uploaded file not found")
    if checksum_sha256_value:
        actual = checksum_sha256_file(upload_path)
        if actual.lower() != checksum_sha256_value.lower():
            raise ValueError("Uploaded file checksum does not match")
    return create_media_asset_record_from_file(
        title=title,
        filename=filename,
        source_path=upload_path,
        content_type=content_type,
        uploaded_by=uploaded_by,
        metadata={"resumable_upload_id": upload_id},
    )


def list_media_assets(
    upload_status: str | None = None,
    limit: int = 200,
    *,
    include_archived: bool = False,
    lifecycle_status: str | None = None,
) -> dict[str, Any]:
    filters = []
    params: dict[str, Any] = {"limit": limit}
    if upload_status:
        filters.append("upload_status = :upload_status")
        params["upload_status"] = upload_status
    if lifecycle_status:
        filters.append("lifecycle_status = :lifecycle_status")
        params["lifecycle_status"] = lifecycle_status
    elif not include_archived:
        filters.append("COALESCE(lifecycle_status, 'active') = 'active'")
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    f"""
                    SELECT id, title, original_file_name, relative_path, checksum_sha256,
                           source_relative_path, thumbnail_relative_path, playback_relative_path,
                           playback_mime_type, mime_type, file_size_bytes, duration_seconds,
                           width, height, fps, bitrate, video_codec, audio_codec,
                           upload_status, lifecycle_status, archived_at, archived_by,
                           archive_reason, archive_metadata,
                           processing_phase, processing_progress,
                           error_reason, created_at, updated_at,
                           (
                             SELECT
                               (
                                 SELECT COUNT(*)
                                 FROM media_bindings mb
                                 WHERE mb.media_asset_id = media_assets.id
                                   AND mb.status <> 'archived'
                               )
                               +
                               (
                                 SELECT COUNT(*)
                                 FROM experiment_catalog_point_media_bindings cmb
                                 WHERE cmb.media_asset_id = media_assets.id
                                   AND cmb.binding_status <> 'archived'
                               )
                           ) AS association_count
                           ,
                           (
                             SELECT COUNT(*)
                             FROM media_bindings mb
                             WHERE mb.media_asset_id = media_assets.id
                               AND mb.status <> 'archived'
                           ) AS legacy_association_count
                           ,
                           (
                             SELECT COUNT(*)
                             FROM experiment_catalog_point_media_bindings cmb
                             WHERE cmb.media_asset_id = media_assets.id
                               AND cmb.binding_status <> 'archived'
                           ) AS catalog_binding_count
                           ,
                           (
                             SELECT jsonb_build_object(
                               'id', mpj.id,
                               'status', mpj.status,
                               'phase', mpj.phase,
                               'progress', mpj.progress,
                               'attempts', mpj.attempts,
                               'error_reason', mpj.error_reason,
                               'updated_at', mpj.updated_at
                             )
                             FROM media_processing_jobs mpj
                             WHERE mpj.media_asset_id = media_assets.id
                             ORDER BY mpj.created_at DESC
                             LIMIT 1
                           ) AS processing_job,
                           COALESCE((
                             SELECT jsonb_agg(jsonb_build_object(
                               'id', mr.id,
                               'kind', mr.kind,
                               'relative_path', mr.relative_path,
                               'mime_type', mr.mime_type,
                               'file_size_bytes', mr.file_size_bytes,
                               'duration_seconds', mr.duration_seconds,
                               'width', mr.width,
                               'height', mr.height,
                               'status', mr.status,
                               'video_codec', mr.video_codec,
                               'audio_codec', mr.audio_codec
                             ) ORDER BY mr.kind)
                             FROM media_renditions mr
                             WHERE mr.media_asset_id = media_assets.id
                           ), '[]'::jsonb) AS renditions,
                           COALESCE((
                             SELECT jsonb_agg(jsonb_build_object(
                               'id', mdc.id,
                               'duplicate_type', mdc.duplicate_type,
                               'score', mdc.score,
                               'algorithm', mdc.algorithm,
                               'status', mdc.status,
                               'candidate_asset_id', mdc.candidate_asset_id,
                               'candidate_title', candidate.title,
                               'candidate_thumbnail_relative_path', candidate.thumbnail_relative_path
                             ) ORDER BY mdc.created_at DESC)
                              FROM media_duplicate_candidates mdc
                              LEFT JOIN media_assets candidate ON candidate.id = mdc.candidate_asset_id
                              WHERE mdc.media_asset_id = media_assets.id
                                AND (
                                  mdc.candidate_asset_id IS NULL
                                  OR COALESCE(candidate.lifecycle_status, 'active') = 'active'
                                )
                            ), '[]'::jsonb) AS duplicate_candidates
                    FROM media_assets
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """
                ),
                params,
            )
            .mappings()
            .all()
        ]
    return {"items": [row_with_file_summary(row) for row in rows], "total": len(rows)}


def decide_duplicate_candidate(candidate_id: str, *, decision: str, actor_user_id: str | None) -> dict[str, Any]:
    if decision not in {"kept", "reused", "ignored"}:
        raise ValueError("Invalid duplicate candidate decision")
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE media_duplicate_candidates
                    SET status = :decision,
                        decided_by = CAST(:actor_user_id AS uuid),
                        decided_at = now(),
                        updated_at = now()
                    WHERE id = CAST(:candidate_id AS uuid)
                    RETURNING id, media_asset_id, candidate_asset_id, duplicate_type,
                              score, algorithm, status, decided_at, updated_at
                    """
                ),
                {
                    "candidate_id": candidate_id,
                    "decision": decision,
                    "actor_user_id": actor_user_id,
                },
            )
            .mappings()
            .first()
        )
    if not row:
        raise ValueError("Duplicate candidate not found")
    return dict(row)

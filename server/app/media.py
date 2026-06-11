from __future__ import annotations

import hashlib
import json
import mimetypes
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import text

from server.app.config import get_settings
from server.app.database import db_session

ALLOWED_MEDIA_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm", ".avi"}
ALLOWED_MEDIA_MIME_PREFIXES = ("video/",)


@dataclass(frozen=True)
class MediaValidation:
    ok: bool
    mime_type: str
    file_size_bytes: int
    error: str | None = None


def validate_media_file(filename: str, content: bytes, content_type: str | None = None) -> MediaValidation:
    suffix = Path(filename).suffix.lower()
    guessed_type = content_type or mimetypes.guess_type(filename)[0] or ""
    if suffix not in ALLOWED_MEDIA_SUFFIXES:
        return MediaValidation(False, guessed_type, len(content), "unsupported_file_extension")
    if guessed_type and not guessed_type.startswith(ALLOWED_MEDIA_MIME_PREFIXES):
        return MediaValidation(False, guessed_type, len(content), "unsupported_mime_type")
    max_bytes = get_settings().max_media_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        return MediaValidation(False, guessed_type, len(content), "file_too_large")
    if not content:
        return MediaValidation(False, guessed_type, len(content), "empty_file")
    return MediaValidation(True, guessed_type or "application/octet-stream", len(content))


def checksum_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def is_student_visible_media(upload_status: str, binding_status: str) -> bool:
    return upload_status == "ready" and binding_status == "published"


def _safe_media_path(filename: str) -> tuple[Path, str]:
    settings = get_settings()
    suffix = Path(filename).suffix.lower()
    relative_path = Path("uploads") / f"{secrets.token_hex(16)}{suffix}"
    absolute_path = settings.media_root / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    return absolute_path, relative_path.as_posix()


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
        with db_session() as session:
            row = (
                session.execute(
                    text(
                        """
                        INSERT INTO media_assets (
                          title, original_file_name, relative_path, mime_type, file_size_bytes,
                          upload_status, error_reason, uploaded_by, metadata
                        )
                        VALUES (
                          :title, :original_file_name, :relative_path, :mime_type, :file_size_bytes,
                          'failed', :error_reason, CAST(:uploaded_by AS uuid), '{}'::jsonb
                        )
                        RETURNING id, title, original_file_name, relative_path, mime_type,
                                  file_size_bytes, upload_status, error_reason, created_at
                        """
                    ),
                    {
                        "title": title,
                        "original_file_name": filename,
                        "relative_path": f"failed/{secrets.token_hex(16)}{Path(filename).suffix.lower()}",
                        "mime_type": validation.mime_type,
                        "file_size_bytes": validation.file_size_bytes,
                        "error_reason": validation.error,
                        "uploaded_by": uploaded_by,
                    },
                )
                .mappings()
                .one()
            )
        return dict(row)

    absolute_path, relative_path = _safe_media_path(filename)
    absolute_path.write_bytes(content)
    digest = checksum_sha256(content)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    INSERT INTO media_assets (
                      title, original_file_name, relative_path, checksum_sha256, mime_type,
                      file_size_bytes, upload_status, uploaded_by, replaced_by, metadata
                    )
                    VALUES (
                      :title, :original_file_name, :relative_path, :checksum_sha256, :mime_type,
                      :file_size_bytes, 'ready', CAST(:uploaded_by AS uuid),
                      CAST(:replaced_by AS uuid), '{}'::jsonb
                    )
                    RETURNING id, title, original_file_name, relative_path, checksum_sha256,
                              mime_type, file_size_bytes, upload_status, error_reason, created_at
                    """
                ),
                {
                    "title": title,
                    "original_file_name": filename,
                    "relative_path": relative_path,
                    "checksum_sha256": digest,
                    "mime_type": validation.mime_type,
                    "file_size_bytes": validation.file_size_bytes,
                    "uploaded_by": uploaded_by,
                    "replaced_by": replace_asset_id,
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
                        replaced_by = :new_asset_id,
                        updated_at = now()
                    WHERE id = CAST(:old_asset_id AS uuid)
                    """
                ),
                {"new_asset_id": row["id"], "old_asset_id": replace_asset_id},
            )
    return dict(row)


def list_media_assets(upload_status: str | None = None, limit: int = 200) -> dict[str, Any]:
    filters = []
    params: dict[str, Any] = {"limit": limit}
    if upload_status:
        filters.append("upload_status = :upload_status")
        params["upload_status"] = upload_status
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    f"""
                    SELECT id, title, original_file_name, relative_path, checksum_sha256,
                           mime_type, file_size_bytes, duration_seconds, upload_status,
                           error_reason, created_at, updated_at,
                           (
                             SELECT COUNT(*)
                             FROM media_bindings mb
                             WHERE mb.media_asset_id = media_assets.id
                               AND mb.status <> 'archived'
                           ) AS association_count
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
    return {"items": rows, "total": len(rows)}


def create_media_binding(
    *,
    media_asset_id: str,
    target_type: str,
    target_id: str,
    title: str | None,
    status: str = "draft",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    INSERT INTO media_bindings (
                      media_asset_id, target_type, target_id, title, status, metadata
                    )
                    VALUES (
                      CAST(:media_asset_id AS uuid), :target_type, :target_id, :title, :status,
                      CAST(:metadata AS jsonb)
                    )
                    ON CONFLICT (media_asset_id, target_type, target_id) DO UPDATE SET
                      title = EXCLUDED.title,
                      status = EXCLUDED.status,
                      metadata = media_bindings.metadata || EXCLUDED.metadata,
                      updated_at = now()
                    RETURNING id, media_asset_id, target_type, target_id, title, status,
                              metadata, created_at, updated_at
                    """
                ),
                {
                    "media_asset_id": media_asset_id,
                    "target_type": target_type,
                    "target_id": target_id,
                    "title": title,
                    "status": status,
                    "metadata": metadata_json,
                },
            )
            .mappings()
            .one()
        )
    return dict(row)


def publish_media_binding(binding_id: str, actor_user_id: str | None) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE media_bindings
                    SET status = 'published',
                        published_by = CAST(:actor AS uuid),
                        published_at = now(),
                        updated_at = now()
                    WHERE id = CAST(:binding_id AS uuid)
                    RETURNING id, media_asset_id, target_type, target_id, title, status,
                              published_at, updated_at
                    """
                ),
                {"binding_id": binding_id, "actor": actor_user_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise ValueError("Media binding not found")
    return dict(row)

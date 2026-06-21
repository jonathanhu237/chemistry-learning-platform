from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings


def _safe_media_path(relative_path: str, *, not_found_detail: str) -> Path:
    root = get_settings().media_root.resolve()
    path = (root / relative_path).resolve()
    if root != path and root not in path.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)
    return path


def student_media_asset_file(asset_id: str) -> tuple[Path, str, str]:
    with db_session() as session:
        row = session.execute(
            text(
                """
                SELECT ma.id,
                       COALESCE(ma.playback_relative_path, ma.relative_path) AS relative_path,
                       COALESCE(ma.playback_mime_type, ma.mime_type) AS mime_type,
                       ma.original_file_name
                FROM media_assets ma
                JOIN experiment_catalog_point_media_bindings mb ON mb.media_asset_id = ma.id
                JOIN experiment_catalog_nodes n ON n.id = mb.node_id
                WHERE ma.id = CAST(:asset_id AS uuid)
                  AND ma.upload_status = 'ready'
                  AND mb.binding_status <> 'archived'
                  AND n.node_kind = 'point'
                  AND n.status = 'published'
                LIMIT 1
                """
            ),
            {"asset_id": asset_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    path = _safe_media_path(str(row["relative_path"]), not_found_detail="Media file not found")
    return path, str(row.get("mime_type") or "application/octet-stream"), str(row.get("original_file_name") or path.name)


def student_media_thumbnail_file(asset_id: str) -> tuple[Path, str, str]:
    with db_session() as session:
        row = session.execute(
            text(
                """
                SELECT ma.id,
                       ma.thumbnail_relative_path,
                       ma.original_file_name
                FROM media_assets ma
                JOIN experiment_catalog_point_media_bindings mb ON mb.media_asset_id = ma.id
                JOIN experiment_catalog_nodes n ON n.id = mb.node_id
                WHERE ma.id = CAST(:asset_id AS uuid)
                  AND ma.upload_status = 'ready'
                  AND mb.binding_status <> 'archived'
                  AND n.node_kind = 'point'
                  AND n.status = 'published'
                  AND ma.thumbnail_relative_path IS NOT NULL
                LIMIT 1
                """
            ),
            {"asset_id": asset_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media thumbnail not found")
    path = _safe_media_path(str(row["thumbnail_relative_path"]), not_found_detail="Media thumbnail not found")
    return path, "image/jpeg", f"{asset_id}.jpg"


def preview_media_asset_file(asset_id: str, *, node_id: str) -> tuple[Path, str, str]:
    with db_session() as session:
        row = session.execute(
            text(
                """
                SELECT ma.id,
                       COALESCE(ma.playback_relative_path, ma.relative_path) AS relative_path,
                       COALESCE(ma.playback_mime_type, ma.mime_type) AS mime_type,
                       ma.original_file_name
                FROM media_assets ma
                JOIN experiment_catalog_point_media_bindings mb ON mb.media_asset_id = ma.id
                JOIN experiment_catalog_nodes n ON n.id = :node_id
                WHERE ma.id = CAST(:asset_id AS uuid)
                  AND ma.upload_status = 'ready'
                  AND mb.binding_status <> 'archived'
                  AND n.node_kind = 'point'
                  AND ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                    OR mb.node_id = :node_id)
                LIMIT 1
                """
            ),
            {"asset_id": asset_id, "node_id": node_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    path = _safe_media_path(str(row["relative_path"]), not_found_detail="Media file not found")
    return path, str(row.get("mime_type") or "application/octet-stream"), str(row.get("original_file_name") or path.name)


def preview_media_thumbnail_file(asset_id: str, *, node_id: str) -> tuple[Path, str, str]:
    with db_session() as session:
        row = session.execute(
            text(
                """
                SELECT ma.id,
                       ma.thumbnail_relative_path,
                       ma.original_file_name
                FROM media_assets ma
                JOIN experiment_catalog_point_media_bindings mb ON mb.media_asset_id = ma.id
                JOIN experiment_catalog_nodes n ON n.id = :node_id
                WHERE ma.id = CAST(:asset_id AS uuid)
                  AND ma.upload_status = 'ready'
                  AND mb.binding_status <> 'archived'
                  AND n.node_kind = 'point'
                  AND ma.thumbnail_relative_path IS NOT NULL
                  AND ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                    OR mb.node_id = :node_id)
                LIMIT 1
                """
            ),
            {"asset_id": asset_id, "node_id": node_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media thumbnail not found")
    path = _safe_media_path(str(row["thumbnail_relative_path"]), not_found_detail="Media thumbnail not found")
    return path, "image/jpeg", f"{asset_id}.jpg"

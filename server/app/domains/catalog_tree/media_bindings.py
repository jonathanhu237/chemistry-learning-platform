from __future__ import annotations

from typing import Any

from sqlalchemy import text

from server.app.catalog_tree_schemas import CatalogPointMediaBindRequest
from server.app.domains.catalog_tree.common import (
    active_placement_ids_for_canonical_point,
    canonical_point_id_for_node,
    clean,
    dump_model,
    get_node,
    json_dump,
    point_capable,
)
from server.app.domains.catalog_tree.jobs import mark_point_evidence_stale
from server.app.domains.catalog_tree.search_documents import queue_index_state
from server.app.domains.catalog_tree.teacher_search import queue_teacher_index_state
from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.infrastructure.database import db_session


def media_bindings(session: Any, node_id: str) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                """
                SELECT mb.id AS binding_id,
                       mb.node_id,
                       mb.media_asset_id AS media_id,
                       COALESCE(mb.title, ma.title, ma.original_file_name) AS title,
                       mb.binding_status,
                       mb.display_order,
                       mb.published_at,
                       mb.metadata,
                       ma.original_file_name,
                       ma.mime_type,
                       COALESCE(playback.mime_type, ma.playback_mime_type, ma.mime_type) AS playback_mime_type,
                       ma.file_size_bytes AS source_file_size_bytes,
                       COALESCE(playback.file_size_bytes, ma.file_size_bytes) AS playback_file_size_bytes,
                       COALESCE(playback.width, ma.width) AS playback_width,
                       COALESCE(playback.height, ma.height) AS playback_height,
                       COALESCE(playback.duration_seconds, ma.duration_seconds) AS playback_duration_seconds,
                       COALESCE(playback.fps, ma.fps) AS playback_fps,
                       COALESCE(playback.bitrate, ma.bitrate) AS playback_bitrate,
                       COALESCE(playback.video_codec, ma.video_codec) AS playback_video_codec,
                       COALESCE(playback.audio_codec, ma.audio_codec) AS playback_audio_codec,
                       playback.kind AS playback_rendition_kind,
                       ma.upload_status,
                       ma.processing_phase,
                       ma.processing_progress,
                       ma.error_reason,
                       ma.thumbnail_relative_path IS NOT NULL AS has_thumbnail,
                       ma.created_at,
                       ma.updated_at
                FROM experiment_catalog_point_media_bindings mb
                JOIN media_assets ma ON ma.id = mb.media_asset_id
                LEFT JOIN LATERAL (
                  SELECT mr.kind,
                         mr.mime_type,
                         mr.file_size_bytes,
                         mr.width,
                         mr.height,
                         mr.duration_seconds,
                         mr.fps,
                         mr.bitrate,
                         mr.video_codec,
                         mr.audio_codec
                  FROM media_renditions mr
                  WHERE mr.media_asset_id = ma.id
                    AND mr.status = 'ready'
                  ORDER BY CASE WHEN mr.kind = 'learning' THEN 0 ELSE 1 END,
                           mr.created_at DESC,
                           mr.id
                  LIMIT 1
                ) playback ON TRUE
                JOIN experiment_catalog_nodes n ON n.id = :node_id
                WHERE ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                    OR mb.node_id = :node_id)
                  AND mb.binding_status <> 'archived'
                  AND COALESCE(ma.lifecycle_status, 'active') = 'active'
                ORDER BY mb.display_order, mb.created_at
                LIMIT 1
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def student_videos(session: Any, node_id: str) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                """
                SELECT ma.id AS media_id,
                       COALESCE(mb.title, ma.title, ma.original_file_name) AS title,
                       COALESCE(ma.playback_mime_type, ma.mime_type) AS mime_type,
                       ma.thumbnail_relative_path IS NOT NULL AS has_thumbnail
                FROM experiment_catalog_point_media_bindings mb
                JOIN media_assets ma ON ma.id = mb.media_asset_id
                JOIN experiment_catalog_nodes n ON n.id = :node_id
                WHERE ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                    OR mb.node_id = :node_id)
                  AND mb.binding_status <> 'archived'
                  AND ma.upload_status = 'ready'
                  AND COALESCE(ma.lifecycle_status, 'active') = 'active'
                ORDER BY mb.display_order, mb.created_at
                LIMIT 1
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .all()
    )
    return [
        {
            "media_id": str(row["media_id"]),
            "title": row["title"],
            "mime_type": row["mime_type"],
            "stream_path": f"/api/student/media/assets/{row['media_id']}/stream",
            "thumbnail_path": f"/api/student/media/assets/{row['media_id']}/thumbnail" if row["has_thumbnail"] else None,
        }
        for row in rows
    ]


def student_video_readiness(session: Any, node_id: str) -> dict[str, Any]:
    has_video = bool(
        session.execute(
            text(
                """
                SELECT EXISTS (
                  SELECT 1
                  FROM experiment_catalog_point_media_bindings mb
                  JOIN media_assets ma ON ma.id = mb.media_asset_id
                  JOIN experiment_catalog_nodes n ON n.id = :node_id
                  WHERE ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                      OR mb.node_id = :node_id)
                    AND mb.binding_status <> 'archived'
                    AND ma.upload_status = 'ready'
                    AND COALESCE(ma.lifecycle_status, 'active') = 'active'
                )
                """
            ),
            {"node_id": node_id},
        ).scalar_one()
    )
    return {"has_video": has_video, "video_count": 1 if has_video else 0}


def bind_existing_media(*, node_id: str, payload: CatalogPointMediaBindRequest, user: Any) -> dict[str, Any]:
    data = dump_model(payload)
    with db_session() as session:
        node = get_node(session, node_id)
        if not point_capable(node):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Directory nodes cannot bind videos")
        canonical_point_id = canonical_point_id_for_node(session, node_id)
        asset_exists = session.execute(
            text(
                """
                SELECT 1
                FROM media_assets
                WHERE id = CAST(:asset_id AS uuid)
                  AND COALESCE(lifecycle_status, 'active') = 'active'
                """
            ),
            {"asset_id": clean(data.get("media_asset_id"))},
        ).first()
        if not asset_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
        params = {
            "node_id": node_id,
            "canonical_point_id": canonical_point_id,
            "media_asset_id": clean(data.get("media_asset_id")),
            "title": clean(data.get("title")) or None,
            "binding_status": "published",
            "metadata": json_dump(data.get("metadata") if isinstance(data.get("metadata"), dict) else {}),
            "user_id": user.id,
        }
        session.execute(
            text(
                """
                WITH selected_binding AS (
                  SELECT id
                  FROM experiment_catalog_point_media_bindings
                  WHERE media_asset_id = CAST(:media_asset_id AS uuid)
                    AND (
                      (CAST(:canonical_point_id AS text) IS NOT NULL AND canonical_point_id = CAST(:canonical_point_id AS text))
                      OR (CAST(:canonical_point_id AS text) IS NULL AND node_id = :node_id)
                    )
                  ORDER BY
                    CASE WHEN binding_status <> 'archived' THEN 0 ELSE 1 END,
                    display_order,
                    created_at,
                    id
                  LIMIT 1
                )
                UPDATE experiment_catalog_point_media_bindings
                SET binding_status = 'archived',
                    metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
                      'archived_reason', 'replaced_by_catalog_point_video_binding',
                      'replacement_media_asset_id', :media_asset_id
                    ),
                    updated_by = CAST(:user_id AS uuid),
                    updated_at = now()
                WHERE binding_status <> 'archived'
                  AND (
                    (CAST(:canonical_point_id AS text) IS NOT NULL AND canonical_point_id = CAST(:canonical_point_id AS text))
                    OR (CAST(:canonical_point_id AS text) IS NULL AND node_id = :node_id)
                  )
                  AND (
                    NOT EXISTS (SELECT 1 FROM selected_binding)
                    OR id <> (SELECT id FROM selected_binding)
                  )
                """
            ),
            params,
        )
        row = (
            session.execute(
                text(
                    """
                    UPDATE experiment_catalog_point_media_bindings
                    SET title = :title,
                        binding_status = :binding_status,
                        source_placement_node_id = :node_id,
                        metadata = experiment_catalog_point_media_bindings.metadata || CAST(:metadata AS jsonb),
                        updated_by = CAST(:user_id AS uuid),
                        published_by = CAST(:user_id AS uuid),
                        published_at = COALESCE(published_at, now()),
                        display_order = 1,
                        updated_at = now()
                    WHERE id = (
                      SELECT existing.id
                      FROM experiment_catalog_point_media_bindings existing
                      WHERE (
                          (CAST(:canonical_point_id AS text) IS NOT NULL AND existing.canonical_point_id = CAST(:canonical_point_id AS text))
                          OR (CAST(:canonical_point_id AS text) IS NULL AND existing.node_id = :node_id)
                        )
                        AND existing.media_asset_id = CAST(:media_asset_id AS uuid)
                      ORDER BY
                        CASE WHEN existing.binding_status <> 'archived' THEN 0 ELSE 1 END,
                        existing.display_order,
                        existing.created_at,
                        existing.id
                      LIMIT 1
                    )
                    RETURNING id
                    """
                ),
                params,
            )
            .mappings()
            .first()
        )
        if row is None:
            row = session.execute(
                text(
                    """
                    INSERT INTO experiment_catalog_point_media_bindings (
                      node_id, canonical_point_id, source_placement_node_id, media_asset_id, title, binding_status, display_order,
                      metadata, created_by, updated_by, published_by, published_at, updated_at
                    )
                    VALUES (
                      :node_id, :canonical_point_id, :node_id, CAST(:media_asset_id AS uuid), :title, :binding_status,
                      1,
                      CAST(:metadata AS jsonb), CAST(:user_id AS uuid), CAST(:user_id AS uuid),
                      CAST(:user_id AS uuid),
                      now(),
                      now()
                    )
                    ON CONFLICT (node_id, media_asset_id) DO UPDATE SET
                      canonical_point_id = EXCLUDED.canonical_point_id,
                      source_placement_node_id = EXCLUDED.source_placement_node_id,
                      title = EXCLUDED.title,
                      binding_status = EXCLUDED.binding_status,
                      metadata = experiment_catalog_point_media_bindings.metadata || EXCLUDED.metadata,
                      updated_by = EXCLUDED.updated_by,
                      published_by = EXCLUDED.published_by,
                      published_at = EXCLUDED.published_at,
                      display_order = EXCLUDED.display_order,
                      updated_at = now()
                    RETURNING id
                    """
                ),
                params,
            ).mappings().one()
        if node["status"] == "published":
            for placement_node_id in active_placement_ids_for_canonical_point(session, canonical_point_id):
                queue_index_state(session, node_id=placement_node_id, action="upsert", soft=True)
        for placement_node_id in active_placement_ids_for_canonical_point(session, canonical_point_id):
            queue_teacher_index_state(session, node_id=placement_node_id, action="upsert", soft=True)
        mark_point_evidence_stale(session, node_id=node_id, reason="point_video_binding_changed")
    from server.app.domains.catalog_tree.nodes import get_node_detail

    return {"binding_id": str(row["id"]), "detail": get_node_detail(node_id=node_id)}


def set_media_binding_status(*, binding_id: str, action: str, user: Any) -> dict[str, Any]:
    if action not in {"publish", "unpublish", "delete"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported media binding action")
    with db_session() as session:
        row = session.execute(
            text(
                """
                SELECT id, node_id, canonical_point_id
                FROM experiment_catalog_point_media_bindings
                WHERE id = CAST(:binding_id AS uuid)
                """
            ),
            {"binding_id": binding_id},
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media binding not found")
        node_id = str(row["node_id"])
        canonical_point_id = str(row["canonical_point_id"] or "") or canonical_point_id_for_node(session, node_id)
        if action == "delete":
            session.execute(
                text(
                    """
                    UPDATE experiment_catalog_point_media_bindings
                    SET binding_status = 'archived',
                        updated_by = CAST(:user_id AS uuid),
                        updated_at = now()
                    WHERE id = CAST(:binding_id AS uuid)
                    """
                ),
                {"binding_id": binding_id, "user_id": user.id},
            )
        else:
            if action == "publish":
                session.execute(
                    text(
                        """
                        UPDATE experiment_catalog_point_media_bindings
                        SET binding_status = 'archived',
                            metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
                              'archived_reason', 'replaced_by_legacy_catalog_point_video_publish',
                              'replacement_binding_id', :binding_id
                            ),
                            updated_by = CAST(:user_id AS uuid),
                            updated_at = now()
                        WHERE binding_status <> 'archived'
                          AND id <> CAST(:binding_id AS uuid)
                          AND (
                            (CAST(:canonical_point_id AS text) IS NOT NULL AND canonical_point_id = CAST(:canonical_point_id AS text))
                            OR (CAST(:canonical_point_id AS text) IS NULL AND node_id = :node_id)
                          )
                        """
                    ),
                    {
                        "binding_id": binding_id,
                        "canonical_point_id": canonical_point_id or None,
                        "node_id": node_id,
                        "user_id": user.id,
                    },
                )
                session.execute(
                    text(
                        """
                        UPDATE experiment_catalog_point_media_bindings
                        SET binding_status = 'published',
                            published_by = CAST(:user_id AS uuid),
                            published_at = COALESCE(published_at, now()),
                            updated_by = CAST(:user_id AS uuid),
                            updated_at = now()
                        WHERE id = CAST(:binding_id AS uuid)
                        """
                    ),
                    {"binding_id": binding_id, "user_id": user.id},
                )
        for placement_node_id in active_placement_ids_for_canonical_point(session, canonical_point_id):
            queue_index_state(session, node_id=placement_node_id, action="upsert", soft=True)
            queue_teacher_index_state(session, node_id=placement_node_id, action="upsert", soft=True)
        mark_point_evidence_stale(session, node_id=node_id, reason=f"point_video_binding_{action}")
    from server.app.domains.catalog_tree.nodes import get_node_detail

    return get_node_detail(node_id=node_id)

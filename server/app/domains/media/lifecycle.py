from __future__ import annotations

from typing import Any

from sqlalchemy import text

from server.app.domains.media.assets import list_media_assets, media_asset_file_summary
from server.app.domains.media.files import json_param
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings


ACTIVE_LIFECYCLE_STATUS = "active"
ARCHIVED_LIFECYCLE_STATUS = "archived"


def _row_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row else {}


def _asset_row(session: Any, asset_id: str) -> dict[str, Any] | None:
    row = (
        session.execute(
            text(
                """
                SELECT id, title, original_file_name, relative_path, source_relative_path,
                       thumbnail_relative_path, playback_relative_path, playback_mime_type,
                       checksum_sha256, mime_type, file_size_bytes, duration_seconds,
                       width, height, fps, bitrate, video_codec, audio_codec,
                       upload_status, processing_phase, processing_progress,
                       lifecycle_status, archived_at, archived_by, archive_reason,
                       archive_metadata, error_reason, created_at, updated_at,
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
                       ), '[]'::jsonb) AS renditions
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
        return None
    asset = dict(row)
    asset.update(media_asset_file_summary(asset))
    return asset


def _catalog_binding_rows(session: Any, asset_id: str) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                """
                SELECT DISTINCT ON (mb.id, placement.id)
                       mb.id AS binding_id,
                       mb.node_id AS binding_node_id,
                       mb.canonical_point_id,
                       mb.source_placement_node_id,
                       mb.binding_status,
                       mb.display_order,
                       mb.published_at,
                       mb.metadata AS binding_metadata,
                       placement.id AS placement_node_id,
                       placement.chapter_id,
                       placement.title AS placement_title,
                       placement.status AS placement_status,
                       cp.status AS canonical_point_status,
                       COALESCE(pc.point_title, cp.title, placement.title) AS point_title,
                       pc.content_status,
                       COALESCE((
                         WITH RECURSIVE path AS (
                           SELECT id, parent_id, title, 0 AS depth
                           FROM experiment_catalog_nodes
                           WHERE id = placement.id
                           UNION ALL
                           SELECT parent.id, parent.parent_id, parent.title, path.depth + 1
                           FROM experiment_catalog_nodes parent
                           JOIN path ON path.parent_id = parent.id
                         )
                         SELECT jsonb_agg(title ORDER BY depth DESC)
                         FROM path
                       ), '[]'::jsonb) AS catalog_path,
                       (
                         placement.status = 'published'
                         AND COALESCE(cp.status, '') = 'published'
                         AND COALESCE(pc.content_status, '') = 'published'
                       ) AS student_visible,
                       EXISTS (
                         SELECT 1
                         FROM experiment_catalog_point_media_bindings other_mb
                         JOIN media_assets other_ma ON other_ma.id = other_mb.media_asset_id
                         WHERE other_mb.id <> mb.id
                           AND other_mb.binding_status <> 'archived'
                           AND other_ma.upload_status = 'ready'
                           AND COALESCE(other_ma.lifecycle_status, 'active') = 'active'
                           AND (
                             (mb.canonical_point_id IS NOT NULL AND other_mb.canonical_point_id = mb.canonical_point_id)
                             OR (mb.canonical_point_id IS NULL AND other_mb.node_id = mb.node_id)
                           )
                       ) AS has_other_ready_video
                FROM experiment_catalog_point_media_bindings mb
                JOIN LATERAL (
                  SELECT n.*
                  FROM experiment_catalog_nodes n
                  WHERE n.node_kind = 'point'
                    AND n.status <> 'archived'
                    AND (
                      (mb.canonical_point_id IS NOT NULL AND n.canonical_point_id = mb.canonical_point_id)
                      OR n.id = mb.node_id
                    )
                ) placement ON true
                LEFT JOIN experiment_catalog_points cp ON cp.id = placement.canonical_point_id
                LEFT JOIN LATERAL (
                  SELECT pc.*
                  FROM experiment_catalog_point_content pc
                  WHERE (placement.canonical_point_id IS NOT NULL AND pc.canonical_point_id = placement.canonical_point_id)
                     OR pc.node_id = placement.id
                  ORDER BY
                    CASE WHEN pc.canonical_point_id = placement.canonical_point_id THEN 0 ELSE 1 END,
                    CASE pc.content_status WHEN 'published' THEN 0 WHEN 'draft' THEN 1 ELSE 2 END,
                    pc.updated_at DESC
                  LIMIT 1
                ) pc ON true
                WHERE mb.media_asset_id = CAST(:asset_id AS uuid)
                  AND mb.binding_status <> 'archived'
                ORDER BY mb.id, placement.id
                """
            ),
            {"asset_id": asset_id},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def _legacy_binding_rows(session: Any, asset_id: str) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                """
                SELECT id AS binding_id, target_type, target_id, title, status,
                       sort_order, published_at, metadata, created_at, updated_at
                FROM media_bindings
                WHERE media_asset_id = CAST(:asset_id AS uuid)
                  AND status <> 'archived'
                ORDER BY target_type, target_id, sort_order, created_at
                """
            ),
            {"asset_id": asset_id},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def _processing_rows(session: Any, asset_id: str) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                """
                SELECT id, job_type, status, phase, progress, attempts, max_attempts,
                       error_reason, worker_id, created_at, updated_at
                FROM media_processing_jobs
                WHERE media_asset_id = CAST(:asset_id AS uuid)
                ORDER BY created_at DESC
                """
            ),
            {"asset_id": asset_id},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def _rendition_rows(session: Any, asset_id: str) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                """
                SELECT id, kind, relative_path, mime_type, file_size_bytes,
                       duration_seconds, width, height, status, created_at, updated_at
                FROM media_renditions
                WHERE media_asset_id = CAST(:asset_id AS uuid)
                ORDER BY kind, created_at
                """
            ),
            {"asset_id": asset_id},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def _fingerprint_rows(session: Any, asset_id: str) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                """
                SELECT id, algorithm, algorithm_version, relative_path, status,
                       signature_hash, created_at, updated_at
                FROM media_video_fingerprints
                WHERE media_asset_id = CAST(:asset_id AS uuid)
                ORDER BY algorithm, created_at
                """
            ),
            {"asset_id": asset_id},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def _duplicate_candidate_rows(session: Any, asset_id: str) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                """
                SELECT mdc.id, mdc.media_asset_id, mdc.candidate_asset_id,
                       mdc.duplicate_type, mdc.score, mdc.algorithm, mdc.status,
                       mdc.decided_at, mdc.created_at, mdc.updated_at
                FROM media_duplicate_candidates mdc
                WHERE mdc.media_asset_id = CAST(:asset_id AS uuid)
                   OR mdc.candidate_asset_id = CAST(:asset_id AS uuid)
                ORDER BY mdc.created_at DESC
                """
            ),
            {"asset_id": asset_id},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def _archive_plan_for_session(session: Any, asset_id: str) -> dict[str, Any]:
    asset = _asset_row(session, asset_id)
    if not asset:
        raise ValueError("Media asset not found")
    catalog_bindings = _catalog_binding_rows(session, asset_id)
    legacy_bindings = _legacy_binding_rows(session, asset_id)
    processing_jobs = _processing_rows(session, asset_id)
    renditions = _rendition_rows(session, asset_id)
    fingerprints = _fingerprint_rows(session, asset_id)
    duplicate_candidates = _duplicate_candidate_rows(session, asset_id)
    active_processing_jobs = [
        item for item in processing_jobs if str(item.get("status") or "") in {"queued", "processing"}
    ]
    student_visible_count = sum(1 for item in catalog_bindings if item.get("student_visible"))
    return {
        "asset": asset,
        "can_archive": asset.get("lifecycle_status", ACTIVE_LIFECYCLE_STATUS) == ACTIVE_LIFECYCLE_STATUS,
        "already_archived": asset.get("lifecycle_status") == ARCHIVED_LIFECYCLE_STATUS,
        "catalog_binding_count": len(catalog_bindings),
        "student_visible_catalog_binding_count": student_visible_count,
        "legacy_generic_binding_count": len(legacy_bindings),
        "processing_job_count": len(processing_jobs),
        "active_processing_job_count": len(active_processing_jobs),
        "rendition_count": len(renditions),
        "fingerprint_count": len(fingerprints),
        "duplicate_candidate_count": len(duplicate_candidates),
        "catalog_bindings": catalog_bindings,
        "legacy_generic_bindings": legacy_bindings,
        "processing_jobs": processing_jobs,
        "renditions": renditions,
        "fingerprints": fingerprints,
        "duplicate_candidates": duplicate_candidates,
        "file_state": {
            "state": asset.get("file_state"),
            "primary_file_available": asset.get("primary_file_available"),
            "existing_file_count": asset.get("existing_file_count"),
            "missing_file_count": asset.get("missing_file_count"),
            "media_files": asset.get("media_files") or [],
        },
        "message": (
            "Point content remains, but active point video bindings for this asset will be removed."
            if catalog_bindings
            else "This asset can be archived without changing point video bindings."
        ),
    }


def media_asset_archive_plan(asset_id: str) -> dict[str, Any]:
    with db_session() as session:
        return _archive_plan_for_session(session, asset_id)


def _archive_summary(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "catalog_binding_count": int(plan.get("catalog_binding_count") or 0),
        "student_visible_catalog_binding_count": int(plan.get("student_visible_catalog_binding_count") or 0),
        "legacy_generic_binding_count": int(plan.get("legacy_generic_binding_count") or 0),
        "processing_job_count": int(plan.get("processing_job_count") or 0),
        "active_processing_job_count": int(plan.get("active_processing_job_count") or 0),
        "rendition_count": int(plan.get("rendition_count") or 0),
        "fingerprint_count": int(plan.get("fingerprint_count") or 0),
        "duplicate_candidate_count": int(plan.get("duplicate_candidate_count") or 0),
        "file_state": plan.get("file_state") or {},
    }


def archive_media_asset(*, asset_id: str, actor_user_id: str | None, reason: str | None = None) -> dict[str, Any]:
    with db_session() as session:
        plan = _archive_plan_for_session(session, asset_id)
        asset = plan["asset"]
        if asset.get("lifecycle_status") != ACTIVE_LIFECYCLE_STATUS:
            return {
                "archived": False,
                "already_archived": asset.get("lifecycle_status") == ARCHIVED_LIFECYCLE_STATUS,
                "asset_id": str(asset["id"]),
                "plan": plan,
                "catalog_cleanup": {"status": "skipped", "reason": "asset_not_active"},
            }
        summary = _archive_summary(plan)
        session.execute(
            text(
                """
                UPDATE media_assets
                SET lifecycle_status = 'archived',
                    archived_at = now(),
                    archived_by = CAST(:actor_user_id AS uuid),
                    archive_reason = :reason,
                    archive_metadata = COALESCE(archive_metadata, '{}'::jsonb) || CAST(:archive_metadata AS jsonb),
                    updated_at = now()
                WHERE id = CAST(:asset_id AS uuid)
                  AND lifecycle_status = 'active'
                """
            ),
            {
                "asset_id": asset_id,
                "actor_user_id": actor_user_id,
                "reason": reason,
                "archive_metadata": json_param({"impact_summary": summary}),
            },
        )
        cancelled_job_rows = (
            session.execute(
                text(
                    """
                    UPDATE media_processing_jobs
                    SET status = 'cancelled',
                        phase = 'cancelled',
                        progress = 0,
                        error_reason = COALESCE(error_reason, 'media_asset_archived'),
                        finished_at = COALESCE(finished_at, now()),
                        updated_at = now()
                    WHERE media_asset_id = CAST(:asset_id AS uuid)
                      AND status IN ('queued', 'processing')
                    RETURNING id
                    """
                ),
                {"asset_id": asset_id},
            )
            .mappings()
            .all()
        )
        cancelled_jobs = len(cancelled_job_rows)
        event_row = (
            session.execute(
                text(
                    """
                    INSERT INTO media_asset_lifecycle_events (
                      media_asset_id, event_type, actor_user_id, reason,
                      previous_lifecycle_status, new_lifecycle_status,
                      affected_binding_summary, payload
                    )
                    VALUES (
                      CAST(:asset_id AS uuid), 'media_asset_archived', CAST(:actor_user_id AS uuid), :reason,
                      :previous_lifecycle_status, 'archived',
                      CAST(:affected_binding_summary AS jsonb), CAST(:payload AS jsonb)
                    )
                    RETURNING id, created_at
                    """
                ),
                {
                    "asset_id": asset_id,
                    "actor_user_id": actor_user_id,
                    "reason": reason,
                    "previous_lifecycle_status": asset.get("lifecycle_status") or ACTIVE_LIFECYCLE_STATUS,
                    "affected_binding_summary": json_param(summary),
                    "payload": json_param({"cancelled_processing_jobs": cancelled_jobs}),
                },
            )
            .mappings()
            .one()
        )
        event_id = str(event_row["id"])
        catalog_cleanup: dict[str, Any]
        try:
            from server.app.domains.catalog_tree.media_asset_events import handle_media_asset_archived

            catalog_cleanup = handle_media_asset_archived(
                session,
                media_asset_id=asset_id,
                lifecycle_event_id=event_id,
                actor_user_id=actor_user_id,
                reason=reason,
            )
            session.execute(
                text(
                    """
                    UPDATE media_asset_lifecycle_events
                    SET handler_status = 'succeeded',
                        affected_binding_summary = affected_binding_summary || CAST(:cleanup AS jsonb),
                        handled_at = now(),
                        updated_at = now()
                    WHERE id = CAST(:event_id AS uuid)
                    """
                ),
                {"event_id": event_id, "cleanup": json_param({"catalog_cleanup": catalog_cleanup})},
            )
        except Exception as exc:  # noqa: BLE001 - lifecycle events must preserve retry diagnostics.
            catalog_cleanup = {"status": "failed", "error": f"{exc.__class__.__name__}: {str(exc)[:900]}"}
            session.execute(
                text(
                    """
                    UPDATE media_asset_lifecycle_events
                    SET handler_status = 'failed',
                        handler_error = :handler_error,
                        updated_at = now()
                    WHERE id = CAST(:event_id AS uuid)
                    """
                ),
                {"event_id": event_id, "handler_error": catalog_cleanup["error"]},
            )
        return {
            "archived": True,
            "already_archived": False,
            "asset_id": str(asset["id"]),
            "lifecycle_status": ARCHIVED_LIFECYCLE_STATUS,
            "lifecycle_event": {"id": event_id, "created_at": event_row["created_at"]},
            "cancelled_processing_jobs": cancelled_jobs,
            "plan": plan,
            "catalog_cleanup": catalog_cleanup,
        }


def media_dependency_counts(limit: int) -> dict[str, dict[str, int]]:
    with db_session() as session:
        rows = session.execute(
            text(
                """
                SELECT ma.id,
                       (
                         SELECT COUNT(*) FROM media_bindings mb
                         WHERE mb.media_asset_id = ma.id
                       ) AS binding_count,
                       (
                         SELECT COUNT(*) FROM media_bindings mb
                         WHERE mb.media_asset_id = ma.id
                           AND mb.status <> 'archived'
                       ) AS active_binding_count,
                       (
                         SELECT COUNT(*) FROM experiment_catalog_point_media_bindings cmb
                         WHERE cmb.media_asset_id = ma.id
                       ) AS catalog_binding_count,
                       (
                         SELECT COUNT(*) FROM experiment_catalog_point_media_bindings cmb
                         WHERE cmb.media_asset_id = ma.id
                           AND cmb.binding_status <> 'archived'
                       ) AS active_catalog_binding_count,
                       (
                         SELECT COUNT(*) FROM media_processing_jobs mpj
                         WHERE mpj.media_asset_id = ma.id
                       ) AS processing_job_count,
                       (
                         SELECT COUNT(*) FROM media_renditions mr
                         WHERE mr.media_asset_id = ma.id
                       ) AS rendition_count,
                       (
                         SELECT COUNT(*) FROM media_video_fingerprints mvf
                         WHERE mvf.media_asset_id = ma.id
                       ) AS fingerprint_count,
                       (
                         SELECT COUNT(*) FROM media_duplicate_candidates mdc
                         WHERE mdc.media_asset_id = ma.id
                            OR mdc.candidate_asset_id = ma.id
                       ) AS duplicate_candidate_count
                FROM media_assets ma
                ORDER BY ma.created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings().all()
    return {
        str(row["id"]): {
            "binding_count": int(row["binding_count"] or 0),
            "active_binding_count": int(row["active_binding_count"] or 0),
            "catalog_binding_count": int(row["catalog_binding_count"] or 0),
            "active_catalog_binding_count": int(row["active_catalog_binding_count"] or 0),
            "processing_job_count": int(row["processing_job_count"] or 0),
            "rendition_count": int(row["rendition_count"] or 0),
            "fingerprint_count": int(row["fingerprint_count"] or 0),
            "duplicate_candidate_count": int(row["duplicate_candidate_count"] or 0),
        }
        for row in rows
    }


def media_cleanup_action(asset: dict[str, Any], dependencies: dict[str, int]) -> str:
    if asset.get("lifecycle_status") in {"archived", "tombstoned"}:
        return "eligible_archived_asset_file_cleanup"
    if dependencies.get("active_binding_count", 0) > 0:
        return "keep_active_binding"
    if dependencies.get("active_catalog_binding_count", 0) > 0:
        return "keep_active_catalog_binding"
    if asset.get("upload_status") == "ready":
        return "keep_ready_asset_without_binding"
    if asset.get("file_state") == "missing":
        return "review_missing_file_record"
    if asset.get("upload_status") in {"failed", "replaced"}:
        return "manual_archive_or_delete_candidate"
    return "review_before_cleanup"


def media_referenced_paths() -> set[str]:
    with db_session() as session:
        rows = session.execute(
            text(
                """
                SELECT relative_path AS path FROM media_assets WHERE relative_path IS NOT NULL
                UNION
                SELECT source_relative_path AS path FROM media_assets WHERE source_relative_path IS NOT NULL
                UNION
                SELECT playback_relative_path AS path FROM media_assets WHERE playback_relative_path IS NOT NULL
                UNION
                SELECT thumbnail_relative_path AS path FROM media_assets WHERE thumbnail_relative_path IS NOT NULL
                UNION
                SELECT relative_path AS path FROM media_renditions WHERE relative_path IS NOT NULL
                """
            )
        ).scalars().all()
    return {str(path).strip().replace("\\", "/") for path in rows if str(path or "").strip()}


def orphan_media_files(referenced_paths: set[str], limit: int) -> tuple[list[dict[str, Any]], int, int]:
    root = get_settings().media_root.resolve()
    if not root.exists():
        return [], 0, 0
    output: list[dict[str, Any]] = []
    total_count = 0
    total_bytes = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root).as_posix()
        if relative_path in referenced_paths:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        total_count += 1
        total_bytes += size
        if len(output) < limit:
            output.append({"relative_path": relative_path, "file_size_bytes": size})
    return output, total_count, total_bytes


def media_cleanup_dry_run(*, limit: int = 500, orphan_limit: int = 200) -> dict[str, Any]:
    assets = list_media_assets(limit=limit, include_archived=True)["items"]
    dependencies_by_id = media_dependency_counts(limit)
    referenced_paths = media_referenced_paths()
    orphan_files, orphan_total_count, orphan_total_bytes = orphan_media_files(referenced_paths, orphan_limit)
    asset_items = []
    for asset in assets:
        dependencies = dependencies_by_id.get(str(asset["id"]), {})
        existing_bytes = sum(int(item.get("file_size_bytes") or 0) for item in asset.get("media_files") or [])
        asset_items.append(
            {
                "id": str(asset["id"]),
                "title": asset.get("title"),
                "original_file_name": asset.get("original_file_name"),
                "upload_status": asset.get("upload_status"),
                "lifecycle_status": asset.get("lifecycle_status"),
                "archived_at": asset.get("archived_at"),
                "file_state": asset.get("file_state"),
                "primary_file_available": asset.get("primary_file_available"),
                "existing_file_count": asset.get("existing_file_count"),
                "missing_file_count": asset.get("missing_file_count"),
                "existing_file_bytes": existing_bytes,
                "dependencies": dependencies,
                "action": media_cleanup_action(asset, dependencies),
                "media_files": asset.get("media_files") or [],
            }
        )
    return {
        "dry_run": True,
        "media_root": str(get_settings().media_root),
        "asset_count": len(asset_items),
        "asset_limit": limit,
        "referenced_path_count": len(referenced_paths),
        "orphan_file_count": orphan_total_count,
        "orphan_file_bytes": orphan_total_bytes,
        "orphan_files_returned": len(orphan_files),
        "orphan_files": orphan_files,
        "assets": asset_items,
        "policy": {
            "asset_file_deletion": "allowed_only_for_archived_or_tombstoned_assets",
            "orphan_file_deletion": "allowed_only_for_files_not_referenced_by_media_database_rows",
        },
    }

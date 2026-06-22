from __future__ import annotations

from typing import Any

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from sqlalchemy import text

from server.app.infrastructure.database import db_session
from server.app.domains.experiment_points.canonical_points import candidate_point_key as _candidate_point_key

def _ensure_experiment(session: Any, experiment_id: str) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                """
                SELECT id, code, title, title_en, summary, status, display_order, source_refs, metadata
                FROM formal_experiments
                WHERE id = :experiment_id
                """
            ),
            {"experiment_id": experiment_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formal experiment not found")
    return dict(row)

def _video_candidates(metadata: Any) -> list[str]:
    if not isinstance(metadata, dict):
        return []
    raw_candidates = metadata.get("video_candidates") or []
    if not isinstance(raw_candidates, list):
        return []
    candidates: list[str] = []
    seen: set[str] = set()
    for raw in raw_candidates:
        title = str(raw or "").strip()
        if not title or title in seen:
            continue
        seen.add(title)
        candidates.append(title)
    return candidates

def _experiment_video_points(experiment: dict[str, Any], resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    by_key: dict[str, dict[str, Any]] = {}
    for index, title in enumerate(_video_candidates(experiment.get("metadata"))):
        point = {
            "point_key": _candidate_point_key(index, title),
            "point_title": title,
            "source": "candidate",
            "resources": [],
            "resource_count": 0,
            "published_count": 0,
        }
        points.append(point)
        by_key[point["point_key"]] = point

    legacy_point: dict[str, Any] | None = None
    for resource in resources:
        point_key = str(resource.get("point_key") or "").strip()
        point_title = str(resource.get("point_title") or "").strip()
        if point_key and point_key not in by_key:
            point = {
                "point_key": point_key,
                "point_title": point_title or str(resource.get("title") or resource.get("media_title") or point_key),
                "source": "stored",
                "resources": [],
                "resource_count": 0,
                "published_count": 0,
            }
            points.append(point)
            by_key[point_key] = point
        elif not point_key:
            if legacy_point is None:
                legacy_point = {
                    "point_key": "legacy-unassigned",
                    "point_title": "Unassigned resources",
                    "source": "legacy",
                    "resources": [],
                    "resource_count": 0,
                    "published_count": 0,
                }
                points.append(legacy_point)
                by_key[legacy_point["point_key"]] = legacy_point
            point_key = legacy_point["point_key"]

        point = by_key.get(point_key)
        if not point:
            continue
        point["resources"].append(resource)
        point["resource_count"] += 1
        if resource.get("binding_status") == "published":
            point["published_count"] += 1

    return points

def _experiment_select_sql(where_clause: str = "") -> str:
    return f"""
        SELECT
          fe.id,
          fe.code,
          fe.title,
          fe.title_en,
          fe.summary,
          fe.status,
          fe.display_order,
          fe.source_refs,
          fe.metadata,
          fe.published_at,
          fe.created_at,
          fe.updated_at,
          COALESCE((
            SELECT jsonb_agg(
              jsonb_build_object(
                'chapter_id', ecb.chapter_id,
                'chapter_title', c.chapter_title,
                'chapter_number', c.chapter_number,
                'coverage_type', ecb.coverage_type,
                'notes', ecb.notes,
                'sort_order', ecb.sort_order
              )
              ORDER BY ecb.sort_order, c.chapter_number NULLS LAST, ecb.chapter_id
            )
            FROM experiment_chapter_bindings ecb
            LEFT JOIN chapters c ON c.id = ecb.chapter_id
            WHERE ecb.experiment_id = fe.id
          ), '[]'::jsonb) AS chapter_bindings,
          COALESCE((
            SELECT jsonb_agg(
              jsonb_build_object(
                'binding_id', mb.id,
                'media_id', ma.id,
                'title', COALESCE(mb.title, ma.title),
                'original_file_name', ma.original_file_name,
                'mime_type', ma.mime_type,
                'file_size_bytes', ma.file_size_bytes,
                'thumbnail_relative_path', ma.thumbnail_relative_path,
                'upload_status', ma.upload_status,
                'binding_status', mb.status,
                'point_key', mb.metadata->>'point_key',
                'point_title', mb.metadata->>'point_title',
                'published_at', mb.published_at
              )
              ORDER BY mb.sort_order, mb.created_at
            )
            FROM media_bindings mb
            JOIN media_assets ma ON ma.id = mb.media_asset_id
            WHERE mb.target_type = 'experiment'
              AND mb.target_id = fe.id
              AND mb.status <> 'archived'
              AND COALESCE(ma.lifecycle_status, 'active') = 'active'
          ), '[]'::jsonb) AS media_resources,
          (SELECT COUNT(*) FROM experiment_questions q WHERE q.experiment_id = fe.id AND q.status = 'published') AS published_question_count,
          (SELECT COUNT(*) FROM experiment_questions q WHERE q.experiment_id = fe.id AND q.status = 'draft') AS draft_question_count,
          (SELECT COUNT(*) FROM experiment_question_drafts d WHERE d.experiment_id = fe.id AND d.status = 'draft') AS generated_draft_count
        FROM formal_experiments fe
        {where_clause}
        ORDER BY fe.display_order, fe.code
    """

def _list_experiments(
    *,
    chapter_id: str | None = None,
    status_filter: str | None = None,
    include_archived: bool = False,
    video_status: str | None = None,
    question_status: str | None = None,
) -> list[dict[str, Any]]:
    filters: list[str] = ["COALESCE(fe.metadata->>'archived_by_catalog_seed', 'false') <> 'true'"]
    params: dict[str, Any] = {}
    if chapter_id:
        filters.append(
            """
            EXISTS (
              SELECT 1 FROM experiment_chapter_bindings ecb
              WHERE ecb.experiment_id = fe.id AND ecb.chapter_id = :chapter_id
            )
            """
        )
        params["chapter_id"] = chapter_id
    if status_filter:
        filters.append("fe.status = :status_filter")
        params["status_filter"] = status_filter
    elif not include_archived:
        filters.append("fe.status <> 'archived'")
    if video_status == "none":
        filters.append(
            """
            NOT EXISTS (
              SELECT 1 FROM media_bindings mb
              JOIN media_assets ma ON ma.id = mb.media_asset_id
              WHERE mb.target_type = 'experiment' AND mb.target_id = fe.id AND mb.status <> 'archived'
                AND COALESCE(ma.lifecycle_status, 'active') = 'active'
            )
            """
        )
    elif video_status:
        filters.append(
            """
            EXISTS (
              SELECT 1 FROM media_bindings mb
              JOIN media_assets ma ON ma.id = mb.media_asset_id
              WHERE mb.target_type = 'experiment'
                AND mb.target_id = fe.id
                AND mb.status <> 'archived'
                AND COALESCE(ma.lifecycle_status, 'active') = 'active'
                AND (ma.upload_status = :video_status OR mb.status = :video_status)
            )
            """
        )
        params["video_status"] = video_status
    if question_status == "empty":
        filters.append("NOT EXISTS (SELECT 1 FROM experiment_questions q WHERE q.experiment_id = fe.id)")
    elif question_status:
        filters.append(
            """
            EXISTS (
              SELECT 1 FROM experiment_questions q
              WHERE q.experiment_id = fe.id AND q.status = :question_status
            )
            """
        )
        params["question_status"] = question_status
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    with db_session() as session:
        return [dict(row) for row in session.execute(text(_experiment_select_sql(where_clause)), params).mappings().all()]

def _list_experiment_video_resources(experiment_id: str | None = None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    filters = ["mb.target_type = 'experiment'", "mb.status <> 'archived'", "COALESCE(ma.lifecycle_status, 'active') = 'active'"]
    if experiment_id:
        filters.append("mb.target_id = :experiment_id")
        params["experiment_id"] = experiment_id
    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    f"""
                    SELECT mb.id AS binding_id, mb.target_id AS experiment_id, fe.code, fe.title AS experiment_title,
                           mb.title AS binding_title, mb.status AS binding_status, mb.published_at,
                           mb.metadata AS binding_metadata,
                           mb.metadata->>'point_key' AS point_key,
                           mb.metadata->>'point_title' AS point_title,
                           ma.id AS media_id, ma.title AS media_title, ma.original_file_name,
                           ma.mime_type, ma.file_size_bytes, ma.thumbnail_relative_path,
                           ma.upload_status, ma.error_reason,
                           ma.created_at, ma.updated_at
                    FROM media_bindings mb
                    JOIN media_assets ma ON ma.id = mb.media_asset_id
                    LEFT JOIN formal_experiments fe ON fe.id = mb.target_id
                    WHERE {" AND ".join(filters)}
                    ORDER BY mb.sort_order, ma.created_at DESC
                    """
                ),
                params,
            )
            .mappings()
            .all()
        ]
    for row in rows:
        row["title"] = row.get("binding_title") or row.get("media_title") or row.get("original_file_name")
        if not isinstance(row.get("binding_metadata"), dict):
            row["binding_metadata"] = {}
    return rows

def _current_experiment_catalog_count() -> int:
    with db_session() as session:
        return int(
            session.execute(
                text("SELECT COUNT(*) FROM formal_experiments WHERE status <> 'archived'")
            ).scalar_one()
            or 0
        )

def list_experiments_overview(
    *,
    chapter_id: str | None = None,
    status_filter: str | None = None,
    include_archived: bool = False,
    video_status: str | None = None,
    question_status: str | None = None,
) -> dict[str, Any]:
    items = _list_experiments(
        chapter_id=chapter_id,
        status_filter=status_filter,
        include_archived=include_archived,
        video_status=video_status,
        question_status=question_status,
    )
    return {
        "items": items,
        "total": len(items),
        "formal_count": _current_experiment_catalog_count(),
        "legacy_fragment_warning": "实验管理以精选目录中的具体实验点为主，不再以 19-1 到 20-3 的大实验单元计数。",
    }


def get_experiment(
    *,
    experiment_id: str,
) -> dict[str, Any]:
    with db_session() as session:
        row = session.execute(text(_experiment_select_sql("WHERE fe.id = :experiment_id")), {"experiment_id": experiment_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formal experiment not found")
    return dict(row)


def list_experiment_videos(
    *,
    experiment_id: str | None = None,
) -> dict[str, Any]:
    rows = _list_experiment_video_resources(experiment_id)
    return {"items": rows, "total": len(rows)}

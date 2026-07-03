from __future__ import annotations

import re
from typing import Any

from sqlalchemy import text

from server.app.infrastructure.database import db_session
from server.app.student_legacy_schemas import LegacyStudentVideoPointItem, LegacyStudentVideoPointResponse


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _query_tokens(query: str) -> list[str]:
    normalized = query.strip().lower()
    if not normalized:
        return []
    return [token for token in re.split(r"[-\s,，;；+→=/\\]+", normalized) if token]


def _row_search_text(row: dict[str, Any]) -> str:
    return " ".join(
        item
        for item in [
            _clean(row.get("chapter_title")),
            *_string_list(row.get("catalog_path")),
            _clean(row.get("node_title")),
            _clean(row.get("point_title")),
            _clean(row.get("summary")),
            _clean(row.get("principle_equation")),
            _clean(row.get("principle_text")),
            _clean(row.get("phenomenon_explanation")),
            _clean(row.get("safety_note")),
        ]
        if item
    ).lower()


def _matches_query(row: dict[str, Any], tokens: list[str]) -> bool:
    if not tokens:
        return True
    text_value = _row_search_text(row)
    return all(token in text_value for token in tokens)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _legacy_point_sort_key(row: dict[str, Any]) -> tuple[int, int, int]:
    has_video_rank = 0 if _safe_int(row.get("media_count")) > 0 else 1
    recommendation_rank = 0 if row.get("is_recommended") else 1
    recommendation_order = _safe_int(row.get("recommended_order")) if row.get("is_recommended") else 0
    return (has_video_rank, recommendation_rank, recommendation_order)


def _ensure_recommendation_table(session: Any) -> None:
    session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS legacy_recommended_video_points (
              node_id text PRIMARY KEY,
              sort_order int NOT NULL DEFAULT 0,
              recommended_by text,
              recommended_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
    )


def _point_item(row: dict[str, Any]) -> LegacyStudentVideoPointItem:
    title = _clean(row.get("point_title")) or _clean(row.get("node_title"))
    snippet = _clean(row.get("phenomenon_explanation")) or _clean(row.get("principle_equation")) or _clean(row.get("principle_text"))
    media_count = int(row.get("media_count") or 0)
    thumbnail_media_id = _clean(row.get("thumbnail_media_id"))
    thumbnail_path = f"/api/student/media/assets/{thumbnail_media_id}/thumbnail" if thumbnail_media_id else _clean(row.get("thumbnail_path"))
    return LegacyStudentVideoPointItem(
        id=_clean(row.get("node_id")),
        node_id=_clean(row.get("node_id")),
        chapter_id=_clean(row.get("chapter_id")) or None,
        title=title,
        summary=_clean(row.get("summary")) or snippet,
        snippet=snippet,
        catalog_path=_string_list(row.get("catalog_path")),
        media_count=media_count,
        published_media_count=media_count,
        thumbnail_path=thumbnail_path or None,
        is_recommended=bool(row.get("is_recommended")),
        recommended_order=int(row["recommended_order"]) if row.get("recommended_order") is not None else None,
    )


def _legacy_video_point_rows(session: Any) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                """
                SELECT
                  n.id AS node_id,
                  n.chapter_id,
                  c.chapter_title,
                  n.title AS node_title,
                  n.summary,
                  n.display_order,
                  pc.point_title,
                  pc.principle_equation,
                  pc.principle_text,
                  pc.phenomenon_explanation,
                  pc.safety_note,
                  COALESCE((
                    WITH RECURSIVE path AS (
                      SELECT id, parent_id, title, 0 AS depth
                      FROM experiment_catalog_nodes
                      WHERE id = n.id
                      UNION ALL
                      SELECT parent.id, parent.parent_id, parent.title, path.depth + 1
                      FROM experiment_catalog_nodes parent
                      JOIN path ON path.parent_id = parent.id
                    )
                    SELECT jsonb_agg(title ORDER BY depth DESC)
                    FROM path
                  ), '[]'::jsonb) AS catalog_path,
                  COALESCE(media_counts.media_count, 0) AS media_count,
                  media_preview.thumbnail_media_id,
                  CASE WHEN lr.node_id IS NULL THEN false ELSE true END AS is_recommended,
                  lr.sort_order AS recommended_order,
                  lr.recommended_at
                FROM experiment_catalog_nodes n
                JOIN chapters c ON c.id = n.chapter_id
                JOIN experiment_catalog_points cp ON cp.id = n.canonical_point_id
                LEFT JOIN legacy_recommended_video_points lr ON lr.node_id = n.id
                JOIN LATERAL (
                  SELECT pc.*
                  FROM experiment_catalog_point_content pc
                  WHERE (pc.canonical_point_id = n.canonical_point_id OR pc.node_id = n.id)
                    AND pc.content_status = 'published'
                  ORDER BY CASE WHEN pc.canonical_point_id = n.canonical_point_id THEN 0 ELSE 1 END,
                           pc.updated_at DESC,
                           pc.node_id
                  LIMIT 1
                ) pc ON true
                LEFT JOIN LATERAL (
                  SELECT COUNT(*) AS media_count
                  FROM experiment_catalog_point_media_bindings mb
                  JOIN media_assets ma ON ma.id = mb.media_asset_id
                  WHERE ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                      OR mb.node_id = n.id)
                    AND ma.upload_status = 'ready'
                    AND COALESCE(ma.lifecycle_status, 'active') = 'active'
                    AND mb.binding_status = 'published'
                    AND COALESCE(mb.metadata->>'placeholder_video', 'false') <> 'true'
                    AND COALESCE(mb.metadata->>'coverage_kind', ma.metadata->>'seed_kind', '') <> 'placeholder_video'
                    AND COALESCE(ma.original_file_name, '') <> 'no-video-placeholder.mp4'
                ) media_counts ON true
                LEFT JOIN LATERAL (
                  SELECT ma.id AS thumbnail_media_id
                  FROM experiment_catalog_point_media_bindings mb
                  JOIN media_assets ma ON ma.id = mb.media_asset_id
                  WHERE ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                      OR mb.node_id = n.id)
                    AND ma.upload_status = 'ready'
                    AND COALESCE(ma.lifecycle_status, 'active') = 'active'
                    AND mb.binding_status = 'published'
                    AND ma.thumbnail_relative_path IS NOT NULL
                    AND COALESCE(mb.metadata->>'placeholder_video', 'false') <> 'true'
                    AND COALESCE(mb.metadata->>'coverage_kind', ma.metadata->>'seed_kind', '') <> 'placeholder_video'
                    AND COALESCE(ma.original_file_name, '') <> 'no-video-placeholder.mp4'
                  ORDER BY mb.display_order, mb.created_at, ma.id
                  LIMIT 1
                ) media_preview ON true
                WHERE n.node_kind = 'point'
                  AND n.status = 'published'
                  AND cp.status = 'published'
                  AND (
                    WITH RECURSIVE path AS (
                      SELECT id, parent_id, status
                      FROM experiment_catalog_nodes
                      WHERE id = n.id
                      UNION ALL
                      SELECT parent.id, parent.parent_id, parent.status
                      FROM experiment_catalog_nodes parent
                      JOIN path ON path.parent_id = parent.id
                    )
                    SELECT COALESCE(bool_and(status = 'published'), false)
                    FROM path
                  )
                ORDER BY CASE WHEN COALESCE(media_counts.media_count, 0) > 0 THEN 0 ELSE 1 END,
                         CASE WHEN lr.node_id IS NULL THEN 1 ELSE 0 END,
                         lr.sort_order,
                         lr.recommended_at DESC NULLS LAST,
                         c.chapter_number NULLS LAST,
                         c.chapter_title,
                         n.display_order,
                         n.id
                """
            )
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def legacy_student_video_points(*, query: str = "", limit: int = 200) -> LegacyStudentVideoPointResponse:
    tokens = _query_tokens(query)
    bounded_limit = max(1, min(limit, 500))
    with db_session() as session:
        _ensure_recommendation_table(session)
        rows = _legacy_video_point_rows(session)
    matched_rows = sorted((row for row in rows if _matches_query(row, tokens)), key=_legacy_point_sort_key)
    items = [_point_item(row) for row in matched_rows]
    limited_items = items[:bounded_limit]
    return LegacyStudentVideoPointResponse(
        status="ok" if limited_items else "empty",
        query=query.strip(),
        total=len(items),
        items=limited_items,
    )


def set_legacy_video_point_recommendation(
    *,
    node_id: str,
    recommended: bool,
    sort_order: int = 0,
    user_id: str | None = None,
) -> bool:
    clean_node_id = node_id.strip()
    if not clean_node_id:
        return False
    with db_session() as session:
        _ensure_recommendation_table(session)
        exists = session.execute(
            text(
                """
                SELECT 1
                FROM experiment_catalog_nodes
                WHERE id = :node_id
                  AND node_kind = 'point'
                  AND status = 'published'
                LIMIT 1
                """
            ),
            {"node_id": clean_node_id},
        ).first()
        if not exists:
            return False
        if recommended:
            session.execute(
                text(
                    """
                    INSERT INTO legacy_recommended_video_points (
                      node_id, sort_order, recommended_by, recommended_at
                    )
                    VALUES (:node_id, :sort_order, :recommended_by, now())
                    ON CONFLICT (node_id) DO UPDATE SET
                      sort_order = EXCLUDED.sort_order,
                      recommended_by = EXCLUDED.recommended_by,
                      recommended_at = now()
                    """
                ),
                {"node_id": clean_node_id, "sort_order": sort_order, "recommended_by": user_id},
            )
        else:
            session.execute(
                text("DELETE FROM legacy_recommended_video_points WHERE node_id = :node_id"),
                {"node_id": clean_node_id},
            )
    return True

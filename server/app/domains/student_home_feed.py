from __future__ import annotations

from typing import Any

from sqlalchemy import text

from server.app.infrastructure.database import db_session
from server.app.student_home_feed_schemas import (
    StudentHomeVideoFeedResponse,
    StudentHomeVideoMedia,
    StudentHomeVideoFeedItem,
)
from server.app.student_video_library_schemas import StudentVideoLibraryRouteTarget


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = value.strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _path_titles(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def _feed_rows(session: Any, *, limit: int) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                """
                SELECT
                  n.id AS node_id,
                  n.id AS placement_node_id,
                  n.canonical_point_id,
                  n.chapter_id,
                  c.chapter_title,
                  c.chapter_number,
                  COALESCE(pc.point_title, n.title) AS point_title,
                  COALESCE(n.summary, '') AS point_summary,
                  COALESCE(pc.phenomenon_explanation, pc.principle_text, pc.principle_equation, n.summary, '') AS snippet,
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
                  media.media_id,
                  media.media_title,
                  media.mime_type,
                  media.duration_seconds,
                  media.has_thumbnail
                FROM experiment_catalog_nodes n
                JOIN chapters c ON c.id = n.chapter_id
                JOIN experiment_catalog_points cp ON cp.id = n.canonical_point_id
                JOIN LATERAL (
                  SELECT pc.point_title,
                         pc.principle_mode,
                         pc.principle_equation,
                         pc.principle_text,
                         pc.phenomenon_explanation,
                         pc.updated_at
                  FROM experiment_catalog_point_content pc
                  WHERE pc.content_status = 'published'
                    AND (
                      (n.canonical_point_id IS NOT NULL AND pc.canonical_point_id = n.canonical_point_id)
                      OR pc.node_id = n.id
                    )
                  ORDER BY CASE WHEN pc.canonical_point_id = n.canonical_point_id THEN 0 ELSE 1 END,
                           pc.updated_at DESC NULLS LAST
                  LIMIT 1
                ) pc ON TRUE
                JOIN LATERAL (
                  SELECT ma.id AS media_id,
                         COALESCE(mb.title, ma.title, ma.original_file_name, '') AS media_title,
                         COALESCE(playback.mime_type, ma.playback_mime_type, ma.mime_type) AS mime_type,
                         COALESCE(playback.duration_seconds, ma.duration_seconds) AS duration_seconds,
                         ma.thumbnail_relative_path IS NOT NULL AS has_thumbnail,
                         mb.display_order,
                         mb.created_at
                  FROM experiment_catalog_point_media_bindings mb
                  JOIN media_assets ma ON ma.id = mb.media_asset_id
                  LEFT JOIN LATERAL (
                    SELECT mr.kind,
                           mr.mime_type,
                           mr.duration_seconds
                    FROM media_renditions mr
                    WHERE mr.media_asset_id = ma.id
                      AND mr.status = 'ready'
                    ORDER BY CASE WHEN mr.kind = 'learning' THEN 0 ELSE 1 END,
                             mr.created_at DESC,
                             mr.id
                    LIMIT 1
                  ) playback ON TRUE
                  WHERE ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                      OR mb.node_id = n.id)
                    AND mb.binding_status = 'published'
                    AND ma.upload_status = 'ready'
                    AND COALESCE(ma.lifecycle_status, 'active') = 'active'
                  ORDER BY mb.display_order, mb.created_at
                  LIMIT 1
                ) media ON TRUE
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
                ORDER BY c.chapter_number NULLS LAST, n.display_order, n.id
                LIMIT :limit
                """
            ),
            {"limit": limit},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def _feed_item(row: dict[str, Any]) -> StudentHomeVideoFeedItem | None:
    node_id = _clean_text(row.get("node_id"))
    placement_node_id = _clean_text(row.get("placement_node_id")) or node_id
    canonical_point_id = _clean_text(row.get("canonical_point_id")) or node_id
    chapter_id = _clean_text(row.get("chapter_id"))
    media_id = _clean_text(row.get("media_id"))
    title = _clean_text(row.get("point_title")) or _clean_text(row.get("media_title"))
    if not node_id or not media_id or not title:
        return None
    catalog_path = _path_titles(row.get("catalog_path"))
    chapter_title = _clean_text(row.get("chapter_title"))
    badges = _unique([chapter_title, *catalog_path[-2:]])[:3]
    target = StudentVideoLibraryRouteTarget(
        kind="point_detail",
        route=f"/point/{placement_node_id}",
        node_id=placement_node_id,
        placement_node_id=placement_node_id,
        source_node_id=placement_node_id,
        canonical_point_id=canonical_point_id,
        chapter_id=chapter_id or None,
        catalog_path=catalog_path,
        point_title=title,
        context_title=title,
        context_summary=_clean_text(row.get("snippet")) or _clean_text(row.get("point_summary")),
    )
    media = StudentHomeVideoMedia(
        media_id=media_id,
        title=_clean_text(row.get("media_title")),
        mime_type=_clean_text(row.get("mime_type")) or None,
        stream_path=f"/api/student/media/assets/{media_id}/stream",
        thumbnail_path=f"/api/student/media/assets/{media_id}/thumbnail" if row.get("has_thumbnail") else None,
        duration_seconds=float(row["duration_seconds"]) if row.get("duration_seconds") is not None else None,
    )
    return StudentHomeVideoFeedItem(
        id=f"home-video:{placement_node_id}:{media_id}",
        node_id=node_id,
        placement_node_id=placement_node_id,
        canonical_point_id=canonical_point_id,
        chapter_id=chapter_id,
        title=title,
        summary=_clean_text(row.get("point_summary")),
        snippet=_clean_text(row.get("snippet")),
        catalog_path=catalog_path,
        badges=badges,
        video=media,
        target=target,
        reason="catalog",
    )


def student_home_video_feed(_user: Any, *, limit: int = 12) -> StudentHomeVideoFeedResponse:
    safe_limit = max(1, min(limit, 30))
    with db_session() as session:
        items = [item for item in (_feed_item(row) for row in _feed_rows(session, limit=safe_limit)) if item]
    if not items:
        return StudentHomeVideoFeedResponse(
            status="empty",
            message="暂无可预览的实验视频，老师发布点位视频后会显示在首页。",
            items=[],
        )
    return StudentHomeVideoFeedResponse(status="ok", items=items)


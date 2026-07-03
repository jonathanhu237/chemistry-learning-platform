from __future__ import annotations

import base64
import hashlib
import json
import random
import secrets
from typing import Any

from sqlalchemy import text

from server.app.domains.student_video_saves import personal_states_for_items
from server.app.infrastructure.database import db_session
from server.app.student_home_feed_schemas import (
    StudentHomeVideoFeedItem,
    StudentHomeVideoFeedResponse,
    StudentHomeVideoMedia,
)
from server.app.student_video_library_schemas import StudentVideoLibraryRouteTarget
from server.app.student_video_save_schemas import StudentVideoPersonalState


DISCOVER_TOPIC = "discover"
WATCH_LATER_TOPIC = "watch_later"
ALL_TOPIC = "all"
FAVORITES_TOPIC = "favorites"

HOME_VIDEO_TOPICS: list[dict[str, Any]] = [
    {"id": DISCOVER_TOPIC, "label": "发现", "repeat": True, "terms": []},
    {"id": WATCH_LATER_TOPIC, "label": "稍后学习", "repeat": False, "terms": []},
    {"id": ALL_TOPIC, "label": "全部", "repeat": False, "terms": []},
    {"id": "color_change", "label": "颜色变化", "repeat": False, "terms": ["颜色变化", "变色", "颜色", "黄色", "绿色", "蓝色", "红色", "橙色", "紫色"]},
    {"id": "precipitation", "label": "沉淀生成", "repeat": False, "terms": ["沉淀", "浑浊", "析出"]},
    {"id": "gas_generation", "label": "气体生成", "repeat": False, "terms": ["气体", "气泡", "冒泡", "刺激性"]},
    {"id": "layer_extraction", "label": "分层萃取", "repeat": False, "terms": ["分层", "萃取", "ccl4", "四氯化碳"]},
    {"id": "fading_bleaching", "label": "褪色漂白", "repeat": False, "terms": ["褪色", "漂白", "品红"]},
    {"id": "flame_light", "label": "发光火焰", "repeat": False, "terms": ["火焰", "燃烧", "发光"]},
    {"id": "temperature_change", "label": "温度变化", "repeat": False, "terms": ["温度", "放热", "吸热", "发热", "冷却"]},
    {"id": "heating", "label": "加热反应", "repeat": False, "terms": ["加热", "微热", "灼烧"]},
    {"id": "test_paper", "label": "试纸检验", "repeat": False, "terms": ["试纸", "ph", "ki-淀粉", "醋酸铅"]},
    {"id": "indicator", "label": "指示剂", "repeat": False, "terms": ["指示剂", "酚酞", "石蕊", "甲基橙"]},
    {"id": "crystallization", "label": "晶体析出", "repeat": False, "terms": ["晶体", "结晶", "析晶"]},
]

TOPIC_BY_ID = {topic["id"]: topic for topic in HOME_VIDEO_TOPICS}
TOPIC_ALIASES = {
    "发现": DISCOVER_TOPIC,
    "推荐": DISCOVER_TOPIC,
    "recommended": DISCOVER_TOPIC,
    "recommend": DISCOVER_TOPIC,
    "稍后学习": WATCH_LATER_TOPIC,
    "watch-later": WATCH_LATER_TOPIC,
    "watch_later": WATCH_LATER_TOPIC,
    "全部": ALL_TOPIC,
    "all": ALL_TOPIC,
    "收藏": FAVORITES_TOPIC,
    "favorite": FAVORITES_TOPIC,
    "favorites": FAVORITES_TOPIC,
}
CURSOR_VERSION = 1


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


def normalize_home_video_topic(topic: str | None) -> str:
    raw = _clean_text(topic)
    if not raw:
        return DISCOVER_TOPIC
    normalized = raw.lower().replace("-", "_")
    return TOPIC_ALIASES.get(raw) or TOPIC_ALIASES.get(normalized) or (normalized if normalized in TOPIC_BY_ID else DISCOVER_TOPIC)


def _cursor_encode(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _cursor_decode(cursor: str | None, *, topic: str, pool_hash: str) -> dict[str, Any] | None:
    if not cursor:
        return None
    try:
        padded = cursor + ("=" * (-len(cursor) % 4))
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("version") != CURSOR_VERSION or payload.get("topic") != topic or payload.get("pool_hash") != pool_hash:
        return None
    return payload


def _canonical_id(row: dict[str, Any]) -> str:
    return f"{_clean_text(row.get('placement_node_id'))}:{_clean_text(row.get('media_id'))}"


def _pool_hash(rows: list[dict[str, Any]]) -> str:
    joined = "|".join(sorted(_canonical_id(row) for row in rows))
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:16]


def _instance_id(*, topic: str, seed: str, offset: int, cycle: int, row: dict[str, Any]) -> str:
    digest = hashlib.sha1(_canonical_id(row).encode("utf-8")).hexdigest()[:12]
    return f"home-feed:{topic}:{seed}:{cycle}:{offset}:{digest}"


def _feed_rows(session: Any, *, limit: int | None = None) -> list[dict[str, Any]]:
    limit_clause = "LIMIT :limit" if limit is not None else ""
    params = {"limit": limit} if limit is not None else {}
    rows = (
        session.execute(
            text(
                f"""
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
                  COALESCE(pc.principle_equation, '') AS principle_equation,
                  COALESCE(pc.principle_text, '') AS principle_text,
                  COALESCE(pc.phenomenon_explanation, '') AS phenomenon_explanation,
                  COALESCE(chemistry.reaction_features, '[]'::jsonb) AS reaction_features,
                  COALESCE(chemistry.condition_tags, '[]'::jsonb) AS condition_tags,
                  COALESCE(chemistry.phenomenon_tags, '[]'::jsonb) AS phenomenon_tags,
                  COALESCE(chemistry.property_tags, '[]'::jsonb) AS property_tags,
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
                LEFT JOIN LATERAL (
                  SELECT
                    COALESCE((
                      SELECT jsonb_agg(DISTINCT feature.value)
                      FROM experiment_catalog_point_reaction_equations eq
                      CROSS JOIN LATERAL jsonb_array_elements_text(COALESCE(eq.reaction_features, '[]'::jsonb)) AS feature(value)
                      WHERE eq.validation_status != 'invalid'
                        AND (
                          (n.canonical_point_id IS NOT NULL AND eq.canonical_point_id = n.canonical_point_id)
                          OR eq.node_id = n.id
                        )
                    ), '[]'::jsonb) AS reaction_features,
                    '[]'::jsonb AS condition_tags,
                    '[]'::jsonb AS phenomenon_tags,
                    '[]'::jsonb AS property_tags
                ) chemistry ON TRUE
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
                    AND COALESCE(mb.metadata->>'placeholder_video', 'false') <> 'true'
                    AND COALESCE(mb.metadata->>'coverage_kind', ma.metadata->>'seed_kind', '') <> 'placeholder_video'
                    AND COALESCE(ma.original_file_name, '') <> 'no-video-placeholder.mp4'
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
                {limit_clause}
                """
            ),
            params,
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def _list_text(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    return []


def _row_haystack(row: dict[str, Any]) -> str:
    values: list[str] = [
        _clean_text(row.get("point_title")),
        _clean_text(row.get("point_summary")),
        _clean_text(row.get("snippet")),
        _clean_text(row.get("principle_equation")),
        _clean_text(row.get("principle_text")),
        _clean_text(row.get("phenomenon_explanation")),
        _clean_text(row.get("media_title")),
        *_path_titles(row.get("catalog_path")),
        *_list_text(row.get("reaction_features")),
        *_list_text(row.get("condition_tags")),
        *_list_text(row.get("phenomenon_tags")),
        *_list_text(row.get("property_tags")),
    ]
    return " ".join(value for value in values if value).lower()


def _topic_rows(rows: list[dict[str, Any]], topic: str, states: dict[str, StudentVideoPersonalState]) -> list[dict[str, Any]]:
    if topic == WATCH_LATER_TOPIC:
        saved = [row for row in rows if states.get(_canonical_id(row), StudentVideoPersonalState()).watch_later]
        return sorted(saved, key=lambda row: states[_canonical_id(row)].watch_later_saved_at or "", reverse=True)
    if topic == FAVORITES_TOPIC:
        saved = [row for row in rows if states.get(_canonical_id(row), StudentVideoPersonalState()).favorite]
        return sorted(saved, key=lambda row: states[_canonical_id(row)].favorite_saved_at or "", reverse=True)
    if topic in {DISCOVER_TOPIC, ALL_TOPIC}:
        return rows
    terms = [str(term).lower() for term in TOPIC_BY_ID.get(topic, {}).get("terms") or []]
    if not terms:
        return rows
    return [row for row in rows if any(term in _row_haystack(row) for term in terms)]


def _ordered_rows_for_batch(rows: list[dict[str, Any]], *, topic: str, seed: str) -> list[dict[str, Any]]:
    if topic != DISCOVER_TOPIC:
        return rows
    decorated = [(random.Random(f"{seed}:{_canonical_id(row)}").random(), _canonical_id(row), row) for row in rows]
    return [row for _score, _identity, row in sorted(decorated)]


def _slice_rows(
    rows: list[dict[str, Any]],
    *,
    topic: str,
    limit: int,
    cursor: str | None,
) -> tuple[list[tuple[dict[str, Any], int, int]], str | None, bool, str, int, str]:
    pool_hash = _pool_hash(rows)
    decoded = _cursor_decode(cursor, topic=topic, pool_hash=pool_hash)
    seed = str(decoded.get("seed") if decoded else "") or secrets.token_hex(4)
    offset = int(decoded.get("offset") if decoded else 0)
    repeat = topic == DISCOVER_TOPIC
    if not rows:
        return [], None, False, seed, 0, pool_hash
    ordered = _ordered_rows_for_batch(rows, topic=topic, seed=seed)
    batch: list[tuple[dict[str, Any], int, int]] = []
    if repeat:
        for absolute_offset in range(offset, offset + limit):
            cycle = absolute_offset // len(ordered)
            index = absolute_offset % len(ordered)
            batch.append((ordered[index], absolute_offset, cycle))
        next_cursor = _cursor_encode(
            {
                "version": CURSOR_VERSION,
                "topic": topic,
                "seed": seed,
                "offset": offset + limit,
                "cycle": (offset + limit) // len(ordered),
                "pool_hash": pool_hash,
            }
        )
        return batch, next_cursor, True, seed, offset, pool_hash
    sliced = ordered[offset : offset + limit]
    batch = [(row, offset + index, 0) for index, row in enumerate(sliced)]
    has_more = offset + len(sliced) < len(ordered)
    next_cursor = (
        _cursor_encode(
            {
                "version": CURSOR_VERSION,
                "topic": topic,
                "seed": seed,
                "offset": offset + len(sliced),
                "cycle": 0,
                "pool_hash": pool_hash,
            }
        )
        if has_more
        else None
    )
    return batch, next_cursor, has_more, seed, offset, pool_hash


def _feed_item(
    row: dict[str, Any],
    *,
    topic: str,
    seed: str,
    offset: int,
    cycle: int,
    personal_state: StudentVideoPersonalState,
) -> StudentHomeVideoFeedItem | None:
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
        instance_id=_instance_id(topic=topic, seed=seed, offset=offset, cycle=cycle, row=row),
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
        personal_state=personal_state,
        reason="recommended" if topic == DISCOVER_TOPIC else "catalog",
    )


def _build_feed_response(
    user: Any,
    *,
    topic: str,
    limit: int,
    cursor: str | None,
) -> StudentHomeVideoFeedResponse:
    safe_limit = max(1, min(limit, 30))
    with db_session() as session:
        all_rows = _feed_rows(session)
        keys = [(_clean_text(row.get("placement_node_id")), _clean_text(row.get("media_id"))) for row in all_rows]
        states = personal_states_for_items(session, user, keys)
        pool = _topic_rows(all_rows, topic, states)
        batch, next_cursor, has_more, seed, _base_offset, _hash = _slice_rows(pool, topic=topic, limit=safe_limit, cursor=cursor)
        items = [
            item
            for row, offset, cycle in batch
            if (
                item := _feed_item(
                    row,
                    topic=topic,
                    seed=seed,
                    offset=offset,
                    cycle=cycle,
                    personal_state=states.get(_canonical_id(row), StudentVideoPersonalState()),
                )
            )
        ]
    if not items:
        return StudentHomeVideoFeedResponse(
            status="empty",
            message="暂无可预览的实验视频，老师发布点位视频后会显示在首页。" if topic not in {WATCH_LATER_TOPIC, FAVORITES_TOPIC} else "这里暂时还没有保存的实验视频。",
            topic=topic,
            items=[],
            next_cursor=None,
            has_more=False,
            batch_size=safe_limit,
            pool_size=len(pool),
            repeat_mode="cycled" if topic == DISCOVER_TOPIC else "none",
        )
    return StudentHomeVideoFeedResponse(
        status="ok",
        topic=topic,
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        batch_size=safe_limit,
        pool_size=len(pool),
        repeat_mode="cycled" if topic == DISCOVER_TOPIC else "none",
    )


def student_home_video_feed(
    user: Any,
    *,
    topic: str | None = None,
    limit: int = 12,
    cursor: str | None = None,
) -> StudentHomeVideoFeedResponse:
    return _build_feed_response(user, topic=normalize_home_video_topic(topic), limit=limit, cursor=cursor)


def student_saved_video_feed(
    user: Any,
    *,
    save_type: str,
    limit: int = 12,
    cursor: str | None = None,
) -> StudentHomeVideoFeedResponse:
    topic = FAVORITES_TOPIC if save_type == "favorite" else WATCH_LATER_TOPIC
    return _build_feed_response(user, topic=topic, limit=limit, cursor=cursor)

from __future__ import annotations

import base64
import hashlib
import json
import re
from typing import Any

from sqlalchemy import text

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.domains.media.student_catalog_visibility import STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES
from server.app.domains.student_video_saves import personal_states_for_items
from server.app.infrastructure.database import db_session
from server.app.student_home_feed_schemas import (
    StudentHomeVideoFeedItem,
    StudentHomeVideoFeedResponse,
    StudentHomeVideoMedia,
    StudentHomeVideoRouteTarget,
)
from server.app.student_video_save_schemas import StudentVideoPersonalState


CURSOR_VERSION = 2
MAX_HOME_QUERY_LENGTH = 120
HOME_QUERY_SEPARATOR = re.compile(r"[-\s,，;；+→=/\\]+")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.strip()
        if cleaned and cleaned not in seen:
            result.append(cleaned)
            seen.add(cleaned)
    return result


def _path_titles(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def _list_text(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_home_video_query(query: str | None) -> tuple[str, list[str]]:
    raw = _clean_text(query)
    if len(raw) > MAX_HOME_QUERY_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Home video query must be at most {MAX_HOME_QUERY_LENGTH} characters",
        )
    tokens = [token for token in HOME_QUERY_SEPARATOR.split(raw.casefold()) if token]
    return " ".join(tokens), tokens


def _canonical_id(row: dict[str, Any]) -> str:
    return f"{_clean_text(row.get('placement_node_id'))}:{_clean_text(row.get('media_id'))}"


def _query_digest(*, scope: str, normalized_query: str) -> str:
    return hashlib.sha256(f"{scope}\0{normalized_query}".encode("utf-8")).hexdigest()


def _pool_revision(rows: list[dict[str, Any]]) -> str:
    revision_rows = [
        {
            "id": _canonical_id(row),
            "node_updated_at": row.get("node_updated_at"),
            "content_updated_at": row.get("content_updated_at"),
            "equations_updated_at": row.get("equations_updated_at"),
            "binding_updated_at": row.get("binding_updated_at"),
            "media_updated_at": row.get("media_updated_at"),
            "recommended": bool(row.get("is_recommended")),
            "recommended_order": row.get("recommended_order"),
            "recommended_updated_at": row.get("recommended_updated_at"),
            "favorite_saved_at": row.get("favorite_saved_at"),
        }
        for row in rows
    ]
    raw = json.dumps(revision_rows, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _cursor_encode(*, query_digest: str, pool_revision: str, offset: int) -> str:
    payload = {
        "version": CURSOR_VERSION,
        "query_digest": query_digest,
        "pool_revision": pool_revision,
        "offset": offset,
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _invalid_cursor() -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or stale Home video feed cursor")


def _cursor_offset(
    cursor: str | None,
    *,
    query_digest: str,
    pool_revision: str,
    pool_size: int,
) -> int:
    if not cursor:
        return 0
    if len(cursor) > 2048:
        raise _invalid_cursor()
    try:
        padded = cursor + ("=" * (-len(cursor) % 4))
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except Exception as exc:
        raise _invalid_cursor() from exc
    if not isinstance(payload, dict):
        raise _invalid_cursor()
    if payload.get("version") != CURSOR_VERSION:
        raise _invalid_cursor()
    if payload.get("query_digest") != query_digest or payload.get("pool_revision") != pool_revision:
        raise _invalid_cursor()
    offset = payload.get("offset")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise _invalid_cursor()
    if pool_size == 0 or offset >= pool_size:
        raise _invalid_cursor()
    return offset


def _catalog_order_path(value: Any) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(_safe_int(item) for item in value)


def _catalog_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    chapter_number = row.get("chapter_number")
    return (
        chapter_number is None,
        _safe_int(chapter_number),
        _clean_text(row.get("chapter_title")).casefold(),
        _catalog_order_path(row.get("catalog_order_path")),
        _safe_int(row.get("node_display_order")),
        _canonical_id(row),
    )


def _ordered_home_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    catalog_ordered = sorted(rows, key=_catalog_sort_key)
    recommendations = [row for row in catalog_ordered if bool(row.get("is_recommended"))]
    recommendations.sort(key=lambda row: _clean_text(row.get("recommended_updated_at")), reverse=True)
    recommendations.sort(key=lambda row: _safe_int(row.get("recommended_order")))
    ordinary = [row for row in catalog_ordered if not bool(row.get("is_recommended"))]
    return [*recommendations, *ordinary]


def _row_search_text(row: dict[str, Any]) -> str:
    values = [
        _clean_text(row.get("chapter_title")),
        *_path_titles(row.get("catalog_path")),
        _clean_text(row.get("node_title")),
        _clean_text(row.get("point_title")),
        _clean_text(row.get("point_summary")),
        _clean_text(row.get("snippet")),
        _clean_text(row.get("principle_equation")),
        _clean_text(row.get("principle_text")),
        _clean_text(row.get("phenomenon_explanation")),
        _clean_text(row.get("safety_note")),
        _clean_text(row.get("equation_search_text")),
        *_list_text(row.get("equation_formulae")),
        *_list_text(row.get("equation_aliases")),
        *_list_text(row.get("equation_reactants")),
        *_list_text(row.get("equation_products")),
        *_list_text(row.get("reaction_features")),
        *_list_text(row.get("condition_tags")),
        *_list_text(row.get("phenomenon_tags")),
        *_list_text(row.get("property_tags")),
    ]
    return " ".join(value for value in values if value).casefold()


def _matches_query(row: dict[str, Any], tokens: list[str]) -> bool:
    if not tokens:
        return True
    search_text = _row_search_text(row)
    return all(token in search_text for token in tokens)


def _feed_rows(session: Any) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                f"""
                WITH RECURSIVE {STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES}
                SELECT
                  placement.id AS node_id,
                  placement.id AS placement_node_id,
                  placement.canonical_point_id,
                  placement.chapter_id,
                  placement.title AS node_title,
                  placement.display_order AS node_display_order,
                  placement.updated_at AS node_updated_at,
                  chapter.chapter_title,
                  chapter.chapter_number,
                  COALESCE(content.point_title, placement.title) AS point_title,
                  COALESCE(placement.summary, '') AS point_summary,
                  COALESCE(
                    content.phenomenon_explanation,
                    content.principle_text,
                    content.principle_equation,
                    placement.summary,
                    ''
                  ) AS snippet,
                  COALESCE(content.principle_equation, '') AS principle_equation,
                  COALESCE(content.principle_text, '') AS principle_text,
                  COALESCE(content.phenomenon_explanation, '') AS phenomenon_explanation,
                  COALESCE(content.safety_note, '') AS safety_note,
                  content.updated_at AS content_updated_at,
                  COALESCE(chemistry.equation_search_text, '') AS equation_search_text,
                  COALESCE(chemistry.formulae, '[]'::jsonb) AS equation_formulae,
                  COALESCE(chemistry.aliases, '[]'::jsonb) AS equation_aliases,
                  COALESCE(chemistry.reactants, '[]'::jsonb) AS equation_reactants,
                  COALESCE(chemistry.products, '[]'::jsonb) AS equation_products,
                  COALESCE(chemistry.reaction_features, '[]'::jsonb) AS reaction_features,
                  chemistry.equations_updated_at,
                  '[]'::jsonb AS condition_tags,
                  '[]'::jsonb AS phenomenon_tags,
                  '[]'::jsonb AS property_tags,
                  COALESCE((
                    WITH RECURSIVE path AS (
                      SELECT id, parent_id, title, display_order, 0 AS depth
                      FROM experiment_catalog_nodes
                      WHERE id = placement.id
                      UNION ALL
                      SELECT parent.id, parent.parent_id, parent.title, parent.display_order, path.depth + 1
                      FROM experiment_catalog_nodes parent
                      JOIN path ON path.parent_id = parent.id
                    )
                    SELECT jsonb_agg(title ORDER BY depth DESC)
                    FROM path
                  ), '[]'::jsonb) AS catalog_path,
                  COALESCE((
                    WITH RECURSIVE path AS (
                      SELECT id, parent_id, display_order, 0 AS depth
                      FROM experiment_catalog_nodes
                      WHERE id = placement.id
                      UNION ALL
                      SELECT parent.id, parent.parent_id, parent.display_order, path.depth + 1
                      FROM experiment_catalog_nodes parent
                      JOIN path ON path.parent_id = parent.id
                    )
                    SELECT jsonb_agg(display_order ORDER BY depth DESC)
                    FROM path
                  ), '[]'::jsonb) AS catalog_order_path,
                  media.media_id,
                  media.media_title,
                  media.mime_type,
                  media.duration_seconds,
                  media.has_thumbnail,
                  media.binding_updated_at,
                  media.media_updated_at,
                  recommendation.placement_node_id IS NOT NULL AS is_recommended,
                  recommendation.sort_order AS recommended_order,
                  recommendation.updated_at AS recommended_updated_at
                FROM student_visible_placements visible_placement
                JOIN experiment_catalog_nodes placement
                  ON placement.id = visible_placement.placement_node_id
                JOIN chapters chapter
                  ON chapter.id = placement.chapter_id
                JOIN LATERAL (
                  SELECT
                    point_content.point_title,
                    point_content.principle_equation,
                    point_content.principle_text,
                    point_content.phenomenon_explanation,
                    point_content.safety_note,
                    point_content.updated_at
                  FROM experiment_catalog_point_content point_content
                  WHERE point_content.content_status = 'published'
                    AND (
                      point_content.canonical_point_id = placement.canonical_point_id
                      OR point_content.node_id = placement.id
                    )
                  ORDER BY
                    CASE WHEN point_content.canonical_point_id = placement.canonical_point_id THEN 0 ELSE 1 END,
                    point_content.updated_at DESC NULLS LAST,
                    point_content.node_id
                  LIMIT 1
                ) content ON TRUE
                LEFT JOIN LATERAL (
                  WITH equations AS (
                    SELECT equation.*
                    FROM experiment_catalog_point_reaction_equations equation
                    WHERE equation.validation_status <> 'invalid'
                      AND (
                        equation.canonical_point_id = placement.canonical_point_id
                        OR equation.node_id = placement.id
                      )
                  )
                  SELECT
                    COALESCE((
                      SELECT string_agg(
                        concat_ws(
                          ' ',
                          NULLIF(btrim(equation.plain_search_text), ''),
                          NULLIF(btrim(equation.canonical_display), ''),
                          NULLIF(btrim(equation.raw_text), '')
                        ),
                        ' ' ORDER BY equation.row_order, equation.id
                      )
                      FROM equations equation
                    ), '') AS equation_search_text,
                    COALESCE((
                      SELECT jsonb_agg(DISTINCT formula_item.value)
                      FROM equations equation
                      CROSS JOIN LATERAL jsonb_array_elements_text(COALESCE(equation.formulae, '[]'::jsonb)) AS formula_item(value)
                    ), '[]'::jsonb) AS formulae,
                    COALESCE((
                      SELECT jsonb_agg(DISTINCT alias_item.value)
                      FROM equations equation
                      CROSS JOIN LATERAL jsonb_array_elements_text(COALESCE(equation.aliases, '[]'::jsonb)) AS alias_item(value)
                    ), '[]'::jsonb) AS aliases,
                    COALESCE((
                      SELECT jsonb_agg(DISTINCT reactant_item.value)
                      FROM equations equation
                      CROSS JOIN LATERAL jsonb_array_elements_text(COALESCE(equation.reactants, '[]'::jsonb)) AS reactant_item(value)
                    ), '[]'::jsonb) AS reactants,
                    COALESCE((
                      SELECT jsonb_agg(DISTINCT product_item.value)
                      FROM equations equation
                      CROSS JOIN LATERAL jsonb_array_elements_text(COALESCE(equation.products, '[]'::jsonb)) AS product_item(value)
                    ), '[]'::jsonb) AS products,
                    COALESCE((
                      SELECT jsonb_agg(DISTINCT feature.value)
                      FROM equations equation
                      CROSS JOIN LATERAL jsonb_array_elements_text(COALESCE(equation.reaction_features, '[]'::jsonb)) AS feature(value)
                    ), '[]'::jsonb) AS reaction_features,
                    (SELECT max(equation.updated_at) FROM equations equation) AS equations_updated_at
                ) chemistry ON TRUE
                JOIN LATERAL (
                  SELECT
                    asset.id AS media_id,
                    COALESCE(binding.title, asset.title, asset.original_file_name, '') AS media_title,
                    COALESCE(playback.mime_type, asset.playback_mime_type, asset.mime_type) AS mime_type,
                    COALESCE(playback.duration_seconds, asset.duration_seconds) AS duration_seconds,
                    asset.thumbnail_relative_path IS NOT NULL AS has_thumbnail,
                    binding.updated_at AS binding_updated_at,
                    asset.updated_at AS media_updated_at
                  FROM student_visible_playable_media visible_media
                  JOIN experiment_catalog_point_media_bindings binding
                    ON binding.id = visible_media.binding_id
                  JOIN media_assets asset
                    ON asset.id = binding.media_asset_id
                  LEFT JOIN LATERAL (
                    SELECT rendition.mime_type, rendition.duration_seconds
                    FROM media_renditions rendition
                    WHERE rendition.media_asset_id = asset.id
                      AND rendition.status = 'ready'
                    ORDER BY
                      CASE WHEN rendition.kind = 'learning' THEN 0 ELSE 1 END,
                      rendition.created_at DESC,
                      rendition.id
                    LIMIT 1
                  ) playback ON TRUE
                  WHERE visible_media.placement_node_id = placement.id
                  ORDER BY binding.display_order, binding.created_at, asset.id
                  LIMIT 1
                ) media ON TRUE
                LEFT JOIN student_home_video_recommendations recommendation
                  ON recommendation.placement_node_id = placement.id
                ORDER BY
                  CASE WHEN recommendation.placement_node_id IS NULL THEN 1 ELSE 0 END,
                  recommendation.sort_order,
                  recommendation.updated_at DESC NULLS LAST,
                  chapter.chapter_number NULLS LAST,
                  chapter.chapter_title,
                  catalog_order_path,
                  placement.id
                """
            )
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def _feed_item(
    row: dict[str, Any],
    *,
    personal_state: StudentVideoPersonalState,
) -> StudentHomeVideoFeedItem | None:
    node_id = _clean_text(row.get("node_id"))
    placement_node_id = _clean_text(row.get("placement_node_id")) or node_id
    canonical_point_id = _clean_text(row.get("canonical_point_id"))
    chapter_id = _clean_text(row.get("chapter_id"))
    media_id = _clean_text(row.get("media_id"))
    title = _clean_text(row.get("point_title")) or _clean_text(row.get("node_title"))
    if not node_id or not placement_node_id or not canonical_point_id or not media_id or not title:
        return None
    catalog_path = _path_titles(row.get("catalog_path"))
    chapter_title = _clean_text(row.get("chapter_title"))
    badges = _unique([chapter_title, *catalog_path[-2:]])[:3]
    target = StudentHomeVideoRouteTarget(
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
    item_id = f"home-video:{placement_node_id}:{media_id}"
    return StudentHomeVideoFeedItem(
        id=item_id,
        instance_id=item_id,
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
        reason="recommended" if bool(row.get("is_recommended")) else "catalog",
    )


def _page_rows(
    rows: list[dict[str, Any]],
    *,
    scope: str,
    normalized_query: str,
    limit: int,
    cursor: str | None,
) -> tuple[list[dict[str, Any]], str | None, bool, int]:
    pool_revision = _pool_revision(rows)
    query_digest = _query_digest(scope=scope, normalized_query=normalized_query)
    offset = _cursor_offset(
        cursor,
        query_digest=query_digest,
        pool_revision=pool_revision,
        pool_size=len(rows),
    )
    batch = rows[offset : offset + limit]
    next_offset = offset + len(batch)
    has_more = next_offset < len(rows)
    next_cursor = (
        _cursor_encode(query_digest=query_digest, pool_revision=pool_revision, offset=next_offset)
        if has_more
        else None
    )
    return batch, next_cursor, has_more, len(rows)


def _response(
    *,
    query: str,
    rows: list[dict[str, Any]],
    states: dict[str, StudentVideoPersonalState],
    next_cursor: str | None,
    has_more: bool,
    batch_size: int,
    pool_size: int,
    empty_message: str,
) -> StudentHomeVideoFeedResponse:
    items = [
        item
        for row in rows
        if (
            item := _feed_item(
                row,
                personal_state=states.get(_canonical_id(row), StudentVideoPersonalState()),
            )
        )
    ]
    return StudentHomeVideoFeedResponse(
        status="ok" if items else "empty",
        message="" if items else empty_message,
        query=query,
        items=items,
        next_cursor=next_cursor if items else None,
        has_more=has_more if items else False,
        batch_size=batch_size,
        pool_size=pool_size,
    )


def student_home_video_feed(
    user: Any,
    *,
    query: str | None = None,
    limit: int = 12,
    cursor: str | None = None,
) -> StudentHomeVideoFeedResponse:
    normalized_query, tokens = normalize_home_video_query(query)
    safe_limit = max(1, min(int(limit), 30))
    with db_session() as session:
        ordered = _ordered_home_rows(_feed_rows(session))
        pool = [row for row in ordered if _matches_query(row, tokens)]
        batch, next_cursor, has_more, pool_size = _page_rows(
            pool,
            scope="home",
            normalized_query=normalized_query,
            limit=safe_limit,
            cursor=cursor,
        )
        keys = [
            (_clean_text(row.get("placement_node_id")), _clean_text(row.get("media_id")))
            for row in batch
        ]
        states = personal_states_for_items(session, user, keys)
    return _response(
        query=normalized_query,
        rows=batch,
        states=states,
        next_cursor=next_cursor,
        has_more=has_more,
        batch_size=safe_limit,
        pool_size=pool_size,
        empty_message="暂无符合条件的实验视频。" if tokens else "暂无可预览的实验视频，老师发布点位视频后会显示在首页。",
    )


def student_saved_video_feed(
    user: Any,
    *,
    limit: int = 12,
    cursor: str | None = None,
) -> StudentHomeVideoFeedResponse:
    safe_limit = max(1, min(int(limit), 30))
    with db_session() as session:
        all_rows = _ordered_home_rows(_feed_rows(session))
        all_keys = [
            (_clean_text(row.get("placement_node_id")), _clean_text(row.get("media_id")))
            for row in all_rows
        ]
        states = personal_states_for_items(session, user, all_keys)
        pool = [
            {**row, "favorite_saved_at": states[_canonical_id(row)].favorite_saved_at}
            for row in all_rows
            if states.get(_canonical_id(row), StudentVideoPersonalState()).favorite
        ]
        pool.sort(key=_canonical_id)
        pool.sort(key=lambda row: _clean_text(row.get("favorite_saved_at")), reverse=True)
        batch, next_cursor, has_more, pool_size = _page_rows(
            pool,
            scope="favorites",
            normalized_query="",
            limit=safe_limit,
            cursor=cursor,
        )
    return _response(
        query="",
        rows=batch,
        states=states,
        next_cursor=next_cursor,
        has_more=has_more,
        batch_size=safe_limit,
        pool_size=pool_size,
        empty_message="这里暂时还没有收藏的实验视频。",
    )

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import text

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.domains.catalog_tree.equations import list_reaction_equations, reaction_principle_text


NODE_KINDS = {"directory", "point"}
POINT_KINDS = {"point"}
MISSING_LEARNING_FIELD_LABELS = {
    "principle": "实验原理",
    "phenomenon": "现象解释",
    "safety": "安全提示",
}
MISSING_LEARNING_FIELD_KEYS = tuple(MISSING_LEARNING_FIELD_LABELS.keys())


def json_dump(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def dump_model(model: Any) -> dict[str, Any]:
    return model.model_dump() if hasattr(model, "model_dump") else dict(model)


def clean(value: Any) -> str:
    return str(value or "").strip()


def new_node_id() -> str:
    return f"cat-node-{uuid.uuid4().hex}"


def new_canonical_point_id() -> str:
    return f"cat-canon-{uuid.uuid4().hex}"


def point_capable(node: dict[str, Any]) -> bool:
    return str(node.get("node_kind") or "") in POINT_KINDS


def actions_for_kind(kind: str) -> list[str]:
    if kind == "directory":
        return ["open_directory"]
    if kind == "point":
        return ["open_point"]
    return []


def derived_point_summary(node: dict[str, Any], content: dict[str, Any] | None = None) -> str:
    source = content or {
        "phenomenon_explanation": node.get("point_phenomenon_explanation"),
        "principle_mode": node.get("point_principle_mode"),
        "principle_equation": node.get("point_principle_equation"),
        "principle_text": node.get("point_principle_text"),
        "safety_note": node.get("point_safety_note"),
    }
    for value in (
        source.get("phenomenon_explanation"),
        reaction_principle_text(source) if source.get("principle_mode") == "equation" else source.get("principle_text"),
        source.get("safety_note"),
    ):
        text_value = clean(value)
        if text_value:
            return text_value[:160]
    return ""


def node_select(where_clause: str) -> str:
    return f"""
        SELECT
          n.id AS node_id,
          n.chapter_id,
          c.chapter_title,
          n.parent_id,
          n.node_kind,
          n.title,
          n.summary,
          n.teacher_note,
          n.canonical_point_id,
          cp.title AS canonical_point_title,
          cp.status AS canonical_point_status,
          pc_summary.content_status AS point_content_status,
          pc_summary.principle_mode AS point_principle_mode,
          pc_summary.principle_equation AS point_principle_equation,
          pc_summary.principle_text AS point_principle_text,
          pc_summary.phenomenon_explanation AS point_phenomenon_explanation,
          pc_summary.safety_note AS point_safety_note,
          n.status,
          n.display_order,
          n.metadata,
          n.published_at,
          n.created_at,
          n.updated_at,
          EXISTS (
            SELECT 1 FROM experiment_catalog_nodes child
            WHERE child.parent_id = n.id AND child.status <> 'archived'
          ) AS has_children,
          CASE
            WHEN n.node_kind = 'directory' THEN (
              WITH RECURSIVE descendant_tree AS (
                SELECT child.id, child.parent_id, child.node_kind
                FROM experiment_catalog_nodes child
                WHERE child.parent_id = n.id
                  AND child.status <> 'archived'
                UNION ALL
                SELECT child.id, child.parent_id, child.node_kind
                FROM experiment_catalog_nodes child
                JOIN descendant_tree parent ON child.parent_id = parent.id
                WHERE child.status <> 'archived'
              )
              SELECT COUNT(*)
              FROM descendant_tree
              WHERE node_kind = 'point'
            )
            ELSE 0
          END AS descendant_point_count,
          EXISTS (
            SELECT 1 FROM experiment_catalog_point_content pc
            WHERE (n.canonical_point_id IS NOT NULL AND pc.canonical_point_id = n.canonical_point_id)
               OR pc.node_id = n.id
          ) AS has_point_content,
          (
            SELECT CASE WHEN EXISTS (
              SELECT 1
              FROM experiment_catalog_point_media_bindings mb
              JOIN media_assets ma ON ma.id = mb.media_asset_id
              WHERE ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                  OR mb.node_id = n.id)
                AND mb.binding_status <> 'archived'
                AND COALESCE(ma.lifecycle_status, 'active') = 'active'
            ) THEN 1 ELSE 0 END
          ) AS media_count,
          (
            SELECT CASE WHEN EXISTS (
              SELECT 1
              FROM experiment_catalog_point_media_bindings mb
              JOIN media_assets ma ON ma.id = mb.media_asset_id
              WHERE ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                  OR mb.node_id = n.id)
                AND mb.binding_status <> 'archived'
                AND ma.upload_status = 'ready'
                AND COALESCE(ma.lifecycle_status, 'active') = 'active'
            ) THEN 1 ELSE 0 END
          ) AS published_media_count,
          CASE
            WHEN n.node_kind = 'point' AND n.canonical_point_id IS NOT NULL THEN (
              SELECT COUNT(*)
              FROM experiment_catalog_nodes placement
              WHERE placement.canonical_point_id = n.canonical_point_id
                AND placement.node_kind = 'point'
                AND placement.status <> 'archived'
            )
            ELSE 0
          END AS active_placement_count,
          (
            SELECT to_jsonb(s)
            FROM experiment_catalog_point_search_index_state s
            WHERE s.node_id = n.id
          ) AS index_state,
          (
            SELECT to_jsonb(es)
            FROM experiment_catalog_point_evidence_state es
            WHERE (n.canonical_point_id IS NOT NULL AND es.canonical_point_id = n.canonical_point_id)
               OR es.node_id = n.id
            ORDER BY
              CASE WHEN n.canonical_point_id IS NOT NULL AND es.canonical_point_id = n.canonical_point_id THEN 0 ELSE 1 END,
              es.updated_at DESC
            LIMIT 1
          ) AS evidence_state,
          CASE
            WHEN n.node_kind = 'directory' THEN (
              WITH RECURSIVE descendant_tree AS (
                SELECT child.id, child.parent_id, child.node_kind, child.status, child.canonical_point_id
                FROM experiment_catalog_nodes child
                WHERE child.parent_id = n.id
                  AND child.status <> 'archived'
                UNION ALL
                SELECT child.id, child.parent_id, child.node_kind, child.status, child.canonical_point_id
                FROM experiment_catalog_nodes child
                JOIN descendant_tree parent ON child.parent_id = parent.id
                WHERE child.status <> 'archived'
              )
              SELECT jsonb_build_object(
                'blocked', COALESCE(COUNT(*) FILTER (
                  WHERE dt.node_kind = 'point'
                    AND dt.canonical_point_id IS NULL
                ), 0),
                'needs_content', COALESCE(COUNT(*) FILTER (
                  WHERE dt.node_kind = 'point'
                    AND dt.canonical_point_id IS NOT NULL
                    AND (
                      dpc.content_id IS NULL
                      OR
                      CASE
                        WHEN COALESCE(NULLIF(trim(dpc.principle_mode), ''), 'text') = 'equation'
                          THEN COALESCE(NULLIF(trim(dpc.principle_equation), ''), '') = ''
                        ELSE COALESCE(NULLIF(trim(dpc.principle_text), ''), '') = ''
                      END
                      OR COALESCE(NULLIF(trim(dpc.phenomenon_explanation), ''), '') = ''
                      OR COALESCE(NULLIF(trim(dpc.safety_note), ''), '') = ''
                    )
                ), 0),
                'needs_video', COALESCE(COUNT(*) FILTER (
                  WHERE dt.node_kind = 'point'
                    AND dt.canonical_point_id IS NOT NULL
                    AND dpc.content_id IS NOT NULL
                    AND NOT (
                      CASE
                        WHEN COALESCE(NULLIF(trim(dpc.principle_mode), ''), 'text') = 'equation'
                          THEN COALESCE(NULLIF(trim(dpc.principle_equation), ''), '') = ''
                        ELSE COALESCE(NULLIF(trim(dpc.principle_text), ''), '') = ''
                      END
                      OR COALESCE(NULLIF(trim(dpc.phenomenon_explanation), ''), '') = ''
                      OR COALESCE(NULLIF(trim(dpc.safety_note), ''), '') = ''
                    )
                    AND COALESCE(dmb.media_count, 0) = 0
                ), 0),
                'draft', COALESCE(COUNT(*) FILTER (
                  WHERE FALSE
                ), 0),
                'ready', COALESCE(COUNT(*) FILTER (
                  WHERE dt.node_kind = 'point'
                    AND dt.canonical_point_id IS NOT NULL
                    AND dpc.content_id IS NOT NULL
                    AND NOT (
                      CASE
                        WHEN COALESCE(NULLIF(trim(dpc.principle_mode), ''), 'text') = 'equation'
                          THEN COALESCE(NULLIF(trim(dpc.principle_equation), ''), '') = ''
                        ELSE COALESCE(NULLIF(trim(dpc.principle_text), ''), '') = ''
                      END
                      OR COALESCE(NULLIF(trim(dpc.phenomenon_explanation), ''), '') = ''
                      OR COALESCE(NULLIF(trim(dpc.safety_note), ''), '') = ''
                    )
                    AND COALESCE(dmb.media_count, 0) > 0
                    AND (
                      COALESCE(dpc.content_status, '') <> 'published'
                      OR (
                        COALESCE(dpc.content_status, '') = 'published'
                        AND dt.status <> 'published'
                      )
                    )
                ), 0),
                'sync_attention', COALESCE(COUNT(*) FILTER (
                  WHERE dt.node_kind = 'point'
                    AND dt.status = 'published'
                    AND dt.canonical_point_id IS NOT NULL
                    AND dpc.content_id IS NOT NULL
                    AND COALESCE(dpc.content_status, '') = 'published'
                    AND COALESCE(dmb.media_count, 0) > 0
                    AND NOT (
                      CASE
                        WHEN COALESCE(NULLIF(trim(dpc.principle_mode), ''), 'text') = 'equation'
                          THEN COALESCE(NULLIF(trim(dpc.principle_equation), ''), '') = ''
                        ELSE COALESCE(NULLIF(trim(dpc.principle_text), ''), '') = ''
                      END
                      OR COALESCE(NULLIF(trim(dpc.phenomenon_explanation), ''), '') = ''
                      OR COALESCE(NULLIF(trim(dpc.safety_note), ''), '') = ''
                    )
                    AND (
                      COALESCE(dsi.sync_status, '') IN ('failed', 'unavailable')
                      OR COALESCE(dev.evidence_status, '') IN ('failed', 'unavailable')
                    )
                ), 0),
                'published', COALESCE(COUNT(*) FILTER (
                  WHERE dt.node_kind = 'point'
                    AND dt.status = 'published'
                    AND dt.canonical_point_id IS NOT NULL
                    AND dpc.content_id IS NOT NULL
                    AND COALESCE(dpc.content_status, '') = 'published'
                    AND COALESCE(dmb.media_count, 0) > 0
                    AND NOT (
                      CASE
                        WHEN COALESCE(NULLIF(trim(dpc.principle_mode), ''), 'text') = 'equation'
                          THEN COALESCE(NULLIF(trim(dpc.principle_equation), ''), '') = ''
                        ELSE COALESCE(NULLIF(trim(dpc.principle_text), ''), '') = ''
                      END
                      OR COALESCE(NULLIF(trim(dpc.phenomenon_explanation), ''), '') = ''
                      OR COALESCE(NULLIF(trim(dpc.safety_note), ''), '') = ''
                    )
                    AND NOT (
                      COALESCE(dsi.sync_status, '') IN ('failed', 'unavailable')
                      OR COALESCE(dev.evidence_status, '') IN ('failed', 'unavailable')
                    )
                ), 0),
                'missing_principle', COALESCE(COUNT(*) FILTER (
                  WHERE dt.node_kind = 'point'
                    AND dt.canonical_point_id IS NOT NULL
                    AND (
                      dpc.content_id IS NULL
                      OR CASE
                        WHEN COALESCE(NULLIF(trim(dpc.principle_mode), ''), 'text') = 'equation'
                          THEN COALESCE(NULLIF(trim(dpc.principle_equation), ''), '') = ''
                        ELSE COALESCE(NULLIF(trim(dpc.principle_text), ''), '') = ''
                      END
                    )
                ), 0),
                'missing_phenomenon', COALESCE(COUNT(*) FILTER (
                  WHERE dt.node_kind = 'point'
                    AND dt.canonical_point_id IS NOT NULL
                    AND (
                      dpc.content_id IS NULL
                      OR COALESCE(NULLIF(trim(dpc.phenomenon_explanation), ''), '') = ''
                    )
                ), 0),
                'missing_safety', COALESCE(COUNT(*) FILTER (
                  WHERE dt.node_kind = 'point'
                    AND dt.canonical_point_id IS NOT NULL
                    AND (
                      dpc.content_id IS NULL
                      OR COALESCE(NULLIF(trim(dpc.safety_note), ''), '') = ''
                    )
                ), 0)
              )
              FROM descendant_tree dt
              LEFT JOIN LATERAL (
                SELECT pc.node_id AS content_id,
                       pc.content_status,
                       pc.principle_mode,
                       pc.principle_equation,
                       pc.principle_text,
                       pc.phenomenon_explanation,
                       pc.safety_note
                FROM experiment_catalog_point_content pc
                WHERE (dt.canonical_point_id IS NOT NULL AND pc.canonical_point_id = dt.canonical_point_id)
                   OR pc.node_id = dt.id
                ORDER BY
                  CASE WHEN pc.canonical_point_id = dt.canonical_point_id THEN 0 ELSE 1 END,
                  CASE pc.content_status WHEN 'published' THEN 0 WHEN 'draft' THEN 1 ELSE 2 END,
                  pc.updated_at DESC
                LIMIT 1
              ) dpc ON TRUE
              LEFT JOIN LATERAL (
                SELECT COUNT(*) AS media_count
                FROM experiment_catalog_point_media_bindings mb
                JOIN media_assets ma ON ma.id = mb.media_asset_id
                WHERE ((dt.canonical_point_id IS NOT NULL AND mb.canonical_point_id = dt.canonical_point_id)
                    OR mb.node_id = dt.id)
                  AND mb.binding_status <> 'archived'
                  AND ma.upload_status = 'ready'
                  AND COALESCE(ma.lifecycle_status, 'active') = 'active'
              ) dmb ON TRUE
              LEFT JOIN experiment_catalog_point_search_index_state dsi ON dsi.node_id = dt.id
              LEFT JOIN LATERAL (
                SELECT es.evidence_status
                FROM experiment_catalog_point_evidence_state es
                WHERE (dt.canonical_point_id IS NOT NULL AND es.canonical_point_id = dt.canonical_point_id)
                   OR es.node_id = dt.id
                ORDER BY
                  CASE WHEN dt.canonical_point_id IS NOT NULL AND es.canonical_point_id = dt.canonical_point_id THEN 0 ELSE 1 END,
                  es.updated_at DESC
                LIMIT 1
              ) dev ON TRUE
            )
            ELSE '{{}}'::jsonb
          END AS descendant_status_counts
        FROM experiment_catalog_nodes n
        JOIN chapters c ON c.id = n.chapter_id
        LEFT JOIN experiment_catalog_points cp ON cp.id = n.canonical_point_id
        LEFT JOIN LATERAL (
          SELECT pc.content_status,
                 pc.principle_mode,
                 pc.principle_equation,
                 pc.principle_text,
                 pc.phenomenon_explanation,
                 pc.safety_note
          FROM experiment_catalog_point_content pc
          WHERE (n.canonical_point_id IS NOT NULL AND pc.canonical_point_id = n.canonical_point_id)
             OR pc.node_id = n.id
          ORDER BY
            CASE WHEN pc.canonical_point_id = n.canonical_point_id THEN 0 ELSE 1 END,
            CASE pc.content_status WHEN 'published' THEN 0 WHEN 'draft' THEN 1 ELSE 2 END,
            pc.updated_at DESC
          LIMIT 1
        ) pc_summary ON TRUE
        {where_clause}
    """


def row_dict(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["node_id"] = str(item.get("node_id") or item.get("id") or "")
    item["descendant_point_count"] = int(item.get("descendant_point_count") or 0)
    item["media_count"] = int(item.get("media_count") or 0)
    item["published_media_count"] = int(item.get("published_media_count") or 0)
    item["active_placement_count"] = int(item.get("active_placement_count") or 0)
    for key in ("metadata",):
        if not isinstance(item.get(key), dict):
            item[key] = {}
    if item.get("index_state") is not None and not isinstance(item.get("index_state"), dict):
        item["index_state"] = dict(item["index_state"])
    if item.get("evidence_state") is not None and not isinstance(item.get("evidence_state"), dict):
        item["evidence_state"] = dict(item["evidence_state"])
    if not isinstance(item.get("descendant_status_counts"), dict):
        item["descendant_status_counts"] = {}
    return item


def _status_condition(
    key: str,
    *,
    group: str,
    severity: str,
    status_value: str,
    reason: str,
    message: str,
    action: str | None = None,
) -> dict[str, Any]:
    return {
        "key": key,
        "group": group,
        "severity": severity,
        "status": status_value,
        "reason": reason,
        "message": message,
        "action": action,
    }


def _content_source(node: dict[str, Any], content: dict[str, Any] | None) -> dict[str, Any]:
    if content:
        return content
    return {
        "content_status": node.get("point_content_status"),
        "principle_mode": node.get("point_principle_mode"),
        "principle_equation": node.get("point_principle_equation"),
        "principle_text": node.get("point_principle_text"),
        "phenomenon_explanation": node.get("point_phenomenon_explanation"),
        "safety_note": node.get("point_safety_note"),
    }


def _has_saved_content(node: dict[str, Any], content: dict[str, Any] | None, source: dict[str, Any]) -> bool:
    return bool(content or node.get("has_point_content") or source.get("content_status"))


def _principle_complete(content: dict[str, Any]) -> bool:
    mode = clean(content.get("principle_mode") or "text")
    if mode == "equation":
        return bool(reaction_principle_text(content))
    if mode == "text":
        return bool(clean(content.get("principle_text")))
    return False


def _missing_learning_field_keys(content: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not _principle_complete(content):
        missing.append("principle")
    if not clean(content.get("phenomenon_explanation")):
        missing.append("phenomenon")
    if not clean(content.get("safety_note")):
        missing.append("safety")
    return missing


def _missing_learning_field_labels(keys: list[str]) -> list[str]:
    return [MISSING_LEARNING_FIELD_LABELS[key] for key in keys if key in MISSING_LEARNING_FIELD_LABELS]


def _missing_learning_fields(content: dict[str, Any]) -> list[str]:
    return _missing_learning_field_labels(_missing_learning_field_keys(content))


def _map_search_index_state(index_state: dict[str, Any] | None) -> str:
    if not index_state:
        return "idle"
    status_value = clean(index_state.get("sync_status"))
    if status_value == "synced":
        return "synced"
    if status_value in {"pending", "running", "stale", "failed", "disabled", "unavailable"}:
        return status_value
    return status_value or "idle"


def _map_ai_evidence_state(evidence_state: dict[str, Any] | None) -> str:
    if not evidence_state:
        return "idle"
    status_value = clean(evidence_state.get("evidence_status"))
    if status_value in {"succeeded", "available", "available_static_fallback"}:
        return "available"
    if status_value in {"pending", "running", "stale", "failed", "disabled", "unavailable"}:
        return status_value
    if status_value in {"missing", "missing_fallback_evidence"}:
        return "idle"
    if status_value == "stale_fallback_evidence":
        return "stale"
    return status_value or "idle"


def _primary_state_label(primary_state: str) -> str:
    labels = {
        "archived": "已归档",
        "blocked": "异常",
        "needs_content": "缺内容",
        "needs_video": "缺视频",
        "draft": "草稿",
        "ready": "待发布",
        "published": "已发布",
        "sync_attention": "同步异常",
    }
    return labels.get(primary_state, "未知状态")


def _directory_node_status(node: dict[str, Any]) -> dict[str, Any]:
    counts = node.get("descendant_status_counts") if isinstance(node.get("descendant_status_counts"), dict) else {}
    blocked = int(counts.get("blocked") or 0)
    needs_content = int(counts.get("needs_content") or 0)
    needs_video = int(counts.get("needs_video") or 0)
    draft = int(counts.get("draft") or 0)
    ready = int(counts.get("ready") or 0)
    published = int(counts.get("published") or 0)
    sync_attention = int(counts.get("sync_attention") or 0)
    descendant_missing_field_counts = {
        "principle": int(counts.get("missing_principle") or 0),
        "phenomenon": int(counts.get("missing_phenomenon") or 0),
        "safety": int(counts.get("missing_safety") or 0),
    }
    actionable_count = blocked + needs_content + needs_video + ready + draft + sync_attention
    conditions: list[dict[str, Any]] = []
    if blocked:
        conditions.append(
            _status_condition(
                "directory_descendant_blocked",
                group="visibility",
                severity="error",
                status_value="blocked",
                reason=f"{blocked} 个后代点位结构异常",
                message=f"目录下有 {blocked} 个点位缺少实验身份，无法稳定复用共享实验。",
                action="定位并修正点位身份",
            )
        )
    if needs_content:
        conditions.append(
            _status_condition(
                "directory_descendant_needs_content",
                group="core_readiness",
                severity="warning",
                status_value="needs_content",
                reason=f"{needs_content} 个后代点位缺内容",
                message=f"目录下有 {needs_content} 个点位需要补齐原理、现象解释或安全提示。",
                action="筛选缺内容点位",
            )
        )
    if needs_video:
        conditions.append(
            _status_condition(
                "directory_descendant_needs_video",
                group="core_readiness",
                severity="warning",
                status_value="needs_video",
                reason=f"{needs_video} 个后代点位缺视频",
                message=f"目录下有 {needs_video} 个点位尚未绑定实验视频。",
                action="筛选缺视频点位",
            )
        )
    if draft:
        conditions.append(
            _status_condition(
                "directory_descendant_draft",
                group="visibility",
                severity="info",
                status_value="draft",
                reason=f"{draft} 个后代点位未发布",
                message=f"目录下有 {draft} 个点位内容完整但尚未学生可见。",
                action="筛选待发布点位",
            )
        )
    if ready:
        conditions.append(
            _status_condition(
                "directory_descendant_ready",
                group="visibility",
                severity="info",
                status_value="ready",
                reason=f"{ready} 个后代点位待发布",
                message=f"目录下有 {ready} 个点位内容已可发布，但尚未学生可见。",
                action="筛选待发布点位",
            )
        )
    if sync_attention:
        conditions.append(
            _status_condition(
                "directory_descendant_sync_attention",
                group="async_consumption",
                severity="warning",
                status_value="sync_attention",
                reason=f"{sync_attention} 个后代点位同步异常",
                message=f"目录下有 {sync_attention} 个已发布点位存在搜索或 AI 证据同步异常。",
                action="筛选同步异常",
            )
        )
    if clean(node.get("status")) == "archived":
        primary_state = "archived"
        primary_reason = "目录已归档"
    elif blocked:
        primary_state = "blocked"
        primary_reason = f"{blocked} 个后代点位结构异常"
    elif needs_content:
        primary_state = "needs_content"
        primary_reason = f"{needs_content} 个后代点位缺内容"
    elif needs_video:
        primary_state = "needs_video"
        primary_reason = f"{needs_video} 个后代点位缺视频"
    elif clean(node.get("status")) != "published":
        primary_state = "draft"
        primary_reason = "目录尚未发布"
    elif ready or draft:
        primary_state = "ready"
        primary_reason = f"{ready + draft} 个后代点位待发布"
    elif sync_attention:
        primary_state = "sync_attention"
        primary_reason = f"{sync_attention} 个后代点位同步异常"
    else:
        primary_state = "published"
        primary_reason = "目录已发布"
    return {
        "primary_state": primary_state,
        "primary_label": _primary_state_label(primary_state),
        "primary_reason": primary_reason,
        "core_readiness": {
            "content_fields": "not_applicable",
            "video": "not_applicable",
            "missing_field_keys": [],
            "missing_field_labels": [],
            "missing_fields": [],
            "descendant_action_count": actionable_count,
            "descendant_status_counts": {
                "blocked": blocked,
                "needs_content": needs_content,
                "needs_video": needs_video,
                "ready": ready,
                "draft": draft,
                "published": published,
                "sync_attention": sync_attention,
            },
            "descendant_missing_field_counts": descendant_missing_field_counts,
        },
        "visibility": {
            "placement": clean(node.get("status")) or "draft",
            "shared_content": "not_applicable",
            "student_available": clean(node.get("status")) == "published",
        },
        "async_consumption": {
            "search_index": "not_applicable",
            "ai_evidence": "not_applicable",
        },
        "conditions": conditions,
    }


def catalog_node_status_summary(
    node: dict[str, Any],
    *,
    content: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
    job_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not point_capable(node):
        return _directory_node_status(node)

    content_source = _content_source(node, content)
    content_exists = _has_saved_content(node, content, content_source)
    missing_field_keys = _missing_learning_field_keys(content_source)
    missing_fields = _missing_learning_field_labels(missing_field_keys)
    validation = validation if validation is not None else validate_node_payload(node, content if content_exists else None)
    placement_state = clean(node.get("status")) or "draft"
    shared_content_state = "missing"
    if content_exists:
        shared_content_state = clean(content_source.get("content_status")) or "draft"
    if clean(node.get("canonical_point_status")) == "archived":
        shared_content_state = "archived"
    video_present = int(node.get("published_media_count") or 0) > 0
    index_state = (job_state or {}).get("es_state") if job_state else node.get("index_state")
    evidence_state = (job_state or {}).get("evidence_state") if job_state else node.get("evidence_state")
    search_state = _map_search_index_state(index_state if isinstance(index_state, dict) else None)
    ai_state = _map_ai_evidence_state(evidence_state if isinstance(evidence_state, dict) else None)
    student_available = placement_state == "published" and shared_content_state == "published" and not validation.get("errors")
    conditions: list[dict[str, Any]] = []

    if placement_state == "archived" or shared_content_state == "archived":
        conditions.append(
            _status_condition(
                "point_archived",
                group="visibility",
                severity="info",
                status_value="archived",
                reason="点位已归档",
                message="此点位已从常规目录中隐藏。",
                action="如需继续维护，请先恢复节点",
            )
        )
    if validation.get("errors"):
        conditions.append(
            _status_condition(
                "point_structure_invalid",
                group="visibility",
                severity="error",
                status_value="blocked",
                reason="点位结构需要处理",
                message="点位目录身份或共享实验身份异常，暂不能发布。",
                action="检查节点身份和共享实验绑定",
            )
        )
    if not content_exists:
        conditions.append(
            _status_condition(
                "shared_content_missing",
                group="core_readiness",
                severity="warning",
                status_value="missing",
                reason="三要素尚未填写",
                message="学生端可先显示点位标题占位；进入视频前请先补齐原理、现象解释和安全提示。",
                action="先补齐三要素",
            )
        )
    elif missing_fields:
        conditions.append(
            _status_condition(
                "learning_fields_missing",
                group="core_readiness",
                severity="warning",
                status_value="missing",
                reason=f"缺少{ '、'.join(missing_fields) }",
                message=f"请补齐{ '、'.join(missing_fields) }。",
                action="补齐学习字段",
            )
        )
    if not video_present and not missing_fields:
        conditions.append(
            _status_condition(
                "experiment_video_missing",
                group="core_readiness",
                severity="warning",
                status_value="absent",
                reason="无视频",
                message="请为此点位添加实验视频。",
                action="绑定实验视频",
            )
        )
    if placement_state != "published" and placement_state != "archived":
        conditions.append(
            _status_condition(
                "placement_not_published",
                group="visibility",
                severity="info",
                status_value=placement_state,
                reason="目录位置未发布",
                message="当前目录位置仍是草稿，学生目录中暂不可见。",
                action="发布节点或所在目录",
            )
        )
    if content_exists and shared_content_state not in {"published", "archived"} and not missing_fields:
        conditions.append(
            _status_condition(
                "shared_content_not_published",
                group="visibility",
                severity="info",
                status_value=shared_content_state,
                reason="学习内容未发布",
                message="当前共享实验内容仍是草稿，学生端暂不可见。",
                action="发布学习内容",
            )
        )
    if search_state in {"failed", "unavailable"}:
        conditions.append(
            _status_condition(
                "search_index_attention",
                group="async_consumption",
                severity="warning",
                status_value=search_state,
                reason="搜索同步异常",
                message="学生搜索消费的 ES 文档同步失败或不可用。",
                action="在同步诊断中重试 ES 刷新",
            )
        )
    elif search_state in {"pending", "running", "stale"}:
        conditions.append(
            _status_condition(
                "search_index_pending",
                group="async_consumption",
                severity="info",
                status_value=search_state,
                reason="搜索同步处理中",
                message="ES 搜索文档仍在异步处理，可能短暂滞后于已保存内容。",
                action=None,
            )
        )
    if ai_state in {"failed", "unavailable"}:
        conditions.append(
            _status_condition(
                "ai_evidence_attention",
                group="async_consumption",
                severity="warning",
                status_value=ai_state,
                reason="AI 证据同步异常",
                message="AI/RAG 证据刷新失败或不可用，不影响点位内容继续编辑。",
                action="在同步诊断中重试 RAG 刷新",
            )
        )
    elif ai_state in {"pending", "running", "stale"}:
        conditions.append(
            _status_condition(
                "ai_evidence_pending",
                group="async_consumption",
                severity="info",
                status_value=ai_state,
                reason="AI 证据处理中",
                message="AI/RAG 证据仍在异步处理，可能滞后于已保存内容。",
                action=None,
            )
        )
    if placement_state == "archived" or shared_content_state == "archived":
        primary_state = "archived"
        primary_reason = "点位已归档"
    elif validation.get("errors"):
        primary_state = "blocked"
        primary_reason = "点位结构异常"
    elif missing_fields:
        primary_state = "needs_content"
        primary_reason = f"缺少{ '、'.join(missing_fields) }"
    elif not video_present:
        primary_state = "needs_video"
        primary_reason = "无视频"
    elif shared_content_state != "published":
        primary_state = "ready"
        primary_reason = "学习内容完整，等待发布学习内容"
    elif placement_state != "published":
        primary_state = "ready"
        primary_reason = "内容和视频完整，等待发布目录位置"
    elif search_state in {"failed", "unavailable"} or ai_state in {"failed", "unavailable"}:
        primary_state = "sync_attention"
        primary_reason = "搜索或 AI 同步异常"
    else:
        primary_state = "published"
        primary_reason = "学生可见"

    return {
        "primary_state": primary_state,
        "primary_label": _primary_state_label(primary_state),
        "primary_reason": primary_reason,
        "core_readiness": {
            "content_fields": "complete" if not missing_fields else "missing",
            "video": "present" if video_present else "absent",
            "video_label": "有视频" if video_present else "无视频",
            "missing_field_keys": missing_field_keys,
            "missing_field_labels": missing_fields,
            "missing_fields": missing_fields,
        },
        "visibility": {
            "placement": placement_state,
            "shared_content": shared_content_state,
            "student_available": student_available,
        },
        "async_consumption": {
            "search_index": search_state,
            "ai_evidence": ai_state,
        },
        "conditions": conditions,
    }


def node_card(
    node: dict[str, Any],
    *,
    content: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
    job_state: dict[str, Any] | None = None,
    include_teacher_note: bool = False,
) -> dict[str, Any]:
    kind = str(node.get("node_kind") or "directory")
    active_validation = validation if validation is not None else validate_node_payload(node, content)
    summary = clean(node.get("summary"))
    if kind == "point" and not summary:
        summary = derived_point_summary(node, content)
    media_count = 1 if int(node.get("media_count") or 0) > 0 else 0
    published_media_count = 1 if int(node.get("published_media_count") or 0) > 0 else 0
    card = {
        "node_id": node["node_id"],
        "chapter_id": node["chapter_id"],
        "parent_id": node.get("parent_id"),
        "node_kind": kind,
        "title": node.get("title") or "",
        "summary": summary,
        "placement_node_id": node["node_id"] if kind == "point" else None,
        "canonical_point_id": node.get("canonical_point_id") if kind == "point" else None,
        "canonical_point_title": node.get("canonical_point_title") if kind == "point" else None,
        "canonical_point_status": node.get("canonical_point_status") if kind == "point" else None,
        "status": node.get("status") or "draft",
        "display_order": int(node.get("display_order") or 0),
        "actions": actions_for_kind(kind),
        "has_children": bool(node.get("has_children")),
        "descendant_point_count": int(node.get("descendant_point_count") or 0) if kind == "directory" else 0,
        "has_point_content": bool(node.get("has_point_content")),
        "media_count": media_count,
        "published_media_count": published_media_count,
        "active_placement_count": int(node.get("active_placement_count") or 0) if kind == "point" else 0,
        "validation": active_validation,
        "node_status": catalog_node_status_summary(node, content=content, validation=active_validation, job_state=job_state),
        "index_state": node.get("index_state"),
    }
    if include_teacher_note:
        card["teacher_note"] = node.get("teacher_note") or ""
    return card


def get_node(session: Any, node_id: str, *, include_archived: bool = True) -> dict[str, Any]:
    status_filter = "" if include_archived else " AND n.status <> 'archived'"
    row = (
        session.execute(
            text(node_select(f"WHERE n.id = :node_id{status_filter}")),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog node not found")
    return row_dict(row)


def canonical_point_id_for_node(session: Any, node_id: str) -> str:
    row = (
        session.execute(
            text(
                """
                SELECT canonical_point_id
                FROM experiment_catalog_nodes
                WHERE id = :node_id
                  AND node_kind = 'point'
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    if not row or not row.get("canonical_point_id"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Catalog point placement has no canonical experiment point")
    return str(row["canonical_point_id"])


def active_placement_ids_for_canonical_point(session: Any, canonical_point_id: str) -> list[str]:
    return [
        str(row)
        for row in session.execute(
            text(
                """
                SELECT id
                FROM experiment_catalog_nodes
                WHERE canonical_point_id = :canonical_point_id
                  AND node_kind = 'point'
                  AND status <> 'archived'
                ORDER BY chapter_id, parent_id NULLS FIRST, display_order, id
                """
            ),
            {"canonical_point_id": canonical_point_id},
        )
        .scalars()
        .all()
    ]


def active_placements_for_canonical_point(session: Any, canonical_point_id: str) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(node_select(
                """
                WHERE n.canonical_point_id = :canonical_point_id
                  AND n.node_kind = 'point'
                  AND n.status <> 'archived'
                ORDER BY n.chapter_id, n.parent_id NULLS FIRST, n.display_order, n.id
                """
            )),
            {"canonical_point_id": canonical_point_id},
        )
        .mappings()
        .all()
    )
    return [row_dict(row) for row in rows]


def get_content(session: Any, node_id: str) -> dict[str, Any] | None:
    row = (
        session.execute(
            text(
                """
                SELECT pc.node_id, pc.canonical_point_id, pc.point_title, pc.teacher_note,
                       pc.principle_mode, pc.principle_equation,
                       principle_text, phenomenon_explanation, safety_note, content_status,
                       pc.published_at, pc.published_by, pc.created_by, pc.updated_by, pc.metadata,
                       pc.created_at, pc.updated_at
                FROM experiment_catalog_nodes n
                JOIN experiment_catalog_point_content pc
                  ON (
                    n.canonical_point_id IS NOT NULL
                    AND pc.canonical_point_id = n.canonical_point_id
                  )
                  OR pc.node_id = n.id
                WHERE n.id = :node_id
                ORDER BY
                  CASE WHEN pc.canonical_point_id = n.canonical_point_id THEN 0 ELSE 1 END,
                  CASE pc.content_status WHEN 'published' THEN 0 WHEN 'draft' THEN 1 ELSE 2 END,
                  pc.updated_at DESC
                LIMIT 1
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    if not row:
        return None
    item = dict(row)
    if not isinstance(item.get("metadata"), dict):
        item["metadata"] = {}
    item["reaction_equations"] = list_reaction_equations(session, node_id) if item.get("principle_mode") == "equation" else []
    return item


def content_publication_errors(node: dict[str, Any], content: dict[str, Any] | None) -> list[str]:
    errors: list[str] = []
    if not clean(node.get("title")):
        errors.append("Node title is required")
    if not point_capable(node):
        return errors
    if not clean(node.get("canonical_point_id")):
        errors.append("Point placement must target a canonical experiment before publishing")
    if node.get("has_children"):
        errors.append("Point nodes cannot have children")
    if not content:
        errors.append("Canonical point content must be saved before publishing")
        return errors
    mode = clean(content.get("principle_mode") or "text")
    equation = clean(content.get("principle_equation"))
    principle_text = clean(content.get("principle_text"))
    if mode == "equation":
        if not reaction_principle_text(content):
            errors.append("Equation-mode principle requires at least one valid reaction equation")
    elif mode == "text":
        if not principle_text:
            errors.append("Text-mode principle requires a principle description")
    else:
        errors.append("Principle mode must be equation or text")
    if not clean(content.get("phenomenon_explanation")):
        errors.append("Phenomenon explanation is required")
    if not clean(content.get("safety_note")):
        errors.append("Safety note is required")
    return errors


def validate_node_payload(node: dict[str, Any], content: dict[str, Any] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    kind = clean(node.get("node_kind"))
    if kind not in NODE_KINDS:
        errors.append("Node kind must be directory or point")
    if not clean(node.get("title")):
        errors.append("Title is required")
    if kind == "directory":
        if node.get("has_point_content") or int(node.get("media_count") or 0) > 0:
            errors.append("Directory nodes cannot own point content or videos")
        if not node.get("has_children"):
            warnings.append("Directory has no children")
    if kind == "point":
        if not clean(node.get("canonical_point_id")):
            errors.append("Point placement must target a canonical experiment point")
        if node.get("has_children"):
            errors.append("Point nodes cannot have children")
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def breadcrumbs(session: Any, node_id: str) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                """
                WITH RECURSIVE path AS (
                  SELECT id, chapter_id, parent_id, node_kind, title, 0 AS depth
                  FROM experiment_catalog_nodes
                  WHERE id = :node_id
                  UNION ALL
                  SELECT parent.id, parent.chapter_id, parent.parent_id, parent.node_kind, parent.title, path.depth + 1
                  FROM experiment_catalog_nodes parent
                  JOIN path ON path.parent_id = parent.id
                )
                SELECT id AS node_id, title, node_kind, chapter_id
                FROM path
                ORDER BY depth DESC
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def catalog_path_titles_with_chapter(
    node: dict[str, Any],
    path: list[dict[str, Any]],
    *,
    include_point: bool = True,
) -> list[str]:
    chapter_title = clean(node.get("chapter_title")) or clean(node.get("chapter_id"))
    titles: list[str] = []
    if chapter_title:
        titles.append(chapter_title)
    for item in path:
        if not include_point and item.get("node_kind") == "point":
            continue
        title = clean(item.get("title"))
        if title and title != chapter_title:
            titles.append(title)
    return titles


def catalog_path_text(session: Any, node_id: str) -> str:
    node = get_node(session, node_id, include_archived=True)
    return " / ".join(catalog_path_titles_with_chapter(node, breadcrumbs(session, node_id)))


def catalog_directory_path_text(session: Any, node_id: str) -> str:
    node = get_node(session, node_id, include_archived=True)
    return " / ".join(catalog_path_titles_with_chapter(node, breadcrumbs(session, node_id), include_point=False))


def published_path_available(session: Any, node_id: str) -> bool:
    return bool(
        session.execute(
            text(
                """
                WITH RECURSIVE path AS (
                  SELECT id, parent_id, status
                  FROM experiment_catalog_nodes
                  WHERE id = :node_id
                  UNION ALL
                  SELECT parent.id, parent.parent_id, parent.status
                  FROM experiment_catalog_nodes parent
                  JOIN path ON path.parent_id = parent.id
                )
                SELECT COALESCE(bool_and(status = 'published'), false)
                FROM path
                """
            ),
            {"node_id": node_id},
        ).scalar_one()
    )


def assert_no_parent_cycle(session: Any, *, node_id: str, new_parent_id: str | None) -> None:
    if not new_parent_id:
        return
    if node_id == new_parent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Node cannot be moved under itself")
    rows = (
        session.execute(
            text(
                """
                WITH RECURSIVE ancestors AS (
                  SELECT id, parent_id
                  FROM experiment_catalog_nodes
                  WHERE id = :parent_id
                  UNION ALL
                  SELECT parent.id, parent.parent_id
                  FROM experiment_catalog_nodes parent
                  JOIN ancestors ON ancestors.parent_id = parent.id
                )
                SELECT id FROM ancestors
                """
            ),
            {"parent_id": new_parent_id},
        )
        .scalars()
        .all()
    )
    if node_id in {str(row) for row in rows}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Move would create a catalog cycle")


def assert_parent_valid(session: Any, *, chapter_id: str, parent_id: str | None, node_id: str | None = None) -> None:
    if not parent_id:
        return
    parent = get_node(session, parent_id)
    if parent["chapter_id"] != chapter_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent must belong to the same chapter")
    if parent["node_kind"] != "directory":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Point nodes cannot have children")
    if node_id:
        assert_no_parent_cycle(session, node_id=node_id, new_parent_id=parent_id)


def max_child_order(session: Any, *, chapter_id: str, parent_id: str | None) -> int:
    if parent_id:
        value = session.execute(
            text("SELECT COALESCE(MAX(display_order), 0) FROM experiment_catalog_nodes WHERE parent_id = :parent_id"),
            {"parent_id": parent_id},
        ).scalar_one()
    else:
        value = session.execute(
            text("SELECT COALESCE(MAX(display_order), 0) FROM experiment_catalog_nodes WHERE chapter_id = :chapter_id AND parent_id IS NULL"),
            {"chapter_id": chapter_id},
        ).scalar_one()
    return int(value or 0)


def has_point_resources(session: Any, node_id: str) -> bool:
    return bool(
        session.execute(
            text(
                """
                SELECT EXISTS (
                  SELECT 1 FROM experiment_catalog_point_content WHERE node_id = :node_id
                  UNION ALL
                  SELECT 1
                  FROM experiment_catalog_point_content pc
                  JOIN experiment_catalog_nodes n ON n.canonical_point_id = pc.canonical_point_id
                  WHERE n.id = :node_id
                  UNION ALL
                  SELECT 1 FROM experiment_catalog_point_media_bindings WHERE node_id = :node_id AND binding_status <> 'archived'
                  UNION ALL
                  SELECT 1
                  FROM experiment_catalog_point_media_bindings mb
                  JOIN experiment_catalog_nodes n ON n.canonical_point_id = mb.canonical_point_id
                  WHERE n.id = :node_id AND mb.binding_status <> 'archived'
                  UNION ALL
                  SELECT 1 FROM experiment_catalog_point_related_links WHERE source_node_id = :node_id
                )
                """
            ),
            {"node_id": node_id},
        ).scalar_one()
    )


def assert_kind_transition(session: Any, *, node: dict[str, Any], new_kind: str) -> None:
    if new_kind == "point" and node.get("has_children"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Point nodes cannot have children")
    if new_kind == "directory" and node["node_kind"] == "point" and has_point_resources(session, node["node_id"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Point nodes with content or videos cannot be converted to directories")

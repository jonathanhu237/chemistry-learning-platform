from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from server.app.database import db_session

TARGET_TABLES = {
    "question": ("questions", "content_status"),
    "experiment": ("experiments", "content_status"),
    "learning_card": ("experiment_learning_cards", "content_status"),
    "source_chunk": ("source_chunks", "content_status"),
    "link": ("links", "content_status"),
    "resource": ("resources", "content_status"),
    "media_binding": ("media_bindings", "status"),
}

ACTION_STATUS = {
    "approve": "approved",
    "reject": "rejected",
    "request_changes": "pending_review",
    "publish": "published",
    "unpublish": "approved",
    "archive": "archived",
}


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def next_review_status(current_status: str, action: str) -> str:
    if action not in ACTION_STATUS:
        raise ValueError(f"Unsupported review action: {action}")
    if action == "publish" and current_status not in {"approved", "published"}:
        raise ValueError("Only approved content can be published")
    if action == "unpublish" and current_status != "published":
        raise ValueError("Only published content can be unpublished")
    return ACTION_STATUS[action]


def list_review_items(
    *,
    item_type: str | None = None,
    status: str | None = None,
    chapter_id: str | None = None,
    search: str | None = None,
    limit: int = 300,
) -> dict[str, Any]:
    filters = ["ri.status <> 'archived'"]
    params: dict[str, Any] = {"limit": limit}
    if item_type:
        filters.append("ri.target_type = :item_type")
        params["item_type"] = item_type
    if status:
        filters.append("ri.status = :status")
        params["status"] = status
    if chapter_id:
        filters.append("ri.chapter_id = :chapter_id")
        params["chapter_id"] = chapter_id
    if search:
        filters.append("(ri.title ILIKE :search OR ri.target_id ILIKE :search)")
        params["search"] = f"%{search}%"
    where_clause = " AND ".join(filters)
    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    f"""
                    SELECT ri.id, ri.target_type AS item_type, ri.target_id, ri.title,
                           ri.chapter_id, ri.knowledge_point_id, ri.status,
                           ri.risk_flags, ri.payload, ri.source_refs, ri.created_at, ri.updated_at
                    FROM review_items ri
                    WHERE {where_clause}
                    ORDER BY ri.created_at DESC
                    LIMIT :limit
                    """
                ),
                params,
            )
            .mappings()
            .all()
        ]
        total = session.execute(text(f"SELECT COUNT(*) FROM review_items ri WHERE {where_clause}"), params).scalar_one()
    return {"items": rows, "total": int(total)}


def get_review_item(item_id: str) -> dict[str, Any] | None:
    with db_session() as session:
        item = (
            session.execute(
                text(
                    """
                    SELECT id, target_type AS item_type, target_id, title, chapter_id,
                           knowledge_point_id, status, risk_flags, payload, source_refs,
                           created_at, updated_at
                    FROM review_items
                    WHERE id = CAST(:item_id AS uuid)
                    """
                ),
                {"item_id": item_id},
            )
            .mappings()
            .first()
        )
        if not item:
            return None
        actions = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT id, action, before_status, after_status, note, payload, created_at
                    FROM review_actions
                    WHERE review_item_id = CAST(:item_id AS uuid)
                    ORDER BY created_at
                    """
                ),
                {"item_id": item_id},
            )
            .mappings()
            .all()
        ]
    result = dict(item)
    result["actions"] = actions
    return result


def _target_id_clause(target_type: str) -> str:
    if target_type == "link":
        return "id = CAST(:target_id AS bigint)"
    return "id = :target_id"


def _apply_target_status(session: Any, target_type: str, target_id: str, new_status: str) -> None:
    target = TARGET_TABLES.get(target_type)
    if not target:
        return
    table, column = target
    status_value = "draft" if target_type == "media_binding" and new_status == "approved" else new_status
    if new_status == "rejected":
        status_value = "archived" if target_type == "media_binding" else "rejected"
    session.execute(
        text(
            f"""
            UPDATE {table}
            SET {column} = :status_value,
                updated_at = now()
            WHERE {_target_id_clause(target_type)}
            """
        ),
        {"target_id": target_id, "status_value": status_value},
    )


def apply_review_action(
    *,
    item_id: str,
    action: str,
    actor_user_id: str | None,
    note: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with db_session() as session:
        item = (
            session.execute(
                text(
                    """
                    SELECT id, target_type, target_id, status
                    FROM review_items
                    WHERE id = CAST(:item_id AS uuid)
                    FOR UPDATE
                    """
                ),
                {"item_id": item_id},
            )
            .mappings()
            .first()
        )
        if not item:
            raise ValueError("Review item not found")
        before = item["status"]
        after = next_review_status(before, action)
        session.execute(
            text(
                """
                UPDATE review_items
                SET status = :after_status,
                    decided_by = CASE WHEN :action IN ('approve', 'reject', 'request_changes') THEN CAST(:actor AS uuid) ELSE decided_by END,
                    decided_at = CASE WHEN :action IN ('approve', 'reject', 'request_changes') THEN now() ELSE decided_at END,
                    published_by = CASE WHEN :action = 'publish' THEN CAST(:actor AS uuid) ELSE published_by END,
                    published_at = CASE WHEN :action = 'publish' THEN now() ELSE published_at END,
                    updated_at = now()
                WHERE id = CAST(:item_id AS uuid)
                """
            ),
            {"item_id": item_id, "after_status": after, "actor": actor_user_id, "action": action},
        )
        session.execute(
            text(
                """
                INSERT INTO review_actions (
                  review_item_id, actor_user_id, action, before_status, after_status, note, payload
                )
                VALUES (
                  CAST(:item_id AS uuid), CAST(:actor AS uuid), :action,
                  :before_status, :after_status, :note, CAST(:payload AS jsonb)
                )
                """
            ),
            {
                "item_id": item_id,
                "actor": actor_user_id,
                "action": action,
                "before_status": before,
                "after_status": after,
                "note": note,
                "payload": _json(payload),
            },
        )
        _apply_target_status(session, item["target_type"], str(item["target_id"]), after)
    result = get_review_item(item_id)
    if not result:
        raise ValueError("Review item not found after action")
    return result

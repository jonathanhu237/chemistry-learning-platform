from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import text

from server.app.catalog_tree_schemas import (
    CatalogNodeCreateRequest,
    CatalogNodeMoveRequest,
    CatalogNodeReorderRequest,
    CatalogNodeStatusRequest,
    CatalogNodeUpdateRequest,
    CatalogPointContentRequest,
    CatalogPointMediaBindRequest,
    CatalogPointPublicationRequest,
    CatalogPointRelatedLinksRequest,
)
from server.app.chemistry_search import chemistry_terms_for_document
from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.domains.media.assets import create_media_asset
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings


POINT_CAPABLE_KINDS = {"point", "hybrid"}
NODE_KINDS = {"directory", "point", "hybrid", "shortcut"}


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _dump(model: Any) -> dict[str, Any]:
    return model.model_dump() if hasattr(model, "model_dump") else dict(model)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _new_node_id() -> str:
    return f"cat-node-{uuid.uuid4().hex}"


def _point_capable(node: dict[str, Any]) -> bool:
    return str(node.get("node_kind") or "") in POINT_CAPABLE_KINDS


def _actions_for_kind(kind: str) -> list[str]:
    if kind == "directory":
        return ["open_directory"]
    if kind == "point":
        return ["open_point"]
    if kind == "hybrid":
        return ["open_directory", "open_point"]
    if kind == "shortcut":
        return ["open_shortcut"]
    return []


def _node_select(where_clause: str) -> str:
    return f"""
        SELECT
          n.id AS node_id,
          n.chapter_id,
          c.chapter_title,
          n.parent_id,
          n.node_kind,
          n.title,
          n.summary,
          n.status,
          n.display_order,
          n.shortcut_target_node_id,
          n.metadata,
          n.published_at,
          n.created_at,
          n.updated_at,
          EXISTS (
            SELECT 1 FROM experiment_catalog_nodes child
            WHERE child.parent_id = n.id AND child.status <> 'archived'
          ) AS has_children,
          EXISTS (
            SELECT 1 FROM experiment_catalog_point_content pc
            WHERE pc.node_id = n.id
          ) AS has_point_content,
          (
            SELECT COUNT(*)
            FROM experiment_catalog_point_media_bindings mb
            WHERE mb.node_id = n.id AND mb.binding_status <> 'archived'
          ) AS media_count,
          (
            SELECT COUNT(*)
            FROM experiment_catalog_point_media_bindings mb
            JOIN media_assets ma ON ma.id = mb.media_asset_id
            WHERE mb.node_id = n.id
              AND mb.binding_status = 'published'
              AND ma.upload_status = 'ready'
          ) AS published_media_count,
          (
            SELECT to_jsonb(s)
            FROM experiment_catalog_point_search_index_state s
            WHERE s.node_id = n.id
          ) AS index_state
        FROM experiment_catalog_nodes n
        JOIN chapters c ON c.id = n.chapter_id
        {where_clause}
    """


def _row_dict(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["node_id"] = str(item.get("node_id") or item.get("id") or "")
    item["media_count"] = int(item.get("media_count") or 0)
    item["published_media_count"] = int(item.get("published_media_count") or 0)
    if not isinstance(item.get("metadata"), dict):
        item["metadata"] = {}
    if item.get("index_state") is not None and not isinstance(item.get("index_state"), dict):
        item["index_state"] = dict(item["index_state"])
    return item


def _node_card(node: dict[str, Any], *, validation: dict[str, Any] | None = None) -> dict[str, Any]:
    kind = str(node.get("node_kind") or "directory")
    return {
        "node_id": node["node_id"],
        "chapter_id": node["chapter_id"],
        "parent_id": node.get("parent_id"),
        "node_kind": kind,
        "title": node.get("title") or "",
        "summary": node.get("summary") or "",
        "status": node.get("status") or "draft",
        "display_order": int(node.get("display_order") or 0),
        "shortcut_target_node_id": node.get("shortcut_target_node_id"),
        "actions": _actions_for_kind(kind),
        "has_children": bool(node.get("has_children")),
        "has_point_content": bool(node.get("has_point_content")),
        "media_count": int(node.get("media_count") or 0),
        "published_media_count": int(node.get("published_media_count") or 0),
        "validation": validation if validation is not None else validate_node_payload(node),
        "index_state": node.get("index_state"),
    }


def _get_node(session: Any, node_id: str, *, include_archived: bool = True) -> dict[str, Any]:
    status_filter = "" if include_archived else " AND n.status <> 'archived'"
    row = (
        session.execute(
            text(_node_select(f"WHERE n.id = :node_id{status_filter}")),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog node not found")
    return _row_dict(row)


def _get_content(session: Any, node_id: str) -> dict[str, Any] | None:
    row = (
        session.execute(
            text(
                """
                SELECT node_id, point_title, teacher_note, principle_mode, principle_equation,
                       principle_text, phenomenon_explanation, safety_note, content_status,
                       published_at, published_by, created_by, updated_by, metadata,
                       created_at, updated_at
                FROM experiment_catalog_point_content
                WHERE node_id = :node_id
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
    return item


def _content_publication_errors(node: dict[str, Any], content: dict[str, Any] | None) -> list[str]:
    errors: list[str] = []
    if not _clean(node.get("title")):
        errors.append("Node title is required")
    if not _point_capable(node):
        return errors
    if not content:
        errors.append("Point content must be saved before publishing")
        return errors
    mode = _clean(content.get("principle_mode") or "text")
    equation = _clean(content.get("principle_equation"))
    principle_text = _clean(content.get("principle_text"))
    if mode == "equation":
        if not equation:
            errors.append("Equation-mode principle requires a chemical equation")
    elif mode == "text":
        if not principle_text:
            errors.append("Text-mode principle requires a principle description")
    else:
        errors.append("Principle mode must be equation or text")
    if not _clean(content.get("phenomenon_explanation")):
        errors.append("Phenomenon explanation is required")
    if not _clean(content.get("safety_note")):
        errors.append("Safety note is required")
    return errors


def validate_node_payload(node: dict[str, Any], content: dict[str, Any] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    kind = _clean(node.get("node_kind"))
    if kind not in NODE_KINDS:
        errors.append("Node kind must be directory, point, hybrid, or shortcut")
    if not _clean(node.get("title")):
        errors.append("Title is required")
    if kind == "shortcut" and not _clean(node.get("shortcut_target_node_id")):
        errors.append("Shortcut target is required")
    if kind != "shortcut" and _clean(node.get("shortcut_target_node_id")):
        errors.append("Only shortcut nodes may have a shortcut target")
    if kind == "directory" and not node.get("has_children"):
        warnings.append("Directory has no children")
    if kind in POINT_CAPABLE_KINDS:
        content = content if content is not None else None
        if content and content.get("content_status") in {"draft", "archived"}:
            warnings.append("Point content is not published")
        elif not content:
            warnings.append("Point content has not been saved")
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def _breadcrumbs(session: Any, node_id: str) -> list[dict[str, Any]]:
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


def _catalog_path_text(session: Any, node_id: str) -> str:
    return " / ".join(item["title"] for item in _breadcrumbs(session, node_id) if item.get("title"))


def _assert_parent_valid(session: Any, *, chapter_id: str, parent_id: str | None, node_id: str | None = None) -> None:
    if not parent_id:
        return
    parent = _get_node(session, parent_id)
    if parent["chapter_id"] != chapter_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent must belong to the same chapter")
    if parent["node_kind"] == "shortcut":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shortcut nodes cannot have children")
    if node_id:
        _assert_no_parent_cycle(session, node_id=node_id, new_parent_id=parent_id)


def _assert_no_parent_cycle(session: Any, *, node_id: str, new_parent_id: str | None) -> None:
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


def _assert_shortcut_target_valid(session: Any, *, node_id: str | None, target_node_id: str | None) -> None:
    if not target_node_id:
        return
    if node_id and node_id == target_node_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shortcut cannot target itself")
    target = _get_node(session, target_node_id, include_archived=False)
    if target["node_kind"] == "shortcut":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shortcut target cannot be another shortcut")
    if target["node_kind"] not in POINT_CAPABLE_KINDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shortcut target must be a point-capable node")


def _max_child_order(session: Any, *, chapter_id: str, parent_id: str | None) -> int:
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


def _queue_index_state(session: Any, *, node_id: str, action: str = "upsert", last_error: str | None = None) -> None:
    session.execute(
        text(
            """
            INSERT INTO experiment_catalog_point_search_index_state (
              node_id, document_id, desired_action, sync_status, attempts, last_error, updated_at
            )
            VALUES (
              :node_id, :node_id, :desired_action, 'pending', 0, :last_error, now()
            )
            ON CONFLICT (node_id) DO UPDATE SET
              document_id = EXCLUDED.document_id,
              desired_action = EXCLUDED.desired_action,
              sync_status = 'pending',
              last_error = EXCLUDED.last_error,
              updated_at = now()
            """
        ),
        {"node_id": node_id, "desired_action": action, "last_error": last_error},
    )


def _queue_subtree_point_indexes(session: Any, *, node_id: str, action: str = "upsert") -> None:
    rows = (
        session.execute(
            text(
                """
                WITH RECURSIVE subtree AS (
                  SELECT id, node_kind
                  FROM experiment_catalog_nodes
                  WHERE id = :node_id
                  UNION ALL
                  SELECT child.id, child.node_kind
                  FROM experiment_catalog_nodes child
                  JOIN subtree ON child.parent_id = subtree.id
                )
                SELECT id FROM subtree WHERE node_kind IN ('point', 'hybrid')
                """
            ),
            {"node_id": node_id},
        )
        .scalars()
        .all()
    )
    for point_node_id in rows:
        _queue_index_state(session, node_id=str(point_node_id), action=action)


def list_chapter_roots(*, chapter_id: str, include_archived: bool = False) -> dict[str, Any]:
    status_clause = "" if include_archived else "AND n.status <> 'archived'"
    with db_session() as session:
        chapter = session.execute(
            text("SELECT id AS chapter_id, chapter_title FROM chapters WHERE id = :chapter_id"),
            {"chapter_id": chapter_id},
        ).mappings().first()
        if not chapter:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
        rows = (
            session.execute(
                text(
                    _node_select(
                        f"""
                        WHERE n.chapter_id = :chapter_id
                          AND n.parent_id IS NULL
                          {status_clause}
                        ORDER BY n.display_order, n.id
                        """
                    )
                ),
                {"chapter_id": chapter_id},
            )
            .mappings()
            .all()
        )
        nodes = [_node_card(_row_dict(row)) for row in rows]
    return {"chapter": dict(chapter), "nodes": nodes}


def list_node_children(*, node_id: str, include_archived: bool = False) -> dict[str, Any]:
    status_clause = "" if include_archived else "AND n.status <> 'archived'"
    with db_session() as session:
        parent = _get_node(session, node_id)
        rows = (
            session.execute(
                text(
                    _node_select(
                        f"""
                        WHERE n.parent_id = :node_id
                          {status_clause}
                        ORDER BY n.display_order, n.id
                        """
                    )
                ),
                {"node_id": node_id},
            )
            .mappings()
            .all()
        )
        children = [_node_card(_row_dict(row)) for row in rows]
    return {"parent": _node_card(parent), "children": children}


def get_node_detail(*, node_id: str) -> dict[str, Any]:
    with db_session() as session:
        node = _get_node(session, node_id)
        content = _get_content(session, node_id)
        children = list_node_children(node_id=node_id, include_archived=False)["children"]
        media = _media_bindings(session, node_id)
        related = _related_links(session, node_id, include_hidden=True, include_defaults=True)
        validation = validate_selected_node(session, node_id=node_id)
        return {
            "node": _node_card(node, validation=validation),
            "breadcrumbs": _breadcrumbs(session, node_id),
            "children": children,
            "point_content": content,
            "media_bindings": media,
            "related_links": related,
            "validation": validation,
            "search_preview": search_preview_for_node(session, node_id=node_id),
            "index_state": node.get("index_state"),
        }


def create_node(*, payload: CatalogNodeCreateRequest, user: Any) -> dict[str, Any]:
    data = _dump(payload)
    kind = _clean(data.get("node_kind") or "directory")
    if kind not in NODE_KINDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid node kind")
    node_id = _new_node_id()
    title = _clean(data.get("title"))
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required")
    with db_session() as session:
        chapter_id = _clean(data.get("chapter_id"))
        if not session.execute(text("SELECT 1 FROM chapters WHERE id = :chapter_id"), {"chapter_id": chapter_id}).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
        parent_id = _clean(data.get("parent_id")) or None
        _assert_parent_valid(session, chapter_id=chapter_id, parent_id=parent_id)
        target_node_id = _clean(data.get("shortcut_target_node_id")) or None
        if kind == "shortcut":
            _assert_shortcut_target_valid(session, node_id=node_id, target_node_id=target_node_id)
        else:
            target_node_id = None
        display_order = _max_child_order(session, chapter_id=chapter_id, parent_id=parent_id) + 1
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_nodes (
                  id, chapter_id, parent_id, node_kind, title, summary, status, display_order,
                  shortcut_target_node_id, metadata, created_by, updated_by, updated_at
                )
                VALUES (
                  :id, :chapter_id, :parent_id, :node_kind, :title, :summary, 'draft', :display_order,
                  :shortcut_target_node_id, CAST(:metadata AS jsonb), CAST(:user_id AS uuid), CAST(:user_id AS uuid), now()
                )
                """
            ),
            {
                "id": node_id,
                "chapter_id": chapter_id,
                "parent_id": parent_id,
                "node_kind": kind,
                "title": title,
                "summary": _clean(data.get("summary")),
                "display_order": display_order,
                "shortcut_target_node_id": target_node_id,
                "metadata": _json(data.get("metadata") if isinstance(data.get("metadata"), dict) else {}),
                "user_id": user.id,
            },
        )
    return get_node_detail(node_id=node_id)


def update_node(*, node_id: str, payload: CatalogNodeUpdateRequest, user: Any) -> dict[str, Any]:
    data = _dump(payload)
    with db_session() as session:
        node = _get_node(session, node_id)
        new_kind = _clean(data.get("node_kind")) or node["node_kind"]
        if new_kind not in NODE_KINDS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid node kind")
        target_node_id = data.get("shortcut_target_node_id")
        if new_kind == "shortcut":
            target_node_id = _clean(target_node_id) or node.get("shortcut_target_node_id")
            _assert_shortcut_target_valid(session, node_id=node_id, target_node_id=target_node_id)
        else:
            target_node_id = None
        title = _clean(data.get("title")) if data.get("title") is not None else node["title"]
        if not title:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required")
        metadata = node["metadata"]
        if isinstance(data.get("metadata"), dict):
            metadata = {**metadata, **data["metadata"]}
        session.execute(
            text(
                """
                UPDATE experiment_catalog_nodes
                SET title = :title,
                    summary = :summary,
                    node_kind = :node_kind,
                    shortcut_target_node_id = :shortcut_target_node_id,
                    metadata = CAST(:metadata AS jsonb),
                    updated_by = CAST(:user_id AS uuid),
                    updated_at = now()
                WHERE id = :node_id
                """
            ),
            {
                "node_id": node_id,
                "title": title,
                "summary": _clean(data.get("summary")) if data.get("summary") is not None else node.get("summary", ""),
                "node_kind": new_kind,
                "shortcut_target_node_id": target_node_id,
                "metadata": _json(metadata),
                "user_id": user.id,
            },
        )
        if new_kind in POINT_CAPABLE_KINDS or node["node_kind"] in POINT_CAPABLE_KINDS:
            _queue_index_state(session, node_id=node_id, action="upsert" if node["status"] == "published" else "delete")
    return get_node_detail(node_id=node_id)


def move_node(*, node_id: str, payload: CatalogNodeMoveRequest, user: Any) -> dict[str, Any]:
    data = _dump(payload)
    with db_session() as session:
        node = _get_node(session, node_id)
        parent_id = _clean(data.get("parent_id")) or None
        _assert_parent_valid(session, chapter_id=node["chapter_id"], parent_id=parent_id, node_id=node_id)
        display_order = int(data["display_order"]) if data.get("display_order") is not None else _max_child_order(
            session, chapter_id=node["chapter_id"], parent_id=parent_id
        ) + 1
        session.execute(
            text(
                """
                UPDATE experiment_catalog_nodes
                SET parent_id = :parent_id,
                    display_order = :display_order,
                    updated_by = CAST(:user_id AS uuid),
                    updated_at = now()
                WHERE id = :node_id
                """
            ),
            {"node_id": node_id, "parent_id": parent_id, "display_order": display_order, "user_id": user.id},
        )
        _queue_subtree_point_indexes(session, node_id=node_id)
    return get_node_detail(node_id=node_id)


def reorder_siblings(*, payload: CatalogNodeReorderRequest, user: Any) -> dict[str, Any]:
    data = _dump(payload)
    items = data.get("items") or []
    if not items:
        return {"updated": 0}
    with db_session() as session:
        node_ids = [_clean(item.get("node_id")) for item in items]
        rows = session.execute(
            text("SELECT id, parent_id, chapter_id FROM experiment_catalog_nodes WHERE id = ANY(:node_ids)"),
            {"node_ids": node_ids},
        ).mappings().all()
        if len(rows) != len(node_ids):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more nodes were not found")
        parents = {(row["chapter_id"], row["parent_id"]) for row in rows}
        if len(parents) != 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reorder only supports siblings")
        for item in items:
            session.execute(
                text(
                    """
                    UPDATE experiment_catalog_nodes
                    SET display_order = :display_order,
                        updated_by = CAST(:user_id AS uuid),
                        updated_at = now()
                    WHERE id = :node_id
                    """
                ),
                {"node_id": _clean(item.get("node_id")), "display_order": int(item.get("display_order") or 0), "user_id": user.id},
            )
        for node_id in node_ids:
            _queue_subtree_point_indexes(session, node_id=node_id)
    return {"updated": len(items)}


def set_node_status(*, node_id: str, payload: CatalogNodeStatusRequest, user: Any) -> dict[str, Any]:
    action = payload.action
    include_subtree = payload.include_subtree
    with db_session() as session:
        node = _get_node(session, node_id)
        node_ids = [node_id]
        if include_subtree:
            node_ids = [
                str(row)
                for row in session.execute(
                    text(
                        """
                        WITH RECURSIVE subtree AS (
                          SELECT id FROM experiment_catalog_nodes WHERE id = :node_id
                          UNION ALL
                          SELECT child.id FROM experiment_catalog_nodes child JOIN subtree ON child.parent_id = subtree.id
                        )
                        SELECT id FROM subtree
                        """
                    ),
                    {"node_id": node_id},
                ).scalars().all()
            ]
        if action == "publish":
            validation = validate_selected_node(session, node_id=node_id, include_subtree=include_subtree)
            if validation["errors"]:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=validation["errors"])
            new_status = "published"
            published_at_sql = "published_at = COALESCE(published_at, now()),"
        elif action == "unpublish":
            new_status = "draft"
            published_at_sql = "published_at = NULL,"
        elif action == "archive":
            new_status = "archived"
            published_at_sql = "published_at = NULL,"
        elif action == "restore":
            new_status = "draft"
            published_at_sql = "published_at = NULL,"
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported status action")
        session.execute(
            text(
                f"""
                UPDATE experiment_catalog_nodes
                SET status = :status,
                    {published_at_sql}
                    updated_by = CAST(:user_id AS uuid),
                    updated_at = now()
                WHERE id = ANY(:node_ids)
                """
            ),
            {"status": new_status, "node_ids": node_ids, "user_id": user.id},
        )
        for changed_node_id in node_ids:
            _queue_subtree_point_indexes(
                session,
                node_id=changed_node_id,
                action="delete" if action in {"unpublish", "archive"} else "upsert",
            )
    return get_node_detail(node_id=node_id)


def validate_selected_node(session: Any, *, node_id: str, include_subtree: bool = False) -> dict[str, Any]:
    node_ids = [node_id]
    if include_subtree:
        node_ids = [
            str(row)
            for row in session.execute(
                text(
                    """
                    WITH RECURSIVE subtree AS (
                      SELECT id FROM experiment_catalog_nodes WHERE id = :node_id
                      UNION ALL
                      SELECT child.id FROM experiment_catalog_nodes child JOIN subtree ON child.parent_id = subtree.id
                    )
                    SELECT id FROM subtree
                    """
                ),
                {"node_id": node_id},
            ).scalars().all()
        ]
    errors: list[str] = []
    warnings: list[str] = []
    nodes: list[dict[str, Any]] = []
    for current_id in node_ids:
        node = _get_node(session, current_id)
        content = _get_content(session, current_id)
        node_validation = validate_node_payload(node, content)
        publish_errors = _content_publication_errors(node, content)
        if node["node_kind"] == "shortcut":
            try:
                _assert_shortcut_target_valid(session, node_id=node["node_id"], target_node_id=node.get("shortcut_target_node_id"))
            except HTTPException as exc:
                publish_errors.append(str(exc.detail))
        current_errors = [*node_validation["errors"], *publish_errors]
        current_warnings = node_validation["warnings"]
        errors.extend(f"{node['title']}: {error}" for error in current_errors)
        warnings.extend(f"{node['title']}: {warning}" for warning in current_warnings)
        nodes.append({"node_id": node["node_id"], "title": node["title"], "errors": current_errors, "warnings": current_warnings})
    return {"ok": not errors, "errors": errors, "warnings": warnings, "nodes": nodes}


def save_point_content(*, node_id: str, payload: CatalogPointContentRequest, user: Any) -> dict[str, Any]:
    data = _dump(payload)
    with db_session() as session:
        node = _get_node(session, node_id)
        if not _point_capable(node):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Node is not point-capable")
        mode = _clean(data.get("principle_mode") or "text")
        principle_equation = _clean(data.get("principle_equation"))
        principle_text = _clean(data.get("principle_text"))
        if mode == "equation":
            principle_text = ""
        elif mode == "text":
            principle_equation = ""
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Principle mode must be equation or text")
        point_title = _clean(data.get("point_title"))
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_content (
                  node_id, point_title, teacher_note, principle_mode, principle_equation, principle_text,
                  phenomenon_explanation, safety_note, content_status, created_by, updated_by, metadata, updated_at
                )
                VALUES (
                  :node_id, :point_title, :teacher_note, :principle_mode, :principle_equation, :principle_text,
                  :phenomenon_explanation, :safety_note, 'draft', CAST(:user_id AS uuid), CAST(:user_id AS uuid),
                  CAST(:metadata AS jsonb), now()
                )
                ON CONFLICT (node_id) DO UPDATE SET
                  point_title = EXCLUDED.point_title,
                  teacher_note = EXCLUDED.teacher_note,
                  principle_mode = EXCLUDED.principle_mode,
                  principle_equation = EXCLUDED.principle_equation,
                  principle_text = EXCLUDED.principle_text,
                  phenomenon_explanation = EXCLUDED.phenomenon_explanation,
                  safety_note = EXCLUDED.safety_note,
                  content_status = 'draft',
                  updated_by = EXCLUDED.updated_by,
                  metadata = experiment_catalog_point_content.metadata || EXCLUDED.metadata,
                  updated_at = now()
                """
            ),
            {
                "node_id": node_id,
                "point_title": point_title,
                "teacher_note": _clean(data.get("teacher_note")),
                "principle_mode": mode,
                "principle_equation": principle_equation or None,
                "principle_text": principle_text or None,
                "phenomenon_explanation": _clean(data.get("phenomenon_explanation")),
                "safety_note": _clean(data.get("safety_note")),
                "metadata": _json(data.get("metadata") if isinstance(data.get("metadata"), dict) else {}),
                "user_id": user.id,
            },
        )
        session.execute(
            text(
                """
                UPDATE experiment_catalog_nodes
                SET title = :title, updated_by = CAST(:user_id AS uuid), updated_at = now()
                WHERE id = :node_id
                """
            ),
            {"node_id": node_id, "title": point_title, "user_id": user.id},
        )
        _queue_index_state(session, node_id=node_id, action="delete")
    return get_node_detail(node_id=node_id)


def set_point_content_publication(*, node_id: str, payload: CatalogPointPublicationRequest, user: Any) -> dict[str, Any]:
    with db_session() as session:
        node = _get_node(session, node_id)
        if not _point_capable(node):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Node is not point-capable")
        content = _get_content(session, node_id)
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Point content must be saved first")
        if payload.action == "publish":
            errors = _content_publication_errors(node, content)
            if errors:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=errors)
            content_status = "published"
            node_status = "published"
            action = "upsert"
            published_sql = "published_at = now(), published_by = CAST(:user_id AS uuid),"
            node_published_sql = "published_at = COALESCE(published_at, now()),"
        elif payload.action in {"unpublish", "archive"}:
            content_status = "archived" if payload.action == "archive" else "draft"
            node_status = "archived" if payload.action == "archive" else "draft"
            action = "delete"
            published_sql = "published_at = NULL, published_by = NULL,"
            node_published_sql = "published_at = NULL,"
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported publication action")
        session.execute(
            text(
                f"""
                UPDATE experiment_catalog_point_content
                SET content_status = :content_status,
                    {published_sql}
                    updated_by = CAST(:user_id AS uuid),
                    updated_at = now()
                WHERE node_id = :node_id
                """
            ),
            {"node_id": node_id, "content_status": content_status, "user_id": user.id},
        )
        session.execute(
            text(
                f"""
                UPDATE experiment_catalog_nodes
                SET status = :status,
                    {node_published_sql}
                    updated_by = CAST(:user_id AS uuid),
                    updated_at = now()
                WHERE id = :node_id
                """
            ),
            {"node_id": node_id, "status": node_status, "user_id": user.id},
        )
        _queue_index_state(session, node_id=node_id, action=action)
    return get_node_detail(node_id=node_id)


def _media_bindings(session: Any, node_id: str) -> list[dict[str, Any]]:
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
                       COALESCE(ma.playback_mime_type, ma.mime_type) AS playback_mime_type,
                       ma.upload_status,
                       ma.processing_phase,
                       ma.processing_progress,
                       ma.error_reason,
                       ma.thumbnail_relative_path IS NOT NULL AS has_thumbnail,
                       ma.created_at,
                       ma.updated_at
                FROM experiment_catalog_point_media_bindings mb
                JOIN media_assets ma ON ma.id = mb.media_asset_id
                WHERE mb.node_id = :node_id
                  AND mb.binding_status <> 'archived'
                ORDER BY mb.display_order, mb.created_at
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def bind_existing_media(*, node_id: str, payload: CatalogPointMediaBindRequest, user: Any) -> dict[str, Any]:
    data = _dump(payload)
    with db_session() as session:
        node = _get_node(session, node_id)
        if not _point_capable(node):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Node is not point-capable")
        asset_exists = session.execute(
            text("SELECT 1 FROM media_assets WHERE id = CAST(:asset_id AS uuid)"),
            {"asset_id": _clean(data.get("media_asset_id"))},
        ).first()
        if not asset_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
        row = session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_media_bindings (
                  node_id, media_asset_id, title, binding_status, display_order,
                  metadata, created_by, updated_by, published_by, published_at, updated_at
                )
                VALUES (
                  :node_id, CAST(:media_asset_id AS uuid), :title, :binding_status,
                  (
                    SELECT COALESCE(MAX(display_order), 0) + 1
                    FROM experiment_catalog_point_media_bindings
                    WHERE node_id = :node_id
                  ),
                  CAST(:metadata AS jsonb), CAST(:user_id AS uuid), CAST(:user_id AS uuid),
                  CASE WHEN :binding_status = 'published' THEN CAST(:user_id AS uuid) ELSE NULL END,
                  CASE WHEN :binding_status = 'published' THEN now() ELSE NULL END,
                  now()
                )
                ON CONFLICT (node_id, media_asset_id) DO UPDATE SET
                  title = EXCLUDED.title,
                  binding_status = EXCLUDED.binding_status,
                  metadata = experiment_catalog_point_media_bindings.metadata || EXCLUDED.metadata,
                  updated_by = EXCLUDED.updated_by,
                  published_by = EXCLUDED.published_by,
                  published_at = EXCLUDED.published_at,
                  updated_at = now()
                RETURNING id
                """
            ),
            {
                "node_id": node_id,
                "media_asset_id": _clean(data.get("media_asset_id")),
                "title": _clean(data.get("title")) or None,
                "binding_status": _clean(data.get("status") or "draft"),
                "metadata": _json(data.get("metadata") if isinstance(data.get("metadata"), dict) else {}),
                "user_id": user.id,
            },
        ).mappings().one()
        _queue_index_state(session, node_id=node_id, action="upsert" if node["status"] == "published" else "delete")
    return {"binding_id": str(row["id"]), "detail": get_node_detail(node_id=node_id)}


def upload_and_bind_media(
    *,
    node_id: str,
    title: str,
    filename: str,
    content: bytes,
    content_type: str | None,
    user: Any,
) -> dict[str, Any]:
    asset = create_media_asset(
        title=title,
        filename=filename,
        content=content,
        content_type=content_type,
        uploaded_by=user.id,
    )
    payload = CatalogPointMediaBindRequest(media_asset_id=str(asset["id"]), title=title, status="draft")
    result = bind_existing_media(node_id=node_id, payload=payload, user=user)
    result["asset"] = asset
    return result


def set_media_binding_status(*, binding_id: str, action: str, user: Any) -> dict[str, Any]:
    if action not in {"publish", "unpublish", "delete"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported media binding action")
    with db_session() as session:
        row = session.execute(
            text(
                """
                SELECT id, node_id
                FROM experiment_catalog_point_media_bindings
                WHERE id = CAST(:binding_id AS uuid)
                """
            ),
            {"binding_id": binding_id},
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media binding not found")
        node_id = str(row["node_id"])
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
            status_value = "published" if action == "publish" else "draft"
            session.execute(
                text(
                    """
                    UPDATE experiment_catalog_point_media_bindings
                    SET binding_status = :status,
                        published_by = CASE WHEN :status = 'published' THEN CAST(:user_id AS uuid) ELSE NULL END,
                        published_at = CASE WHEN :status = 'published' THEN now() ELSE NULL END,
                        updated_by = CAST(:user_id AS uuid),
                        updated_at = now()
                    WHERE id = CAST(:binding_id AS uuid)
                    """
                ),
                {"binding_id": binding_id, "status": status_value, "user_id": user.id},
            )
        _queue_index_state(session, node_id=node_id, action="upsert")
    return get_node_detail(node_id=node_id)


def _related_links(session: Any, node_id: str, *, include_hidden: bool, include_defaults: bool) -> list[dict[str, Any]]:
    hidden_clause = "" if include_hidden else "AND l.hidden = false"
    rows = (
        session.execute(
            text(
                f"""
                SELECT l.id, l.source_node_id, l.target_node_id, l.relation_type, l.hidden,
                       l.sort_order, l.label, l.metadata, target.title AS target_title,
                       target.status AS target_status, target.node_kind AS target_kind
                FROM experiment_catalog_point_related_links l
                JOIN experiment_catalog_nodes target ON target.id = l.target_node_id
                WHERE l.source_node_id = :node_id
                  {hidden_clause}
                ORDER BY l.sort_order, l.created_at
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .all()
    )
    result = [
        {
            "id": str(row["id"]),
            "source_node_id": row["source_node_id"],
            "target_node_id": row["target_node_id"],
            "target_title": row["label"] or row["target_title"],
            "relation_type": row["relation_type"],
            "hidden": bool(row["hidden"]),
            "sort_order": int(row["sort_order"] or 0),
            "label": row["label"],
            "source": "manual",
            "metadata": row["metadata"] if isinstance(row["metadata"], dict) else {},
        }
        for row in rows
        if include_hidden or (not row["hidden"] and row["target_status"] == "published")
    ]
    if not include_defaults:
        return result
    existing_targets = {item["target_node_id"] for item in result}
    node = _get_node(session, node_id)
    default_rows = (
        session.execute(
            text(
                """
                SELECT sibling.id AS target_node_id, sibling.title AS target_title, sibling.display_order
                FROM experiment_catalog_nodes sibling
                WHERE sibling.parent_id IS NOT DISTINCT FROM :parent_id
                  AND sibling.id <> :node_id
                  AND sibling.node_kind IN ('point', 'hybrid')
                  AND sibling.status = 'published'
                ORDER BY ABS(sibling.display_order - :display_order), sibling.display_order
                LIMIT 6
                """
            ),
            {"node_id": node_id, "parent_id": node.get("parent_id"), "display_order": int(node.get("display_order") or 0)},
        )
        .mappings()
        .all()
    )
    for index, row in enumerate(default_rows, start=len(result) + 1):
        if row["target_node_id"] in existing_targets:
            continue
        result.append(
            {
                "id": None,
                "source_node_id": node_id,
                "target_node_id": row["target_node_id"],
                "target_title": row["target_title"],
                "relation_type": "generated_default",
                "hidden": False,
                "sort_order": index,
                "label": None,
                "source": "generated_default",
                "metadata": {"generated_from": "same_parent_neighborhood"},
            }
        )
    return result


def replace_related_links(*, node_id: str, payload: CatalogPointRelatedLinksRequest, user: Any) -> dict[str, Any]:
    data = _dump(payload)
    links = data.get("links") or []
    with db_session() as session:
        source = _get_node(session, node_id)
        if not _point_capable(source):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source node is not point-capable")
        for link in links:
            target = _get_node(session, _clean(link.get("target_node_id")), include_archived=False)
            if not _point_capable(target):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Related link target must be point-capable")
            if target["node_id"] == node_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Related link cannot target itself")
        session.execute(
            text("DELETE FROM experiment_catalog_point_related_links WHERE source_node_id = :node_id"),
            {"node_id": node_id},
        )
        for index, link in enumerate(links):
            session.execute(
                text(
                    """
                    INSERT INTO experiment_catalog_point_related_links (
                      source_node_id, target_node_id, relation_type, hidden, sort_order, label,
                      metadata, created_by, updated_by, updated_at
                    )
                    VALUES (
                      :source_node_id, :target_node_id, :relation_type, :hidden, :sort_order, :label,
                      CAST(:metadata AS jsonb), CAST(:user_id AS uuid), CAST(:user_id AS uuid), now()
                    )
                    ON CONFLICT (source_node_id, target_node_id) DO UPDATE SET
                      relation_type = EXCLUDED.relation_type,
                      hidden = EXCLUDED.hidden,
                      sort_order = EXCLUDED.sort_order,
                      label = EXCLUDED.label,
                      metadata = EXCLUDED.metadata,
                      updated_by = EXCLUDED.updated_by,
                      updated_at = now()
                    """
                ),
                {
                    "source_node_id": node_id,
                    "target_node_id": _clean(link.get("target_node_id")),
                    "relation_type": _clean(link.get("relation_type") or "manual"),
                    "hidden": bool(link.get("hidden")),
                    "sort_order": int(link.get("sort_order") or index + 1),
                    "label": _clean(link.get("label")) or None,
                    "metadata": _json(link.get("metadata") if isinstance(link.get("metadata"), dict) else {}),
                    "user_id": user.id,
                },
            )
        _queue_index_state(session, node_id=node_id, action="upsert" if source["status"] == "published" else "delete")
    return get_node_detail(node_id=node_id)


def search_catalog_nodes(*, query: str, chapter_id: str | None = None, limit: int = 80) -> dict[str, Any]:
    term = f"%{_clean(query)}%"
    filters = ["n.status <> 'archived'"]
    params: dict[str, Any] = {"term": term, "limit": limit}
    if chapter_id:
        filters.append("n.chapter_id = :chapter_id")
        params["chapter_id"] = chapter_id
    where = " AND ".join(filters)
    with db_session() as session:
        rows = (
            session.execute(
                text(
                    _node_select(
                        f"""
                        LEFT JOIN experiment_catalog_point_content pc ON pc.node_id = n.id
                        LEFT JOIN experiment_catalog_legacy_identity_map legacy ON legacy.catalog_node_id = n.id
                        WHERE {where}
                          AND (
                            n.title ILIKE :term
                            OR n.summary ILIKE :term
                            OR pc.point_title ILIKE :term
                            OR pc.principle_equation ILIKE :term
                            OR pc.principle_text ILIKE :term
                            OR pc.phenomenon_explanation ILIKE :term
                            OR pc.safety_note ILIKE :term
                            OR pc.teacher_note ILIKE :term
                            OR legacy.legacy_experiment_id ILIKE :term
                            OR legacy.legacy_point_key ILIKE :term
                          )
                        ORDER BY n.updated_at DESC
                        LIMIT :limit
                        """
                    )
                ),
                params,
            )
            .mappings()
            .all()
        )
    return {"query": query, "items": [_node_card(_row_dict(row)) for row in rows]}


def search_preview_for_node(session: Any, *, node_id: str) -> dict[str, Any] | None:
    node = _get_node(session, node_id)
    if node["node_kind"] == "shortcut" and node.get("shortcut_target_node_id"):
        node = _get_node(session, str(node["shortcut_target_node_id"]))
    if not _point_capable(node):
        return None
    document = student_search_document_for_node(session, node_id=node["node_id"], require_published=False)
    return document


def student_search_document_for_node(session: Any, *, node_id: str, require_published: bool = True) -> dict[str, Any] | None:
    node = _get_node(session, node_id, include_archived=not require_published)
    content = _get_content(session, node["node_id"])
    if not _point_capable(node):
        return None
    if require_published and (node["status"] != "published" or not content or content.get("content_status") != "published"):
        return None
    if not content:
        return None
    breadcrumbs = _breadcrumbs(session, node["node_id"])
    path_text = " / ".join(item["title"] for item in breadcrumbs)
    related = _related_links(session, node["node_id"], include_hidden=False, include_defaults=True)
    videos = _student_videos(session, node["node_id"])
    principle = (
        _clean(content.get("principle_equation"))
        if content.get("principle_mode") == "equation"
        else _clean(content.get("principle_text"))
    )
    phenomenon = _clean(content.get("phenomenon_explanation"))
    safety = _clean(content.get("safety_note"))
    chemistry = chemistry_terms_for_document(content.get("point_title"), principle, phenomenon, safety)
    search_text = " ".join(
        item
        for item in [
            path_text,
            _clean(content.get("point_title")),
            principle,
            phenomenon,
            safety,
            " ".join(_clean(link.get("target_title")) for link in related),
            " ".join(_clean(video.get("title")) for video in videos),
            " ".join(chemistry["formulae"]),
            " ".join(chemistry["aliases"]),
            " ".join(chemistry["reaction_features"]),
        ]
        if item
    )
    return {
        "id": node["node_id"],
        "result_type": "video_point",
        "node_id": node["node_id"],
        "chapter_id": node["chapter_id"],
        "chapter_path": [breadcrumbs[0]["title"]] if breadcrumbs else [],
        "catalog_path": [item["title"] for item in breadcrumbs],
        "title": _clean(content.get("point_title")) or node["title"],
        "subtitle": path_text,
        "snippet": phenomenon or principle,
        "search_text": search_text,
        "principle": principle,
        "phenomenon_explanation": phenomenon,
        "safety_note": safety,
        "formulae": chemistry["formulae"],
        "aliases": chemistry["aliases"],
        "reaction_features": chemistry["reaction_features"],
        "related_text": [_clean(link.get("target_title")) for link in related if _clean(link.get("target_title"))],
        "has_video": bool(videos),
        "video_count": len(videos),
        "videos": [{"media_id": video["media_id"], "title": video["title"]} for video in videos],
        "target": {
            "kind": "point_detail",
            "route": f"/point/{node['node_id']}",
            "node_id": node["node_id"],
            "chapter_id": node["chapter_id"],
            "context_title": _clean(content.get("point_title")) or node["title"],
            "context_summary": phenomenon or principle,
        },
        "updated_at": content.get("updated_at") or node.get("updated_at"),
    }


def _student_videos(session: Any, node_id: str) -> list[dict[str, Any]]:
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
                WHERE mb.node_id = :node_id
                  AND mb.binding_status = 'published'
                  AND ma.upload_status = 'ready'
                ORDER BY mb.display_order, mb.created_at
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


def student_chapter_catalog(*, chapter_id: str) -> dict[str, Any]:
    with db_session() as session:
        chapter = session.execute(
            text("SELECT id AS chapter_id, chapter_title FROM chapters WHERE id = :chapter_id"),
            {"chapter_id": chapter_id},
        ).mappings().first()
        if not chapter:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
        rows = session.execute(
            text(
                _node_select(
                    """
                    WHERE n.chapter_id = :chapter_id
                      AND n.parent_id IS NULL
                      AND n.status = 'published'
                    ORDER BY n.display_order, n.id
                    """
                )
            ),
            {"chapter_id": chapter_id},
        ).mappings().all()
        return {"chapter_id": chapter["chapter_id"], "chapter_title": chapter["chapter_title"], "nodes": [_node_card(_row_dict(row)) for row in rows]}


def student_catalog_node(*, node_id: str) -> dict[str, Any]:
    with db_session() as session:
        node = _get_node(session, node_id, include_archived=False)
        if node["status"] != "published":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog node not available")
        rows = session.execute(
            text(
                _node_select(
                    """
                    WHERE n.parent_id = :node_id
                      AND n.status = 'published'
                    ORDER BY n.display_order, n.id
                    """
                )
            ),
            {"node_id": node_id},
        ).mappings().all()
        return {"node": _node_card(node), "breadcrumbs": _breadcrumbs(session, node_id), "children": [_node_card(_row_dict(row)) for row in rows]}


def _resolve_point_node(session: Any, node_id: str) -> tuple[dict[str, Any], str | None]:
    node = _get_node(session, node_id, include_archived=False)
    if node["status"] != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point node not available")
    if node["node_kind"] == "shortcut":
        target_id = _clean(node.get("shortcut_target_node_id"))
        if not target_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shortcut target not available")
        target = _get_node(session, target_id, include_archived=False)
        if target["status"] != "published" or target["node_kind"] not in POINT_CAPABLE_KINDS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shortcut target not available")
        return target, node["node_id"]
    if node["node_kind"] not in POINT_CAPABLE_KINDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Catalog node is not a point")
    return node, None


def student_point_detail(*, node_id: str) -> dict[str, Any]:
    with db_session() as session:
        node, source_node_id = _resolve_point_node(session, node_id)
        content = _get_content(session, node["node_id"])
        if not content or content.get("content_status") != "published":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point content not available")
        breadcrumbs = _breadcrumbs(session, source_node_id or node["node_id"])
        videos = _student_videos(session, node["node_id"])
        related = _related_links(session, node["node_id"], include_hidden=False, include_defaults=True)
        return {
            "node_id": node_id,
            "canonical_node_id": node["node_id"],
            "source_node_id": source_node_id,
            "chapter_id": node["chapter_id"],
            "title": content.get("point_title") or node["title"],
            "summary": node.get("summary") or "",
            "breadcrumbs": breadcrumbs,
            "principle_mode": content.get("principle_mode") or "text",
            "principle_equation": content.get("principle_equation"),
            "principle_text": content.get("principle_text"),
            "phenomenon_explanation": content.get("phenomenon_explanation"),
            "safety_note": content.get("safety_note"),
            "videos": videos,
            "has_video": bool(videos),
            "no_video_reason": None if videos else "No published video is bound to this point yet.",
            "related_points": [
                {
                    "node_id": link["target_node_id"],
                    "title": link["target_title"],
                    "relation_type": link["relation_type"],
                    "source_node_id": node_id,
                }
                for link in related
                if not link.get("hidden")
            ],
            "assessment_context": {
                "point_node_id": node["node_id"],
                "chapter_id": node["chapter_id"],
                "source_node_id": source_node_id,
                "catalog_path": breadcrumbs,
            },
        }


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
                JOIN experiment_catalog_point_content pc ON pc.node_id = n.id
                WHERE ma.id = CAST(:asset_id AS uuid)
                  AND ma.upload_status = 'ready'
                  AND mb.binding_status = 'published'
                  AND n.status = 'published'
                  AND pc.content_status = 'published'
                LIMIT 1
                """
            ),
            {"asset_id": asset_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    root = get_settings().media_root.resolve()
    path = (root / str(row["relative_path"])).resolve()
    if root != path and root not in path.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found")
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
                JOIN experiment_catalog_point_content pc ON pc.node_id = n.id
                WHERE ma.id = CAST(:asset_id AS uuid)
                  AND ma.upload_status = 'ready'
                  AND mb.binding_status = 'published'
                  AND n.status = 'published'
                  AND pc.content_status = 'published'
                  AND ma.thumbnail_relative_path IS NOT NULL
                LIMIT 1
                """
            ),
            {"asset_id": asset_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media thumbnail not found")
    root = get_settings().media_root.resolve()
    path = (root / str(row["thumbnail_relative_path"])).resolve()
    if root != path and root not in path.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media thumbnail not found")
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media thumbnail not found")
    return path, "image/jpeg", f"{asset_id}.jpg"

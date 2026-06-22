from __future__ import annotations

from typing import Any

from sqlalchemy import text

from server.app.catalog_tree_schemas import (
    CatalogNodeCopyRequest,
    CatalogNodeCreateRequest,
    CatalogNodeMoveRequest,
    CatalogNodeReorderRequest,
    CatalogNodeStatusRequest,
    CatalogNodeUpdateRequest,
)
from server.app.domains.catalog_tree.common import (
    MISSING_LEARNING_FIELD_KEYS,
    NODE_KINDS,
    active_placements_for_canonical_point,
    assert_kind_transition,
    assert_parent_valid,
    breadcrumbs,
    catalog_node_status_summary,
    canonical_point_id_for_node,
    clean,
    dump_model,
    get_content,
    get_node,
    json_dump,
    max_child_order,
    new_canonical_point_id,
    new_node_id,
    node_card,
    node_select,
    point_capable,
    row_dict,
    validate_node_payload,
)
from server.app.domains.catalog_tree.directories import create_node_params, update_node_params
from server.app.domains.catalog_tree.jobs import get_point_job_state, mark_point_evidence_stale, mark_subtree_evidence_stale
from server.app.domains.catalog_tree.search_documents import queue_index_state, queue_subtree_point_indexes, search_preview_for_node
from server.app.domains.catalog_tree.teacher_search import queue_subtree_teacher_indexes, queue_teacher_index_state, search_teacher_catalog_nodes
from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.infrastructure.database import db_session


def _payload_data(payload: Any, *, exclude_unset: bool = False) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_unset=exclude_unset)
    return dict(payload)


def _child_cards(session: Any, *, node_id: str, include_archived: bool, include_teacher_note: bool) -> list[dict[str, Any]]:
    status_clause = "" if include_archived else "AND n.status <> 'archived'"
    rows = (
        session.execute(
            text(
                node_select(
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
    return [node_card(row_dict(row), include_teacher_note=include_teacher_note) for row in rows]


def _normalize_sibling_orders(session: Any, *, chapter_id: str, parent_id: str | None) -> None:
    if parent_id:
        rows = session.execute(
            text("SELECT id FROM experiment_catalog_nodes WHERE parent_id = :parent_id ORDER BY display_order, updated_at DESC, id"),
            {"parent_id": parent_id},
        ).scalars().all()
    else:
        rows = session.execute(
            text(
                """
                SELECT id
                FROM experiment_catalog_nodes
                WHERE chapter_id = :chapter_id AND parent_id IS NULL
                ORDER BY display_order, updated_at DESC, id
                """
            ),
            {"chapter_id": chapter_id},
        ).scalars().all()
    for index, sibling_id in enumerate(rows, start=1):
        session.execute(
            text("UPDATE experiment_catalog_nodes SET display_order = :display_order WHERE id = :node_id"),
            {"node_id": str(sibling_id), "display_order": index},
        )


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
                    node_select(
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
        nodes = [node_card(row_dict(row), include_teacher_note=True) for row in rows]
    return {"chapter": dict(chapter), "nodes": nodes}


def list_node_children(*, node_id: str, include_archived: bool = False) -> dict[str, Any]:
    with db_session() as session:
        parent = get_node(session, node_id)
        children = _child_cards(session, node_id=node_id, include_archived=include_archived, include_teacher_note=True)
    return {"parent": node_card(parent, include_teacher_note=True), "children": children}


def get_node_detail(*, node_id: str) -> dict[str, Any]:
    from server.app.domains.catalog_tree.media_bindings import media_bindings
    from server.app.domains.catalog_tree.related_links import related_links

    with db_session() as session:
        node = get_node(session, node_id)
        content = get_content(session, node_id) if point_capable(node) else None
        children = _child_cards(session, node_id=node_id, include_archived=False, include_teacher_note=True)
        media = media_bindings(session, node_id) if point_capable(node) else []
        related = related_links(session, node_id, include_hidden=True, include_defaults=True) if point_capable(node) else []
        validation = validate_selected_node(session, node_id=node_id)
        job_state = get_point_job_state(session, node_id=node_id) if point_capable(node) else None
        placements = (
            [
                {
                    **node_card(placement, include_teacher_note=True),
                    "breadcrumbs": breadcrumbs(session, placement["node_id"]),
                }
                for placement in active_placements_for_canonical_point(session, str(node.get("canonical_point_id")))
            ]
            if point_capable(node) and node.get("canonical_point_id")
            else []
        )
        node_status = catalog_node_status_summary(node, content=content, validation=validation, job_state=job_state)
        return {
            "node": node_card(node, content=content, validation=validation, job_state=job_state, include_teacher_note=True),
            "canonical_point": {
                "canonical_point_id": node.get("canonical_point_id"),
                "title": node.get("canonical_point_title") or node.get("title"),
                "status": node.get("canonical_point_status"),
                "active_placement_count": len(placements),
            }
            if point_capable(node)
            else None,
            "placements": placements,
            "breadcrumbs": breadcrumbs(session, node_id),
            "children": children,
            "point_content": content,
            "media_bindings": media,
            "related_links": related,
            "validation": validation,
            "node_status": node_status,
            "search_preview": search_preview_for_node(session, node_id=node_id),
            "index_state": node.get("index_state"),
            "job_state": job_state,
        }


def create_node(*, payload: CatalogNodeCreateRequest, user: Any) -> dict[str, Any]:
    data = dump_model(payload)
    kind = clean(data.get("node_kind") or "directory")
    if kind not in NODE_KINDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid node kind")
    node_id = new_node_id()
    title = clean(data.get("title"))
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required")
    with db_session() as session:
        chapter_id = clean(data.get("chapter_id"))
        if not session.execute(text("SELECT 1 FROM chapters WHERE id = :chapter_id"), {"chapter_id": chapter_id}).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
        parent_id = clean(data.get("parent_id")) or None
        assert_parent_valid(session, chapter_id=chapter_id, parent_id=parent_id)
        display_order = max_child_order(session, chapter_id=chapter_id, parent_id=parent_id) + 1
        card = create_node_params(data, kind=kind)
        canonical_point_id = clean(data.get("canonical_point_id")) or None
        if kind == "point":
            if canonical_point_id:
                canonical = session.execute(
                    text(
                        """
                        SELECT id, title, status
                        FROM experiment_catalog_points
                        WHERE id = :canonical_point_id
                          AND status <> 'archived'
                        """
                    ),
                    {"canonical_point_id": canonical_point_id},
                ).mappings().first()
                if not canonical:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canonical experiment point not found")
                title = clean(canonical["title"]) or title
            else:
                canonical_point_id = new_canonical_point_id()
                session.execute(
                    text(
                        """
                        INSERT INTO experiment_catalog_points (
                          id, title, summary, status, metadata, created_by, updated_by, updated_at
                        )
                        VALUES (
                          :id, :title, :summary, 'draft', CAST(:metadata AS jsonb),
                          CAST(:user_id AS uuid), CAST(:user_id AS uuid), now()
                        )
                        """
                    ),
                    {
                        "id": canonical_point_id,
                        "title": title,
                        "summary": clean(data.get("summary")),
                        "metadata": json_dump({"created_from": "catalog_point_placement"}),
                        "user_id": user.id,
                    },
                )
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_nodes (
                  id, chapter_id, parent_id, node_kind, title, summary, teacher_note,
                  status, display_order, canonical_point_id, metadata, created_by, updated_by, updated_at
                )
                VALUES (
                  :id, :chapter_id, :parent_id, :node_kind, :title, :summary, :teacher_note,
                  'draft', :display_order, :canonical_point_id, CAST(:metadata AS jsonb),
                  CAST(:user_id AS uuid), CAST(:user_id AS uuid), now()
                )
                """
            ),
            {
                "id": node_id,
                "chapter_id": chapter_id,
                "parent_id": parent_id,
                "node_kind": kind,
                "title": title,
                "display_order": display_order,
                "canonical_point_id": canonical_point_id if kind == "point" else None,
                "metadata": json_dump(data.get("metadata") if isinstance(data.get("metadata"), dict) else {}),
                "user_id": user.id,
                **card,
            },
        )
        queue_teacher_index_state(session, node_id=node_id, action="upsert", soft=True)
    return get_node_detail(node_id=node_id)


def _parent_matches(left: str | None, right: str | None) -> bool:
    return (left or None) == (right or None)


def _target_chapter_for_copy(session: Any, *, source: dict[str, Any], data: dict[str, Any]) -> tuple[str, str | None]:
    parent_id = clean(data.get("parent_id")) or None
    chapter_id = clean(data.get("chapter_id")) or None
    if parent_id:
        parent = get_node(session, parent_id, include_archived=False)
        if parent["node_kind"] != "directory":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Copy target parent must be a directory")
        if chapter_id and chapter_id != parent["chapter_id"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Copy target chapter must match target parent")
        return str(parent["chapter_id"]), parent_id
    target_chapter_id = chapter_id or str(source["chapter_id"])
    if not session.execute(text("SELECT 1 FROM chapters WHERE id = :chapter_id"), {"chapter_id": target_chapter_id}).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Copy target chapter not found")
    return target_chapter_id, None


def _copy_display_order(
    session: Any,
    *,
    source: dict[str, Any],
    target_chapter_id: str,
    target_parent_id: str | None,
) -> int:
    same_parent = source["chapter_id"] == target_chapter_id and _parent_matches(source.get("parent_id"), target_parent_id)
    if not same_parent:
        return max_child_order(session, chapter_id=target_chapter_id, parent_id=target_parent_id) + 1
    after_order = int(source.get("display_order") or 0)
    if target_parent_id is None:
        session.execute(
            text(
                """
                UPDATE experiment_catalog_nodes
                SET display_order = display_order + 1,
                    updated_at = now()
                WHERE chapter_id = :chapter_id
                  AND parent_id IS NULL
                  AND display_order > :after_order
                """
            ),
            {"chapter_id": target_chapter_id, "after_order": after_order},
        )
    else:
        session.execute(
            text(
                """
                UPDATE experiment_catalog_nodes
                SET display_order = display_order + 1,
                    updated_at = now()
                WHERE chapter_id = :chapter_id
                  AND parent_id = :parent_id
                  AND display_order > :after_order
                """
            ),
            {"chapter_id": target_chapter_id, "parent_id": target_parent_id, "after_order": after_order},
        )
    return after_order + 1


def _assert_point_copy_target_available(
    session: Any,
    *,
    target_chapter_id: str,
    target_parent_id: str | None,
    canonical_point_id: str | None,
) -> None:
    if not canonical_point_id:
        return
    if target_parent_id is None:
        existing = session.execute(
            text(
                """
                SELECT id
                FROM experiment_catalog_nodes
                WHERE chapter_id = :chapter_id
                  AND parent_id IS NULL
                  AND node_kind = 'point'
                  AND canonical_point_id = :canonical_point_id
                  AND status <> 'archived'
                LIMIT 1
                """
            ),
            {"chapter_id": target_chapter_id, "canonical_point_id": canonical_point_id},
        ).scalar_one_or_none()
    else:
        existing = session.execute(
            text(
                """
                SELECT id
                FROM experiment_catalog_nodes
                WHERE chapter_id = :chapter_id
                  AND parent_id = :parent_id
                  AND node_kind = 'point'
                  AND canonical_point_id = :canonical_point_id
                  AND status <> 'archived'
                LIMIT 1
                """
            ),
            {"chapter_id": target_chapter_id, "parent_id": target_parent_id, "canonical_point_id": canonical_point_id},
        ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="目标目录已包含同一实验点位，请选择其他目录")


def _assert_copy_target_outside_source(session: Any, *, source: dict[str, Any], target_parent_id: str | None) -> None:
    if source["node_kind"] != "directory" or not target_parent_id:
        return
    ancestor_ids = {
        str(row)
        for row in session.execute(
            text(
                """
                WITH RECURSIVE ancestors AS (
                  SELECT id, parent_id
                  FROM experiment_catalog_nodes
                  WHERE id = :target_parent_id
                  UNION ALL
                  SELECT parent.id, parent.parent_id
                  FROM experiment_catalog_nodes parent
                  JOIN ancestors ON ancestors.parent_id = parent.id
                )
                SELECT id FROM ancestors
                """
            ),
            {"target_parent_id": target_parent_id},
        ).scalars().all()
    }
    if source["node_id"] in ancestor_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Directory cannot be copied into itself or its descendants")


def _insert_copied_node(
    session: Any,
    *,
    source: dict[str, Any],
    target_chapter_id: str,
    target_parent_id: str | None,
    display_order: int,
    title: str,
    root_source_node_id: str,
    user: Any,
) -> str:
    canonical_point_id = None
    if point_capable(source):
        canonical_point_id = clean(source.get("canonical_point_id"))
        if not canonical_point_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Point placement has no canonical experiment point to copy")
        if clean(source.get("canonical_point_status")) == "archived":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Archived canonical experiment points cannot be copied")
        _assert_point_copy_target_available(
            session,
            target_chapter_id=target_chapter_id,
            target_parent_id=target_parent_id,
            canonical_point_id=canonical_point_id,
        )
    node_id = new_node_id()
    metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
    metadata = {
        **metadata,
        "copied_from_node_id": source["node_id"],
        "copy_root_source_node_id": root_source_node_id,
    }
    if canonical_point_id:
        metadata = {
            **metadata,
            "copied_from_canonical_point_id": canonical_point_id,
            "copy_reuses_canonical_point": True,
        }
    session.execute(
        text(
            """
            INSERT INTO experiment_catalog_nodes (
              id, chapter_id, parent_id, node_kind, title, summary, teacher_note,
              status, display_order, canonical_point_id, metadata, created_by, updated_by, updated_at
            )
            VALUES (
              :id, :chapter_id, :parent_id, :node_kind, :title, :summary, :teacher_note,
              'draft', :display_order, :canonical_point_id, CAST(:metadata AS jsonb),
              CAST(:user_id AS uuid), CAST(:user_id AS uuid), now()
            )
            """
        ),
        {
            "id": node_id,
            "chapter_id": target_chapter_id,
            "parent_id": target_parent_id,
            "node_kind": source["node_kind"],
            "title": title,
            "summary": source.get("summary") or "",
            "teacher_note": source.get("teacher_note") or "",
            "display_order": display_order,
            "canonical_point_id": canonical_point_id,
            "metadata": json_dump(metadata),
            "user_id": user.id,
        },
    )
    return node_id


def _copy_node_tree(
    session: Any,
    *,
    source_node_id: str,
    target_chapter_id: str,
    target_parent_id: str | None,
    display_order: int,
    title_override: str | None,
    include_subtree: bool,
    root_source_node_id: str,
    user: Any,
) -> str:
    source = get_node(session, source_node_id, include_archived=False)
    title = clean(title_override) or clean(source.get("title"))
    copied_node_id = _insert_copied_node(
        session,
        source=source,
        target_chapter_id=target_chapter_id,
        target_parent_id=target_parent_id,
        display_order=display_order,
        title=title,
        root_source_node_id=root_source_node_id,
        user=user,
    )
    if include_subtree and source["node_kind"] == "directory":
        child_ids = session.execute(
            text(
                """
                SELECT id
                FROM experiment_catalog_nodes
                WHERE parent_id = :source_node_id
                  AND status <> 'archived'
                ORDER BY display_order, id
                """
            ),
            {"source_node_id": source_node_id},
        ).scalars().all()
        for child_index, child_id in enumerate(child_ids, start=1):
            _copy_node_tree(
                session,
                source_node_id=str(child_id),
                target_chapter_id=target_chapter_id,
                target_parent_id=copied_node_id,
                display_order=child_index,
                title_override=None,
                include_subtree=True,
                root_source_node_id=root_source_node_id,
                user=user,
            )
    return copied_node_id


def copy_node(*, node_id: str, payload: CatalogNodeCopyRequest, user: Any) -> dict[str, Any]:
    data = dump_model(payload)
    with db_session() as session:
        source = get_node(session, node_id, include_archived=False)
        target_chapter_id, target_parent_id = _target_chapter_for_copy(session, source=source, data=data)
        assert_parent_valid(session, chapter_id=target_chapter_id, parent_id=target_parent_id)
        _assert_copy_target_outside_source(session, source=source, target_parent_id=target_parent_id)
        display_order = _copy_display_order(
            session,
            source=source,
            target_chapter_id=target_chapter_id,
            target_parent_id=target_parent_id,
        )
        copied_node_id = _copy_node_tree(
            session,
            source_node_id=node_id,
            target_chapter_id=target_chapter_id,
            target_parent_id=target_parent_id,
            display_order=display_order,
            title_override=clean(data.get("title")) or None,
            include_subtree=bool(data.get("include_subtree", True)),
            root_source_node_id=node_id,
            user=user,
        )
        _normalize_sibling_orders(session, chapter_id=target_chapter_id, parent_id=target_parent_id)
        queue_subtree_teacher_indexes(session, node_id=copied_node_id, action="upsert", soft=True)
    return get_node_detail(node_id=copied_node_id)


def update_node(*, node_id: str, payload: CatalogNodeUpdateRequest, user: Any) -> dict[str, Any]:
    data = _payload_data(payload, exclude_unset=True)
    with db_session() as session:
        node = get_node(session, node_id)
        new_kind = clean(data.get("node_kind")) or node["node_kind"]
        if new_kind not in NODE_KINDS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid node kind")
        assert_kind_transition(session, node=node, new_kind=new_kind)
        title = clean(data.get("title")) if data.get("title") is not None else node["title"]
        if not title:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required")
        metadata = node["metadata"]
        if isinstance(data.get("metadata"), dict):
            metadata = {**metadata, **data["metadata"]}
        card = update_node_params(data, node, kind=new_kind)
        title_changed = title != node["title"]
        kind_changed = new_kind != node["node_kind"]
        session.execute(
            text(
                """
                UPDATE experiment_catalog_nodes
                SET title = :title,
                    summary = :summary,
                    teacher_note = :teacher_note,
                    node_kind = :node_kind,
                    metadata = CAST(:metadata AS jsonb),
                    updated_by = CAST(:user_id AS uuid),
                    updated_at = now()
                WHERE id = :node_id
                """
            ),
            {
                "node_id": node_id,
                "title": title,
                "node_kind": new_kind,
                "metadata": json_dump(metadata),
                "user_id": user.id,
                **card,
            },
        )
        if point_capable(node):
            canonical_point_id = canonical_point_id_for_node(session, node_id)
            session.execute(
                text(
                    """
                    UPDATE experiment_catalog_points
                    SET title = :title,
                        summary = :summary,
                        updated_by = CAST(:user_id AS uuid),
                        updated_at = now()
                    WHERE id = :canonical_point_id
                    """
                ),
                {
                    "canonical_point_id": canonical_point_id,
                    "title": title,
                    "summary": clean(data.get("summary")) if data.get("summary") is not None else clean(node.get("summary")),
                    "user_id": user.id,
                },
            )
        if new_kind == "point" or node["node_kind"] == "point":
            if title_changed or kind_changed:
                queue_teacher_index_state(session, node_id=node_id, action="upsert", soft=True)
                if node["status"] == "published":
                    queue_index_state(session, node_id=node_id, action="upsert", soft=True)
                mark_point_evidence_stale(session, node_id=node_id, reason="point_node_metadata_edited")
        else:
            if title_changed or kind_changed:
                queue_subtree_teacher_indexes(session, node_id=node_id, action="upsert", soft=True)
                queue_subtree_point_indexes(session, node_id=node_id, soft=True)
                mark_subtree_evidence_stale(session, node_id=node_id, reason="directory_context_edited")
    return get_node_detail(node_id=node_id)


def move_node(*, node_id: str, payload: CatalogNodeMoveRequest, user: Any) -> dict[str, Any]:
    data = dump_model(payload)
    with db_session() as session:
        node = get_node(session, node_id)
        parent_id = clean(data.get("parent_id")) or None
        assert_parent_valid(session, chapter_id=node["chapter_id"], parent_id=parent_id, node_id=node_id)
        display_order = int(data["display_order"]) if data.get("display_order") is not None else max_child_order(
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
        _normalize_sibling_orders(session, chapter_id=node["chapter_id"], parent_id=parent_id)
        queue_subtree_teacher_indexes(session, node_id=node_id, action="upsert", soft=True)
        queue_subtree_point_indexes(session, node_id=node_id, soft=True)
        mark_subtree_evidence_stale(session, node_id=node_id, reason="catalog_path_moved")
    return get_node_detail(node_id=node_id)


def reorder_siblings(*, payload: CatalogNodeReorderRequest, user: Any) -> dict[str, Any]:
    data = dump_model(payload)
    items = data.get("items") or []
    if not items:
        return {"updated": 0}
    with db_session() as session:
        node_ids = [clean(item.get("node_id")) for item in items]
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
                {"node_id": clean(item.get("node_id")), "display_order": int(item.get("display_order") or 0), "user_id": user.id},
            )
        chapter_id, parent_id = next(iter(parents))
        _normalize_sibling_orders(session, chapter_id=str(chapter_id), parent_id=str(parent_id) if parent_id else None)
        for changed_node_id in node_ids:
            queue_subtree_teacher_indexes(session, node_id=changed_node_id, action="upsert", soft=True)
            queue_subtree_point_indexes(session, node_id=changed_node_id, soft=True)
            mark_subtree_evidence_stale(session, node_id=changed_node_id, reason="catalog_order_changed")
    return {"updated": len(items)}


def set_node_status(*, node_id: str, payload: CatalogNodeStatusRequest, user: Any) -> dict[str, Any]:
    action = payload.action
    include_subtree = payload.include_subtree
    with db_session() as session:
        get_node(session, node_id)
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
            final_placement_rows = (
                session.execute(
                    text(
                        """
                        WITH selected_points AS (
                          SELECT id, canonical_point_id
                          FROM experiment_catalog_nodes
                          WHERE id = ANY(:node_ids)
                            AND node_kind = 'point'
                            AND canonical_point_id IS NOT NULL
                            AND status <> 'archived'
                        ),
                        selected_counts AS (
                          SELECT canonical_point_id, COUNT(*) AS selected_count, MIN(id) AS sample_placement_node_id
                          FROM selected_points
                          GROUP BY canonical_point_id
                        ),
                        active_counts AS (
                          SELECT n.canonical_point_id, COUNT(*) AS active_count
                          FROM experiment_catalog_nodes n
                          JOIN selected_counts sc ON sc.canonical_point_id = n.canonical_point_id
                          WHERE n.node_kind = 'point'
                            AND n.status <> 'archived'
                          GROUP BY n.canonical_point_id
                        )
                        SELECT sc.canonical_point_id, sc.sample_placement_node_id, sc.selected_count, ac.active_count
                        FROM selected_counts sc
                        JOIN active_counts ac ON ac.canonical_point_id = sc.canonical_point_id
                        WHERE sc.selected_count >= ac.active_count
                        ORDER BY sc.canonical_point_id
                        LIMIT 5
                        """
                    ),
                    {"node_ids": node_ids},
                )
                .mappings()
                .all()
            )
            if final_placement_rows:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "message": "Archiving the final placement requires an explicit canonical archive decision",
                        "blocked_canonical_points": [dict(row) for row in final_placement_rows],
                    },
                )
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
            queue_subtree_teacher_indexes(
                session,
                node_id=changed_node_id,
                action="delete" if action == "archive" else "upsert",
            )
            queue_subtree_point_indexes(
                session,
                node_id=changed_node_id,
                action="delete" if action in {"unpublish", "archive"} else "upsert",
            )
            mark_subtree_evidence_stale(session, node_id=changed_node_id, reason=f"node_status_{action}")
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
        node = get_node(session, current_id)
        content = get_content(session, current_id) if point_capable(node) else None
        node_validation = validate_node_payload(node, content)
        current_errors = [*node_validation["errors"]]
        current_warnings = node_validation["warnings"]
        errors.extend(f"{node['title']}: {error}" for error in current_errors)
        warnings.extend(f"{node['title']}: {warning}" for warning in current_warnings)
        nodes.append({"node_id": node["node_id"], "title": node["title"], "errors": current_errors, "warnings": current_warnings})
    return {"ok": not errors, "errors": errors, "warnings": warnings, "nodes": nodes}


def search_catalog_nodes(
    *,
    query: str,
    chapter_id: str | None = None,
    limit: int = 80,
    status_filter: str = "all",
) -> dict[str, Any]:
    return search_teacher_catalog_nodes(query=query, chapter_id=chapter_id, limit=limit, status_filter=status_filter)


def _legacy_postgres_search_catalog_nodes(*, query: str, chapter_id: str | None = None, limit: int = 80) -> dict[str, Any]:
    term = f"%{clean(query)}%"
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
                    node_select(
                        f"""
                        LEFT JOIN experiment_catalog_point_content pc ON pc.node_id = n.id
                          OR (n.canonical_point_id IS NOT NULL AND pc.canonical_point_id = n.canonical_point_id)
                        LEFT JOIN experiment_catalog_legacy_identity_map legacy ON legacy.catalog_node_id = n.id
                        WHERE {where}
                          AND (
                            n.title ILIKE :term
                            OR n.summary ILIKE :term
                            OR n.teacher_note ILIKE :term
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
    return {"query": query, "items": [node_card(row_dict(row), include_teacher_note=True) for row in rows]}


def chapter_tree_summary(*, chapter_id: str) -> dict[str, Any]:
    status_keys = ("blocked", "needs_content", "needs_video", "ready", "draft", "published", "sync_attention", "archived")
    point_status_counts = dict.fromkeys(status_keys, 0)
    directory_status_counts = dict.fromkeys(status_keys, 0)
    point_missing_field_counts = dict.fromkeys(MISSING_LEARNING_FIELD_KEYS, 0)
    with db_session() as session:
        rows = (
            session.execute(
                text(
                    node_select(
                        """
                        WHERE n.chapter_id = :chapter_id
                          AND n.status <> 'archived'
                        ORDER BY n.parent_id NULLS FIRST, n.display_order, n.id
                        """
                    )
                ),
                {"chapter_id": chapter_id},
            )
            .mappings()
            .all()
        )

    cards = [node_card(row_dict(row)) for row in rows]
    directory_count = 0
    point_count = 0
    video_binding_count = 0
    playable_video_count = 0
    for card in cards:
        status_summary = card.get("node_status") if isinstance(card.get("node_status"), dict) else {}
        primary_state = clean(status_summary.get("primary_state")) or clean(card.get("status")) or "draft"
        if primary_state not in point_status_counts:
            primary_state = "draft"
        if card.get("node_kind") == "directory":
            directory_count += 1
            directory_status_counts[primary_state] += 1
            continue
        point_count += 1
        point_status_counts[primary_state] += 1
        core_readiness = status_summary.get("core_readiness") if isinstance(status_summary.get("core_readiness"), dict) else {}
        missing_field_keys = core_readiness.get("missing_field_keys") if isinstance(core_readiness.get("missing_field_keys"), list) else []
        for missing_field_key in missing_field_keys:
            if missing_field_key in point_missing_field_counts:
                point_missing_field_counts[missing_field_key] += 1
        if int(card.get("media_count") or 0) > 0:
            video_binding_count += 1
        if int(card.get("published_media_count") or 0) > 0:
            playable_video_count += 1

    actionable_point_count = (
        point_status_counts["blocked"]
        + point_status_counts["needs_content"]
        + point_status_counts["needs_video"]
        + point_status_counts["ready"]
        + point_status_counts["draft"]
        + point_status_counts["sync_attention"]
    )
    return {
        "chapter_id": chapter_id,
        "node_count": len(cards),
        "directory_count": directory_count,
        "point_count": point_count,
        "video_binding_count": video_binding_count,
        "playable_video_count": playable_video_count,
        "missing_video_count": max(point_count - playable_video_count, 0),
        "actionable_point_count": actionable_point_count,
        "point_status_counts": point_status_counts,
        "point_missing_field_counts": point_missing_field_counts,
        "directory_status_counts": directory_status_counts,
    }

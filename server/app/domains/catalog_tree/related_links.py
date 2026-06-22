from __future__ import annotations

from typing import Any

from sqlalchemy import text

from server.app.catalog_tree_schemas import CatalogPointRelatedLinksRequest
from server.app.domains.catalog_tree.common import (
    active_placement_ids_for_canonical_point,
    canonical_point_id_for_node,
    clean,
    dump_model,
    get_node,
    json_dump,
    point_capable,
)
from server.app.domains.catalog_tree.jobs import mark_point_evidence_stale
from server.app.domains.catalog_tree.search_documents import queue_index_state
from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.infrastructure.database import db_session


def related_links(session: Any, node_id: str, *, include_hidden: bool, include_defaults: bool) -> list[dict[str, Any]]:
    hidden_clause = "" if include_hidden else "AND l.hidden = false"
    rows = (
        session.execute(
            text(
                f"""
                WITH source AS (
                  SELECT id, chapter_id, canonical_point_id
                  FROM experiment_catalog_nodes
                  WHERE id = :node_id
                )
                SELECT l.id,
                       COALESCE(l.source_placement_node_id, l.source_node_id) AS source_node_id,
                       COALESCE(target_placement.id, l.target_placement_node_id, l.target_node_id) AS target_node_id,
                       COALESCE(l.source_canonical_point_id, source.canonical_point_id) AS source_canonical_point_id,
                       COALESCE(l.target_canonical_point_id, target_node.canonical_point_id) AS target_canonical_point_id,
                       l.relation_type, l.hidden,
                       l.sort_order, l.metadata,
                       COALESCE(target_point.title, target_placement.title, target_node.title) AS target_title,
                       COALESCE(target_placement.status, target_node.status) AS target_status,
                       COALESCE(target_placement.node_kind, target_node.node_kind) AS target_kind
                FROM experiment_catalog_point_related_links l
                JOIN source ON true
                LEFT JOIN experiment_catalog_nodes target_node ON target_node.id = l.target_node_id
                LEFT JOIN experiment_catalog_points target_point
                  ON target_point.id = COALESCE(l.target_canonical_point_id, target_node.canonical_point_id)
                LEFT JOIN LATERAL (
                  SELECT placement.id, placement.title, placement.status, placement.node_kind, placement.chapter_id
                  FROM experiment_catalog_nodes placement
                  WHERE placement.canonical_point_id = COALESCE(l.target_canonical_point_id, target_node.canonical_point_id)
                    AND placement.node_kind = 'point'
                    AND (:include_hidden OR placement.status = 'published')
                  ORDER BY CASE WHEN placement.chapter_id = source.chapter_id THEN 0 ELSE 1 END,
                           placement.status = 'published' DESC,
                           placement.display_order,
                           placement.id
                  LIMIT 1
                ) target_placement ON true
                WHERE (
                    l.source_node_id = :node_id
                    OR l.source_placement_node_id = :node_id
                    OR (source.canonical_point_id IS NOT NULL AND l.source_canonical_point_id = source.canonical_point_id)
                  )
                  {hidden_clause}
                ORDER BY l.sort_order, l.created_at
                """
            ),
            {"node_id": node_id, "include_hidden": include_hidden},
        )
        .mappings()
        .all()
    )
    result = [
        {
            "id": str(row["id"]),
            "source_node_id": row["source_node_id"],
            "target_node_id": row["target_node_id"],
            "source_canonical_point_id": row["source_canonical_point_id"],
            "target_canonical_point_id": row["target_canonical_point_id"],
            "target_placement_node_id": row["target_node_id"],
            "target_title": row["target_title"],
            "relation_type": row["relation_type"],
            "hidden": bool(row["hidden"]),
            "sort_order": int(row["sort_order"] or 0),
            "source": "manual",
            "metadata": row["metadata"] if isinstance(row["metadata"], dict) else {},
        }
        for row in rows
        if row["target_kind"] == "point" and (include_hidden or (not row["hidden"] and row["target_status"] == "published"))
    ]
    if not include_defaults:
        return result
    existing_targets = {item["target_node_id"] for item in result}
    node = get_node(session, node_id)
    default_rows = (
        session.execute(
            text(
                """
                SELECT sibling.id AS target_node_id, sibling.title AS target_title, sibling.display_order
                FROM experiment_catalog_nodes sibling
                WHERE sibling.parent_id IS NOT DISTINCT FROM :parent_id
                  AND sibling.id <> :node_id
                  AND sibling.node_kind = 'point'
                  AND sibling.status <> 'archived'
                  AND (
                    CAST(:source_canonical_point_id AS text) IS NULL
                    OR sibling.canonical_point_id IS DISTINCT FROM CAST(:source_canonical_point_id AS text)
                  )
                  AND (:include_hidden OR sibling.status = 'published')
                ORDER BY sibling.display_order, sibling.title, sibling.id
                """
            ),
            {
                "node_id": node_id,
                "parent_id": node.get("parent_id"),
                "source_canonical_point_id": node.get("canonical_point_id"),
                "include_hidden": include_hidden,
            },
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
                "source": "generated_default",
                "metadata": {
                    "generated_from": "same_parent_points",
                    "default_scope": "same_parent",
                    "default_scope_label": "同目录默认",
                },
            }
        )
    return result


def replace_related_links(*, node_id: str, payload: CatalogPointRelatedLinksRequest, user: Any) -> dict[str, Any]:
    data = dump_model(payload)
    links = data.get("links") or []
    with db_session() as session:
        source = get_node(session, node_id)
        if not point_capable(source):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Directory nodes cannot own related point links")
        source_canonical_point_id = canonical_point_id_for_node(session, node_id)
        for link in links:
            target = get_node(session, clean(link.get("target_node_id")), include_archived=False)
            if not point_capable(target):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Related link target must be a point")
            if target["node_id"] == node_id or target.get("canonical_point_id") == source_canonical_point_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Related link cannot target itself")
        session.execute(
            text(
                """
                DELETE FROM experiment_catalog_point_related_links
                WHERE source_node_id = :node_id
                   OR source_placement_node_id = :node_id
                   OR source_canonical_point_id = :source_canonical_point_id
                """
            ),
            {"node_id": node_id, "source_canonical_point_id": source_canonical_point_id},
        )
        for index, link in enumerate(links):
            target = get_node(session, clean(link.get("target_node_id")), include_archived=False)
            target_canonical_point_id = canonical_point_id_for_node(session, target["node_id"])
            session.execute(
                text(
                    """
                    INSERT INTO experiment_catalog_point_related_links (
                      source_node_id, target_node_id, source_canonical_point_id, target_canonical_point_id,
                      source_placement_node_id, target_placement_node_id, relation_type, hidden, sort_order,
                      metadata, created_by, updated_by, updated_at
                    )
                    VALUES (
                      :source_node_id, :target_node_id, :source_canonical_point_id, :target_canonical_point_id,
                      :source_node_id, :target_node_id, :relation_type, :hidden, :sort_order,
                      CAST(:metadata AS jsonb), CAST(:user_id AS uuid), CAST(:user_id AS uuid), now()
                    )
                    ON CONFLICT (source_node_id, target_node_id) DO UPDATE SET
                      source_canonical_point_id = EXCLUDED.source_canonical_point_id,
                      target_canonical_point_id = EXCLUDED.target_canonical_point_id,
                      source_placement_node_id = EXCLUDED.source_placement_node_id,
                      target_placement_node_id = EXCLUDED.target_placement_node_id,
                      relation_type = EXCLUDED.relation_type,
                      hidden = EXCLUDED.hidden,
                      sort_order = EXCLUDED.sort_order,
                      metadata = EXCLUDED.metadata,
                      updated_by = EXCLUDED.updated_by,
                      updated_at = now()
                    """
                ),
                {
                    "source_node_id": node_id,
                    "target_node_id": target["node_id"],
                    "source_canonical_point_id": source_canonical_point_id,
                    "target_canonical_point_id": target_canonical_point_id,
                    "relation_type": clean(link.get("relation_type") or "manual"),
                    "hidden": bool(link.get("hidden")),
                    "sort_order": int(link.get("sort_order") or index + 1),
                    "metadata": json_dump(link.get("metadata") if isinstance(link.get("metadata"), dict) else {}),
                    "user_id": user.id,
                },
            )
        if source["status"] == "published":
            for placement_node_id in active_placement_ids_for_canonical_point(session, source_canonical_point_id):
                queue_index_state(session, node_id=placement_node_id, action="upsert", soft=True)
        mark_point_evidence_stale(session, node_id=node_id, reason="related_point_context_changed")
    from server.app.domains.catalog_tree.nodes import get_node_detail

    return get_node_detail(node_id=node_id)

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from server.app.domains.catalog_tree.common import active_placement_ids_for_canonical_point
from server.app.domains.catalog_tree.jobs import mark_point_evidence_stale
from server.app.domains.catalog_tree.search_documents import queue_index_state


def _affected_placement_ids(session: Any, rows: list[dict[str, Any]]) -> list[str]:
    placement_ids: list[str] = []
    seen: set[str] = set()
    for row in rows:
        canonical_point_id = str(row.get("canonical_point_id") or "").strip()
        if canonical_point_id:
            candidates = active_placement_ids_for_canonical_point(session, canonical_point_id)
        else:
            candidates = [str(row.get("node_id") or "").strip()]
        for node_id in candidates:
            if node_id and node_id not in seen:
                seen.add(node_id)
                placement_ids.append(node_id)
    return placement_ids


def handle_media_asset_archived(
    session: Any,
    *,
    media_asset_id: str,
    lifecycle_event_id: str,
    actor_user_id: str | None,
    reason: str | None,
) -> dict[str, Any]:
    rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                UPDATE experiment_catalog_point_media_bindings
                SET binding_status = 'archived',
                    metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
                      'archived_reason', 'media_asset_archived',
                      'archived_media_asset_id', CAST(:media_asset_id AS text),
                      'media_asset_lifecycle_event_id', CAST(:lifecycle_event_id AS text),
                      'archived_by', CAST(:actor_user_id AS text),
                      'archive_reason', CAST(:reason AS text),
                      'previous_binding_status', binding_status
                    ),
                    updated_by = CAST(:actor_user_id AS uuid),
                    updated_at = now()
                WHERE media_asset_id = CAST(:media_asset_id AS uuid)
                  AND binding_status <> 'archived'
                RETURNING id AS binding_id, node_id, canonical_point_id, source_placement_node_id
                """
            ),
            {
                "media_asset_id": media_asset_id,
                "lifecycle_event_id": lifecycle_event_id,
                "actor_user_id": actor_user_id,
                "reason": reason,
            },
        )
        .mappings()
        .all()
    ]
    placement_ids = _affected_placement_ids(session, rows)
    for placement_node_id in placement_ids:
        queue_index_state(
            session,
            node_id=placement_node_id,
            action="upsert",
            trigger_source="system",
        )
        mark_point_evidence_stale(
            session,
            node_id=placement_node_id,
            reason="media_asset_archived",
            trigger_source="system",
        )
    return {
        "status": "succeeded",
        "archived_binding_count": len(rows),
        "affected_placement_count": len(placement_ids),
        "affected_placement_node_ids": placement_ids,
        "archived_binding_ids": [str(row["binding_id"]) for row in rows],
    }

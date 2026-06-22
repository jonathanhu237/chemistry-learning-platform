from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def queue_index_state(
    session: Any,
    *,
    node_id: str,
    action: str,
    status_value: str = "pending",
    last_error: str | None = None,
) -> None:
    session.execute(
        text(
            """
            INSERT INTO experiment_catalog_point_search_index_state (
              node_id, document_id, desired_action, sync_status,
              attempts, last_error, updated_at
            )
            VALUES (
              :node_id, :document_id, :desired_action, :sync_status,
              0, :last_error, now()
            )
            ON CONFLICT (node_id) DO UPDATE SET
              document_id = EXCLUDED.document_id,
              desired_action = EXCLUDED.desired_action,
              sync_status = EXCLUDED.sync_status,
              last_error = EXCLUDED.last_error,
              updated_at = now()
            """
        ),
        {
            "node_id": node_id,
            "document_id": node_id,
            "desired_action": action,
            "sync_status": status_value,
            "last_error": last_error,
        },
    )


def queue_point_search_index_for_media_binding(session: Any, binding: dict[str, Any]) -> None:
    if binding.get("target_type") != "experiment":
        return
    metadata = binding.get("metadata") if isinstance(binding.get("metadata"), dict) else {}
    point_key = _clean(metadata.get("point_key"))
    experiment_id = _clean(binding.get("target_id"))
    if not experiment_id or not point_key:
        return
    row = (
        session.execute(
            text(
                """
                SELECT n.id AS node_id,
                       n.status AS node_status,
                       pc.content_status
                FROM experiment_catalog_legacy_identity_map lm
                JOIN experiment_catalog_nodes n ON n.id = lm.catalog_node_id
                LEFT JOIN experiment_catalog_point_content pc ON pc.node_id = n.id
                WHERE lm.legacy_kind = 'point'
                  AND lm.legacy_experiment_id = :experiment_id
                  AND lm.legacy_point_key = :point_key
                  AND n.node_kind = 'point'
                """
            ),
            {"experiment_id": experiment_id, "point_key": point_key},
        )
        .mappings()
        .first()
    )
    if not row:
        return
    should_upsert = (
        row.get("node_status") == "published"
        and row.get("content_status") == "published"
    )
    queue_index_state(
        session,
        node_id=str(row["node_id"]),
        action="upsert" if should_upsert else "delete",
    )

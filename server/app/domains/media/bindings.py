from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from server.app.infrastructure.database import db_session


def create_media_binding(
    *,
    media_asset_id: str,
    target_type: str,
    target_id: str,
    title: str | None,
    status: str = "draft",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    INSERT INTO media_bindings (
                      media_asset_id, target_type, target_id, title, status, metadata
                    )
                    VALUES (
                      CAST(:media_asset_id AS uuid), :target_type, :target_id, :title, :status,
                      CAST(:metadata AS jsonb)
                    )
                    ON CONFLICT (media_asset_id, target_type, target_id) DO UPDATE SET
                      title = EXCLUDED.title,
                      status = EXCLUDED.status,
                      metadata = media_bindings.metadata || EXCLUDED.metadata,
                      updated_at = now()
                    RETURNING id, media_asset_id, target_type, target_id, title, status,
                              metadata, created_at, updated_at
                    """
                ),
                {
                    "media_asset_id": media_asset_id,
                    "target_type": target_type,
                    "target_id": target_id,
                    "title": title,
                    "status": status,
                    "metadata": metadata_json,
                },
            )
            .mappings()
            .one()
        )
    return dict(row)


def publish_media_binding(binding_id: str, actor_user_id: str | None) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE media_bindings
                    SET status = 'published',
                        published_by = CAST(:actor AS uuid),
                        published_at = now(),
                        updated_at = now()
                    WHERE id = CAST(:binding_id AS uuid)
                    RETURNING id, media_asset_id, target_type, target_id, title, status,
                              metadata, published_at, updated_at
                    """
                ),
                {"binding_id": binding_id, "actor": actor_user_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise ValueError("Media binding not found")
    return dict(row)


def unpublish_media_binding(binding_id: str) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE media_bindings
                    SET status = 'draft',
                        published_by = NULL,
                        published_at = NULL,
                        updated_at = now()
                    WHERE id = CAST(:binding_id AS uuid)
                      AND status <> 'archived'
                    RETURNING id, media_asset_id, target_type, target_id, title, status,
                              metadata, published_at, updated_at
                    """
                ),
                {"binding_id": binding_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise ValueError("Media binding not found")
    return dict(row)


def delete_media_binding(binding_id: str) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    DELETE FROM media_bindings
                    WHERE id = CAST(:binding_id AS uuid)
                    RETURNING id, media_asset_id, target_type, target_id, title, status,
                              metadata, published_at, updated_at
                    """
                ),
                {"binding_id": binding_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise ValueError("Media binding not found")
    return dict(row)

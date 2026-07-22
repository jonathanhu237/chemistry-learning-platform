from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.domains.media.student_catalog_visibility import STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES
from server.app.infrastructure.database import db_session
from server.app.student_video_save_schemas import (
    StudentVideoPersonalState,
    StudentVideoSaveRequest,
    StudentVideoSaveResponse,
)


def student_user_id(user: Any) -> str:
    return str(getattr(user, "id", "") or "").strip()


def _format_dt(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _save_key(placement_node_id: str, media_id: str) -> str:
    return f"{placement_node_id}:{media_id}"


def personal_states_for_items(
    session: Any,
    user: Any,
    items: list[tuple[str, str]],
) -> dict[str, StudentVideoPersonalState]:
    default_states = {
        _save_key(placement, media): StudentVideoPersonalState()
        for placement, media in items
    }
    user_id = student_user_id(user)
    if not user_id or not items or not hasattr(session, "execute"):
        return default_states
    values = [
        {"placement_node_id": str(placement), "media_id": str(media)}
        for placement, media in items
        if str(placement).strip() and str(media).strip()
    ]
    if not values:
        return {}
    rows = (
        session.execute(
            text(
                """
                WITH requested(placement_node_id, media_asset_id) AS (
                  SELECT placement_node_id, CAST(media_id AS uuid)
                  FROM jsonb_to_recordset(CAST(:items AS jsonb))
                    AS item(placement_node_id text, media_id text)
                )
                SELECT
                  saves.placement_node_id,
                  saves.media_asset_id,
                  saves.created_at,
                  saves.updated_at
                FROM student_video_saves saves
                JOIN requested requested_item
                  ON requested_item.placement_node_id = saves.placement_node_id
                 AND requested_item.media_asset_id = saves.media_asset_id
                WHERE saves.student_id = CAST(:student_id AS uuid)
                  AND saves.archived_at IS NULL
                  AND saves.save_type = 'favorite'
                """
            ),
            {"student_id": user_id, "items": json.dumps(values, ensure_ascii=False)},
        )
        .mappings()
        .all()
    )
    for row in rows:
        key = _save_key(str(row["placement_node_id"]), str(row["media_asset_id"]))
        default_states[key] = StudentVideoPersonalState(
            favorite=True,
            favorite_saved_at=_format_dt(row.get("updated_at") or row.get("created_at")),
        )
    return default_states


def personal_state_for_item(
    session: Any,
    user: Any,
    *,
    placement_node_id: str,
    media_id: str,
) -> StudentVideoPersonalState:
    return personal_states_for_items(session, user, [(placement_node_id, media_id)]).get(
        _save_key(placement_node_id, media_id),
        StudentVideoPersonalState(),
    )


def _visible_point_media(session: Any, *, placement_node_id: str, media_id: str) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                f"""
                WITH RECURSIVE {STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES}
                SELECT
                  visible_media.placement_node_id,
                  visible_media.canonical_point_id,
                  visible_media.media_asset_id
                FROM student_visible_playable_media visible_media
                WHERE visible_media.placement_node_id = :placement_node_id
                  AND visible_media.media_asset_id = CAST(:media_id AS uuid)
                LIMIT 1
                """
            ),
            {"placement_node_id": placement_node_id, "media_id": media_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video item not available")
    return dict(row)


def set_student_video_favorite(
    user: Any,
    *,
    payload: StudentVideoSaveRequest,
    active: bool,
) -> StudentVideoSaveResponse:
    user_id = student_user_id(user)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Student user required")
    with db_session() as session:
        visible = _visible_point_media(
            session,
            placement_node_id=payload.placement_node_id,
            media_id=payload.media_id,
        )
        params = {
            "student_id": user_id,
            "placement_node_id": str(visible["placement_node_id"]),
            "canonical_point_id": str(visible["canonical_point_id"]),
            "media_id": str(visible["media_asset_id"]),
            "source": payload.source or "unknown",
        }
        if active:
            session.execute(
                text(
                    """
                    INSERT INTO student_video_saves (
                      student_id, save_type, placement_node_id, canonical_point_id, media_asset_id,
                      source, archived_at, created_at, updated_at
                    )
                    VALUES (
                      CAST(:student_id AS uuid), 'favorite', :placement_node_id, :canonical_point_id,
                      CAST(:media_id AS uuid), :source, NULL, now(), now()
                    )
                    ON CONFLICT (student_id, save_type, placement_node_id, media_asset_id)
                    DO UPDATE SET
                      canonical_point_id = EXCLUDED.canonical_point_id,
                      source = EXCLUDED.source,
                      archived_at = NULL,
                      updated_at = now()
                    """
                ),
                params,
            )
        else:
            session.execute(
                text(
                    """
                    UPDATE student_video_saves
                    SET archived_at = COALESCE(archived_at, now()),
                        updated_at = now()
                    WHERE student_id = CAST(:student_id AS uuid)
                      AND save_type = 'favorite'
                      AND placement_node_id = :placement_node_id
                      AND media_asset_id = CAST(:media_id AS uuid)
                    """
                ),
                params,
            )
        state = personal_state_for_item(
            session,
            user,
            placement_node_id=params["placement_node_id"],
            media_id=params["media_id"],
        )
    return StudentVideoSaveResponse(
        save_type="favorite",
        placement_node_id=params["placement_node_id"],
        canonical_point_id=params["canonical_point_id"],
        media_id=params["media_id"],
        active=active,
        personal_state=state,
    )

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.infrastructure.database import db_session


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _format_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _setting(row: Any | None) -> dict[str, Any]:
    if not row:
        return {
            "recommended": False,
            "sort_order": 0,
            "recommended_by": None,
            "updated_at": None,
        }
    mapping = dict(row)
    return {
        "recommended": True,
        "sort_order": int(mapping.get("sort_order") or 0),
        "recommended_by": _clean(mapping.get("recommended_by")) or None,
        "updated_at": _format_datetime(mapping.get("updated_at")),
    }


def home_video_recommendation_for_node(session: Any, *, node_id: str) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                """
                SELECT placement_node_id, sort_order, recommended_by, updated_at
                FROM student_home_video_recommendations
                WHERE placement_node_id = :node_id
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    return _setting(row)


def set_home_video_recommendation(
    *,
    node_id: str,
    recommended: bool,
    sort_order: int,
    user_id: str | None,
) -> dict[str, Any]:
    placement_node_id = _clean(node_id)
    if not placement_node_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Catalog point placement is required")
    if isinstance(sort_order, bool) or int(sort_order) < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recommendation order must be nonnegative")

    with db_session() as session:
        placement = (
            session.execute(
                text(
                    """
                    SELECT placement.id
                    FROM experiment_catalog_nodes placement
                    JOIN experiment_catalog_points point
                      ON point.id = placement.canonical_point_id
                    WHERE placement.id = :node_id
                      AND placement.node_kind = 'point'
                      AND placement.status <> 'archived'
                      AND point.status <> 'archived'
                    LIMIT 1
                    """
                ),
                {"node_id": placement_node_id},
            )
            .mappings()
            .first()
        )
        if not placement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog point placement not found")

        if recommended:
            session.execute(
                text(
                    """
                    INSERT INTO student_home_video_recommendations (
                      placement_node_id, sort_order, recommended_by, created_at, updated_at
                    )
                    VALUES (
                      :node_id,
                      :sort_order,
                      (SELECT id FROM app_users WHERE id::text = :user_id),
                      now(),
                      now()
                    )
                    ON CONFLICT (placement_node_id) DO UPDATE SET
                      sort_order = EXCLUDED.sort_order,
                      recommended_by = EXCLUDED.recommended_by,
                      updated_at = now()
                    """
                ),
                {
                    "node_id": placement_node_id,
                    "sort_order": int(sort_order),
                    "user_id": _clean(user_id) or None,
                },
            )
        else:
            session.execute(
                text("DELETE FROM student_home_video_recommendations WHERE placement_node_id = :node_id"),
                {"node_id": placement_node_id},
            )

        setting = home_video_recommendation_for_node(session, node_id=placement_node_id)
    return {"node_id": placement_node_id, "home_recommendation": setting}

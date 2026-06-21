from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from server.app.auth import AuthUser
from server.app.domains.catalog_tree.common import breadcrumbs, clean, get_content, get_node, point_capable
from server.app.domains.catalog_tree.related_links import related_links
from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.infrastructure.database import db_session
from server.app.security import AuthError, create_access_token, decode_access_token


PREVIEW_PURPOSE = "catalog_point_preview"
PREVIEW_TOKEN_EXPIRES_MINUTES = 15


def _preview_url(node_id: str, token: str) -> str:
    return f"/preview/catalog/points/{node_id}?preview_token={token}"


def create_catalog_point_preview_token(*, node_id: str, user: AuthUser) -> dict[str, Any]:
    with db_session() as session:
        node = get_node(session, node_id, include_archived=False)
        if not point_capable(node):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Catalog node is not a point")
        if node.get("canonical_point_status") == "archived":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point node not available")
    token, claims = create_access_token(
        subject=user.id,
        role="catalog_preview",
        username=user.username,
        display_name=user.display_name,
        password_version=user.password_version,
        expires_minutes=PREVIEW_TOKEN_EXPIRES_MINUTES,
        extra_claims={
            "purpose": PREVIEW_PURPOSE,
            "node_id": node_id,
            "teacher_user_id": user.id,
        },
    )
    expires_at = datetime.fromtimestamp(int(claims["exp"]), tz=timezone.utc).isoformat()
    return {"preview_url": _preview_url(node_id, token), "token": token, "expires_at": expires_at}


def decode_catalog_preview_token(token: str, *, node_id: str | None = None) -> dict[str, Any]:
    try:
        claims = decode_access_token(token)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if claims.get("purpose") != PREVIEW_PURPOSE or claims.get("role") != "catalog_preview":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid preview token")
    scoped_node_id = clean(claims.get("node_id"))
    if node_id is not None and scoped_node_id != node_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Preview token is not scoped to this point")
    return claims


def _preview_videos(session: Any, node_id: str, token: str) -> list[dict[str, Any]]:
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
                JOIN experiment_catalog_nodes n ON n.id = :node_id
                WHERE ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                    OR mb.node_id = :node_id)
                  AND mb.binding_status <> 'archived'
                  AND ma.upload_status = 'ready'
                ORDER BY mb.display_order, mb.created_at
                LIMIT 1
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
            "stream_path": f"/api/preview/media/assets/{row['media_id']}/stream?preview_token={token}",
            "thumbnail_path": f"/api/preview/media/assets/{row['media_id']}/thumbnail?preview_token={token}" if row["has_thumbnail"] else None,
        }
        for row in rows
    ]


def preview_point_detail(*, node_id: str, preview_token: str) -> dict[str, Any]:
    decode_catalog_preview_token(preview_token, node_id=node_id)
    with db_session() as session:
        node = get_node(session, node_id, include_archived=False)
        if not point_capable(node):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Catalog node is not a point")
        if node.get("canonical_point_status") == "archived":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point node not available")
        content = get_content(session, node["node_id"])
        path = breadcrumbs(session, node["node_id"])
        videos = _preview_videos(session, node["node_id"], preview_token)
        related = related_links(session, node["node_id"], include_hidden=False, include_defaults=True)
        return {
            "node_id": node["node_id"],
            "canonical_node_id": node.get("canonical_point_id") or node["node_id"],
            "source_node_id": None,
            "placement_node_id": node["node_id"],
            "canonical_point_id": node.get("canonical_point_id") or node["node_id"],
            "chapter_id": node["chapter_id"],
            "title": (content or {}).get("point_title") or node["title"],
            "summary": node.get("summary") or "",
            "breadcrumbs": path,
            "principle_mode": (content or {}).get("principle_mode") or "text",
            "principle_equation": (content or {}).get("principle_equation"),
            "principle_text": (content or {}).get("principle_text"),
            "reaction_equations": content.get("reaction_equations") if content and content.get("principle_mode") == "equation" else [],
            "phenomenon_explanation": (content or {}).get("phenomenon_explanation"),
            "safety_note": (content or {}).get("safety_note"),
            "videos": videos,
            "has_video": bool(videos),
            "no_video_reason": None if videos else "No previewable video is bound to this point yet.",
            "related_points": [
                {
                    "node_id": link["target_node_id"],
                    "placement_node_id": link.get("target_placement_node_id") or link["target_node_id"],
                    "canonical_point_id": link.get("target_canonical_point_id"),
                    "title": link["target_title"],
                    "relation_type": link["relation_type"],
                    "source_node_id": node_id,
                }
                for link in related
                if not link.get("hidden")
            ],
            "assessment_context": {
                "point_node_id": node["node_id"],
                "placement_node_id": node["node_id"],
                "canonical_point_id": node.get("canonical_point_id") or node["node_id"],
                "chapter_id": node["chapter_id"],
                "source_node_id": None,
                "catalog_path": path,
            },
        }


def assert_preview_media_scope(*, asset_id: str, preview_token: str) -> str:
    claims = decode_catalog_preview_token(preview_token)
    node_id = clean(claims.get("node_id"))
    with db_session() as session:
        exists = session.execute(
            text(
                """
                SELECT 1
                FROM experiment_catalog_point_media_bindings mb
                JOIN media_assets ma ON ma.id = mb.media_asset_id
                JOIN experiment_catalog_nodes n ON n.id = :node_id
                WHERE ma.id = CAST(:asset_id AS uuid)
                  AND ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                    OR mb.node_id = :node_id)
                  AND mb.binding_status <> 'archived'
                  AND ma.upload_status = 'ready'
                LIMIT 1
                """
            ),
            {"asset_id": asset_id, "node_id": node_id},
        ).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not available for this preview")
    return node_id

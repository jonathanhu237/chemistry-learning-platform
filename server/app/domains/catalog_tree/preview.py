from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypedDict

from sqlalchemy import text

from server.app.domains.catalog_tree.common import breadcrumbs, clean, get_content, get_node, node_card, node_select, point_capable, row_dict
from server.app.domains.catalog_tree.related_links import related_links
from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.infrastructure.database import db_session
from server.app.security import AuthError, create_access_token, decode_access_token
from server.app.domains.student_learning.point_detail import get_student_learning_page_by_chapter


PREVIEW_PURPOSE = "catalog_node_preview"
LEGACY_PREVIEW_PURPOSE = "catalog_point_preview"
PREVIEW_TOKEN_EXPIRES_MINUTES = 15
STUDENT_VALIDATION = {"ok": True, "errors": [], "warnings": []}


class PreviewTeacherIdentity(TypedDict):
    id: str
    username: str
    display_name: str | None
    password_version: int


def _preview_url(node_id: str, token: str, *, node_kind: str) -> str:
    route = "points" if node_kind == "point" else "nodes"
    return f"/preview/catalog/{route}/{node_id}?preview_token={token}"


def create_catalog_node_preview_token(*, node_id: str, teacher: PreviewTeacherIdentity) -> dict[str, Any]:
    with db_session() as session:
        node = get_node(session, node_id, include_archived=True)
        node_kind = clean(node.get("node_kind")) or "directory"
        if node_kind not in {"directory", "point"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Catalog node kind is not previewable")
        if node.get("canonical_point_status") == "archived":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point node not available")
    token, claims = create_access_token(
        subject=teacher["id"],
        role="catalog_preview",
        username=teacher["username"],
        display_name=teacher["display_name"],
        password_version=teacher["password_version"],
        expires_minutes=PREVIEW_TOKEN_EXPIRES_MINUTES,
        extra_claims={
            "purpose": PREVIEW_PURPOSE,
            "node_id": node_id,
            "root_node_id": node_id,
            "node_kind": node_kind,
            "teacher_user_id": teacher["id"],
        },
    )
    expires_at = datetime.fromtimestamp(int(claims["exp"]), tz=timezone.utc).isoformat()
    return {"preview_url": _preview_url(node_id, token, node_kind=node_kind), "token": token, "expires_at": expires_at}


def create_catalog_point_preview_token(*, node_id: str, teacher: PreviewTeacherIdentity) -> dict[str, Any]:
    return create_catalog_node_preview_token(node_id=node_id, teacher=teacher)


def decode_catalog_preview_token(token: str, *, node_id: str | None = None) -> dict[str, Any]:
    try:
        claims = decode_access_token(token)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if claims.get("purpose") not in {PREVIEW_PURPOSE, LEGACY_PREVIEW_PURPOSE} or claims.get("role") != "catalog_preview":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid preview token")
    scoped_node_id = clean(claims.get("root_node_id")) or clean(claims.get("node_id"))
    node_kind = clean(claims.get("node_kind")) or "point"
    claims["root_node_id"] = scoped_node_id
    claims["node_id"] = scoped_node_id
    claims["node_kind"] = node_kind
    if node_id is not None and node_kind != "directory" and scoped_node_id != node_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Preview token is not scoped to this point")
    return claims


def _preview_card(node: dict[str, Any]) -> dict[str, Any]:
    return node_card(node, validation=STUDENT_VALIDATION, include_teacher_note=False)


def _preview_children(session: Any, *, parent_id: str) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                node_select(
                    """
                    WHERE n.parent_id = :node_id
                      AND n.status <> 'archived'
                    ORDER BY n.display_order, n.id
                    """
                )
            ),
            {"node_id": parent_id},
        )
        .mappings()
        .all()
    )
    return [_preview_card(row_dict(row)) for row in rows]


def _preview_node_in_scope(session: Any, *, node_id: str, claims: dict[str, Any]) -> bool:
    root_node_id = clean(claims.get("root_node_id")) or clean(claims.get("node_id"))
    node_kind = clean(claims.get("node_kind")) or "point"
    if not root_node_id:
        return False
    if node_kind != "directory":
        return root_node_id == node_id
    if root_node_id == node_id:
        return True
    row = session.execute(
        text(
            """
            WITH RECURSIVE subtree AS (
              SELECT id
              FROM experiment_catalog_nodes
              WHERE id = :root_node_id
              UNION ALL
              SELECT child.id
              FROM experiment_catalog_nodes child
              JOIN subtree parent ON child.parent_id = parent.id
              WHERE child.status <> 'archived'
            )
            SELECT 1
            FROM subtree
            WHERE id = :target_node_id
            LIMIT 1
            """
        ),
        {"root_node_id": root_node_id, "target_node_id": node_id},
    ).first()
    return bool(row)


def _assert_preview_node_scope(session: Any, *, node_id: str, claims: dict[str, Any]) -> None:
    if not _preview_node_in_scope(session, node_id=node_id, claims=claims):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Preview token is not scoped to this catalog node")


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
                  AND COALESCE(ma.lifecycle_status, 'active') = 'active'
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


def _preview_point_detail(session: Any, *, node: dict[str, Any], preview_token: str, claims: dict[str, Any]) -> dict[str, Any]:
    if not point_capable(node):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Catalog node is not a point")
    if node.get("canonical_point_status") == "archived":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point node not available")
    content = get_content(session, node["node_id"])
    path = breadcrumbs(session, node["node_id"])
    videos = _preview_videos(session, node["node_id"], preview_token)
    related = related_links(session, node["node_id"], include_hidden=False, include_defaults=True)
    if clean(claims.get("node_kind")) == "directory":
        related = [link for link in related if _preview_node_in_scope(session, node_id=link["target_node_id"], claims=claims)]
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
                "source_node_id": node["node_id"],
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


def preview_point_detail(*, node_id: str, preview_token: str) -> dict[str, Any]:
    claims = decode_catalog_preview_token(preview_token, node_id=node_id)
    with db_session() as session:
        _assert_preview_node_scope(session, node_id=node_id, claims=claims)
        node = get_node(session, node_id, include_archived=True)
        return _preview_point_detail(session, node=node, preview_token=preview_token, claims=claims)


def preview_catalog_node(*, node_id: str, preview_token: str) -> dict[str, Any]:
    claims = decode_catalog_preview_token(preview_token)
    with db_session() as session:
        _assert_preview_node_scope(session, node_id=node_id, claims=claims)
        node = get_node(session, node_id, include_archived=True)
        if point_capable(node):
            return {
                "node_kind": "point",
                "directory": None,
                "point": _preview_point_detail(session, node=node, preview_token=preview_token, claims=claims),
                "learning_page": None,
            }
        if node["node_kind"] != "directory":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Catalog node is not previewable")
        return {
            "node_kind": "directory",
            "directory": {
                "node": _preview_card(node),
                "breadcrumbs": breadcrumbs(session, node_id),
                "children": _preview_children(session, parent_id=node_id),
            },
            "point": None,
            "learning_page": get_student_learning_page_by_chapter(chapter_id=node["chapter_id"]),
        }


def assert_preview_media_scope(*, asset_id: str, preview_token: str) -> str:
    claims = decode_catalog_preview_token(preview_token)
    node_id = clean(claims.get("root_node_id")) or clean(claims.get("node_id"))
    node_kind = clean(claims.get("node_kind")) or "point"
    with db_session() as session:
        exists = session.execute(
            text(
                """
                WITH RECURSIVE scoped_nodes AS (
                  SELECT id, canonical_point_id, node_kind
                  FROM experiment_catalog_nodes
                  WHERE id = :node_id
                  UNION ALL
                  SELECT child.id, child.canonical_point_id, child.node_kind
                  FROM experiment_catalog_nodes child
                  JOIN scoped_nodes parent ON child.parent_id = parent.id
                  WHERE :node_kind = 'directory'
                    AND child.status <> 'archived'
                )
                SELECT n.id AS node_id
                FROM scoped_nodes n
                JOIN experiment_catalog_point_media_bindings mb
                  ON ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                    OR mb.node_id = n.id)
                JOIN media_assets ma ON ma.id = mb.media_asset_id
                WHERE ma.id = CAST(:asset_id AS uuid)
                  AND n.node_kind = 'point'
                  AND mb.binding_status <> 'archived'
                  AND ma.upload_status = 'ready'
                  AND COALESCE(ma.lifecycle_status, 'active') = 'active'
                  AND (:node_kind = 'directory' OR n.id = :node_id)
                LIMIT 1
                """
            ),
            {"asset_id": asset_id, "node_id": node_id, "node_kind": node_kind},
        ).first()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not available for this preview")
    return str(exists[0] if not isinstance(exists, dict) else exists["node_id"])

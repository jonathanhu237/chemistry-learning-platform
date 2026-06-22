from __future__ import annotations

from typing import Any

from sqlalchemy import text

from server.app.domains.catalog_tree.common import (
    breadcrumbs,
    get_content,
    get_node,
    node_card,
    node_select,
    point_capable,
    published_path_available,
    row_dict,
)
from server.app.domains.catalog_tree.media_bindings import student_videos
from server.app.domains.catalog_tree.related_links import related_links
from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.infrastructure.database import db_session


STUDENT_VALIDATION = {"ok": True, "errors": [], "warnings": []}


def _student_card(node: dict[str, Any]) -> dict[str, Any]:
    return node_card(node, validation=STUDENT_VALIDATION, include_teacher_note=False)


def _published_children(session: Any, *, parent_id: str) -> list[dict[str, Any]]:
    rows = session.execute(
        text(
            node_select(
                """
                WHERE n.parent_id = :node_id
                  AND n.status = 'published'
                ORDER BY n.display_order, n.id
                """
            )
        ),
        {"node_id": parent_id},
    ).mappings().all()
    return [_student_card(row_dict(row)) for row in rows if published_path_available(session, row["node_id"])]


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
                node_select(
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
        nodes = [_student_card(row_dict(row)) for row in rows if published_path_available(session, row["node_id"])]
        return {"chapter_id": chapter["chapter_id"], "chapter_title": chapter["chapter_title"], "nodes": nodes}


def student_catalog_node(*, node_id: str) -> dict[str, Any]:
    with db_session() as session:
        node = get_node(session, node_id, include_archived=False)
        if node["status"] != "published" or not published_path_available(session, node_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog node not available")
        if node["node_kind"] != "directory":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Catalog node is not a directory")
        return {"node": _student_card(node), "breadcrumbs": breadcrumbs(session, node_id), "children": _published_children(session, parent_id=node_id)}


def student_point_detail(*, node_id: str) -> dict[str, Any]:
    with db_session() as session:
        node = get_node(session, node_id, include_archived=False)
        if node["status"] != "published" or not published_path_available(session, node_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point node not available")
        if not point_capable(node):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Catalog node is not a point")
        if node.get("canonical_point_status") == "archived":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point node not available")
        content = get_content(session, node["node_id"])
        published_content = content if content and content.get("content_status") == "published" else None
        path = breadcrumbs(session, node["node_id"])
        videos = student_videos(session, node["node_id"])
        related = related_links(session, node["node_id"], include_hidden=False, include_defaults=True)
        return {
            "node_id": node["node_id"],
            "canonical_node_id": node.get("canonical_point_id") or node["node_id"],
            "source_node_id": None,
            "placement_node_id": node["node_id"],
            "canonical_point_id": node.get("canonical_point_id") or node["node_id"],
            "chapter_id": node["chapter_id"],
            "title": (published_content or {}).get("point_title") or node["title"],
            "summary": node.get("summary") or "",
            "breadcrumbs": path,
            "principle_mode": (published_content or {}).get("principle_mode") or "text",
            "principle_equation": (published_content or {}).get("principle_equation"),
            "principle_text": (published_content or {}).get("principle_text"),
            "reaction_equations": published_content.get("reaction_equations") if published_content and published_content.get("principle_mode") == "equation" else [],
            "phenomenon_explanation": (published_content or {}).get("phenomenon_explanation"),
            "safety_note": (published_content or {}).get("safety_note"),
            "videos": videos,
            "has_video": bool(videos),
            "no_video_reason": None if videos else "No published video is bound to this point yet.",
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

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, Path, Query, UploadFile

from server.app.auth import AuthUser, require_roles
from server.app.catalog_tree_schemas import (
    CatalogNodeCreateRequest,
    CatalogNodeMoveRequest,
    CatalogNodeReorderRequest,
    CatalogNodeStatusRequest,
    CatalogNodeUpdateRequest,
    CatalogPointContentRequest,
    CatalogPointMediaBindRequest,
    CatalogPointPublicationRequest,
    CatalogPointRelatedLinksRequest,
)
from server.app.domains.catalog_tree.tree import (
    bind_existing_media,
    create_node,
    get_node_detail,
    list_chapter_roots,
    list_node_children,
    move_node,
    reorder_siblings,
    replace_related_links,
    save_point_content,
    search_catalog_nodes,
    set_media_binding_status,
    set_node_status,
    set_point_content_publication,
    update_node,
    upload_and_bind_media,
    validate_selected_node,
)
from server.app.infrastructure.database import db_session


router = APIRouter(prefix="/api/admin/catalog", tags=["admin-catalog-tree"])


@router.get("/chapters/{chapter_id}/roots")
async def admin_catalog_chapter_roots(
    chapter_id: str = Path(min_length=1),
    include_archived: bool = False,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return list_chapter_roots(chapter_id=chapter_id, include_archived=include_archived)


@router.get("/nodes/{node_id}/children")
async def admin_catalog_node_children(
    node_id: str = Path(min_length=1),
    include_archived: bool = False,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return list_node_children(node_id=node_id, include_archived=include_archived)


@router.get("/nodes/{node_id}")
async def admin_catalog_node_detail(
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return get_node_detail(node_id=node_id)


@router.post("/nodes")
async def admin_catalog_create_node(
    payload: CatalogNodeCreateRequest,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return create_node(payload=payload, user=user)


@router.patch("/nodes/{node_id}")
async def admin_catalog_update_node(
    payload: CatalogNodeUpdateRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return update_node(node_id=node_id, payload=payload, user=user)


@router.post("/nodes/{node_id}/move")
async def admin_catalog_move_node(
    payload: CatalogNodeMoveRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return move_node(node_id=node_id, payload=payload, user=user)


@router.post("/nodes/reorder")
async def admin_catalog_reorder_nodes(
    payload: CatalogNodeReorderRequest,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return reorder_siblings(payload=payload, user=user)


@router.post("/nodes/{node_id}/status")
async def admin_catalog_node_status(
    payload: CatalogNodeStatusRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return set_node_status(node_id=node_id, payload=payload, user=user)


@router.put("/nodes/{node_id}/point-content")
async def admin_catalog_save_point_content(
    payload: CatalogPointContentRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return save_point_content(node_id=node_id, payload=payload, user=user)


@router.post("/nodes/{node_id}/point-content/publication")
async def admin_catalog_point_content_publication(
    payload: CatalogPointPublicationRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return set_point_content_publication(node_id=node_id, payload=payload, user=user)


@router.post("/nodes/{node_id}/media-bindings")
async def admin_catalog_bind_media(
    payload: CatalogPointMediaBindRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return bind_existing_media(node_id=node_id, payload=payload, user=user)


@router.post("/nodes/{node_id}/media/upload")
async def admin_catalog_upload_and_bind_media(
    node_id: str = Path(min_length=1),
    title: str = Form(...),
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    content = await file.read()
    return upload_and_bind_media(
        node_id=node_id,
        title=title,
        filename=file.filename or "upload.mp4",
        content=content,
        content_type=file.content_type,
        user=user,
    )


@router.post("/media-bindings/{binding_id}/{action}")
async def admin_catalog_media_binding_status(
    binding_id: str = Path(min_length=1),
    action: str = Path(pattern="^(publish|unpublish|delete)$"),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return set_media_binding_status(binding_id=binding_id, action=action, user=user)


@router.put("/nodes/{node_id}/related-links")
async def admin_catalog_replace_related_links(
    payload: CatalogPointRelatedLinksRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return replace_related_links(node_id=node_id, payload=payload, user=user)


@router.get("/nodes/{node_id}/validation")
async def admin_catalog_validate_node(
    node_id: str = Path(min_length=1),
    include_subtree: bool = False,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        return validate_selected_node(session, node_id=node_id, include_subtree=include_subtree)


@router.get("/search")
async def admin_catalog_search(
    q: str = Query(default="", max_length=200),
    chapter_id: str | None = None,
    limit: int = Query(default=80, ge=1, le=200),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return search_catalog_nodes(query=q, chapter_id=chapter_id, limit=limit)

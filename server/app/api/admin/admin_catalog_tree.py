from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path, Query

from server.app.auth import AuthUser, require_teacher_console_user
from server.app.catalog_tree_schemas import (
    CatalogEquationAssistRequest,
    CatalogEquationAssistResponse,
    CatalogNodeCopyRequest,
    CatalogEquationPreviewRequest,
    CatalogEquationPreviewResponse,
    CatalogNodeCreateRequest,
    CatalogNodeMoveRequest,
    CatalogPreviewTokenResponse,
    CatalogNodeReorderRequest,
    CatalogNodeStatusRequest,
    CatalogNodeUpdateRequest,
    CatalogPointContentRequest,
    CatalogPointMediaBindRequest,
    CatalogPointPublicationRequest,
    CatalogPointRelatedLinksRequest,
)
from server.app.domains.catalog_tree.equations import assist_reaction_equations, equation_rows_from_inputs, normalize_reaction_equations
from server.app.domains.catalog_tree.ai_context import catalog_point_ai_context, catalog_point_rag_probe
from server.app.domains.catalog_tree.jobs import catalog_point_job_state, trigger_catalog_point_job
from server.app.domains.catalog_tree.preview import PreviewTeacherIdentity, create_catalog_point_preview_token
from server.app.domains.catalog_tree.tree import (
    bind_existing_media,
    chapter_tree_summary,
    copy_node,
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
    validate_selected_node,
)
from server.app.infrastructure.database import db_session


router = APIRouter(prefix="/api/admin/catalog", tags=["admin-catalog-tree"])


@router.get("/chapters/{chapter_id}/roots")
async def admin_catalog_chapter_roots(
    chapter_id: str = Path(min_length=1),
    include_archived: bool = False,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return list_chapter_roots(chapter_id=chapter_id, include_archived=include_archived)


@router.get("/chapters/{chapter_id}/summary")
async def admin_catalog_chapter_summary(
    chapter_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return chapter_tree_summary(chapter_id=chapter_id)


@router.get("/nodes/{node_id}/children")
async def admin_catalog_node_children(
    node_id: str = Path(min_length=1),
    include_archived: bool = False,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return list_node_children(node_id=node_id, include_archived=include_archived)


@router.get("/nodes/{node_id}")
async def admin_catalog_node_detail(
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return get_node_detail(node_id=node_id)


@router.post("/nodes")
async def admin_catalog_create_node(
    payload: CatalogNodeCreateRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return create_node(payload=payload, user=user)


@router.patch("/nodes/{node_id}")
async def admin_catalog_update_node(
    payload: CatalogNodeUpdateRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return update_node(node_id=node_id, payload=payload, user=user)


@router.post("/nodes/{node_id}/move")
async def admin_catalog_move_node(
    payload: CatalogNodeMoveRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return move_node(node_id=node_id, payload=payload, user=user)


@router.post("/nodes/{node_id}/copy")
async def admin_catalog_copy_node(
    payload: CatalogNodeCopyRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return copy_node(node_id=node_id, payload=payload, user=user)


@router.post("/nodes/reorder")
async def admin_catalog_reorder_nodes(
    payload: CatalogNodeReorderRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return reorder_siblings(payload=payload, user=user)


@router.post("/nodes/{node_id}/status")
async def admin_catalog_node_status(
    payload: CatalogNodeStatusRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return set_node_status(node_id=node_id, payload=payload, user=user)


@router.post("/nodes/{node_id}/preview-token", response_model=CatalogPreviewTokenResponse)
async def admin_catalog_point_preview_token(
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> CatalogPreviewTokenResponse:
    teacher: PreviewTeacherIdentity = {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "password_version": user.password_version,
    }
    return CatalogPreviewTokenResponse(**create_catalog_point_preview_token(node_id=node_id, teacher=teacher))


@router.put("/nodes/{node_id}/point-content")
async def admin_catalog_save_point_content(
    payload: CatalogPointContentRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return save_point_content(node_id=node_id, payload=payload, user=user)


@router.post("/equations/preview", response_model=CatalogEquationPreviewResponse)
async def admin_catalog_preview_equations(
    payload: CatalogEquationPreviewRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> CatalogEquationPreviewResponse:
    equations = normalize_reaction_equations(equation_rows_from_inputs(payload.equations, payload.multiline_text))
    return CatalogEquationPreviewResponse(
        ok=all(row["validation_status"] != "invalid" for row in equations),
        equations=equations,
    )


@router.post("/equations/assist", response_model=CatalogEquationAssistResponse)
async def admin_catalog_assist_equations(
    payload: CatalogEquationAssistRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> CatalogEquationAssistResponse:
    return CatalogEquationAssistResponse(**assist_reaction_equations(payload))


@router.post("/nodes/{node_id}/point-content/publication")
async def admin_catalog_point_content_publication(
    payload: CatalogPointPublicationRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return set_point_content_publication(node_id=node_id, payload=payload, user=user)


@router.post("/nodes/{node_id}/media-bindings")
async def admin_catalog_bind_media(
    payload: CatalogPointMediaBindRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return bind_existing_media(node_id=node_id, payload=payload, user=user)


@router.post("/media-bindings/{binding_id}/{action}")
async def admin_catalog_media_binding_status(
    binding_id: str = Path(min_length=1),
    action: str = Path(pattern="^(publish|unpublish|delete)$"),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return set_media_binding_status(binding_id=binding_id, action=action, user=user)


@router.put("/nodes/{node_id}/related-links")
async def admin_catalog_replace_related_links(
    payload: CatalogPointRelatedLinksRequest,
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return replace_related_links(node_id=node_id, payload=payload, user=user)


@router.get("/nodes/{node_id}/validation")
async def admin_catalog_validate_node(
    node_id: str = Path(min_length=1),
    include_subtree: bool = False,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    with db_session() as session:
        return validate_selected_node(session, node_id=node_id, include_subtree=include_subtree)


@router.get("/nodes/{node_id}/job-state")
async def admin_catalog_point_job_state(
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return catalog_point_job_state(node_id=node_id)


@router.get("/nodes/{node_id}/ai-context")
async def admin_catalog_point_ai_context(
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return catalog_point_ai_context(node_id=node_id)


@router.post("/nodes/{node_id}/rag-probe")
async def admin_catalog_point_rag_probe(
    node_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return catalog_point_rag_probe(node_id=node_id)


@router.post("/nodes/{node_id}/jobs/{action}")
async def admin_catalog_trigger_point_job(
    node_id: str = Path(min_length=1),
    action: str = Path(pattern="^(es-refresh|es-delete|rag-refresh|rag-delete|retry)$"),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return trigger_catalog_point_job(node_id=node_id, action=action, user=user)


@router.get("/search")
async def admin_catalog_search(
    q: str = Query(default="", max_length=200),
    chapter_id: str | None = None,
    limit: int = Query(default=80, ge=1, le=200),
    status_filter: str = Query(default="all", max_length=40),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return search_catalog_nodes(query=q, chapter_id=chapter_id, limit=limit, status_filter=status_filter)

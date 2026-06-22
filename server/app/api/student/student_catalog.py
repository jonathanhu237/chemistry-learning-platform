from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from server.app.auth import AuthUser, require_roles
from server.app.catalog_tree_schemas import (
    StudentCatalogChapterResponse,
    StudentCatalogNodeResponse,
    StudentPointDetailResponse,
)
from server.app.domains.catalog_tree.tree import (
    student_catalog_node,
    student_chapter_catalog,
    student_point_detail,
)


router = APIRouter(prefix="/api/student", tags=["student-catalog"])
StudentUser = Annotated[AuthUser, Depends(require_roles("student"))]


@router.get("/chapters/{chapter_id}/catalog", response_model=StudentCatalogChapterResponse)
def student_chapter_catalog_route(
    chapter_id: Annotated[str, Path(min_length=1)],
    user: StudentUser,
) -> StudentCatalogChapterResponse:
    return StudentCatalogChapterResponse(**student_chapter_catalog(chapter_id=chapter_id))


@router.get("/catalog/nodes/{node_id}", response_model=StudentCatalogNodeResponse)
def student_catalog_node_route(
    node_id: Annotated[str, Path(min_length=1)],
    user: StudentUser,
) -> StudentCatalogNodeResponse:
    return StudentCatalogNodeResponse(**student_catalog_node(node_id=node_id))


@router.get("/catalog/points/{node_id}", response_model=StudentPointDetailResponse)
def student_point_detail_route(
    node_id: Annotated[str, Path(min_length=1)],
    user: StudentUser,
) -> StudentPointDetailResponse:
    return StudentPointDetailResponse(**student_point_detail(node_id=node_id))

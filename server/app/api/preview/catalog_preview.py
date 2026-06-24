from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query
from fastapi.responses import FileResponse

from server.app.catalog_tree_schemas import CatalogPreviewNodeResponse, StudentPointDetailResponse
from server.app.domains.catalog_tree.files import preview_media_asset_file, preview_media_thumbnail_file
from server.app.domains.catalog_tree.preview import assert_preview_media_scope, preview_catalog_node, preview_point_detail


router = APIRouter(prefix="/api/preview", tags=["catalog-preview"])


@router.get("/catalog/points/{node_id}", response_model=StudentPointDetailResponse)
def preview_catalog_point_detail_route(
    node_id: Annotated[str, Path(min_length=1)],
    preview_token: Annotated[str, Query(min_length=1)],
) -> StudentPointDetailResponse:
    return StudentPointDetailResponse(**preview_point_detail(node_id=node_id, preview_token=preview_token))


@router.get("/catalog/nodes/{node_id}", response_model=CatalogPreviewNodeResponse)
def preview_catalog_node_route(
    node_id: Annotated[str, Path(min_length=1)],
    preview_token: Annotated[str, Query(min_length=1)],
) -> CatalogPreviewNodeResponse:
    return CatalogPreviewNodeResponse(**preview_catalog_node(node_id=node_id, preview_token=preview_token))


@router.get("/media/assets/{asset_id}/stream", include_in_schema=False)
def preview_media_stream(
    asset_id: Annotated[str, Path(min_length=1)],
    preview_token: Annotated[str, Query(min_length=1)],
) -> FileResponse:
    node_id = assert_preview_media_scope(asset_id=asset_id, preview_token=preview_token)
    path, media_type, filename = preview_media_asset_file(asset_id, node_id=node_id)
    return FileResponse(path, media_type=media_type, filename=filename)


@router.get("/media/assets/{asset_id}/thumbnail", include_in_schema=False)
def preview_media_thumbnail(
    asset_id: Annotated[str, Path(min_length=1)],
    preview_token: Annotated[str, Query(min_length=1)],
) -> FileResponse:
    node_id = assert_preview_media_scope(asset_id=asset_id, preview_token=preview_token)
    path, media_type, filename = preview_media_thumbnail_file(asset_id, node_id=node_id)
    return FileResponse(path, media_type=media_type, filename=filename)

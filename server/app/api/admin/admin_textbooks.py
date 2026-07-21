from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from server.app.auth import AuthUser, require_teacher_console_user
from server.app.domains.errors import DomainHTTPException
from server.app.domains.textbook_ingestion.contracts import IngestionJobView, TextbookDocumentView
from server.app.domains.textbook_ingestion.config import (
    effective_ingestion_settings,
    ingestion_processing_readiness,
)
from server.app.domains.textbook_ingestion.errors import TextbookIngestionError
from server.app.domains.textbook_ingestion.lifecycle import (
    deactivate_textbook,
    delete_textbook,
    publish_textbook,
)
from server.app.domains.textbook_ingestion.queue import request_cancellation, retry_job
from server.app.domains.textbook_ingestion.repository import (
    create_textbook_upload,
    get_ingestion_job,
    get_textbook_document,
    list_document_chunks,
    list_document_pages,
    list_ingestion_job_events,
    list_textbook_documents,
)
from server.app.domains.textbook_ingestion.views import (
    public_chunk,
    public_document,
    public_job,
    public_page,
)
from server.app.domains.textbook_rag.clients import endpoint_configured


router = APIRouter(prefix="/api/admin/textbooks", tags=["admin-textbooks"])


def _translate_error(exc: TextbookIngestionError) -> DomainHTTPException:
    return DomainHTTPException(status_code=exc.status_code, detail=exc.detail())


@router.get("/upload-policy")
def admin_textbook_upload_policy(
    _user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    settings = effective_ingestion_settings()
    readiness = ingestion_processing_readiness(settings)
    return {
        "enabled": readiness["ready"],
        "processing_readiness": readiness,
        "max_upload_mb": settings.max_textbook_upload_mb,
        "max_upload_bytes": settings.max_textbook_upload_mb * 1024 * 1024,
        "max_pages": settings.max_textbook_pages,
        "allowed_extensions": [".pdf"],
        "ocr": {
            "provider": settings.textbook_ocr_provider,
            "protocol": settings.textbook_ocr_protocol,
            "endpoint_configured": endpoint_configured(
                settings.textbook_ocr_base_url,
                settings.textbook_ocr_endpoint,
            ),
            "model": settings.textbook_ocr_model,
            "enabled": settings.textbook_ocr_enabled,
            "credential_configured": bool(settings.textbook_ocr_api_key),
        },
    }


@router.post("", response_model=TextbookDocumentView, status_code=201)
def admin_upload_textbook(
    title: str = Form(min_length=1, max_length=300),
    file: UploadFile = File(),
    logical_textbook_key: str | None = Form(default=None, max_length=128),
    version_label: str | None = Form(default=None, max_length=120),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        document = create_textbook_upload(
            title=title,
            filename=file.filename or "textbook.pdf",
            stream=file.file,
            content_type=file.content_type,
            uploaded_by=user.id,
            logical_textbook_key=logical_textbook_key,
            version_label=version_label,
        )
        return public_document(document)
    except TextbookIngestionError as exc:
        raise _translate_error(exc) from exc
    finally:
        file.file.close()


@router.get("")
def admin_list_textbooks(
    include_deleted: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    _user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        result = list_textbook_documents(include_deleted=include_deleted, limit=limit)
        return {"items": [public_document(item) for item in result["items"]], "total": result["total"]}
    except TextbookIngestionError as exc:
        raise _translate_error(exc) from exc


@router.get("/jobs/{job_id}", response_model=IngestionJobView)
def admin_get_textbook_job(
    job_id: UUID,
    _user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return public_job(get_ingestion_job(str(job_id))) or {}
    except TextbookIngestionError as exc:
        raise _translate_error(exc) from exc


@router.get("/jobs/{job_id}/events")
def admin_get_textbook_job_events(
    job_id: UUID,
    limit: int = Query(default=500, ge=1, le=2000),
    _user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return list_ingestion_job_events(str(job_id), limit=limit)
    except TextbookIngestionError as exc:
        raise _translate_error(exc) from exc


@router.post("/jobs/{job_id}/cancel", response_model=IngestionJobView)
def admin_cancel_textbook_job(
    job_id: UUID,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return public_job(request_cancellation(str(job_id), actor_id=user.id)) or {}
    except TextbookIngestionError as exc:
        raise _translate_error(exc) from exc


@router.post("/jobs/{job_id}/retry", response_model=IngestionJobView)
def admin_retry_textbook_job(
    job_id: UUID,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return public_job(retry_job(str(job_id), actor_id=user.id)) or {}
    except TextbookIngestionError as exc:
        raise _translate_error(exc) from exc


@router.post("/{document_id}/publish", response_model=TextbookDocumentView)
def admin_publish_textbook(
    document_id: str,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return public_document(publish_textbook(document_id, actor_id=user.id))
    except TextbookIngestionError as exc:
        raise _translate_error(exc) from exc


@router.post("/{document_id}/deactivate", response_model=TextbookDocumentView)
def admin_deactivate_textbook(
    document_id: str,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return public_document(deactivate_textbook(document_id, actor_id=user.id))
    except TextbookIngestionError as exc:
        raise _translate_error(exc) from exc


@router.delete("/{document_id}", response_model=TextbookDocumentView)
def admin_delete_textbook(
    document_id: str,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return public_document(delete_textbook(document_id, actor_id=user.id))
    except TextbookIngestionError as exc:
        raise _translate_error(exc) from exc


@router.get("/{document_id}", response_model=TextbookDocumentView)
def admin_get_textbook(
    document_id: str,
    _user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        return public_document(get_textbook_document(document_id))
    except TextbookIngestionError as exc:
        raise _translate_error(exc) from exc


@router.get("/{document_id}/pages")
def admin_get_textbook_pages(
    document_id: str,
    limit: int = Query(default=1000, ge=1, le=5000),
    _user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        result = list_document_pages(document_id, limit=limit)
        return {"items": [public_page(item) for item in result["items"]], "total": result["total"]}
    except TextbookIngestionError as exc:
        raise _translate_error(exc) from exc


@router.get("/{document_id}/chunks")
def admin_get_textbook_chunks(
    document_id: str,
    limit: int = Query(default=500, ge=1, le=5000),
    _user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    try:
        result = list_document_chunks(document_id, limit=limit)
        return {"items": [public_chunk(item) for item in result["items"]], "total": result["total"]}
    except TextbookIngestionError as exc:
        raise _translate_error(exc) from exc

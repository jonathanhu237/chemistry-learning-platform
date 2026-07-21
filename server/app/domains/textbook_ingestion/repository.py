from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, BinaryIO

from sqlalchemy import text

from server.app.domains.textbook_ingestion.config import processing_config_snapshot, processing_fingerprint
from server.app.domains.textbook_ingestion.errors import TextbookIngestionError
from server.app.domains.textbook_ingestion.identity import normalize_logical_textbook_key
from server.app.domains.textbook_ingestion.storage import LocalTextbookBlobStore, TextbookStorageError
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _document_id() -> str:
    return f"tbk_{uuid.uuid4().hex}"


def _job_id() -> str:
    return str(uuid.uuid4())


def _require_postgres_feature() -> None:
    settings = get_settings()
    if not settings.textbook_ingestion_enabled:
        raise TextbookIngestionError(
            "textbook_ingestion_disabled",
            "Online textbook ingestion is not enabled",
            status_code=409,
        )
    if settings.data_backend != "postgres":
        raise TextbookIngestionError(
            "postgres_required",
            "Online textbook ingestion requires the PostgreSQL data backend",
            status_code=503,
        )


def create_textbook_upload(
    *,
    title: str,
    filename: str,
    stream: BinaryIO,
    content_type: str | None,
    uploaded_by: str | None,
    logical_textbook_key: str | None = None,
    version_label: str | None = None,
) -> dict[str, Any]:
    _require_postgres_feature()
    settings = get_settings()
    logical_key = normalize_logical_textbook_key(title, logical_textbook_key)
    document_id = _document_id()
    store = LocalTextbookBlobStore(settings.textbook_storage_root)
    try:
        blob = store.store_pdf(
            document_id=document_id,
            filename=filename,
            stream=stream,
            content_type=content_type,
            max_bytes=settings.max_textbook_upload_mb * 1024 * 1024,
        )
    except TextbookStorageError as exc:
        status_code = 413 if exc.reason == "file_too_large" else 422
        raise TextbookIngestionError(exc.reason, exc.message, status_code=status_code, **exc.details) from exc

    snapshot = processing_config_snapshot(settings)
    fingerprint = processing_fingerprint(snapshot)
    job_id = _job_id()
    try:
        with db_session() as session:
            session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:logical_key))"), {"logical_key": logical_key})
            previous = (
                session.execute(
                    text(
                        """
                        SELECT id, version_number
                        FROM source_documents
                        WHERE logical_textbook_key = :logical_key
                        ORDER BY version_number DESC
                        LIMIT 1
                        """
                    ),
                    {"logical_key": logical_key},
                )
                .mappings()
                .first()
            )
            version_number = int(previous["version_number"] if previous else 0) + 1
            duplicate = (
                session.execute(
                    text(
                        """
                        SELECT id, logical_textbook_key, version_number
                        FROM source_documents
                        WHERE checksum_sha256 = :checksum_sha256
                          AND size_bytes = :size_bytes
                        ORDER BY created_at DESC
                        LIMIT 1
                        """
                    ),
                    {"checksum_sha256": blob.checksum_sha256, "size_bytes": blob.size_bytes},
                )
                .mappings()
                .first()
            )
            metadata = {
                "book_title": title.strip(),
                "source_collection": logical_key,
                "source_role": "canonical_textbook",
                "authority_level": "primary",
                "source_origin": "online_upload",
                "duplicate_of_document_id": str(duplicate["id"]) if duplicate else None,
            }
            effective_version_label = (version_label or "").strip() or f"v{version_number}"
            session.execute(
                text(
                    """
                    INSERT INTO source_documents (
                      id, title, file_name, path, type, document_kind, size_bytes,
                      processing_status, metadata, logical_textbook_key, version_number,
                      version_label, publication_status, checksum_sha256, mime_type,
                      uploaded_by, supersedes_document_id, processing_fingerprint,
                      quality_summary, updated_at
                    )
                    VALUES (
                      :id, :title, :file_name, :path, 'pdf', 'textbook', :size_bytes,
                      'uploaded', CAST(:metadata AS jsonb), :logical_textbook_key, :version_number,
                      :version_label, 'draft', :checksum_sha256, :mime_type,
                      CAST(:uploaded_by AS uuid), :supersedes_document_id, :processing_fingerprint,
                      '{}'::jsonb, now()
                    )
                    """
                ),
                {
                    "id": document_id,
                    "title": title.strip(),
                    "file_name": Path(filename).name,
                    "path": blob.relative_path,
                    "size_bytes": blob.size_bytes,
                    "metadata": _json(metadata),
                    "logical_textbook_key": logical_key,
                    "version_number": version_number,
                    "version_label": effective_version_label,
                    "checksum_sha256": blob.checksum_sha256,
                    "mime_type": blob.mime_type,
                    "uploaded_by": uploaded_by,
                    "supersedes_document_id": str(previous["id"]) if previous else None,
                    "processing_fingerprint": fingerprint,
                },
            )
            session.execute(
                text(
                    """
                    INSERT INTO textbook_ingestion_jobs (
                      id, document_id, status, progress, idempotency_key,
                      processing_fingerprint, config_snapshot, created_by
                    )
                    VALUES (
                      CAST(:id AS uuid), :document_id, 'uploaded', 0, :idempotency_key,
                      :processing_fingerprint, CAST(:config_snapshot AS jsonb), CAST(:created_by AS uuid)
                    )
                    """
                ),
                {
                    "id": job_id,
                    "document_id": document_id,
                    "idempotency_key": f"{document_id}:{fingerprint}",
                    "processing_fingerprint": fingerprint,
                    "config_snapshot": _json(snapshot),
                    "created_by": uploaded_by,
                },
            )
            session.execute(
                text(
                    """
                    INSERT INTO textbook_ingestion_job_events (
                      job_id, status, progress, event_type, message, details
                    )
                    VALUES (
                      CAST(:job_id AS uuid), 'uploaded', 0, 'created',
                      'Textbook uploaded and queued for processing', CAST(:details AS jsonb)
                    )
                    """
                ),
                {
                    "job_id": job_id,
                    "details": _json({"checksum_sha256": blob.checksum_sha256, "size_bytes": blob.size_bytes}),
                },
            )
            session.execute(
                text(
                    """
                    INSERT INTO textbook_lifecycle_events (
                      document_id, job_id, action, actor_id, details
                    )
                    VALUES (
                      :document_id, CAST(:job_id AS uuid), 'uploaded', CAST(:actor_id AS uuid),
                      CAST(:details AS jsonb)
                    )
                    """
                ),
                {
                    "document_id": document_id,
                    "job_id": job_id,
                    "actor_id": uploaded_by,
                    "details": _json({"file_name": Path(filename).name, "duplicate_of": metadata["duplicate_of_document_id"]}),
                },
            )
    except Exception:
        store.delete(blob.relative_path)
        raise

    return get_textbook_document(document_id)


def _latest_job_select() -> str:
    return """
      SELECT tij.*
      FROM textbook_ingestion_jobs tij
      WHERE tij.document_id = sd.id
      ORDER BY tij.created_at DESC
      LIMIT 1
    """


def _serialize_row(row: Any) -> dict[str, Any]:
    result = dict(row)
    for key in ("metadata", "quality_summary", "config_snapshot", "stage_metrics", "quality_report", "outputs"):
        if key in result:
            result[key] = dict(result[key] or {})
    return result


def list_textbook_documents(*, include_deleted: bool = False, limit: int = 100) -> dict[str, Any]:
    _require_postgres_feature()
    with db_session() as session:
        rows = (
            session.execute(
                text(
                    f"""
                    SELECT sd.*,
                           row_to_json(latest_job) AS latest_job
                    FROM source_documents sd
                    LEFT JOIN LATERAL ({_latest_job_select()}) latest_job ON true
                    WHERE sd.document_kind IN ('textbook', 'canonical_textbook')
                      AND (:include_deleted OR sd.publication_status <> 'deleted')
                    ORDER BY sd.updated_at DESC
                    LIMIT :limit
                    """
                ),
                {"include_deleted": include_deleted, "limit": max(1, min(limit, 500))},
            )
            .mappings()
            .all()
        )
    items = []
    for row in rows:
        item = _serialize_row(row)
        item["latest_job"] = dict(item["latest_job"] or {}) or None
        items.append(item)
    return {"items": items, "total": len(items)}


def get_textbook_document(document_id: str) -> dict[str, Any]:
    _require_postgres_feature()
    with db_session() as session:
        row = (
            session.execute(
                text(
                    f"""
                    SELECT sd.*,
                           row_to_json(latest_job) AS latest_job
                    FROM source_documents sd
                    LEFT JOIN LATERAL ({_latest_job_select()}) latest_job ON true
                    WHERE sd.id = :document_id
                      AND sd.document_kind IN ('textbook', 'canonical_textbook')
                    """
                ),
                {"document_id": document_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise TextbookIngestionError("textbook_not_found", "Textbook document not found", status_code=404)
    result = _serialize_row(row)
    result["latest_job"] = dict(result["latest_job"] or {}) or None
    return result


def get_ingestion_job(job_id: str) -> dict[str, Any]:
    _require_postgres_feature()
    with db_session() as session:
        row = (
            session.execute(
                text("SELECT * FROM textbook_ingestion_jobs WHERE id = CAST(:job_id AS uuid)"),
                {"job_id": job_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise TextbookIngestionError("ingestion_job_not_found", "Textbook ingestion job not found", status_code=404)
    return _serialize_row(row)


def list_ingestion_job_events(job_id: str, *, limit: int = 500) -> dict[str, Any]:
    get_ingestion_job(job_id)
    with db_session() as session:
        rows = (
            session.execute(
                text(
                    """
                    SELECT id, job_id, status, progress, event_type, message, details, created_at
                    FROM textbook_ingestion_job_events
                    WHERE job_id = CAST(:job_id AS uuid)
                    ORDER BY id
                    LIMIT :limit
                    """
                ),
                {"job_id": job_id, "limit": max(1, min(limit, 2000))},
            )
            .mappings()
            .all()
        )
    return {"items": [_serialize_row(row) for row in rows], "total": len(rows)}


def list_document_pages(document_id: str, *, limit: int = 1000) -> dict[str, Any]:
    get_textbook_document(document_id)
    with db_session() as session:
        rows = (
            session.execute(
                text(
                    """
                    SELECT document_id, page_number, extraction_method, text, markdown,
                           blocks, content_hash, quality_score, quality_flags, needs_ocr,
                           ocr_provider, ocr_model, diagnostics, updated_at
                    FROM textbook_document_pages
                    WHERE document_id = :document_id
                    ORDER BY page_number
                    LIMIT :limit
                    """
                ),
                {"document_id": document_id, "limit": max(1, min(limit, 5000))},
            )
            .mappings()
            .all()
        )
    return {"items": [dict(row) for row in rows], "total": len(rows)}


def list_document_chunks(document_id: str, *, limit: int = 500) -> dict[str, Any]:
    get_textbook_document(document_id)
    with db_session() as session:
        rows = (
            session.execute(
                text(
                    """
                    SELECT id, document_id, document_version, chunk_index, text, markdown,
                           page_number AS page_start, page_end, section_title, section_path,
                           content_type, content_hash, parent_chunk_id, previous_chunk_id,
                           next_chunk_id, extraction_method, quality_flags, review_required,
                           content_status, metadata, updated_at
                    FROM source_chunks
                    WHERE document_id = :document_id
                    ORDER BY chunk_index
                    LIMIT :limit
                    """
                ),
                {"document_id": document_id, "limit": max(1, min(limit, 5000))},
            )
            .mappings()
            .all()
        )
    return {"items": [_serialize_row(row) for row in rows], "total": len(rows)}

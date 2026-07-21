from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from server.app.domains.textbook_ingestion.contracts import NormalizedPage, StableChunk
from server.app.domains.textbook_ingestion.errors import (
    TextbookIngestionError,
    TextbookJobLeaseLostError,
)
from server.app.domains.textbook_ingestion.queue import ClaimedIngestionJob
from server.app.domains.textbook_ingestion.storage import (
    PDF_MAGIC,
    LocalTextbookBlobStore,
    TextbookStorageError,
)
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings


@dataclass(frozen=True)
class TextbookProcessingInput:
    job_id: str
    document_id: str
    logical_textbook_key: str
    document_version: int
    title: str
    file_name: str
    relative_path: str
    source_path: Path
    mime_type: str
    checksum_sha256: str | None
    metadata: dict[str, Any]
    processing_fingerprint: str
    config_snapshot: dict[str, Any]


def _json(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )


def _dict(value: Any, *, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TextbookIngestionError(
            "invalid_textbook_record",
            f"Textbook {field_name} must be a JSON object",
            status_code=500,
        )
    return dict(value)


def _lock_leased_document(
    session: Session,
    job: ClaimedIngestionJob,
) -> Mapping[str, Any]:
    row = (
        session.execute(
            text(
                """
                SELECT
                  sd.id AS document_id,
                  sd.logical_textbook_key,
                  sd.version_number,
                  sd.title,
                  sd.file_name,
                  sd.path,
                  sd.mime_type,
                  sd.checksum_sha256,
                  sd.metadata,
                  tij.processing_fingerprint,
                  tij.config_snapshot
                FROM textbook_ingestion_jobs tij
                JOIN source_documents sd ON sd.id = tij.document_id
                WHERE tij.id = CAST(:job_id AS uuid)
                  AND tij.document_id = :document_id
                  AND tij.worker_id = :worker_id
                  AND tij.lease_token = CAST(:lease_token AS uuid)
                  AND tij.status = :status
                  AND tij.lease_expires_at > now()
                  AND tij.cancellation_requested_at IS NULL
                FOR UPDATE OF tij, sd
                """
            ),
            {
                "job_id": job.id,
                "document_id": job.document_id,
                "worker_id": job.worker_id,
                "lease_token": job.lease_token,
                "status": job.status.value,
            },
        )
        .mappings()
        .first()
    )
    if row is None:
        raise TextbookJobLeaseLostError(
            f"Lease lost or cancellation requested for textbook ingestion job {job.id}"
        )
    return row


def load_processing_input(
    job: ClaimedIngestionJob,
    *,
    storage_root: Path | None = None,
) -> TextbookProcessingInput:
    """Load immutable source metadata for a currently leased ingestion job."""

    with db_session() as session:
        row = _lock_leased_document(session, job)
        record = dict(row)

    relative_path = str(record.get("path") or "")
    store = LocalTextbookBlobStore(storage_root or get_settings().textbook_storage_root)
    try:
        source_path = store.resolve(relative_path)
    except TextbookStorageError as exc:
        raise TextbookIngestionError(
            exc.reason,
            exc.message,
            status_code=500,
            **exc.details,
        ) from exc

    try:
        with source_path.open("rb") as source:
            signature = source.read(len(PDF_MAGIC))
    except OSError as exc:
        raise TextbookIngestionError(
            "textbook_source_unavailable",
            "The uploaded textbook source is unavailable",
            status_code=500,
            document_id=job.document_id,
        ) from exc
    if signature != PDF_MAGIC:
        raise TextbookIngestionError(
            "invalid_pdf_signature",
            "The stored textbook source does not have a PDF signature",
            status_code=500,
            document_id=job.document_id,
        )

    document_version = int(record["version_number"])
    if document_version <= 0:
        raise TextbookIngestionError(
            "invalid_textbook_record",
            "Textbook document version must be positive",
            status_code=500,
        )
    return TextbookProcessingInput(
        job_id=job.id,
        document_id=str(record["document_id"]),
        logical_textbook_key=str(record["logical_textbook_key"]),
        document_version=document_version,
        title=str(record["title"]),
        file_name=str(record["file_name"]),
        relative_path=relative_path,
        source_path=source_path,
        mime_type=str(record.get("mime_type") or "application/pdf"),
        checksum_sha256=(
            str(record["checksum_sha256"])
            if record.get("checksum_sha256") is not None
            else None
        ),
        metadata=_dict(record.get("metadata"), field_name="metadata"),
        processing_fingerprint=str(record["processing_fingerprint"]),
        config_snapshot=_dict(record.get("config_snapshot"), field_name="config_snapshot"),
    )


def _page_content_hash(page: NormalizedPage, blocks_json: str) -> str:
    if page.content_hash.strip():
        return page.content_hash.strip()
    digest = hashlib.sha256()
    digest.update(page.text.encode("utf-8"))
    digest.update(b"\0")
    digest.update(page.markdown.encode("utf-8"))
    digest.update(b"\0")
    digest.update(blocks_json.encode("utf-8"))
    return digest.hexdigest()


def _page_parameters(
    *,
    job: ClaimedIngestionJob,
    page: NormalizedPage,
) -> dict[str, Any]:
    dumped_page = page.model_dump(mode="json")
    blocks_json = _json(dumped_page["blocks"])
    return {
        "document_id": job.document_id,
        "page_number": page.page_number,
        "job_id": job.id,
        "width_points": page.width_points,
        "height_points": page.height_points,
        "extraction_method": page.extraction_method.value,
        "text": page.text,
        "markdown": page.markdown,
        "blocks": blocks_json,
        "content_hash": _page_content_hash(page, blocks_json),
        "quality_score": page.quality.score,
        "quality_flags": list(page.quality.flags),
        "needs_ocr": page.quality.needs_ocr,
        "ocr_provider": page.ocr_provider,
        "ocr_model": page.ocr_model,
        "diagnostics": _json(dumped_page["diagnostics"]),
    }


def upsert_normalized_pages(
    job: ClaimedIngestionJob,
    pages: Iterable[NormalizedPage],
) -> int:
    """Upsert normalized page facts while fencing every write by the job lease."""

    page_list = list(pages)
    page_numbers = [page.page_number for page in page_list]
    if len(page_numbers) != len(set(page_numbers)):
        raise ValueError("Normalized pages must have unique page numbers")

    with db_session() as session:
        _lock_leased_document(session, job)
        if not page_list:
            return 0
        session.execute(
            text(
                """
                INSERT INTO textbook_document_pages (
                  document_id, page_number, last_job_id, width_points, height_points,
                  extraction_method, text, markdown, blocks, content_hash,
                  quality_score, quality_flags, needs_ocr, ocr_provider, ocr_model,
                  diagnostics, updated_at
                )
                VALUES (
                  :document_id, :page_number, CAST(:job_id AS uuid), :width_points, :height_points,
                  :extraction_method, :text, :markdown, CAST(:blocks AS jsonb), :content_hash,
                  :quality_score, :quality_flags, :needs_ocr, :ocr_provider, :ocr_model,
                  CAST(:diagnostics AS jsonb), now()
                )
                ON CONFLICT (document_id, page_number) DO UPDATE SET
                  last_job_id = EXCLUDED.last_job_id,
                  width_points = EXCLUDED.width_points,
                  height_points = EXCLUDED.height_points,
                  extraction_method = EXCLUDED.extraction_method,
                  text = EXCLUDED.text,
                  markdown = EXCLUDED.markdown,
                  blocks = EXCLUDED.blocks,
                  content_hash = EXCLUDED.content_hash,
                  quality_score = EXCLUDED.quality_score,
                  quality_flags = EXCLUDED.quality_flags,
                  needs_ocr = EXCLUDED.needs_ocr,
                  ocr_provider = EXCLUDED.ocr_provider,
                  ocr_model = EXCLUDED.ocr_model,
                  diagnostics = EXCLUDED.diagnostics,
                  updated_at = now()
                """
            ),
            [_page_parameters(job=job, page=page) for page in page_list],
        )
    return len(page_list)


def _validate_chunks(
    *,
    document_id: str,
    document_version: int,
    chunks: Sequence[StableChunk],
) -> None:
    chunk_ids: set[str] = set()
    chunk_indices: set[int] = set()
    for chunk in chunks:
        if chunk.document_id != document_id:
            raise ValueError(
                f"Chunk {chunk.chunk_id} belongs to {chunk.document_id}, expected {document_id}"
            )
        if chunk.document_version != document_version:
            raise ValueError(
                f"Chunk {chunk.chunk_id} has document version {chunk.document_version}, "
                f"expected {document_version}"
            )
        if chunk.page_end < chunk.page_start:
            raise ValueError(f"Chunk {chunk.chunk_id} ends before it starts")
        if chunk.chunk_id in chunk_ids:
            raise ValueError(f"Duplicate chunk id: {chunk.chunk_id}")
        if chunk.chunk_index in chunk_indices:
            raise ValueError(f"Duplicate chunk index: {chunk.chunk_index}")
        chunk_ids.add(chunk.chunk_id)
        chunk_indices.add(chunk.chunk_index)


def _chunk_parameters(
    *,
    row: Mapping[str, Any],
    chunk: StableChunk,
) -> dict[str, Any]:
    document_version = int(row["version_number"])
    dumped_chunk = chunk.model_dump(mode="json")
    metadata = dict(dumped_chunk["metadata"])
    metadata.update(
        {
            "book_title": str(row["title"]),
            "logical_textbook_key": str(row["logical_textbook_key"]),
            "document_version": document_version,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "section_path": list(chunk.section_path),
            "content_type": chunk.content_type,
            "content_hash": chunk.content_hash,
            "processing_fingerprint": str(row["processing_fingerprint"]),
        }
    )
    return {
        "id": chunk.chunk_id,
        "document_id": str(row["document_id"]),
        "document_version": document_version,
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
        "section_title": chunk.section_title,
        "section_path": list(chunk.section_path),
        "chunk_index": chunk.chunk_index,
        "text": chunk.text,
        "markdown": chunk.markdown,
        "tags": [chunk.content_type],
        "metadata": _json(metadata),
        "content_type": chunk.content_type,
        "content_hash": chunk.content_hash,
        "parent_chunk_id": chunk.parent_chunk_id,
        "previous_chunk_id": chunk.previous_chunk_id,
        "next_chunk_id": chunk.next_chunk_id,
        "extraction_method": chunk.extraction_method.value,
        "processing_fingerprint": str(row["processing_fingerprint"]),
        "quality_flags": list(chunk.quality_flags),
    }


def replace_document_chunks(
    job: ClaimedIngestionJob,
    chunks: Iterable[StableChunk],
) -> int:
    """Atomically replace one draft document's chunks under a fenced lease."""

    chunk_list = list(chunks)
    with db_session() as session:
        row = _lock_leased_document(session, job)
        document_version = int(row["version_number"])
        _validate_chunks(
            document_id=str(row["document_id"]),
            document_version=document_version,
            chunks=chunk_list,
        )
        session.execute(
            text("DELETE FROM source_chunks WHERE document_id = :document_id"),
            {"document_id": str(row["document_id"])},
        )
        if chunk_list:
            session.execute(
                text(
                    """
                    INSERT INTO source_chunks (
                      id, document_id, document_version, page_number, page_end,
                      section_title, section_path, chunk_index, text, markdown,
                      related_knowledge_point_ids, related_experiment_ids, tags,
                      metadata, review_required, content_status, published_at,
                      content_type, content_hash, parent_chunk_id, previous_chunk_id,
                      next_chunk_id, extraction_method, processing_fingerprint,
                      quality_flags, updated_at
                    )
                    VALUES (
                      :id, :document_id, :document_version, :page_start, :page_end,
                      :section_title, :section_path, :chunk_index, :text, :markdown,
                      '{}'::text[], '{}'::text[], :tags,
                      CAST(:metadata AS jsonb), true, 'pending_review', NULL,
                      :content_type, :content_hash, :parent_chunk_id, :previous_chunk_id,
                      :next_chunk_id, :extraction_method, :processing_fingerprint,
                      :quality_flags, now()
                    )
                    """
                ),
                [_chunk_parameters(row=row, chunk=chunk) for chunk in chunk_list],
            )
    return len(chunk_list)

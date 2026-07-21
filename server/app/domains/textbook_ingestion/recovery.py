from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy import text

from server.app.domains.textbook_ingestion.config import effective_ingestion_settings
from server.app.domains.textbook_ingestion.contracts import ExtractionMethod, StableChunk
from server.app.domains.textbook_ingestion.embedding import BatchTextbookEmbedder
from server.app.domains.textbook_ingestion.projection import (
    OnlineTextbookSearchProjector,
    ProjectionDocument,
)
from server.app.domains.textbook_rag.clients import (
    OpenAICompatibleEmbeddingClient,
    TextbookRAGClientError,
    embedding_profile_fingerprint,
    endpoint_configured,
    validate_embedding_protocol,
)
from server.app.domains.textbook_rag.index import TextbookElasticsearchClient
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import Settings


RETAINED_PUBLICATION_STATUSES = ("published", "inactive")
RECREATE_SAFE_PUBLICATION_STATUSES = ("published", "inactive", "review_ready")


class TextbookRecoveryError(RuntimeError):
    def __init__(self, reason: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.reason = reason
        self.details = details


class RecoveryEmbedder(Protocol):
    @property
    def model(self) -> str: ...

    @property
    def profile_fingerprint(self) -> str: ...

    def embed_chunks(self, chunks: Sequence[StableChunk], **kwargs: Any) -> Any: ...


class RecoveryProjector(Protocol):
    def project(
        self,
        chunks: Sequence[StableChunk],
        embeddings: Sequence[Sequence[float]],
        *,
        embedding_model: str,
        embedding_profile_fingerprint: str = "",
    ) -> dict[str, object]: ...

    def delete_projection_run(
        self,
        document_id: str,
        projection_run_id: str,
    ) -> dict[str, object]: ...


@dataclass(frozen=True)
class RetainedOnlineTextbook:
    document_id: str
    logical_textbook_key: str
    document_version: int
    title: str
    publication_status: str
    processing_fingerprint: str
    active_projection_run_id: str | None
    expected_embedding_model: str
    expected_embedding_dimension: int
    chunks: tuple[StableChunk, ...]
    expected_embedding_profile_fingerprint: str = ""


RecoveryProjectorFactory = Callable[[RetainedOnlineTextbook, str], RecoveryProjector]
RecoveryRunCommitter = Callable[
    [RetainedOnlineTextbook, str, dict[str, object]],
    None,
]


def online_textbook_inventory() -> dict[str, Any]:
    """Return online facts that a destructive shared-index recreate could erase."""

    with db_session() as session:
        rows = (
            session.execute(
                text(
                    """
                    SELECT sd.publication_status,
                           count(DISTINCT sd.id) AS document_count,
                           count(sc.id) AS chunk_count
                    FROM source_documents sd
                    LEFT JOIN source_chunks sc ON sc.document_id = sd.id
                    WHERE sd.document_kind = 'textbook'
                      AND sd.publication_status <> 'deleted'
                    GROUP BY sd.publication_status
                    ORDER BY sd.publication_status
                    """
                )
            )
            .mappings()
            .all()
        )
    by_status = {
        str(row["publication_status"]): {
            "documents": int(row["document_count"] or 0),
            "chunks": int(row["chunk_count"] or 0),
        }
        for row in rows
    }
    return {
        "documents": sum(item["documents"] for item in by_status.values()),
        "chunks": sum(item["chunks"] for item in by_status.values()),
        "by_status": by_status,
    }


def count_online_textbooks() -> int:
    return int(online_textbook_inventory()["documents"])


def _embedding_contract(row: dict[str, Any]) -> tuple[str, int, str]:
    config_snapshot = dict(row.get("config_snapshot") or {})
    snapshot_embedding = dict(config_snapshot.get("embedding") or {})
    outputs = dict(row.get("outputs") or {})
    model = str(snapshot_embedding.get("model") or outputs.get("embedding_model") or "").strip()
    dimension = int(
        snapshot_embedding.get("dimension") or outputs.get("embedding_dimension") or 0
    )
    profile = str(
        snapshot_embedding.get("profile_fingerprint")
        or outputs.get("embedding_profile_fingerprint")
        or ""
    ).strip()
    if not profile and snapshot_embedding.get("protocol") and model and dimension > 0:
        profile = embedding_profile_fingerprint(
            provider=str(snapshot_embedding.get("provider") or "openai_compatible"),
            protocol=str(snapshot_embedding.get("protocol") or "openai_embeddings"),
            base_url=str(snapshot_embedding.get("base_url") or ""),
            endpoint=str(snapshot_embedding.get("endpoint") or ""),
            model=model,
            dimensions=dimension,
            send_dimensions=bool(snapshot_embedding.get("send_dimensions", True)),
        )
    return model, dimension, profile


def _stable_chunk(
    row: dict[str, Any],
    *,
    document_version: int,
    processing_fingerprint: str,
) -> StableChunk:
    chunk_document_version = int(row.get("document_version") or 0)
    if chunk_document_version != document_version:
        raise TextbookRecoveryError(
            "chunk_document_version_mismatch",
            f"Chunk {row.get('chunk_id')} does not match its textbook document version",
            expected=document_version,
            actual=chunk_document_version,
        )
    chunk_fingerprint = str(row.get("processing_fingerprint") or "").strip()
    if chunk_fingerprint != processing_fingerprint:
        raise TextbookRecoveryError(
            "chunk_processing_fingerprint_mismatch",
            f"Chunk {row.get('chunk_id')} does not match its textbook processing fingerprint",
        )
    extraction_method = str(row.get("extraction_method") or ExtractionMethod.NATIVE.value)
    try:
        normalized_method = ExtractionMethod(extraction_method)
    except ValueError as exc:
        raise TextbookRecoveryError(
            "invalid_chunk_extraction_method",
            f"Chunk {row.get('chunk_id')} has unsupported extraction method {extraction_method!r}",
        ) from exc
    return StableChunk(
        chunk_id=str(row["chunk_id"]),
        document_id=str(row["document_id"]),
        document_version=document_version,
        chunk_index=int(row["chunk_index"]),
        text=str(row["text"]),
        markdown=str(row.get("markdown") or row["text"]),
        page_start=int(row["page_start"]),
        page_end=int(row.get("page_end") or row["page_start"]),
        section_title=str(row.get("section_title") or ""),
        section_path=[str(item) for item in row.get("section_path") or []],
        content_type=str(row.get("content_type") or "text"),
        content_hash=str(row.get("content_hash") or ""),
        parent_chunk_id=(
            str(row["parent_chunk_id"]) if row.get("parent_chunk_id") else None
        ),
        previous_chunk_id=(
            str(row["previous_chunk_id"]) if row.get("previous_chunk_id") else None
        ),
        next_chunk_id=(str(row["next_chunk_id"]) if row.get("next_chunk_id") else None),
        extraction_method=normalized_method,
        quality_flags=[str(item) for item in row.get("quality_flags") or []],
        metadata=dict(row.get("metadata") or {}),
    )


def load_online_textbooks_for_reprojection(
    *,
    publication_statuses: Sequence[str] = RETAINED_PUBLICATION_STATUSES,
    document_ids: Sequence[str] | None = None,
) -> list[RetainedOnlineTextbook]:
    statuses = [str(item) for item in dict.fromkeys(publication_statuses) if str(item)]
    if not statuses:
        return []
    selected_ids = [str(item) for item in dict.fromkeys(document_ids or ()) if str(item)]
    with db_session() as session:
        document_rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT sd.id, sd.logical_textbook_key, sd.version_number, sd.title,
                           sd.publication_status, sd.processing_fingerprint,
                           sd.active_projection_run_id,
                           latest_job.config_snapshot, latest_job.outputs
                    FROM source_documents sd
                    LEFT JOIN LATERAL (
                      SELECT tij.config_snapshot, tij.outputs
                      FROM textbook_ingestion_jobs tij
                      WHERE tij.document_id = sd.id
                      ORDER BY tij.created_at DESC
                      LIMIT 1
                    ) latest_job ON true
                    WHERE sd.document_kind = 'textbook'
                      AND sd.publication_status = ANY(CAST(:statuses AS text[]))
                      AND (:all_documents OR sd.id = ANY(CAST(:document_ids AS text[])))
                    ORDER BY sd.logical_textbook_key, sd.version_number, sd.id
                    """
                ),
                {
                    "statuses": statuses,
                    "all_documents": not selected_ids,
                    "document_ids": selected_ids,
                },
            )
            .mappings()
            .all()
        ]
        found_ids = {str(row["id"]) for row in document_rows}
        missing_ids = sorted(set(selected_ids) - found_ids)
        if missing_ids:
            raise TextbookRecoveryError(
                "online_textbook_not_rebuildable",
                "One or more requested online textbooks are absent or not in a rebuildable state",
                document_ids=missing_ids,
            )
        chunk_rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT id AS chunk_id, document_id, document_version,
                           processing_fingerprint, chunk_index, text, markdown,
                           page_number AS page_start, page_end, section_title,
                           section_path, content_type, content_hash, parent_chunk_id,
                           previous_chunk_id, next_chunk_id, extraction_method,
                           quality_flags, metadata
                    FROM source_chunks
                    WHERE document_id = ANY(CAST(:document_ids AS text[]))
                    ORDER BY document_id, chunk_index, id
                    """
                ),
                {"document_ids": sorted(found_ids)},
            )
            .mappings()
            .all()
        ] if found_ids else []

    chunks_by_document: dict[str, list[dict[str, Any]]] = {}
    for row in chunk_rows:
        chunks_by_document.setdefault(str(row["document_id"]), []).append(row)

    documents: list[RetainedOnlineTextbook] = []
    for row in document_rows:
        document_id = str(row["id"])
        document_version = int(row["version_number"])
        processing_fingerprint = str(row.get("processing_fingerprint") or "").strip()
        if not processing_fingerprint:
            raise TextbookRecoveryError(
                "processing_fingerprint_missing",
                f"Online textbook {document_id} has no processing fingerprint",
            )
        chunks = tuple(
            _stable_chunk(
                chunk_row,
                document_version=document_version,
                processing_fingerprint=processing_fingerprint,
            )
            for chunk_row in chunks_by_document.get(document_id, [])
        )
        if not chunks:
            raise TextbookRecoveryError(
                "online_textbook_chunks_missing",
                f"Online textbook {document_id} has no PostgreSQL chunks to reproject",
            )
        expected_model, expected_dimension, expected_profile = _embedding_contract(row)
        documents.append(
            RetainedOnlineTextbook(
                document_id=document_id,
                logical_textbook_key=str(row["logical_textbook_key"]),
                document_version=document_version,
                title=str(row["title"]),
                publication_status=str(row["publication_status"]),
                processing_fingerprint=processing_fingerprint,
                active_projection_run_id=(
                    str(row["active_projection_run_id"])
                    if row.get("active_projection_run_id")
                    else None
                ),
                expected_embedding_model=expected_model,
                expected_embedding_dimension=expected_dimension,
                chunks=chunks,
                expected_embedding_profile_fingerprint=expected_profile,
            )
        )
    return documents


def reproject_online_textbooks(
    documents: Sequence[RetainedOnlineTextbook],
    *,
    embedder: RecoveryEmbedder,
    embedding_dimension: int,
    projector_factory: RecoveryProjectorFactory,
    run_committer: RecoveryRunCommitter,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    profile_fingerprint = str(getattr(embedder, "profile_fingerprint", "") or "")
    for document in documents:
        _validate_embedding_contract(
            document,
            embedding_model=embedder.model,
            embedding_dimension=embedding_dimension,
            embedding_profile_fingerprint=profile_fingerprint,
        )
        embedding_result = embedder.embed_chunks(document.chunks)
        vectors = getattr(embedding_result, "vectors", None)
        if not isinstance(vectors, list):
            vectors = list(vectors or [])
        projection_run_id = f"recovery-{uuid.uuid4().hex}"
        projector = projector_factory(document, projection_run_id)
        try:
            projection_kwargs: dict[str, Any] = {"embedding_model": embedder.model}
            if profile_fingerprint:
                projection_kwargs["embedding_profile_fingerprint"] = profile_fingerprint
            projection = projector.project(document.chunks, vectors, **projection_kwargs)
            if not bool(projection.get("index_verified")) or int(
                projection.get("indexed_chunks") or 0
            ) != len(document.chunks):
                raise TextbookRecoveryError(
                    "online_textbook_reprojection_unverified",
                    "Elasticsearch did not verify every recovered online textbook chunk",
                    document_id=document.document_id,
                    expected_chunks=len(document.chunks),
                    projection=projection,
                )
            projected_run_id = str(projection.get("projection_run_id") or "").strip()
            if projected_run_id != projection_run_id:
                raise TextbookRecoveryError(
                    "online_textbook_projection_run_mismatch",
                    "Elasticsearch recovery did not verify the requested projection run",
                    document_id=document.document_id,
                    expected_projection_run_id=projection_run_id,
                    actual_projection_run_id=projected_run_id or None,
                )
            run_committer(document, projection_run_id, projection)
        except Exception as exc:
            try:
                projector.delete_projection_run(
                    document.document_id,
                    projection_run_id,
                )
            except Exception as cleanup_exc:
                raise TextbookRecoveryError(
                    "online_textbook_reprojection_cleanup_failed",
                    "A failed recovery run could not be removed from Elasticsearch",
                    document_id=document.document_id,
                    projection_run_id=projection_run_id,
                    original_reason=str(
                        getattr(exc, "reason", "") or exc.__class__.__name__
                    ),
                    cleanup_reason=str(
                        getattr(cleanup_exc, "reason", "")
                        or cleanup_exc.__class__.__name__
                    ),
                ) from cleanup_exc
            raise
        results.append(
            {
                "document_id": document.document_id,
                "publication_status": document.publication_status,
                "chunks": len(document.chunks),
                "projection_run_id": projection_run_id,
                "projection": projection,
            }
        )
    return {
        "ok": True,
        "documents": len(results),
        "chunks": sum(int(item["chunks"]) for item in results),
        "embedding_model": embedder.model,
        "embedding_dimension": embedding_dimension,
        "embedding_profile_fingerprint": profile_fingerprint,
        "results": results,
    }


def commit_recovered_projection_run(
    document: RetainedOnlineTextbook,
    projection_run_id: str,
    projection: dict[str, object],
) -> None:
    """Fence a verified recovery run into PostgreSQL in its own transaction."""

    if not projection_run_id:
        raise ValueError("projection_run_id is required")
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT id, logical_textbook_key, version_number,
                           publication_status, processing_fingerprint
                    FROM source_documents
                    WHERE id = :document_id
                      AND document_kind = 'textbook'
                    FOR UPDATE
                    """
                ),
                {"document_id": document.document_id},
            )
            .mappings()
            .first()
        )
        if row is None:
            raise TextbookRecoveryError(
                "online_textbook_changed_during_recovery",
                "The online textbook disappeared before its recovered run could be activated",
                document_id=document.document_id,
            )
        record = dict(row)
        session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:logical_key))"),
            {"logical_key": str(record["logical_textbook_key"])},
        )
        if (
            str(record["logical_textbook_key"]) != document.logical_textbook_key
            or int(record["version_number"]) != document.document_version
            or str(record["publication_status"]) != document.publication_status
            or str(record.get("processing_fingerprint") or "")
            != document.processing_fingerprint
        ):
            raise TextbookRecoveryError(
                "online_textbook_changed_during_recovery",
                "The online textbook changed before its recovered run could be activated",
                document_id=document.document_id,
            )
        chunk_facts = [
            (str(chunk_id), str(content_hash or ""))
            for chunk_id, content_hash in session.execute(
                text(
                    """
                    SELECT id, content_hash
                    FROM source_chunks
                    WHERE document_id = :document_id
                    ORDER BY chunk_index, id
                    FOR SHARE
                    """
                ),
                {"document_id": document.document_id},
            ).all()
        ]
        expected_chunk_facts = [
            (chunk.chunk_id, chunk.content_hash)
            for chunk in sorted(document.chunks, key=lambda item: (item.chunk_index, item.chunk_id))
        ]
        if chunk_facts != expected_chunk_facts:
            raise TextbookRecoveryError(
                "online_textbook_changed_during_recovery",
                "The online textbook chunks changed before the recovered run could be activated",
                document_id=document.document_id,
            )
        session.execute(
            text(
                """
                UPDATE source_documents
                SET active_projection_run_id = :projection_run_id,
                    updated_at = now()
                WHERE id = :document_id
                """
            ),
            {
                "document_id": document.document_id,
                "projection_run_id": projection_run_id,
            },
        )
        latest_job_id = session.execute(
            text(
                """
                SELECT id
                FROM textbook_ingestion_jobs
                WHERE document_id = :document_id
                ORDER BY created_at DESC
                LIMIT 1
                FOR UPDATE
                """
            ),
            {"document_id": document.document_id},
        ).scalar_one_or_none()
        if latest_job_id is not None:
            recovered_outputs = {
                "projection_run_id": projection_run_id,
                "index_verified": True,
                "indexed_chunks": len(document.chunks),
                "recovered_projection": dict(projection),
            }
            session.execute(
                text(
                    """
                    UPDATE textbook_ingestion_jobs
                    SET outputs = COALESCE(outputs, '{}'::jsonb) || CAST(:outputs AS jsonb),
                        indexed_chunks = :indexed_chunks,
                        updated_at = now()
                    WHERE id = :job_id
                    """
                ),
                {
                    "job_id": latest_job_id,
                    "indexed_chunks": len(document.chunks),
                    "outputs": json.dumps(recovered_outputs, ensure_ascii=False, default=str),
                },
            )


def _validate_embedding_contract(
    document: RetainedOnlineTextbook,
    *,
    embedding_model: str,
    embedding_dimension: int,
    embedding_profile_fingerprint: str = "",
) -> None:
    if document.expected_embedding_model and document.expected_embedding_model != embedding_model:
        raise TextbookRecoveryError(
            "embedding_model_changed",
            "Configured embedding model does not match the retained textbook processing contract",
            document_id=document.document_id,
            expected=document.expected_embedding_model,
            configured=embedding_model,
        )
    if (
        document.expected_embedding_dimension > 0
        and document.expected_embedding_dimension != embedding_dimension
    ):
        raise TextbookRecoveryError(
            "embedding_dimension_changed",
            "Configured embedding dimension does not match the retained textbook processing contract",
            document_id=document.document_id,
            expected=document.expected_embedding_dimension,
            configured=embedding_dimension,
        )
    if (
        document.expected_embedding_profile_fingerprint
        and document.expected_embedding_profile_fingerprint
        != embedding_profile_fingerprint
    ):
        raise TextbookRecoveryError(
            "embedding_profile_changed",
            "Configured embedding provider contract does not match the retained textbook processing contract",
            document_id=document.document_id,
            expected=document.expected_embedding_profile_fingerprint,
            configured=embedding_profile_fingerprint or None,
        )


def validate_reprojection_configuration(
    settings: Settings,
    *,
    elasticsearch_url: str | None = None,
    index: str | None = None,
) -> None:
    missing: list[str] = []
    if settings.data_backend != "postgres":
        missing.append("postgres_required")
    if not (elasticsearch_url or settings.textbook_rag_elasticsearch_url):
        missing.append("elasticsearch_url_missing")
    if not (index or settings.textbook_rag_elasticsearch_index):
        missing.append("elasticsearch_index_missing")
    if not endpoint_configured(
        settings.textbook_rag_embedding_base_url,
        settings.textbook_rag_embedding_endpoint,
    ):
        missing.append("embedding_base_url_missing")
    if not settings.textbook_rag_embedding_api_key:
        missing.append("embedding_credential_missing")
    if not settings.textbook_rag_embedding_model:
        missing.append("embedding_model_missing")
    if settings.textbook_rag_embedding_dimension <= 0:
        missing.append("embedding_dimension_invalid")
    try:
        validate_embedding_protocol(settings.textbook_rag_embedding_protocol)
    except TextbookRAGClientError:
        missing.append("embedding_protocol_unsupported")
    if missing:
        raise TextbookRecoveryError(
            "online_textbook_reprojection_not_configured",
            "Online textbook reprojection dependencies are not configured",
            missing=missing,
        )


def _settings_embedding_profile(settings: Settings) -> str:
    return embedding_profile_fingerprint(
        provider=settings.textbook_rag_embedding_provider,
        protocol=settings.textbook_rag_embedding_protocol,
        base_url=settings.textbook_rag_embedding_base_url,
        endpoint=settings.textbook_rag_embedding_endpoint,
        model=settings.textbook_rag_embedding_model,
        dimensions=settings.textbook_rag_embedding_dimension,
        send_dimensions=settings.textbook_rag_embedding_send_dimensions,
    )


def preflight_configured_online_reprojection(
    *,
    settings: Settings | None = None,
    elasticsearch_url: str | None = None,
    index: str | None = None,
    publication_statuses: Sequence[str] = RETAINED_PUBLICATION_STATUSES,
    document_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Validate every retained PostgreSQL fact before any destructive ES recreate."""

    effective = effective_ingestion_settings(settings)
    validate_reprojection_configuration(
        effective,
        elasticsearch_url=elasticsearch_url,
        index=index,
    )
    documents = load_online_textbooks_for_reprojection(
        publication_statuses=publication_statuses,
        document_ids=document_ids,
    )
    profile_fingerprint = _settings_embedding_profile(effective)
    for document in documents:
        _validate_embedding_contract(
            document,
            embedding_model=effective.textbook_rag_embedding_model,
            embedding_dimension=effective.textbook_rag_embedding_dimension,
            embedding_profile_fingerprint=profile_fingerprint,
        )
    return {
        "documents": len(documents),
        "chunks": sum(len(document.chunks) for document in documents),
        "embedding_model": effective.textbook_rag_embedding_model,
        "embedding_dimension": effective.textbook_rag_embedding_dimension,
        "embedding_profile_fingerprint": profile_fingerprint,
    }


def reproject_configured_online_textbooks(
    *,
    settings: Settings | None = None,
    elasticsearch_url: str | None = None,
    index: str | None = None,
    publication_statuses: Sequence[str] = RETAINED_PUBLICATION_STATUSES,
    document_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    effective = effective_ingestion_settings(settings)
    preflight_configured_online_reprojection(
        settings=effective,
        elasticsearch_url=elasticsearch_url,
        index=index,
        publication_statuses=publication_statuses,
        document_ids=document_ids,
    )
    documents = load_online_textbooks_for_reprojection(
        publication_statuses=publication_statuses,
        document_ids=document_ids,
    )
    es = TextbookElasticsearchClient(
        base_url=elasticsearch_url or effective.textbook_rag_elasticsearch_url,
        index=index or effective.textbook_rag_elasticsearch_index,
        timeout=effective.textbook_rag_timeout_seconds,
    )
    client = OpenAICompatibleEmbeddingClient(
        base_url=effective.textbook_rag_embedding_base_url,
        api_key=effective.textbook_rag_embedding_api_key,
        model=effective.textbook_rag_embedding_model,
        dimensions=effective.textbook_rag_embedding_dimension,
        timeout_seconds=effective.textbook_rag_timeout_seconds,
        provider=effective.textbook_rag_embedding_provider,
        protocol=effective.textbook_rag_embedding_protocol,
        endpoint=effective.textbook_rag_embedding_endpoint,
        send_dimensions=effective.textbook_rag_embedding_send_dimensions,
    )
    # ES is the only vector store. Recovery intentionally does not use the ES
    # reuse store: after index loss every vector is recomputed by the configured
    # provider from PostgreSQL chunk text.
    embedder = BatchTextbookEmbedder(
        client,
        embedding_dimension=effective.textbook_rag_embedding_dimension,
        batch_size=effective.textbook_embedding_batch_size,
        reuse_store=None,
    )

    def projector_factory(
        document: RetainedOnlineTextbook,
        projection_run_id: str,
    ) -> OnlineTextbookSearchProjector:
        return OnlineTextbookSearchProjector(
            es=es,
            document=ProjectionDocument(
                document_id=document.document_id,
                logical_textbook_key=document.logical_textbook_key,
                document_version=document.document_version,
                title=document.title,
                processing_fingerprint=document.processing_fingerprint,
                projection_run_id=projection_run_id,
            ),
            embedding_dimension=effective.textbook_rag_embedding_dimension,
            batch_size=effective.textbook_index_batch_size,
        )

    return reproject_online_textbooks(
        documents,
        embedder=embedder,
        embedding_dimension=effective.textbook_rag_embedding_dimension,
        projector_factory=projector_factory,
        run_committer=commit_recovered_projection_run,
    )

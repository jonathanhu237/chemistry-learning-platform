from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

from server.app.domains.textbook_ingestion.contracts import StableChunk
from server.app.domains.textbook_rag.index import (
    TextbookElasticsearchClient,
    chunk_document,
    validate_bulk_index_response,
)


class TextbookProjectionError(RuntimeError):
    def __init__(self, reason: str, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.reason = reason
        self.details = details or {}


def elasticsearch_operation_issues(response: Any) -> list[str]:
    """Return integrity issues that make an ES response unsafe to trust.

    Elasticsearch can return HTTP 200 while a delete/count operation timed
    out or only reached part of the index. Cleanup callers must not interpret
    a zero count from a partial shard response as proof that a run is gone.
    """

    if not isinstance(response, dict):
        return ["malformed_response"]

    issues: list[str] = []
    if bool(response.get("timed_out")):
        issues.append("timed_out")
    if response.get("failures"):
        issues.append("failures_reported")

    shards_value = response.get("_shards")
    if shards_value is not None:
        if not isinstance(shards_value, dict):
            issues.append("malformed_shard_summary")
        else:
            try:
                total = int(shards_value.get("total") or 0)
                successful = int(shards_value.get("successful") or 0)
                skipped = int(shards_value.get("skipped") or 0)
                failed = int(shards_value.get("failed") or 0)
            except (TypeError, ValueError):
                issues.append("malformed_shard_summary")
            else:
                if failed:
                    issues.append("shards_failed")
                if total > successful + skipped + failed:
                    issues.append("shards_incomplete")
    return list(dict.fromkeys(issues))


@dataclass(frozen=True)
class ProjectionDocument:
    document_id: str
    logical_textbook_key: str
    document_version: int
    title: str
    processing_fingerprint: str
    projection_run_id: str


class OnlineTextbookSearchProjector:
    def __init__(
        self,
        *,
        es: TextbookElasticsearchClient,
        document: ProjectionDocument,
        embedding_dimension: int,
        batch_size: int = 64,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> None:
        if embedding_dimension <= 0:
            raise ValueError("embedding_dimension must be positive")
        self.es = es
        self.document = document
        self.embedding_dimension = embedding_dimension
        self.batch_size = max(1, batch_size)
        self.progress_callback = progress_callback

    def _source(self, chunk: StableChunk, embedding: Sequence[float], embedding_model: str) -> dict[str, Any]:
        metadata = dict(chunk.metadata)
        row = {
            **metadata,
            "chunk_id": chunk.chunk_id,
            "doc_id": self.document.document_id,
            "document_id": self.document.document_id,
            "logical_textbook_key": self.document.logical_textbook_key,
            "document_version": self.document.document_version,
            "processing_fingerprint": self.document.processing_fingerprint,
            "projection_run_id": self.document.projection_run_id,
            "source_collection": self.document.logical_textbook_key,
            "source_role": "canonical_textbook",
            "authority_level": "primary",
            "book_title": self.document.title,
            "chapter": chunk.section_path[0] if chunk.section_path else chunk.section_title,
            "content_type": chunk.content_type,
            "knowledge_unit": chunk.section_title,
            "section_path": chunk.section_path,
            "clean_text_for_embedding": chunk.text,
            "raw_markdown": chunk.markdown or chunk.text,
            "formulas": metadata.get("formulas") or [],
            "reactions": metadata.get("reactions") or [],
            "compounds": metadata.get("compounds") or [],
            "elements": metadata.get("elements") or [],
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "use_for_question_generation": not bool(metadata.get("exclude_from_question_generation")),
            "content_hash": chunk.content_hash,
            "extraction_method": chunk.extraction_method.value,
            "quality_flags": chunk.quality_flags,
        }
        return chunk_document(
            row,
            source_file=f"online:{self.document.document_id}",
            embedding=[float(value) for value in embedding],
            embedding_model=embedding_model,
        )

    def _index_id(self, chunk: StableChunk) -> str:
        """Keep physical ES identities isolated between worker lease generations."""

        return f"{self.document.projection_run_id}:{chunk.chunk_id}"

    def project(
        self,
        chunks: Sequence[StableChunk],
        embeddings: Sequence[Sequence[float]],
        *,
        embedding_model: str,
    ) -> dict[str, object]:
        if not chunks:
            raise TextbookProjectionError("no_chunks", "A textbook projection cannot be created without chunks")
        if len(chunks) != len(embeddings):
            raise TextbookProjectionError(
                "embedding_count_mismatch",
                "Embedding count does not match textbook chunk count",
                details={"chunks": len(chunks), "embeddings": len(embeddings)},
            )
        if any(chunk.document_id != self.document.document_id for chunk in chunks):
            raise TextbookProjectionError("document_mismatch", "A chunk belongs to a different textbook document")
        if any(chunk.document_version != self.document.document_version for chunk in chunks):
            raise TextbookProjectionError("document_version_mismatch", "A chunk has a different document version")
        invalid_dimensions = [index for index, vector in enumerate(embeddings) if len(vector) != self.embedding_dimension]
        if invalid_dimensions:
            raise TextbookProjectionError(
                "embedding_dimension_mismatch",
                "One or more textbook embeddings have the wrong dimension",
                details={"expected": self.embedding_dimension, "invalid_indexes": invalid_dimensions[:20]},
            )

        self.es.ensure_index(
            embedding_model=embedding_model,
            embedding_dimension=self.embedding_dimension,
            recreate=False,
        )
        # Only clear a partial projection owned by this exact lease generation.
        # Another worker may have reclaimed the job after our last database
        # fence; neither cleanup nor deterministic chunk ids may affect its run.
        if self.progress_callback is not None:
            # Fence external side effects as close as possible to the first ES
            # mutation. The worker heartbeat protects the lease during the call.
            self.progress_callback(0, len(chunks))
        cleanup = self.delete_projection_run(
            self.document.document_id,
            self.document.projection_run_id,
        )
        indexed_ids: list[str] = []
        failures: list[str] = []
        for start in range(0, len(chunks), self.batch_size):
            operations: list[dict[str, Any]] = []
            batch_chunks = chunks[start : start + self.batch_size]
            batch_embeddings = embeddings[start : start + self.batch_size]
            for chunk, embedding in zip(batch_chunks, batch_embeddings):
                operations.append({"index": {"_index": self.es.index, "_id": self._index_id(chunk)}})
                operations.append(self._source(chunk, embedding, embedding_model))
            response = self.es.bulk(operations)
            expected_ids = [self._index_id(chunk) for chunk in batch_chunks]
            successful, batch_failures = validate_bulk_index_response(response, expected_ids=expected_ids)
            indexed_ids.extend(successful)
            failures.extend(batch_failures)
            if self.progress_callback is not None:
                self.progress_callback(len(indexed_ids), len(chunks))
        if failures or len(indexed_ids) != len(chunks):
            raise TextbookProjectionError(
                "elasticsearch_bulk_failed",
                "Elasticsearch did not accept every textbook chunk",
                details={"indexed": len(indexed_ids), "expected": len(chunks), "failures": failures[:50]},
            )

        self.es.request("POST", f"/{self.es.index}/_refresh")
        count_response = self.es.request(
            "POST",
            f"/{self.es.index}/_count",
            {
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"document_id": self.document.document_id}},
                            {"term": {"projection_run_id": self.document.projection_run_id}},
                        ]
                    }
                }
            },
        )
        count_issues = elasticsearch_operation_issues(count_response)
        if count_issues:
            raise TextbookProjectionError(
                "elasticsearch_count_incomplete",
                "Elasticsearch did not verify every shard for the textbook projection",
                details={"issues": count_issues},
            )
        actual_count = int(count_response.get("count") or 0) if isinstance(count_response, dict) else 0
        if actual_count != len(chunks):
            raise TextbookProjectionError(
                "elasticsearch_count_mismatch",
                "Elasticsearch textbook document count does not match PostgreSQL chunks",
                details={"indexed": actual_count, "expected": len(chunks)},
            )
        return {
            "index_verified": True,
            "index_name": self.es.index,
            "document_id": self.document.document_id,
            "projection_run_id": self.document.projection_run_id,
            "indexed_chunks": actual_count,
            "embedding_model": embedding_model,
            "embedding_dimension": self.embedding_dimension,
            "removed_stale_chunks": int(cleanup.get("deleted") or 0),
        }

    def delete_document(self, document_id: str) -> dict[str, object]:
        if document_id != self.document.document_id:
            raise TextbookProjectionError("document_mismatch", "Cannot delete a different textbook projection")
        response = self.es.request(
            "POST",
            f"/{self.es.index}/_delete_by_query?conflicts=proceed&refresh=true",
            {"query": {"term": {"document_id": document_id}}},
        )
        count_response = self.es.request(
            "POST",
            f"/{self.es.index}/_count",
            {"query": {"term": {"document_id": document_id}}},
        )
        delete_issues = elasticsearch_operation_issues(response)
        count_issues = elasticsearch_operation_issues(count_response)
        if delete_issues or count_issues:
            raise TextbookProjectionError(
                "elasticsearch_delete_incomplete",
                "Elasticsearch did not confirm complete textbook deletion across every shard",
                details={
                    "delete_issues": delete_issues,
                    "count_issues": count_issues,
                },
            )
        remaining = int(count_response.get("count") or 0) if isinstance(count_response, dict) else 0
        if remaining:
            raise TextbookProjectionError(
                "elasticsearch_delete_incomplete",
                "Elasticsearch retained textbook chunks after deletion",
                details={"remaining": remaining},
            )
        return {
            "deleted": int(response.get("deleted") or 0) if isinstance(response, dict) else 0,
            "document_id": document_id,
            "index_name": self.es.index,
        }

    def delete_projection_run(self, document_id: str, projection_run_id: str) -> dict[str, object]:
        if document_id != self.document.document_id:
            raise TextbookProjectionError("document_mismatch", "Cannot delete a different textbook projection")
        if not projection_run_id or projection_run_id != self.document.projection_run_id:
            raise TextbookProjectionError("projection_run_mismatch", "Cannot delete a different projection run")
        response = self.es.request(
            "POST",
            f"/{self.es.index}/_delete_by_query?conflicts=proceed&refresh=true",
            {
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"document_id": document_id}},
                            {"term": {"projection_run_id": projection_run_id}},
                        ]
                    }
                }
            },
        )
        count_response = self.es.request(
            "POST",
            f"/{self.es.index}/_count",
            {
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"document_id": document_id}},
                            {"term": {"projection_run_id": projection_run_id}},
                        ]
                    }
                }
            },
        )
        delete_issues = elasticsearch_operation_issues(response)
        count_issues = elasticsearch_operation_issues(count_response)
        if delete_issues or count_issues:
            raise TextbookProjectionError(
                "elasticsearch_delete_incomplete",
                "Elasticsearch did not confirm complete projection-run deletion across every shard",
                details={
                    "delete_issues": delete_issues,
                    "count_issues": count_issues,
                    "projection_run_id": projection_run_id,
                },
            )
        remaining = int(count_response.get("count") or 0) if isinstance(count_response, dict) else 0
        if remaining:
            raise TextbookProjectionError(
                "elasticsearch_delete_incomplete",
                "Elasticsearch retained chunks from this projection run after deletion",
                details={"remaining": remaining, "projection_run_id": projection_run_id},
            )
        return {
            "deleted": int(response.get("deleted") or 0) if isinstance(response, dict) else 0,
            "document_id": document_id,
            "projection_run_id": projection_run_id,
            "index_name": self.es.index,
        }

from __future__ import annotations

import json
import os
import time
from typing import Any, Callable

from server.app.domains.textbook_ingestion.chunking import StructureAwareChunker
from server.app.domains.textbook_ingestion.embedding import (
    BatchTextbookEmbedder,
    ElasticsearchEmbeddingReuseStore,
)
from server.app.domains.textbook_ingestion.extraction import PyMuPDFExtractor
from server.app.domains.textbook_ingestion.mineru import MinerUHTTPProvider
from server.app.domains.textbook_ingestion.persistence import TextbookProcessingInput
from server.app.domains.textbook_ingestion.pipeline import PipelineOutcome, TextbookIngestionPipeline
from server.app.domains.textbook_ingestion.projection import (
    OnlineTextbookSearchProjector,
    ProjectionDocument,
)
from server.app.domains.textbook_ingestion.queue import claim_next_job
from server.app.domains.textbook_rag.clients import QwenEmbeddingClient
from server.app.domains.textbook_rag.index import TextbookElasticsearchClient
from server.app.infrastructure.settings import Settings, get_settings


def build_pipeline(settings: Settings | None = None) -> TextbookIngestionPipeline:
    effective = settings or get_settings()
    es = TextbookElasticsearchClient(
        base_url=effective.textbook_rag_elasticsearch_url,
        index=effective.textbook_rag_elasticsearch_index,
        timeout=effective.textbook_rag_timeout_seconds,
    )
    embedding_client = QwenEmbeddingClient(
        base_url=effective.textbook_rag_embedding_base_url,
        api_key=effective.textbook_rag_embedding_api_key,
        model=effective.textbook_rag_embedding_model,
        dimensions=effective.textbook_rag_embedding_dimension,
        timeout_seconds=effective.textbook_rag_timeout_seconds,
    )
    embedder = BatchTextbookEmbedder(
        embedding_client,
        embedding_dimension=effective.textbook_rag_embedding_dimension,
        batch_size=effective.textbook_embedding_batch_size,
        reuse_store=ElasticsearchEmbeddingReuseStore(es),
    )

    def projector_factory(
        processing_input: TextbookProcessingInput,
        progress_callback: Callable[[int, int], None],
    ) -> OnlineTextbookSearchProjector:
        return OnlineTextbookSearchProjector(
            es=es,
            document=ProjectionDocument(
                document_id=processing_input.document_id,
                logical_textbook_key=processing_input.logical_textbook_key,
                document_version=processing_input.document_version,
                title=processing_input.title,
                processing_fingerprint=processing_input.processing_fingerprint,
            ),
            embedding_dimension=effective.textbook_rag_embedding_dimension,
            batch_size=effective.textbook_index_batch_size,
            progress_callback=progress_callback,
        )

    return TextbookIngestionPipeline(
        extractor=PyMuPDFExtractor(settings=effective),
        ocr_provider=MinerUHTTPProvider(
            base_url=effective.textbook_ocr_base_url,
            api_key=effective.textbook_ocr_api_key,
            model=effective.textbook_ocr_model,
            enabled=effective.textbook_ocr_enabled,
            timeout_seconds=effective.textbook_ocr_timeout_seconds,
            concurrency=effective.textbook_ocr_concurrency,
            max_retries=effective.textbook_ocr_max_retries,
        ),
        chunker=StructureAwareChunker(settings=effective),
        embedder=embedder,
        projector_factory=projector_factory,
        ocr_page_concurrency=effective.textbook_ocr_concurrency,
    )


def _outcome_log(outcome: PipelineOutcome) -> str:
    payload: dict[str, Any] = {
        "event": "textbook_ingestion_job_finished",
        "job_id": outcome.job_id,
        "document_id": outcome.document_id,
        "status": outcome.status.value,
        "total_pages": outcome.total_pages,
        "ocr_pages": outcome.ocr_pages,
        "total_chunks": outcome.total_chunks,
        "retry_scheduled": outcome.retry_scheduled,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def run_once(worker_id: str | None = None, *, settings: Settings | None = None) -> bool:
    effective = settings or get_settings()
    if not effective.textbook_ingestion_enabled:
        raise RuntimeError("TEXTBOOK_INGESTION_ENABLED must be true for the textbook ingestion worker")
    if effective.data_backend != "postgres":
        raise RuntimeError("The textbook ingestion worker requires DATA_BACKEND=postgres")
    job = claim_next_job(worker_id or effective.textbook_ingestion_worker_id)
    if job is None:
        return False
    outcome = build_pipeline(effective).process(job)
    print(_outcome_log(outcome), flush=True)
    return True


def main() -> None:
    settings = get_settings()
    settings.validate_startup()
    once = os.getenv("TEXTBOOK_INGESTION_WORKER_ONCE", "").strip().lower() in {"1", "true", "yes", "on"}
    while True:
        processed = run_once(settings.textbook_ingestion_worker_id, settings=settings)
        if once:
            return
        if not processed:
            time.sleep(max(1, settings.textbook_ingestion_worker_poll_seconds))


if __name__ == "__main__":
    main()

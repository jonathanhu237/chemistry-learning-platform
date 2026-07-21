from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Callable

from server.app.domains.textbook_ingestion.chunking import StructureAwareChunker
from server.app.domains.textbook_ingestion.config import (
    effective_ingestion_settings,
    ingestion_processing_readiness,
    processing_config_snapshot,
    processing_fingerprint,
)
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
from server.app.domains.textbook_ingestion.errors import TextbookJobLeaseLostError
from server.app.domains.textbook_ingestion.queue import (
    ClaimedIngestionJob,
    claim_next_job,
    fail_job,
    heartbeat,
)
from server.app.domains.textbook_ingestion.contracts import IngestionStage
from server.app.domains.textbook_rag.clients import QwenEmbeddingClient
from server.app.domains.textbook_rag.index import TextbookElasticsearchClient
from server.app.infrastructure.settings import Settings


def build_pipeline(settings: Settings | None = None) -> TextbookIngestionPipeline:
    effective = effective_ingestion_settings(settings)
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
        projection_run_id: str,
    ) -> OnlineTextbookSearchProjector:
        return OnlineTextbookSearchProjector(
            es=es,
            document=ProjectionDocument(
                document_id=processing_input.document_id,
                logical_textbook_key=processing_input.logical_textbook_key,
                document_version=processing_input.document_version,
                title=processing_input.title,
                processing_fingerprint=processing_input.processing_fingerprint,
                projection_run_id=projection_run_id,
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


def _worker_error_log(job: ClaimedIngestionJob, error: Exception, *, event: str) -> str:
    return json.dumps(
        {
            "event": event,
            "job_id": job.id,
            "document_id": job.document_id,
            "error_type": error.__class__.__name__,
            "message": " ".join(str(error).split())[:500],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


class _LeaseHeartbeat:
    def __init__(self, job: ClaimedIngestionJob, *, lease_seconds: int) -> None:
        self.job = job
        self.lease_seconds = max(1, lease_seconds)
        self.interval_seconds = max(1, min(30, self.lease_seconds // 3))
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name=f"textbook-heartbeat-{job.id}",
            daemon=True,
        )
        self.error: Exception | None = None

    def _run(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            try:
                heartbeat(self.job, lease_seconds=self.lease_seconds)
            except Exception as exc:  # surfaced by the next fenced pipeline write
                self.error = exc
                self._stop.set()
                return

    def __enter__(self) -> "_LeaseHeartbeat":
        self._thread.start()
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _traceback: Any) -> None:
        self._stop.set()
        self._thread.join(timeout=max(2, self.interval_seconds + 1))


def run_once(worker_id: str | None = None, *, settings: Settings | None = None) -> bool:
    effective = effective_ingestion_settings(settings)
    if not effective.textbook_ingestion_enabled:
        raise RuntimeError("TEXTBOOK_INGESTION_ENABLED must be true for the textbook ingestion worker")
    if effective.data_backend != "postgres":
        raise RuntimeError("The textbook ingestion worker requires DATA_BACKEND=postgres")
    readiness = ingestion_processing_readiness(effective)
    if not readiness["ready"]:
        raise RuntimeError(
            "Textbook ingestion worker dependencies are not configured: "
            + ", ".join(readiness["missing"])
        )
    job = claim_next_job(worker_id or effective.textbook_ingestion_worker_id)
    if job is None:
        return False
    current_snapshot = processing_config_snapshot(effective)
    current_fingerprint = processing_fingerprint(current_snapshot)
    if current_fingerprint != job.processing_fingerprint or current_snapshot != job.config_snapshot:
        error = RuntimeError("Worker processing configuration changed; retry the job to capture the new configuration")
        try:
            fail_job(job, error_code="processing_config_changed", error_message=str(error))
        except TextbookJobLeaseLostError as lease_error:
            print(_worker_error_log(job, lease_error, event="textbook_ingestion_lease_lost"), flush=True)
            return True
        print(_worker_error_log(job, error, event="textbook_ingestion_config_rejected"), flush=True)
        return True
    heartbeat_runner = _LeaseHeartbeat(job, lease_seconds=effective.textbook_ingestion_lease_seconds)
    try:
        with heartbeat_runner:
            outcome = build_pipeline(effective).process(job)
    except TextbookJobLeaseLostError as exc:
        print(_worker_error_log(job, exc, event="textbook_ingestion_lease_lost"), flush=True)
        return True
    except Exception as exc:
        # One unexpected per-job failure must not terminate the long-lived worker.
        print(_worker_error_log(job, exc, event="textbook_ingestion_job_crashed"), flush=True)
        return True
    if heartbeat_runner.error is not None and outcome.status in {
        IngestionStage.EXTRACTING,
        IngestionStage.OCR,
        IngestionStage.STRUCTURING,
        IngestionStage.CHUNKING,
        IngestionStage.EMBEDDING,
        IngestionStage.INDEXING,
    }:
        print(
            _worker_error_log(job, heartbeat_runner.error, event="textbook_ingestion_heartbeat_failed"),
            flush=True,
        )
    print(_outcome_log(outcome), flush=True)
    return True


def main() -> None:
    settings = effective_ingestion_settings()
    settings.validate_startup()
    once = os.getenv("TEXTBOOK_INGESTION_WORKER_ONCE", "").strip().lower() in {"1", "true", "yes", "on"}
    while True:
        # Refresh DB-backed RAG settings between jobs so upload, indexing,
        # publication, and retrieval always share one target contract.
        processed = run_once(settings.textbook_ingestion_worker_id)
        if once:
            return
        if not processed:
            time.sleep(max(1, settings.textbook_ingestion_worker_poll_seconds))


if __name__ == "__main__":
    main()

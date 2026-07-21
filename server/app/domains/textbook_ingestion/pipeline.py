from __future__ import annotations

import asyncio
import time
import urllib.error
from dataclasses import dataclass
from typing import Any, Callable, Protocol, Sequence

from server.app.domains.textbook_ingestion.contracts import (
    IngestionStage,
    NormalizedPage,
    StableChunk,
)
from server.app.domains.textbook_ingestion.embedding import BatchEmbeddingResult
from server.app.domains.textbook_ingestion.errors import (
    TextbookIngestionError,
    TextbookJobLeaseLostError,
)
from server.app.domains.textbook_ingestion.persistence import (
    TextbookProcessingInput,
    load_processing_input,
    replace_document_chunks,
    upsert_normalized_pages,
)
from server.app.domains.textbook_ingestion.ports import OCRProvider, PDFExtractor, TextbookChunker, TextbookSearchProjector
from server.app.domains.textbook_ingestion.quality import build_textbook_quality_report
from server.app.domains.textbook_ingestion.queue import (
    ClaimedIngestionJob,
    acknowledge_cancellation,
    advance_job,
    cancellation_requested,
    fail_job,
    release_job_for_retry,
    update_job_progress,
)
from server.app.domains.textbook_rag.clients import TextbookRAGClientError


class PipelineCancelled(RuntimeError):
    pass


class ChunkEmbedder(Protocol):
    @property
    def model(self) -> str: ...

    def embed_chunks(
        self,
        chunks: Sequence[StableChunk],
        *,
        on_batch: Callable[[int, int], None] | None = None,
    ) -> BatchEmbeddingResult: ...


ProjectorFactory = Callable[
    [TextbookProcessingInput, Callable[[int, int], None]],
    TextbookSearchProjector,
]


@dataclass(frozen=True)
class PipelineOutcome:
    job_id: str
    document_id: str
    status: IngestionStage
    total_pages: int = 0
    ocr_pages: int = 0
    total_chunks: int = 0
    retry_scheduled: bool = False


def _duration_metric(started: float) -> dict[str, int]:
    return {"duration_ms": round((time.monotonic() - started) * 1000)}


def _error_details(exc: Exception) -> tuple[str, str, bool]:
    reason = str(getattr(exc, "reason", "") or exc.__class__.__name__).lower()[:120]
    message = " ".join(str(exc).split())[:1000] or exc.__class__.__name__
    retryable = bool(getattr(exc, "retryable", False)) or isinstance(
        exc,
        (urllib.error.URLError, TimeoutError, OSError),
    )
    if isinstance(exc, TextbookRAGClientError):
        retryable = "not configured" not in message.lower()
    return reason, message, retryable


class TextbookIngestionPipeline:
    def __init__(
        self,
        *,
        extractor: PDFExtractor,
        ocr_provider: OCRProvider,
        chunker: TextbookChunker,
        embedder: ChunkEmbedder,
        projector_factory: ProjectorFactory,
        ocr_page_concurrency: int = 2,
        input_loader: Callable[[ClaimedIngestionJob], TextbookProcessingInput] = load_processing_input,
        page_writer: Callable[[ClaimedIngestionJob, Sequence[NormalizedPage]], int] = upsert_normalized_pages,
        chunk_writer: Callable[[ClaimedIngestionJob, Sequence[StableChunk]], int] = replace_document_chunks,
    ) -> None:
        self.extractor = extractor
        self.ocr_provider = ocr_provider
        self.chunker = chunker
        self.embedder = embedder
        self.projector_factory = projector_factory
        self.ocr_page_concurrency = max(1, ocr_page_concurrency)
        self.input_loader = input_loader
        self.page_writer = page_writer
        self.chunk_writer = chunk_writer

    @staticmethod
    def _ensure_active(job: ClaimedIngestionJob) -> None:
        if cancellation_requested(job):
            raise PipelineCancelled("Textbook ingestion cancellation requested")

    def _extract_pages(
        self,
        job: ClaimedIngestionJob,
        processing_input: TextbookProcessingInput,
    ) -> list[NormalizedPage]:
        pages: list[NormalizedPage] = []
        last_heartbeat = time.monotonic()
        for page in self.extractor.extract(processing_input.source_path):
            pages.append(page)
            if len(pages) % 10 == 0 or time.monotonic() - last_heartbeat >= 30:
                self._ensure_active(job)
                update_job_progress(
                    job,
                    progress=min(18, 1 + len(pages) // 5),
                    counters={"total_pages": len(pages)},
                )
                last_heartbeat = time.monotonic()
        return pages

    async def _ocr_rejected_pages(
        self,
        job: ClaimedIngestionJob,
        processing_input: TextbookProcessingInput,
        pages: list[NormalizedPage],
        rejected_indexes: list[int],
    ) -> list[NormalizedPage]:
        semaphore = asyncio.Semaphore(self.ocr_page_concurrency)
        completed = 0
        native_good = len(pages) - len(rejected_indexes)

        async def process(index: int) -> tuple[int, NormalizedPage]:
            nonlocal completed
            native_page = pages[index]
            async with semaphore:
                rendered = await asyncio.to_thread(
                    self.extractor.render_page,
                    processing_input.source_path,
                    native_page.page_number,
                )
                result = await self.ocr_provider.recognize(
                    rendered,
                    idempotency_key=f"{job.id}:page:{native_page.page_number}:{job.processing_fingerprint}",
                )
                ocr_page = result.page.model_copy(
                    update={
                        "width_points": result.page.width_points or native_page.width_points,
                        "height_points": result.page.height_points or native_page.height_points,
                        "diagnostics": {
                            **native_page.diagnostics,
                            **result.page.diagnostics,
                            "native_quality": native_page.quality.model_dump(mode="json"),
                        },
                    }
                )
                completed += 1
                progress = 20 + round(25 * completed / max(1, len(rejected_indexes)))
                await asyncio.to_thread(
                    update_job_progress,
                    job,
                    progress=progress,
                    counters={
                        "total_pages": len(pages),
                        "processed_pages": native_good + completed,
                        "ocr_pages": completed,
                    },
                    message=(
                        f"OCR processed {completed}/{len(rejected_indexes)} page(s)"
                        if completed == len(rejected_indexes) or completed % 10 == 0
                        else None
                    ),
                )
                return index, ocr_page

        try:
            recognized = await asyncio.gather(*(process(index) for index in rejected_indexes))
            for index, page in recognized:
                pages[index] = page
            return pages
        finally:
            close = getattr(self.ocr_provider, "aclose", None)
            if callable(close):
                await close()

    def _embedding_progress(self, job: ClaimedIngestionJob, completed: int, total: int) -> None:
        self._ensure_active(job)
        progress = 70 + round(15 * completed / max(1, total))
        update_job_progress(
            job,
            progress=progress,
            counters={"embedded_chunks": completed},
            message=f"Embedded {completed}/{total} unique chunk text(s)" if completed == total else None,
        )

    def _index_progress(self, job: ClaimedIngestionJob, completed: int, total: int) -> None:
        self._ensure_active(job)
        progress = 88 + round(10 * completed / max(1, total))
        update_job_progress(
            job,
            progress=progress,
            counters={"indexed_chunks": completed},
            message=f"Indexed {completed}/{total} textbook chunk(s)" if completed == total else None,
        )

    def process(self, claimed_job: ClaimedIngestionJob) -> PipelineOutcome:
        current = claimed_job
        total_pages = 0
        ocr_page_count = 0
        total_chunks = 0
        try:
            self._ensure_active(current)
            processing_input = self.input_loader(current)

            started = time.monotonic()
            pages = self._extract_pages(current, processing_input)
            total_pages = len(pages)
            if not pages:
                raise TextbookIngestionError("pdf_has_no_pages", "The uploaded textbook PDF has no pages", status_code=422)
            rejected_indexes = [index for index, page in enumerate(pages) if page.quality.needs_ocr]
            ocr_page_count = len(rejected_indexes)
            native_processed = total_pages - ocr_page_count
            update_job_progress(
                current,
                progress=20,
                counters={
                    "total_pages": total_pages,
                    "processed_pages": native_processed,
                    "ocr_pages": 0,
                },
                stage_metrics={"extracting": _duration_metric(started)},
                message=f"Native extraction completed for {total_pages} page(s)",
            )

            if rejected_indexes and not self.ocr_provider.configured:
                self.page_writer(current, pages)
                awaiting_report = build_textbook_quality_report(pages, [])
                current = advance_job(
                    current,
                    IngestionStage.AWAITING_OCR,
                    progress=20,
                    counters={
                        "total_pages": total_pages,
                        "processed_pages": native_processed,
                        "ocr_pages": 0,
                    },
                    quality_report=awaiting_report,
                    outputs={"ocr_required_pages": [pages[index].page_number for index in rejected_indexes]},
                    message="OCR is required but the SYSU MinerU provider is not configured",
                )
                return PipelineOutcome(
                    job_id=current.id,
                    document_id=current.document_id,
                    status=current.status,
                    total_pages=total_pages,
                    ocr_pages=ocr_page_count,
                )

            if rejected_indexes:
                current = advance_job(
                    current,
                    IngestionStage.OCR,
                    progress=20,
                    counters={"total_pages": total_pages, "processed_pages": native_processed, "ocr_pages": 0},
                    outputs={"ocr_required_pages": [pages[index].page_number for index in rejected_indexes]},
                    message=f"Queued {ocr_page_count} rejected page(s) for SYSU MinerU OCR",
                )
                ocr_started = time.monotonic()
                pages = asyncio.run(
                    self._ocr_rejected_pages(current, processing_input, pages, rejected_indexes)
                )
                ocr_metric = {
                    **_duration_metric(ocr_started),
                    "page_count": ocr_page_count,
                    "provider": "sysu_aigw_mineru",
                }
            else:
                ocr_metric = {"duration_ms": 0, "page_count": 0, "provider": None}

            self._ensure_active(current)
            current = advance_job(
                current,
                IngestionStage.STRUCTURING,
                progress=50,
                counters={
                    "total_pages": total_pages,
                    "processed_pages": total_pages,
                    "ocr_pages": ocr_page_count,
                },
                stage_metrics={"ocr": ocr_metric},
                message="Normalized textbook page structure",
            )
            structure_started = time.monotonic()
            self.page_writer(current, pages)

            current = advance_job(
                current,
                IngestionStage.CHUNKING,
                progress=58,
                stage_metrics={"structuring": _duration_metric(structure_started)},
                message="Persisted normalized textbook pages",
            )
            chunk_started = time.monotonic()
            chunks = self.chunker.chunk(
                document_id=processing_input.document_id,
                document_version=processing_input.document_version,
                pages=pages,
                processing_fingerprint=processing_input.processing_fingerprint,
            )
            total_chunks = len(chunks)
            self.chunk_writer(current, chunks)
            quality_report = build_textbook_quality_report(pages, chunks)
            update_job_progress(
                current,
                progress=68,
                counters={"total_chunks": total_chunks},
                stage_metrics={"chunking": _duration_metric(chunk_started)},
                quality_report=quality_report,
                message=f"Created {total_chunks} structure-aware textbook chunk(s)",
            )
            if not bool(quality_report.get("publishable")):
                blockers = ", ".join(str(item) for item in quality_report.get("blocking_issues") or [])
                raise TextbookIngestionError(
                    "quality_gate_failed",
                    f"Textbook quality gate failed: {blockers or 'unknown issue'}",
                    status_code=422,
                )

            current = advance_job(
                current,
                IngestionStage.EMBEDDING,
                progress=70,
                counters={"total_chunks": total_chunks},
                quality_report=quality_report,
                message="Textbook chunks passed the quality gate",
            )
            embedding_started = time.monotonic()
            embedding_result = self.embedder.embed_chunks(
                chunks,
                on_batch=lambda completed, total: self._embedding_progress(current, completed, total),
            )

            current = advance_job(
                current,
                IngestionStage.INDEXING,
                progress=88,
                counters={"embedded_chunks": total_chunks},
                stage_metrics={
                    "embedding": {
                        **_duration_metric(embedding_started),
                        "model": self.embedder.model,
                        "reused_chunks": embedding_result.reused_count,
                        "computed_chunks": embedding_result.computed_count,
                        "unique_computed_chunks": embedding_result.unique_computed_count,
                    }
                },
                message=f"Embedded {total_chunks} textbook chunk(s)",
            )
            indexing_started = time.monotonic()
            projector = self.projector_factory(
                processing_input,
                lambda completed, total: self._index_progress(current, completed, total),
            )
            projection = projector.project(
                chunks,
                embedding_result.vectors,
                embedding_model=self.embedder.model,
            )
            if not bool(projection.get("index_verified")):
                raise TextbookIngestionError(
                    "index_not_verified",
                    "Textbook Elasticsearch projection was not verified",
                    status_code=502,
                )

            current = advance_job(
                current,
                IngestionStage.REVIEW_READY,
                progress=100,
                counters={
                    "total_pages": total_pages,
                    "processed_pages": total_pages,
                    "ocr_pages": ocr_page_count,
                    "total_chunks": total_chunks,
                    "embedded_chunks": total_chunks,
                    "indexed_chunks": total_chunks,
                },
                stage_metrics={"indexing": _duration_metric(indexing_started)},
                quality_report=quality_report,
                outputs=dict(projection),
                message="Textbook ingestion completed and is ready for review",
            )
            return PipelineOutcome(
                job_id=current.id,
                document_id=current.document_id,
                status=current.status,
                total_pages=total_pages,
                ocr_pages=ocr_page_count,
                total_chunks=total_chunks,
            )
        except PipelineCancelled:
            acknowledge_cancellation(current)
            return PipelineOutcome(
                job_id=current.id,
                document_id=current.document_id,
                status=IngestionStage.CANCELLED,
                total_pages=total_pages,
                ocr_pages=ocr_page_count,
                total_chunks=total_chunks,
            )
        except TextbookJobLeaseLostError:
            try:
                if cancellation_requested(current):
                    acknowledge_cancellation(current)
                    return PipelineOutcome(
                        job_id=current.id,
                        document_id=current.document_id,
                        status=IngestionStage.CANCELLED,
                        total_pages=total_pages,
                        ocr_pages=ocr_page_count,
                        total_chunks=total_chunks,
                    )
            except TextbookJobLeaseLostError:
                pass
            raise
        except Exception as exc:
            reason, message, retryable = _error_details(exc)
            if retryable and release_job_for_retry(current, error_code=reason, error_message=message):
                return PipelineOutcome(
                    job_id=current.id,
                    document_id=current.document_id,
                    status=IngestionStage.UPLOADED,
                    total_pages=total_pages,
                    ocr_pages=ocr_page_count,
                    total_chunks=total_chunks,
                    retry_scheduled=True,
                )
            fail_job(current, error_code=reason, error_message=message)
            return PipelineOutcome(
                job_id=current.id,
                document_id=current.document_id,
                status=IngestionStage.FAILED,
                total_pages=total_pages,
                ocr_pages=ocr_page_count,
                total_chunks=total_chunks,
            )

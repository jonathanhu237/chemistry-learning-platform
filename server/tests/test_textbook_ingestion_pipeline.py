from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from server.app.domains.textbook_ingestion import pipeline as pipeline_module
from server.app.domains.textbook_ingestion.contracts import (
    ExtractionMethod,
    IngestionStage,
    NormalizedBlock,
    NormalizedPage,
    OCRPageResult,
    PageQuality,
    StableChunk,
)
from server.app.domains.textbook_ingestion.embedding import BatchEmbeddingResult
from server.app.domains.textbook_ingestion.persistence import TextbookProcessingInput
from server.app.domains.textbook_ingestion.pipeline import TextbookIngestionPipeline
from server.app.domains.textbook_ingestion.ports import RenderedPage
from server.app.domains.textbook_ingestion.queue import ClaimedIngestionJob


def _job() -> ClaimedIngestionJob:
    return ClaimedIngestionJob(
        id="11111111-1111-4111-8111-111111111111",
        document_id="tbk-1",
        status=IngestionStage.EXTRACTING,
        attempts=1,
        max_attempts=3,
        worker_id="worker-1",
        lease_token="22222222-2222-4222-8222-222222222222",
        processing_fingerprint="fingerprint",
        config_snapshot={},
    )


def _input() -> TextbookProcessingInput:
    return TextbookProcessingInput(
        job_id=_job().id,
        document_id="tbk-1",
        logical_textbook_key="textbook-inorganic",
        document_version=2,
        title="无机化学",
        file_name="book.pdf",
        relative_path="originals/tbk-1/source.pdf",
        source_path=Path("/tmp/book.pdf"),
        mime_type="application/pdf",
        checksum_sha256="a" * 64,
        metadata={},
        processing_fingerprint="fingerprint",
        config_snapshot={},
    )


def _page(number: int, *, needs_ocr: bool = False, text: str = "原生教材正文") -> NormalizedPage:
    return NormalizedPage(
        page_number=number,
        width_points=595,
        height_points=842,
        text=text,
        markdown=text,
        blocks=[
            NormalizedBlock(
                block_id=f"p{number}-b1",
                block_type="text",
                text=text,
                markdown=text,
            )
        ],
        extraction_method=ExtractionMethod.NATIVE,
        quality=PageQuality(score=0.9 if not needs_ocr else 0.1, needs_ocr=needs_ocr),
        content_hash=f"page-{number}",
    )


def _chunk(page_number: int = 1) -> StableChunk:
    return StableChunk(
        chunk_id=f"chunk-{page_number}",
        document_id="tbk-1",
        document_version=2,
        chunk_index=page_number,
        text=f"教材正文 {page_number}",
        markdown=f"教材正文 {page_number}",
        page_start=page_number,
        page_end=page_number,
        content_hash=f"chunk-hash-{page_number}",
    )


class _Extractor:
    def __init__(self, pages: list[NormalizedPage]) -> None:
        self.pages = pages
        self.rendered: list[int] = []

    def extract(self, _path: Path) -> list[NormalizedPage]:
        return self.pages

    def render_page(self, _path: Path, page_number: int) -> RenderedPage:
        self.rendered.append(page_number)
        return RenderedPage(
            page_number=page_number,
            image_bytes=b"png",
            mime_type="image/png",
            pixel_width=100,
            pixel_height=100,
        )


class _OCR:
    def __init__(self, *, configured: bool = True) -> None:
        self._configured = configured
        self.calls: list[int] = []

    @property
    def configured(self) -> bool:
        return self._configured

    async def recognize(self, page: RenderedPage, *, idempotency_key: str) -> OCRPageResult:
        assert str(page.page_number) in idempotency_key
        self.calls.append(page.page_number)
        normalized = _page(page.page_number, text="OCR 教材正文").model_copy(
            update={
                "extraction_method": ExtractionMethod.MINERU,
                "quality": PageQuality(score=0.95, needs_ocr=False),
            }
        )
        return OCRPageResult(page=normalized, provider="fake", model="fake", latency_ms=1)


class _Chunker:
    def __init__(self, chunks: list[StableChunk]) -> None:
        self.chunks = chunks

    def chunk(self, **_: Any) -> list[StableChunk]:
        return self.chunks


class _Embedder:
    model = "embed-model"

    def embed_chunks(self, chunks: list[StableChunk], *, on_batch: Any = None) -> BatchEmbeddingResult:
        if on_batch:
            on_batch(len(chunks), len(chunks))
        return BatchEmbeddingResult(
            vectors=[[0.1, 0.2] for _ in chunks],
            reused_count=0,
            computed_count=len(chunks),
            unique_computed_count=len(chunks),
        )


class _Projector:
    def project(self, chunks: list[StableChunk], embeddings: list[list[float]], *, embedding_model: str) -> dict[str, Any]:
        assert len(chunks) == len(embeddings)
        assert embedding_model == "embed-model"
        return {"index_verified": True, "indexed_chunks": len(chunks), "index_name": "idx"}

    def delete_document(self, _document_id: str) -> dict[str, Any]:
        return {}


def _install_queue_fakes(monkeypatch: Any) -> dict[str, Any]:
    events: dict[str, Any] = {"transitions": [], "progress": [], "failures": []}

    monkeypatch.setattr(pipeline_module, "cancellation_requested", lambda _job: False)
    monkeypatch.setattr(pipeline_module, "acknowledge_cancellation", lambda _job: None)

    def advance(job: ClaimedIngestionJob, target: IngestionStage, **kwargs: Any) -> ClaimedIngestionJob:
        target = IngestionStage(target)
        events["transitions"].append(target)
        events["advance_kwargs"] = kwargs
        return replace(job, status=target)

    monkeypatch.setattr(pipeline_module, "advance_job", advance)
    monkeypatch.setattr(
        pipeline_module,
        "update_job_progress",
        lambda job, **kwargs: events["progress"].append((job.status, kwargs)),
    )
    monkeypatch.setattr(
        pipeline_module,
        "fail_job",
        lambda job, **kwargs: events["failures"].append((job.status, kwargs)),
    )
    monkeypatch.setattr(pipeline_module, "release_job_for_retry", lambda *_args, **_kwargs: False)
    return events


def _pipeline(
    *,
    extractor: _Extractor,
    ocr: _OCR,
    chunks: list[StableChunk],
    pages_written: list[list[NormalizedPage]],
    chunks_written: list[list[StableChunk]],
) -> TextbookIngestionPipeline:
    return TextbookIngestionPipeline(
        extractor=extractor,
        ocr_provider=ocr,
        chunker=_Chunker(chunks),
        embedder=_Embedder(),
        projector_factory=lambda _input, callback: (
            callback(len(chunks), len(chunks)) or _Projector()
        ),
        input_loader=lambda _job: _input(),
        page_writer=lambda _job, pages: pages_written.append(list(pages)) or len(pages),
        chunk_writer=lambda _job, values: chunks_written.append(list(values)) or len(values),
    )


def test_pipeline_runs_native_pdf_through_review_ready(monkeypatch: Any) -> None:
    events = _install_queue_fakes(monkeypatch)
    pages_written: list[list[NormalizedPage]] = []
    chunks_written: list[list[StableChunk]] = []
    extractor = _Extractor([_page(1)])
    ocr = _OCR()

    outcome = _pipeline(
        extractor=extractor,
        ocr=ocr,
        chunks=[_chunk(1)],
        pages_written=pages_written,
        chunks_written=chunks_written,
    ).process(_job())

    assert outcome.status == IngestionStage.REVIEW_READY
    assert events["transitions"] == [
        IngestionStage.STRUCTURING,
        IngestionStage.CHUNKING,
        IngestionStage.EMBEDDING,
        IngestionStage.INDEXING,
        IngestionStage.REVIEW_READY,
    ]
    assert extractor.rendered == []
    assert ocr.calls == []
    assert len(pages_written) == 1
    assert len(chunks_written) == 1
    assert events["failures"] == []


def test_pipeline_stops_at_awaiting_ocr_when_provider_is_not_configured(monkeypatch: Any) -> None:
    events = _install_queue_fakes(monkeypatch)
    pages_written: list[list[NormalizedPage]] = []
    chunks_written: list[list[StableChunk]] = []

    outcome = _pipeline(
        extractor=_Extractor([_page(1, needs_ocr=True, text="")]),
        ocr=_OCR(configured=False),
        chunks=[],
        pages_written=pages_written,
        chunks_written=chunks_written,
    ).process(_job())

    assert outcome.status == IngestionStage.AWAITING_OCR
    assert events["transitions"] == [IngestionStage.AWAITING_OCR]
    assert len(pages_written) == 1
    assert chunks_written == []


def test_pipeline_ocr_only_replaces_rejected_pages(monkeypatch: Any) -> None:
    events = _install_queue_fakes(monkeypatch)
    pages_written: list[list[NormalizedPage]] = []
    chunks_written: list[list[StableChunk]] = []
    extractor = _Extractor([_page(1), _page(2, needs_ocr=True, text="")])
    ocr = _OCR()

    outcome = _pipeline(
        extractor=extractor,
        ocr=ocr,
        chunks=[_chunk(1), _chunk(2)],
        pages_written=pages_written,
        chunks_written=chunks_written,
    ).process(_job())

    assert outcome.status == IngestionStage.REVIEW_READY
    assert events["transitions"][0] == IngestionStage.OCR
    assert extractor.rendered == [2]
    assert ocr.calls == [2]
    assert pages_written[0][0].extraction_method == ExtractionMethod.NATIVE
    assert pages_written[0][1].extraction_method == ExtractionMethod.MINERU


def test_pipeline_records_terminal_quality_failure(monkeypatch: Any) -> None:
    events = _install_queue_fakes(monkeypatch)

    outcome = _pipeline(
        extractor=_Extractor([_page(1)]),
        ocr=_OCR(),
        chunks=[],
        pages_written=[],
        chunks_written=[],
    ).process(_job())

    assert outcome.status == IngestionStage.FAILED
    assert events["transitions"] == [IngestionStage.STRUCTURING, IngestionStage.CHUNKING]
    assert events["failures"][0][1]["error_code"] == "quality_gate_failed"

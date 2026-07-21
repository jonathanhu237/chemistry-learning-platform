from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable, Protocol, Sequence

from server.app.domains.textbook_ingestion.contracts import NormalizedPage, OCRPageResult, StableChunk


@dataclass(frozen=True)
class StoredTextbookBlob:
    relative_path: str
    absolute_path: Path
    checksum_sha256: str
    size_bytes: int
    mime_type: str


@dataclass(frozen=True)
class RenderedPage:
    page_number: int
    image_bytes: bytes
    mime_type: str
    pixel_width: int
    pixel_height: int


class TextbookBlobStore(Protocol):
    def store_pdf(
        self,
        *,
        document_id: str,
        filename: str,
        stream: BinaryIO,
        content_type: str | None,
        max_bytes: int,
        max_pages: int,
        render_dpi: int,
        max_render_pixels: int,
    ) -> StoredTextbookBlob: ...

    def resolve(self, relative_path: str) -> Path: ...

    def delete(self, relative_path: str) -> None: ...


class PDFExtractor(Protocol):
    def extract(self, pdf_path: Path) -> Iterable[NormalizedPage]: ...

    def render_page(self, pdf_path: Path, page_number: int) -> RenderedPage: ...


class OCRProvider(Protocol):
    @property
    def configured(self) -> bool: ...

    async def recognize(self, page: RenderedPage, *, idempotency_key: str) -> OCRPageResult: ...


class TextbookChunker(Protocol):
    def chunk(
        self,
        *,
        document_id: str,
        document_version: int,
        pages: Sequence[NormalizedPage],
        processing_fingerprint: str,
    ) -> list[StableChunk]: ...


class TextEmbedder(Protocol):
    @property
    def model(self) -> str: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class TextbookSearchProjector(Protocol):
    def project(
        self,
        chunks: Sequence[StableChunk],
        embeddings: Sequence[Sequence[float]],
        *,
        embedding_model: str,
    ) -> dict[str, object]: ...

    def delete_document(self, document_id: str) -> dict[str, object]: ...

    def delete_projection_run(self, document_id: str, projection_run_id: str) -> dict[str, object]: ...

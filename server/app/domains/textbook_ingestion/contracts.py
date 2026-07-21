from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IngestionStage(str, Enum):
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    AWAITING_OCR = "awaiting_ocr"
    OCR = "ocr"
    STRUCTURING = "structuring"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    REVIEW_READY = "review_ready"
    READY = "ready"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_INGESTION_STAGES = frozenset(
    {IngestionStage.READY, IngestionStage.FAILED, IngestionStage.CANCELLED}
)

ACTIVE_INGESTION_STAGES = frozenset(
    {
        IngestionStage.EXTRACTING,
        IngestionStage.OCR,
        IngestionStage.STRUCTURING,
        IngestionStage.CHUNKING,
        IngestionStage.EMBEDDING,
        IngestionStage.INDEXING,
    }
)

ALLOWED_STAGE_TRANSITIONS: dict[IngestionStage, frozenset[IngestionStage]] = {
    IngestionStage.UPLOADED: frozenset(
        {IngestionStage.EXTRACTING, IngestionStage.CANCELLED, IngestionStage.FAILED}
    ),
    IngestionStage.EXTRACTING: frozenset(
        {
            IngestionStage.AWAITING_OCR,
            IngestionStage.OCR,
            IngestionStage.STRUCTURING,
            IngestionStage.CANCELLED,
            IngestionStage.FAILED,
        }
    ),
    IngestionStage.AWAITING_OCR: frozenset(
        {IngestionStage.UPLOADED, IngestionStage.OCR, IngestionStage.CANCELLED, IngestionStage.FAILED}
    ),
    IngestionStage.OCR: frozenset(
        {IngestionStage.STRUCTURING, IngestionStage.CANCELLED, IngestionStage.FAILED}
    ),
    IngestionStage.STRUCTURING: frozenset(
        {IngestionStage.CHUNKING, IngestionStage.CANCELLED, IngestionStage.FAILED}
    ),
    IngestionStage.CHUNKING: frozenset(
        {IngestionStage.EMBEDDING, IngestionStage.CANCELLED, IngestionStage.FAILED}
    ),
    IngestionStage.EMBEDDING: frozenset(
        {IngestionStage.INDEXING, IngestionStage.CANCELLED, IngestionStage.FAILED}
    ),
    IngestionStage.INDEXING: frozenset(
        {IngestionStage.REVIEW_READY, IngestionStage.CANCELLED, IngestionStage.FAILED}
    ),
    IngestionStage.REVIEW_READY: frozenset(
        {IngestionStage.READY, IngestionStage.UPLOADED, IngestionStage.CANCELLED, IngestionStage.FAILED}
    ),
    IngestionStage.READY: frozenset({IngestionStage.UPLOADED}),
    IngestionStage.FAILED: frozenset({IngestionStage.UPLOADED, IngestionStage.CANCELLED}),
    IngestionStage.CANCELLED: frozenset({IngestionStage.UPLOADED}),
}


def validate_stage_transition(current: IngestionStage | str, target: IngestionStage | str) -> None:
    current_stage = IngestionStage(current)
    target_stage = IngestionStage(target)
    if target_stage not in ALLOWED_STAGE_TRANSITIONS[current_stage]:
        raise ValueError(f"Invalid ingestion stage transition: {current_stage.value} -> {target_stage.value}")


class DocumentPublicationStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    REVIEW_READY = "review_ready"
    PUBLISHED = "published"
    INACTIVE = "inactive"
    FAILED = "failed"
    DELETED = "deleted"


class BlockType(str, Enum):
    TITLE = "title"
    SECTION_HEADER = "section_header"
    TEXT = "text"
    LIST = "list"
    LIST_ITEM = "list_item"
    TABLE = "table"
    EQUATION = "equation"
    FORMULA_NUMBER = "formula_number"
    CODE = "code"
    ALGORITHM = "algorithm"
    ASIDE_TEXT = "aside_text"
    REF_TEXT = "ref_text"
    INDEX = "index"
    PHONETIC = "phonetic"
    IMAGE = "image"
    CHART = "chart"
    IMAGE_CAPTION = "image_caption"
    TABLE_CAPTION = "table_caption"
    CODE_CAPTION = "code_caption"
    TABLE_FOOTNOTE = "table_footnote"
    IMAGE_FOOTNOTE = "image_footnote"
    PAGE_FOOTNOTE = "page_footnote"
    PAGE_NUMBER = "page_number"
    HEADER = "header"
    FOOTER = "footer"
    IMAGE_BLOCK = "image_block"
    EQUATION_BLOCK = "equation_block"
    UNKNOWN = "unknown"
    OTHER = "other"


class ExtractionMethod(str, Enum):
    NATIVE = "native"
    MINERU = "mineru"
    MIXED = "mixed"


class NormalizedBlock(BaseModel):
    block_id: str
    block_type: BlockType = BlockType.TEXT
    bbox: tuple[int, int, int, int] | None = None
    text: str = ""
    markdown: str = ""
    confidence: float | None = Field(default=None, ge=0, le=1)
    parent_id: str | None = None
    child_ids: list[str] = Field(default_factory=list)
    quality_flags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PageQuality(BaseModel):
    score: float = Field(ge=0, le=1)
    needs_ocr: bool = False
    flags: list[str] = Field(default_factory=list)
    metrics: dict[str, float | int | str | bool | None] = Field(default_factory=dict)


class NormalizedPage(BaseModel):
    page_number: int = Field(gt=0)
    width_points: float | None = Field(default=None, gt=0)
    height_points: float | None = Field(default=None, gt=0)
    text: str = ""
    markdown: str = ""
    blocks: list[NormalizedBlock] = Field(default_factory=list)
    extraction_method: ExtractionMethod = ExtractionMethod.NATIVE
    quality: PageQuality = Field(default_factory=lambda: PageQuality(score=0, needs_ocr=True))
    content_hash: str = ""
    ocr_provider: str | None = None
    ocr_model: str | None = None
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class StableChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_version: int = Field(gt=0)
    chunk_index: int = Field(gt=0)
    text: str = Field(min_length=1)
    markdown: str = ""
    page_start: int = Field(gt=0)
    page_end: int = Field(gt=0)
    section_title: str = ""
    section_path: list[str] = Field(default_factory=list)
    content_type: str = "text"
    content_hash: str
    parent_chunk_id: str | None = None
    previous_chunk_id: str | None = None
    next_chunk_id: str | None = None
    extraction_method: ExtractionMethod = ExtractionMethod.NATIVE
    quality_flags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OCRPageResult(BaseModel):
    page: NormalizedPage
    provider: str
    model: str
    latency_ms: int = Field(ge=0)
    request_id: str | None = None
    warnings: list[str] = Field(default_factory=list)


class IngestionJobView(BaseModel):
    id: str
    document_id: str
    status: IngestionStage
    progress: int = Field(ge=0, le=100)
    attempts: int = Field(ge=0)
    max_attempts: int = Field(gt=0)
    total_pages: int = Field(ge=0)
    processed_pages: int = Field(ge=0)
    ocr_pages: int = Field(ge=0)
    total_chunks: int = Field(ge=0)
    embedded_chunks: int = Field(ge=0)
    indexed_chunks: int = Field(ge=0)
    error_code: str | None = None
    error_message: str | None = None
    stage_metrics: dict[str, Any] = Field(default_factory=dict)
    quality_report: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    allowed_actions: list[str] = Field(default_factory=list)
    ocr: dict[str, Any] = Field(default_factory=dict)


class TextbookDocumentView(BaseModel):
    id: str
    logical_textbook_key: str
    version_number: int = Field(gt=0)
    version_label: str | None = None
    title: str
    file_name: str
    size_bytes: int | None = Field(default=None, ge=0)
    checksum_sha256: str | None = None
    publication_status: DocumentPublicationStatus
    quality_summary: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    published_at: datetime | None = None
    deactivated_at: datetime | None = None
    deleted_at: datetime | None = None
    corpus_revision: int | None = Field(default=None, gt=0)
    active_projection_run_id: str | None = None
    latest_job: IngestionJobView | None = None
    allowed_actions: list[str] = Field(default_factory=list)
    can_publish: bool = False
    publish_blockers: list[str] = Field(default_factory=list)
    ocr: dict[str, Any] = Field(default_factory=dict)

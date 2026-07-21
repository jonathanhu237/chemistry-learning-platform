from __future__ import annotations

import pytest

from server.app.domains.textbook_ingestion.contracts import (
    IngestionStage,
    NormalizedBlock,
    NormalizedPage,
    PageQuality,
    validate_stage_transition,
)


def test_ingestion_stage_transition_accepts_pipeline_and_rejects_skips() -> None:
    validate_stage_transition(IngestionStage.UPLOADED, IngestionStage.EXTRACTING)
    validate_stage_transition(IngestionStage.EXTRACTING, IngestionStage.AWAITING_OCR)
    validate_stage_transition(IngestionStage.AWAITING_OCR, IngestionStage.OCR)
    validate_stage_transition(IngestionStage.INDEXING, IngestionStage.REVIEW_READY)

    with pytest.raises(ValueError, match="uploaded -> indexing"):
        validate_stage_transition(IngestionStage.UPLOADED, IngestionStage.INDEXING)


def test_normalized_page_owns_block_and_quality_contract() -> None:
    page = NormalizedPage(
        page_number=3,
        text="氯气的实验室制法",
        markdown="## 氯气的实验室制法",
        blocks=[
            NormalizedBlock(
                block_id="p3-b1",
                block_type="section_header",
                bbox=(20, 30, 800, 90),
                text="氯气的实验室制法",
            )
        ],
        quality=PageQuality(score=0.98, needs_ocr=False, metrics={"non_whitespace_chars": 9}),
        content_hash="abc123",
    )

    assert page.blocks[0].block_type.value == "section_header"
    assert page.quality.needs_ocr is False
    assert page.quality.metrics["non_whitespace_chars"] == 9

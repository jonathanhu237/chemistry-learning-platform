from __future__ import annotations

from server.app.domains.textbook_ingestion.contracts import (
    ExtractionMethod,
    NormalizedPage,
    PageQuality,
    StableChunk,
)
from server.app.domains.textbook_ingestion.quality import (
    CONFIRMED_BLANK_PAGE_FLAG,
    build_textbook_quality_report,
)


def _page(
    number: int,
    *,
    text: str = "有效教材正文",
    needs_ocr: bool = False,
    quality_flags: list[str] | None = None,
    extraction_method: ExtractionMethod = ExtractionMethod.NATIVE,
    diagnostics: dict[str, object] | None = None,
) -> NormalizedPage:
    return NormalizedPage(
        page_number=number,
        text=text,
        markdown=text,
        extraction_method=extraction_method,
        quality=PageQuality(
            score=0.9,
            needs_ocr=needs_ocr,
            flags=quality_flags or [],
        ),
        content_hash=f"page-{number}",
        diagnostics=diagnostics or {},
    )


def _chunk(number: int) -> StableChunk:
    return StableChunk(
        chunk_id=f"chunk-{number}",
        document_id="tbk-1",
        document_version=1,
        chunk_index=number,
        text=f"有效教材正文 {number}",
        page_start=number,
        page_end=number,
        content_hash=f"chunk-hash-{number}",
    )


def test_quality_report_accepts_complete_traceable_text() -> None:
    report = build_textbook_quality_report([_page(1), _page(2)], [_chunk(1), _chunk(2)])

    assert report["publishable"] is True
    assert report["blocking_issues"] == []
    assert report["page_count"] == 2
    assert report["chunk_count"] == 2


def test_quality_report_blocks_empty_or_unresolved_pages() -> None:
    report = build_textbook_quality_report(
        [_page(1), _page(2, text="", needs_ocr=True)],
        [_chunk(1)],
    )

    assert report["publishable"] is False
    assert "empty_pages" in report["blocking_issues"]
    assert "unresolved_ocr_pages" in report["blocking_issues"]


def test_quality_report_accepts_explicitly_confirmed_blank_ocr_page() -> None:
    confirmed_blank = _page(
        2,
        text="",
        quality_flags=[CONFIRMED_BLANK_PAGE_FLAG],
        extraction_method=ExtractionMethod.MINERU,
        diagnostics={"blank_page_detection": {"confirmed": True}},
    )

    report = build_textbook_quality_report([_page(1), confirmed_blank], [_chunk(1)])

    assert report["publishable"] is True
    assert report["blocking_issues"] == []
    assert report["confirmed_blank_pages"] == [2]
    assert report["empty_pages"] == []
    assert report["unresolved_ocr_pages"] == []
    assert CONFIRMED_BLANK_PAGE_FLAG in report["quality_flags"]


def test_quality_report_does_not_exempt_unconfirmed_or_unresolved_blank_page() -> None:
    unconfirmed = _page(2, text="")
    unresolved = _page(
        2,
        text="",
        needs_ocr=True,
        quality_flags=[CONFIRMED_BLANK_PAGE_FLAG],
        extraction_method=ExtractionMethod.MINERU,
        diagnostics={"blank_page_detection": {"confirmed": True}},
    )

    unconfirmed_report = build_textbook_quality_report([_page(1), unconfirmed], [_chunk(1)])
    unresolved_report = build_textbook_quality_report([_page(1), unresolved], [_chunk(1)])

    assert unconfirmed_report["publishable"] is False
    assert unconfirmed_report["confirmed_blank_pages"] == []
    assert unconfirmed_report["empty_pages"] == [2]
    assert unresolved_report["publishable"] is False
    assert unresolved_report["confirmed_blank_pages"] == []
    assert unresolved_report["empty_pages"] == [2]
    assert unresolved_report["unresolved_ocr_pages"] == [2]


def test_quality_report_distinguishes_true_duplicate_chunks_from_repeated_source_text() -> None:
    original = _chunk(1).model_copy(update={"section_path": ["Chapter 1"]})
    same_location_copy = original.model_copy(update={"chunk_id": "chunk-copy", "chunk_index": 2})

    duplicated = build_textbook_quality_report([_page(1)], [original, same_location_copy])

    assert duplicated["publishable"] is False
    assert "duplicate_chunk_content" in duplicated["blocking_issues"]
    assert duplicated["duplicate_chunk_hashes"] == [original.content_hash]

    relocated_copy = same_location_copy.model_copy(
        update={
            "page_start": 2,
            "page_end": 2,
            "section_path": ["Chapter 2"],
        }
    )
    repeated_source_text = build_textbook_quality_report(
        [_page(1), _page(2)],
        [original, relocated_copy],
    )

    assert repeated_source_text["publishable"] is True
    assert "duplicate_chunk_content" not in repeated_source_text["blocking_issues"]
    assert repeated_source_text["duplicate_chunk_hashes"] == []

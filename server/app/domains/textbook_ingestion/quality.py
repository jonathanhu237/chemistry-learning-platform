from __future__ import annotations

from collections import Counter
from typing import Sequence

from server.app.domains.textbook_ingestion.contracts import ExtractionMethod, NormalizedPage, StableChunk


def build_textbook_quality_report(
    pages: Sequence[NormalizedPage],
    chunks: Sequence[StableChunk],
) -> dict[str, object]:
    blocking_issues: list[str] = []
    warnings: list[str] = []
    page_numbers = [page.page_number for page in pages]
    expected_pages = list(range(1, max(page_numbers, default=0) + 1))
    missing_pages = sorted(set(expected_pages) - set(page_numbers))
    duplicate_pages = sorted(number for number, count in Counter(page_numbers).items() if count > 1)
    empty_pages = sorted(page.page_number for page in pages if not page.text.strip())
    unresolved_ocr_pages = sorted(page.page_number for page in pages if page.quality.needs_ocr)
    low_quality_pages = sorted(page.page_number for page in pages if page.quality.score < 0.55)

    if not pages:
        blocking_issues.append("no_pages")
    if missing_pages:
        blocking_issues.append("missing_pages")
    if duplicate_pages:
        blocking_issues.append("duplicate_pages")
    if empty_pages:
        blocking_issues.append("empty_pages")
    if unresolved_ocr_pages:
        blocking_issues.append("unresolved_ocr_pages")
    if not chunks:
        blocking_issues.append("no_chunks")

    # Identical short headings or equations can legitimately recur in different
    # chapters/pages. Only repeated content at the same structural location is
    # a duplicated chunk artifact that should block publication.
    chunk_location_counts = Counter(
        (
            chunk.content_hash,
            chunk.page_start,
            chunk.page_end,
            tuple(chunk.section_path),
        )
        for chunk in chunks
    )
    duplicate_chunk_hashes = sorted(
        {
            content_hash
            for (content_hash, _page_start, _page_end, _section_path), count in chunk_location_counts.items()
            if count > 1
        }
    )
    if duplicate_chunk_hashes:
        blocking_issues.append("duplicate_chunk_content")
    invalid_chunk_pages = sorted(
        chunk.chunk_id
        for chunk in chunks
        if chunk.page_start not in set(page_numbers)
        or chunk.page_end not in set(page_numbers)
        or chunk.page_end < chunk.page_start
    )
    if invalid_chunk_pages:
        blocking_issues.append("invalid_chunk_page_range")

    covered_pages: set[int] = set()
    for chunk in chunks:
        covered_pages.update(range(chunk.page_start, chunk.page_end + 1))
    searchable_pages = {page.page_number for page in pages if page.text.strip()}
    uncovered_searchable_pages = sorted(searchable_pages - covered_pages)
    if uncovered_searchable_pages:
        blocking_issues.append("uncovered_searchable_pages")

    all_quality_flags = sorted(
        {
            flag
            for page in pages
            for flag in page.quality.flags
        }
        | {
            flag
            for page in pages
            for block in page.blocks
            for flag in block.quality_flags
        }
        | {flag for chunk in chunks for flag in chunk.quality_flags}
    )
    if low_quality_pages:
        warnings.append("low_quality_pages")
    for flag in all_quality_flags:
        warnings.append(flag)

    ocr_pages = [page for page in pages if page.extraction_method == ExtractionMethod.MINERU]
    mixed_pages = [page for page in pages if page.extraction_method == ExtractionMethod.MIXED]
    average_quality = sum(page.quality.score for page in pages) / len(pages) if pages else 0.0
    return {
        "publishable": not blocking_issues,
        "blocking_issues": list(dict.fromkeys(blocking_issues)),
        "warnings": list(dict.fromkeys(warnings)),
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "ocr_page_count": len(ocr_pages),
        "mixed_page_count": len(mixed_pages),
        "native_page_count": len(pages) - len(ocr_pages) - len(mixed_pages),
        "average_page_quality": round(average_quality, 6),
        "missing_pages": missing_pages,
        "duplicate_pages": duplicate_pages,
        "empty_pages": empty_pages,
        "unresolved_ocr_pages": unresolved_ocr_pages,
        "low_quality_pages": low_quality_pages,
        "uncovered_searchable_pages": uncovered_searchable_pages,
        "duplicate_chunk_hashes": duplicate_chunk_hashes[:100],
        "invalid_chunk_ids": invalid_chunk_pages[:100],
        "quality_flags": all_quality_flags,
    }

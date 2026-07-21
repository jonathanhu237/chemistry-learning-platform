from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest

from server.app.domains.textbook_ingestion.contracts import BlockType, NormalizedBlock
from server.app.domains.textbook_ingestion.extraction import (
    PDFExtractionError,
    PyMuPDFExtractor,
    _classify_text_block,
    block_is_embeddable,
    normalize_structural_blocks,
)


def _native_pdf(path: Path, *, page_count: int = 2) -> None:
    document = pymupdf.open()
    for index in range(page_count):
        page = document.new_page(width=595, height=842)
        page.insert_text((72, 35), "Synthetic Inorganic Chemistry", fontsize=9)
        heading = "Chapter 1 Atomic Structure" if index == 0 else "1.1 Electron Configuration"
        page.insert_text((72, 100), heading, fontsize=18)
        body = (
            "Native text explains sodium chloride NaCl, water H2O, and electron transfer. "
            "The page contains enough selectable chemistry text for the native quality gate. "
        ) * 3
        page.insert_textbox(pymupdf.Rect(72, 140, 520, 440), body, fontsize=11)
        page.insert_text((292, 820), str(index + 1), fontsize=9)
    document.save(path)
    document.close()


def _scan_and_blank_pdf(path: Path) -> None:
    image_document = pymupdf.open()
    image_page = image_document.new_page(width=240, height=320)
    image_page.draw_rect(image_page.rect, color=(0, 0, 0), fill=(0.92, 0.92, 0.92))
    image_page.insert_text((30, 150), "RASTER SCAN", fontsize=22)
    image_bytes = image_page.get_pixmap(alpha=False).tobytes("png")
    image_document.close()

    document = pymupdf.open()
    scan_page = document.new_page(width=240, height=320)
    scan_page.insert_image(scan_page.rect, stream=image_bytes)
    document.new_page(width=240, height=320)
    document.save(path)
    document.close()


def test_pymupdf_extractor_returns_native_pages_blocks_quality_and_render(tmp_path: Path) -> None:
    pdf_path = tmp_path / "native.pdf"
    _native_pdf(pdf_path)
    extractor = PyMuPDFExtractor(max_pages=10, min_chars=40, render_dpi=72)

    pages = list(extractor.extract(pdf_path))

    assert [page.page_number for page in pages] == [1, 2]
    assert all(not page.quality.needs_ocr for page in pages)
    assert all(page.content_hash and len(page.content_hash) == 64 for page in pages)
    assert "Synthetic Inorganic Chemistry" not in pages[0].text
    assert any(block.block_type == BlockType.HEADER for block in pages[0].blocks)
    assert any(block.block_type == BlockType.SECTION_HEADER for block in pages[0].blocks)
    assert any(block.block_type == BlockType.PAGE_NUMBER for block in pages[0].blocks)
    assert pages[0].diagnostics["extractor"] == "pymupdf"

    rendered = extractor.render_page(pdf_path, 1)
    assert rendered.mime_type == "image/png"
    assert rendered.image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert (rendered.pixel_width, rendered.pixel_height) == (595, 842)


def test_pymupdf_extractor_marks_scanned_and_blank_pages_for_ocr(tmp_path: Path) -> None:
    pdf_path = tmp_path / "scan-and-blank.pdf"
    _scan_and_blank_pdf(pdf_path)

    scan, blank = list(PyMuPDFExtractor(max_pages=10, min_chars=1).extract(pdf_path))

    assert scan.quality.needs_ocr is True
    assert {"image_only", "scanned_page"}.issubset(scan.quality.flags)
    assert scan.quality.metrics["image_coverage_ratio"] == pytest.approx(1.0)
    assert any(block.block_type == BlockType.IMAGE for block in scan.blocks)
    assert blank.quality.needs_ocr is True
    assert "blank_page" in blank.quality.flags
    assert blank.text == ""


def test_pymupdf_extractor_enforces_document_page_limit(tmp_path: Path) -> None:
    pdf_path = tmp_path / "too-many-pages.pdf"
    _native_pdf(pdf_path, page_count=3)

    with pytest.raises(PDFExtractionError) as exc_info:
        list(PyMuPDFExtractor(max_pages=2, min_chars=1).extract(pdf_path))

    assert exc_info.value.reason == "page_limit_exceeded"
    assert exc_info.value.details == {"page_count": 3, "max_pages": 2}


def test_structural_normalization_retains_container_but_deduplicates_its_text() -> None:
    blocks = [
        NormalizedBlock(
            block_id="list-container",
            block_type=BlockType.LIST,
            bbox=(20, 20, 400, 140),
            text="Add acid slowly. Observe the color change.",
            child_ids=["item-1", "item-2"],
        ),
        NormalizedBlock(
            block_id="item-1",
            block_type=BlockType.LIST_ITEM,
            bbox=(30, 35, 390, 70),
            text="Add acid slowly.",
        ),
        NormalizedBlock(
            block_id="item-2",
            block_type=BlockType.LIST_ITEM,
            bbox=(30, 80, 390, 120),
            text="Observe the color change.",
        ),
    ]

    normalized = normalize_structural_blocks(
        blocks,
        page_number=1,
        width_points=500,
        height_points=700,
    )

    container, first_child, second_child = normalized
    assert container.text
    assert container.metadata["exclude_from_embedding"] is True
    assert "container_text_deduplicated" in container.quality_flags
    assert block_is_embeddable(container) is False
    assert first_child.parent_id == container.block_id
    assert second_child.parent_id == container.block_id
    assert block_is_embeddable(first_child) is True


def test_native_classification_rejects_formula_and_large_prose_as_headings() -> None:
    equation_type, equation_metadata = _classify_text_block(
        "2 H2 + O2 = 2 H2O",
        max_font_size=18,
        body_font_size=11,
        bold=False,
    )
    prose_type, prose_metadata = _classify_text_block(
        "这一段大字号正文仍然是完整陈述句，不应污染章节路径。",
        max_font_size=18,
        body_font_size=11,
        bold=False,
    )
    numbered_prose_type, _ = _classify_text_block(
        "1. 这是普通字号的编号正文。",
        max_font_size=11,
        body_font_size=11,
        bold=False,
    )
    heading_type, heading_metadata = _classify_text_block(
        "12.3 卤素及其化合物",
        max_font_size=12,
        body_font_size=11,
        bold=True,
    )

    assert equation_type == BlockType.EQUATION
    assert equation_metadata == {}
    assert prose_type == BlockType.TEXT
    assert prose_metadata == {}
    assert numbered_prose_type not in {BlockType.TITLE, BlockType.SECTION_HEADER}
    assert heading_type == BlockType.SECTION_HEADER
    assert heading_metadata["heading_level"] == 2


def test_pymupdf_extractor_removes_variable_running_headers_by_layout(tmp_path: Path) -> None:
    pdf_path = tmp_path / "variable-running-headers.pdf"
    document = pymupdf.open()
    for index in range(6):
        page = document.new_page(width=595, height=842)
        page.insert_text((72, 35), f"{index + 1} Running topic {index + 1}", fontsize=9)
        page.insert_text((72, 100), "12.3 Halogen Chemistry", fontsize=16)
        page.insert_textbox(
            pymupdf.Rect(72, 140, 520, 440),
            ("Selectable native chemistry body text remains available for retrieval. " * 4),
            fontsize=11,
        )
    document.save(pdf_path)
    document.close()

    pages = list(PyMuPDFExtractor(max_pages=10, min_chars=40).extract(pdf_path))

    assert len(pages) == 6
    assert all(any(block.block_type == BlockType.HEADER for block in page.blocks) for page in pages)
    assert all("Running topic" not in page.text for page in pages)
    assert all(not page.quality.needs_ocr for page in pages)


def test_pymupdf_extractor_keeps_repeated_top_layout_when_it_uses_heading_typography(tmp_path: Path) -> None:
    pdf_path = tmp_path / "top-content-headings.pdf"
    document = pymupdf.open()
    for index in range(6):
        page = document.new_page(width=595, height=842)
        page.insert_text((72, 35), f"{index + 1}. Major chemistry topic", fontsize=18)
        page.insert_textbox(
            pymupdf.Rect(72, 140, 520, 440),
            ("Selectable body text provides the page-level native quality baseline. " * 4),
            fontsize=11,
        )
    document.save(pdf_path)
    document.close()

    pages = list(PyMuPDFExtractor(max_pages=10, min_chars=40).extract(pdf_path))

    assert all(not any(block.block_type == BlockType.HEADER for block in page.blocks) for page in pages)
    assert all(
        any(block.block_type in {BlockType.TITLE, BlockType.SECTION_HEADER} for block in page.blocks)
        for page in pages
    )

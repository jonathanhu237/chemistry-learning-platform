from __future__ import annotations

from server.app.domains.textbook_ingestion.chunking import StructureAwareChunker
from server.app.domains.textbook_ingestion.contracts import (
    BlockType,
    NormalizedBlock,
    NormalizedPage,
    PageQuality,
)


def _page(page_number: int, blocks: list[NormalizedBlock]) -> NormalizedPage:
    return NormalizedPage(
        page_number=page_number,
        blocks=blocks,
        quality=PageQuality(score=1.0, needs_ocr=False),
        content_hash=f"page-{page_number}",
    )


def test_structure_aware_chunker_has_stable_ids_headings_and_adjacency() -> None:
    pages = [
        _page(
            1,
            [
                NormalizedBlock(
                    block_id="chapter",
                    block_type=BlockType.TITLE,
                    text="Chapter 1 Atomic Structure",
                    markdown="# Chapter 1 Atomic Structure",
                    metadata={"heading_level": 1},
                ),
                NormalizedBlock(
                    block_id="body-1",
                    block_type=BlockType.TEXT,
                    text=("Electrons occupy orbitals according to quantum rules. " * 4).strip(),
                ),
            ],
        ),
        _page(
            2,
            [
                NormalizedBlock(
                    block_id="section",
                    block_type=BlockType.SECTION_HEADER,
                    text="1.1 Electron Configuration",
                    markdown="## 1.1 Electron Configuration",
                    metadata={"heading_level": 2},
                ),
                NormalizedBlock(
                    block_id="body-2",
                    block_type=BlockType.TEXT,
                    text=("The Aufbau sequence provides a practical filling order. " * 4).strip(),
                ),
            ],
        ),
    ]
    chunker = StructureAwareChunker(max_chars=150, overlap_chars=20)

    first = chunker.chunk(
        document_id="tbk-atomic",
        document_version=2,
        pages=pages,
        processing_fingerprint="parser-a",
    )
    repeated = chunker.chunk(
        document_id="tbk-atomic",
        document_version=2,
        pages=list(reversed(pages)),
        processing_fingerprint="parser-b",
    )

    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in repeated]
    assert [chunk.chunk_index for chunk in first] == list(range(1, len(first) + 1))
    assert first[0].section_path == ["Chapter 1 Atomic Structure"]
    assert any(
        chunk.section_path == ["Chapter 1 Atomic Structure", "1.1 Electron Configuration"]
        for chunk in first
    )
    assert first[0].previous_chunk_id is None
    assert first[-1].next_chunk_id is None
    for previous, current in zip(first[:-1], first[1:], strict=True):
        assert previous.next_chunk_id == current.chunk_id
        assert current.previous_chunk_id == previous.chunk_id
    assert all(len(chunk.content_hash) == 64 for chunk in first)
    assert first[0].metadata["processing_fingerprint"] == "parser-a"
    assert repeated[0].metadata["processing_fingerprint"] == "parser-b"


def test_structure_aware_chunker_keeps_tables_and_equations_atomic() -> None:
    table_text = "\n".join(f"row {index} | reagent {index} | {index * 0.25:.2f} mol/L" for index in range(12))
    equation_text = "2 KMnO4 + 16 HCl -> 2 KCl + 2 MnCl2 + 5 Cl2 + 8 H2O"
    pages = [
        _page(
            3,
            [
                NormalizedBlock(
                    block_id="heading",
                    block_type=BlockType.SECTION_HEADER,
                    text="2.3 Redox Reactions",
                    metadata={"heading_level": 2},
                ),
                NormalizedBlock(
                    block_id="table",
                    block_type=BlockType.TABLE,
                    text=table_text,
                    markdown=table_text,
                ),
                NormalizedBlock(
                    block_id="equation",
                    block_type=BlockType.EQUATION,
                    text=equation_text,
                    markdown=f"$$\n{equation_text}\n$$",
                ),
            ],
        )
    ]

    chunks = StructureAwareChunker(max_chars=80, overlap_chars=8).chunk(
        document_id="tbk-redox",
        document_version=1,
        pages=pages,
        processing_fingerprint="fp",
    )

    table_chunk = next(chunk for chunk in chunks if chunk.content_type == "table")
    equation_chunk = next(chunk for chunk in chunks if chunk.content_type == "equation")
    assert table_text in table_chunk.text
    assert equation_chunk.text == equation_text
    assert len(table_chunk.text) > 80
    assert "oversized_atomic_block" in table_chunk.quality_flags
    assert table_chunk.metadata["atomic"] is True
    assert equation_chunk.metadata["atomic"] is True


def test_structure_aware_chunker_uses_children_once_for_overlapping_container() -> None:
    page = _page(
        4,
        [
            NormalizedBlock(
                block_id="procedure",
                block_type=BlockType.LIST,
                text="Add acid slowly. Observe the color change.",
                child_ids=["step-1", "step-2"],
            ),
            NormalizedBlock(
                block_id="step-1",
                block_type=BlockType.LIST_ITEM,
                text="Add acid slowly.",
                parent_id="procedure",
            ),
            NormalizedBlock(
                block_id="step-2",
                block_type=BlockType.LIST_ITEM,
                text="Observe the color change.",
                parent_id="procedure",
            ),
        ],
    )

    chunks = StructureAwareChunker(max_chars=200, overlap_chars=0).chunk(
        document_id="tbk-procedure",
        document_version=1,
        pages=[page],
        processing_fingerprint="fp",
    )

    assert len(chunks) == 1
    assert chunks[0].text.count("Add acid slowly.") == 1
    assert chunks[0].text.count("Observe the color change.") == 1
    assert chunks[0].metadata["source_block_ids"] == ["step-1", "step-2"]


def test_structure_aware_chunker_packs_short_equation_with_adjacent_explanation() -> None:
    equation = "2 H2 + O2 = 2 H2O"
    page = _page(
        5,
        [
            NormalizedBlock(
                block_id="heading",
                block_type=BlockType.SECTION_HEADER,
                text="3.2 Reaction Stoichiometry",
                metadata={"heading_level": 2},
            ),
            NormalizedBlock(
                block_id="body-before",
                block_type=BlockType.TEXT,
                text="Hydrogen reacts with oxygen in a fixed stoichiometric ratio.",
            ),
            NormalizedBlock(
                block_id="equation",
                block_type=BlockType.EQUATION,
                text=equation,
                markdown=f"$$\n{equation}\n$$",
            ),
            NormalizedBlock(
                block_id="body-after",
                block_type=BlockType.TEXT,
                text="The coefficients preserve both hydrogen and oxygen atoms.",
            ),
        ],
    )

    chunks = StructureAwareChunker(max_chars=300, overlap_chars=0).chunk(
        document_id="tbk-equation-context",
        document_version=1,
        pages=[page],
        processing_fingerprint="fp",
    )

    assert len(chunks) == 1
    assert chunks[0].text.count(equation) == 1
    assert chunks[0].metadata["source_block_ids"] == ["heading", "body-before", "equation", "body-after"]
    assert chunks[0].metadata["atomic"] is True
    assert chunks[0].content_type == "text"


def test_structure_aware_chunker_keeps_consecutive_hierarchy_with_body() -> None:
    page = _page(
        6,
        [
            NormalizedBlock(
                block_id="chapter",
                block_type=BlockType.TITLE,
                text="Chapter 3 Reactions",
                metadata={"heading_level": 1},
            ),
            NormalizedBlock(
                block_id="section",
                block_type=BlockType.SECTION_HEADER,
                text="3.1 Stoichiometry",
                metadata={"heading_level": 2},
            ),
            NormalizedBlock(
                block_id="body",
                block_type=BlockType.TEXT,
                text="Balanced equations conserve every element in the reaction.",
            ),
        ],
    )

    chunks = StructureAwareChunker(max_chars=300, overlap_chars=0).chunk(
        document_id="tbk-heading-context",
        document_version=1,
        pages=[page],
        processing_fingerprint="fp",
    )

    assert len(chunks) == 1
    assert chunks[0].section_path == ["Chapter 3 Reactions", "3.1 Stoichiometry"]
    assert chunks[0].metadata["source_block_ids"] == ["chapter", "section", "body"]


def test_structure_aware_chunker_deduplicates_same_content_at_same_location() -> None:
    page = _page(
        7,
        [
            NormalizedBlock(
                block_id="heading-copy-1",
                block_type=BlockType.SECTION_HEADER,
                text="Exercises",
                metadata={"heading_level": 3},
            ),
            NormalizedBlock(
                block_id="heading-copy-2",
                block_type=BlockType.SECTION_HEADER,
                text="Exercises",
                metadata={"heading_level": 3},
            ),
        ],
    )

    chunks = StructureAwareChunker(max_chars=200, overlap_chars=0).chunk(
        document_id="tbk-dedup",
        document_version=1,
        pages=[page],
        processing_fingerprint="fp",
    )

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 1
    assert chunks[0].text == "Exercises"

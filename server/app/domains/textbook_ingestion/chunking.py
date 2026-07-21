from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from server.app.domains.textbook_ingestion.contracts import (
    BlockType,
    ExtractionMethod,
    NormalizedBlock,
    NormalizedPage,
    StableChunk,
)
from server.app.domains.textbook_ingestion.extraction import (
    block_is_embeddable,
    normalize_content_text,
    normalize_structural_blocks,
)
from server.app.infrastructure.settings import Settings, get_settings


CHUNKING_STRATEGY = "structure-aware-v2"

_HEADING_TYPES = frozenset({BlockType.TITLE, BlockType.SECTION_HEADER})
_ATOMIC_TYPES = frozenset({BlockType.TABLE, BlockType.EQUATION, BlockType.EQUATION_BLOCK})
_PACKABLE_ATOMIC_TYPES = frozenset({BlockType.EQUATION, BlockType.EQUATION_BLOCK})
_CAPTION_TYPES = frozenset({BlockType.TABLE_CAPTION, BlockType.IMAGE_CAPTION})
_SENTENCE_BOUNDARY_RE = re.compile(r"[。！？；.!?;]\s*|\n+")
_SAFETY_RE = re.compile(r"(?:安全|注意|警告|危险|防护|废液|有毒|腐蚀|易燃)")


def _ordered_unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _canonical_text(value: str) -> str:
    return re.sub(r"\s+", " ", normalize_content_text(value)).strip()


def _infer_heading_level(block: NormalizedBlock) -> int:
    raw_level = block.metadata.get("heading_level")
    if isinstance(raw_level, int) and 1 <= raw_level <= 6:
        return raw_level
    text = block.text.strip()
    if block.block_type == BlockType.TITLE or re.match(
        r"^第[0-9一二三四五六七八九十百零〇两]+[篇编章]", text
    ):
        return 1
    if re.match(r"^(?:第[0-9一二三四五六七八九十百零〇两]+节|实验\s*\d+)", text):
        return 2
    numbered = re.match(r"^(\d+(?:\.\d+){0,4})[\s、.．]+", text)
    if numbered:
        return min(6, numbered.group(1).count(".") + 1)
    return 3


def _split_point(text: str, start: int, hard_end: int) -> int:
    if hard_end >= len(text):
        return len(text)
    minimum = start + max(1, (hard_end - start) // 2)
    candidates = [
        match.end()
        for match in _SENTENCE_BOUNDARY_RE.finditer(text, start, hard_end)
        if match.end() >= minimum
    ]
    if candidates:
        return candidates[-1]
    whitespace = max(text.rfind(" ", minimum, hard_end), text.rfind("\t", minimum, hard_end))
    return whitespace + 1 if whitespace >= minimum else hard_end


def _next_overlap_start(text: str, tentative: int, end: int) -> int:
    if tentative <= 0:
        return 0
    boundary_end = min(end, tentative + max(24, (end - tentative) // 3))
    match = _SENTENCE_BOUNDARY_RE.search(text, tentative, boundary_end)
    return match.end() if match and match.end() < end else tentative


@dataclass(frozen=True)
class _Unit:
    locator: str
    block_id: str
    page_number: int
    text: str
    markdown: str
    block_type: BlockType
    section_path: tuple[str, ...]
    extraction_method: ExtractionMethod
    quality_flags: tuple[str, ...] = ()
    atomic: bool = False
    heading: bool = False
    overlap: bool = False


@dataclass
class _Draft:
    units: list[_Unit] = field(default_factory=list)
    oversized_atomic: bool = False

    @property
    def length(self) -> int:
        return sum(len(unit.text) for unit in self.units) + 2 * max(0, len(self.units) - 1)

    @property
    def section_path(self) -> tuple[str, ...]:
        for unit in reversed(self.units):
            if unit.section_path:
                return unit.section_path
        return ()

    @property
    def has_body(self) -> bool:
        return any(not unit.heading and unit.block_type not in _CAPTION_TYPES for unit in self.units)

    @property
    def has_atomic(self) -> bool:
        return any(unit.atomic for unit in self.units)


def _split_unit(unit: _Unit, *, max_chars: int, overlap_chars: int) -> list[_Unit]:
    if unit.atomic or len(unit.text) <= max_chars:
        return [unit]
    parts: list[_Unit] = []
    start = 0
    part_index = 1
    while start < len(unit.text):
        hard_end = min(len(unit.text), start + max_chars)
        end = _split_point(unit.text, start, hard_end)
        if end <= start:
            end = hard_end
        part_text = unit.text[start:end].strip()
        if part_text:
            flags = list(unit.quality_flags)
            if len(unit.text) > max_chars:
                flags.append("structural_block_split")
            parts.append(
                _Unit(
                    locator=f"{unit.locator}:part{part_index}",
                    block_id=unit.block_id,
                    page_number=unit.page_number,
                    text=part_text,
                    markdown=part_text,
                    block_type=unit.block_type,
                    section_path=unit.section_path,
                    extraction_method=unit.extraction_method,
                    quality_flags=tuple(_ordered_unique(flags)),
                    heading=unit.heading,
                )
            )
            part_index += 1
        if end >= len(unit.text):
            break
        next_start = max(start + 1, end - overlap_chars)
        start = _next_overlap_start(unit.text, next_start, end)
        if start >= end:
            start = next_start
    return parts


def _page_units(page: NormalizedPage) -> list[tuple[NormalizedBlock, list[str]]]:
    blocks = normalize_structural_blocks(
        page.blocks,
        page_number=page.page_number,
        width_points=page.width_points,
        height_points=page.height_points,
    )
    if not blocks and normalize_content_text(page.text):
        blocks = [
            NormalizedBlock(
                block_id=f"p{page.page_number}-text",
                block_type=BlockType.TEXT,
                text=normalize_content_text(page.text),
                markdown=normalize_content_text(page.markdown) or normalize_content_text(page.text),
            )
        ]
    return [(block, list(page.quality.flags)) for block in blocks if block_is_embeddable(block)]


def _flatten_units(pages: Sequence[NormalizedPage], *, max_chars: int, overlap_chars: int) -> list[_Unit]:
    hierarchy: dict[int, str] = {}
    flattened: list[_Unit] = []
    for page in sorted(pages, key=lambda item: item.page_number):
        for block, page_flags in _page_units(page):
            text = normalize_content_text(block.text)
            if not text:
                continue
            heading = block.block_type in _HEADING_TYPES
            if heading:
                level = _infer_heading_level(block)
                hierarchy = {depth: title for depth, title in hierarchy.items() if depth < level}
                hierarchy[level] = text
            section_path = tuple(hierarchy[level] for level in sorted(hierarchy))
            flags = _ordered_unique(
                [
                    *page_flags,
                    *(("page_needs_ocr",) if page.quality.needs_ocr else ()),
                    *block.quality_flags,
                ]
            )
            unit = _Unit(
                locator=f"p{page.page_number}:{block.block_id}",
                block_id=block.block_id,
                page_number=page.page_number,
                text=text,
                markdown=normalize_content_text(block.markdown) or text,
                block_type=block.block_type,
                section_path=section_path,
                extraction_method=page.extraction_method,
                quality_flags=tuple(flags),
                atomic=block.block_type in _ATOMIC_TYPES,
                heading=heading,
            )
            flattened.extend(_split_unit(unit, max_chars=max_chars, overlap_chars=overlap_chars))
    return flattened


def _overlap_unit(draft: _Draft, *, max_chars: int) -> _Unit | None:
    if max_chars <= 0 or draft.has_atomic:
        return None
    candidates = [unit for unit in draft.units if not unit.heading and not unit.overlap]
    if not candidates:
        return None
    source = candidates[-1]
    tail = source.text[-max_chars:]
    if len(source.text) > max_chars:
        boundary = _SENTENCE_BOUNDARY_RE.search(tail, 0, max(1, len(tail) // 2))
        if boundary:
            tail = tail[boundary.end() :]
    tail = tail.strip()
    if not tail:
        return None
    digest = hashlib.sha256(tail.encode("utf-8")).hexdigest()[:12]
    return _Unit(
        locator=f"overlap:{source.locator}:{digest}",
        block_id=source.block_id,
        page_number=source.page_number,
        text=tail,
        markdown=tail,
        block_type=source.block_type,
        section_path=source.section_path,
        extraction_method=source.extraction_method,
        quality_flags=source.quality_flags,
        overlap=True,
    )


def _build_drafts(units: Sequence[_Unit], *, max_chars: int, overlap_chars: int) -> list[_Draft]:
    drafts: list[_Draft] = []
    current = _Draft()

    def flush() -> _Draft | None:
        nonlocal current
        if not current.units:
            return None
        emitted = current
        drafts.append(emitted)
        current = _Draft()
        return emitted

    for unit in units:
        if unit.heading and current.units:
            if current.has_body:
                flush()
            else:
                if any(
                    candidate.heading
                    and candidate.section_path == unit.section_path
                    and _canonical_text(candidate.text) == _canonical_text(unit.text)
                    for candidate in current.units
                ):
                    continue
                current_path = current.section_path
                extends_current_heading = bool(
                    current_path
                    and len(unit.section_path) > len(current_path)
                    and unit.section_path[: len(current_path)] == current_path
                )
                if not extends_current_heading:
                    flush()

        if unit.atomic:
            # Atomic means the structural block cannot be split; it does not
            # require every short formula to become a singleton chunk. Keeping
            # equations with their adjacent explanation preserves retrieval
            # context while tables and oversized formulae remain standalone.
            if unit.block_type in _PACKABLE_ATOMIC_TYPES and len(unit.text) <= max_chars:
                added_length = len(unit.text) + (2 if current.units else 0)
                if current.units and current.length + added_length > max_chars:
                    flush()
                current.units.append(unit)
                if current.length >= max_chars:
                    flush()
                continue
            context_units: list[_Unit] = []
            if current.units and not current.has_body:
                context_units = current.units
                current = _Draft()
            else:
                flush()
            atomic = _Draft(units=[*context_units, unit])
            atomic.oversized_atomic = atomic.length > max_chars
            drafts.append(atomic)
            continue

        added_length = len(unit.text) + (2 if current.units else 0)
        if current.units and current.length + added_length > max_chars:
            previous = flush()
            available_for_overlap = max(0, min(overlap_chars, max_chars - len(unit.text) - 2))
            previous_source_ids = {
                candidate.block_id for candidate in previous.units if not candidate.overlap
            } if previous else set()
            # Parts split from one structural block already carry the configured
            # in-block overlap; adding a second tail here would duplicate it twice.
            overlap = (
                _overlap_unit(previous, max_chars=available_for_overlap)
                if previous and unit.block_id not in previous_source_ids
                else None
            )
            if overlap is not None and overlap.section_path == unit.section_path:
                current.units.append(overlap)
        current.units.append(unit)
        if current.length >= max_chars:
            flush()
    flush()
    return drafts


def _draft_text(draft: _Draft) -> tuple[str, str]:
    text = "\n\n".join(unit.text for unit in draft.units if unit.text).strip()
    markdown = "\n\n".join((unit.markdown or unit.text) for unit in draft.units if unit.text).strip()
    return text, markdown


def _content_type(draft: _Draft) -> str:
    types = {unit.block_type for unit in draft.units if not unit.heading and not unit.overlap}
    if BlockType.TABLE in types:
        return "table"
    equation_types = {BlockType.EQUATION, BlockType.EQUATION_BLOCK, BlockType.FORMULA_NUMBER}
    if types and types.issubset(equation_types):
        return "equation"
    if types and types.issubset({BlockType.IMAGE_CAPTION, BlockType.IMAGE_FOOTNOTE}):
        return "figure_caption"
    if not types:
        return "heading"
    text, _ = _draft_text(draft)
    if len(text) <= 500 and _SAFETY_RE.search(text):
        return "safety_notice"
    if BlockType.LIST_ITEM in types or BlockType.LIST in types:
        return "list"
    return "text"


def _extraction_method(draft: _Draft) -> ExtractionMethod:
    methods = {unit.extraction_method for unit in draft.units}
    if len(methods) == 1:
        return next(iter(methods))
    return ExtractionMethod.MIXED


def _locator(draft: _Draft) -> str:
    locators = _ordered_unique(unit.locator for unit in draft.units)
    path = " / ".join(draft.section_path)
    return f"{path}|{'|'.join(locators)}"


def _stable_chunk_id(
    *,
    document_id: str,
    document_version: int,
    structural_locator: str,
    content_hash: str,
) -> str:
    payload = json.dumps(
        [document_id, document_version, structural_locator, content_hash],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return f"tchunk_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:32]}"


class StructureAwareChunker:
    """Create deterministic chunks from page/block structure and hierarchy."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        max_chars: int | None = None,
        overlap_chars: int | None = None,
        chunk_max_chars: int | None = None,
        chunk_overlap_chars: int | None = None,
    ) -> None:
        effective = settings or get_settings()
        self.max_chars = (
            max_chars
            if max_chars is not None
            else chunk_max_chars
            if chunk_max_chars is not None
            else effective.textbook_chunk_max_chars
        )
        self.overlap_chars = (
            overlap_chars
            if overlap_chars is not None
            else chunk_overlap_chars
            if chunk_overlap_chars is not None
            else effective.textbook_chunk_overlap_chars
        )
        if self.max_chars <= 0:
            raise ValueError("max_chars must be positive")
        if not 0 <= self.overlap_chars < self.max_chars:
            raise ValueError("overlap_chars must be non-negative and smaller than max_chars")

    def chunk(
        self,
        *,
        document_id: str,
        document_version: int,
        pages: Sequence[NormalizedPage],
        processing_fingerprint: str,
    ) -> list[StableChunk]:
        normalized_document_id = str(document_id or "").strip()
        if not normalized_document_id:
            raise ValueError("document_id is required")
        if document_version <= 0:
            raise ValueError("document_version must be positive")
        page_numbers = [page.page_number for page in pages]
        if len(page_numbers) != len(set(page_numbers)):
            raise ValueError("pages must have unique page numbers")

        units = _flatten_units(
            pages,
            max_chars=self.max_chars,
            overlap_chars=self.overlap_chars,
        )
        drafts = _build_drafts(
            units,
            max_chars=self.max_chars,
            overlap_chars=self.overlap_chars,
        )
        chunks: list[StableChunk] = []
        seen_content_locations: set[tuple[str, int, int, tuple[str, ...]]] = set()
        for draft in drafts:
            text, markdown = _draft_text(draft)
            if not _canonical_text(text):
                continue
            content_hash = hashlib.sha256(_canonical_text(text).encode("utf-8")).hexdigest()
            structural_locator = _locator(draft)
            page_numbers_in_chunk = [unit.page_number for unit in draft.units]
            content_location = (
                content_hash,
                min(page_numbers_in_chunk),
                max(page_numbers_in_chunk),
                draft.section_path,
            )
            if content_location in seen_content_locations:
                continue
            seen_content_locations.add(content_location)
            chunk_id = _stable_chunk_id(
                document_id=normalized_document_id,
                document_version=document_version,
                structural_locator=structural_locator,
                content_hash=content_hash,
            )
            quality_flags = _ordered_unique(
                flag for unit in draft.units for flag in unit.quality_flags
            )
            if draft.oversized_atomic:
                quality_flags.append("oversized_atomic_block")
            chunks.append(
                StableChunk(
                    chunk_id=chunk_id,
                    document_id=normalized_document_id,
                    document_version=document_version,
                    chunk_index=len(chunks) + 1,
                    text=text,
                    markdown=markdown,
                    page_start=min(page_numbers_in_chunk),
                    page_end=max(page_numbers_in_chunk),
                    section_title=draft.section_path[-1] if draft.section_path else "",
                    section_path=list(draft.section_path),
                    content_type=_content_type(draft),
                    content_hash=content_hash,
                    extraction_method=_extraction_method(draft),
                    quality_flags=_ordered_unique(quality_flags),
                    metadata={
                        "chunking_strategy": CHUNKING_STRATEGY,
                        "processing_fingerprint": processing_fingerprint,
                        "structural_locator": structural_locator,
                        "source_block_ids": _ordered_unique(unit.block_id for unit in draft.units),
                        "source_page_numbers": sorted(set(page_numbers_in_chunk)),
                        "overlap_chars": sum(len(unit.text) for unit in draft.units if unit.overlap),
                        "atomic": draft.has_atomic,
                    },
                )
            )

        anchor_by_path: dict[tuple[str, ...], str] = {}
        linked: list[StableChunk] = []
        for index, chunk in enumerate(chunks):
            path = tuple(chunk.section_path)
            parent_id: str | None = None
            if path in anchor_by_path:
                parent_id = anchor_by_path[path]
            else:
                for depth in range(len(path) - 1, 0, -1):
                    if path[:depth] in anchor_by_path:
                        parent_id = anchor_by_path[path[:depth]]
                        break
                if path:
                    anchor_by_path[path] = chunk.chunk_id
            linked.append(
                chunk.model_copy(
                    update={
                        "parent_chunk_id": parent_id,
                        "previous_chunk_id": chunks[index - 1].chunk_id if index > 0 else None,
                        "next_chunk_id": chunks[index + 1].chunk_id if index + 1 < len(chunks) else None,
                    }
                )
            )
        return linked


StableTextbookChunker = StructureAwareChunker

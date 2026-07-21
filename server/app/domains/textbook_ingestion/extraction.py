from __future__ import annotations

import hashlib
import math
import re
import statistics
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence

import pymupdf

from server.app.domains.textbook_ingestion.contracts import (
    BlockType,
    NormalizedBlock,
    NormalizedPage,
    PageQuality,
)
from server.app.domains.textbook_ingestion.ports import RenderedPage
from server.app.infrastructure.settings import Settings, get_settings


EXTRACTOR_NAME = "pymupdf"
EXTRACTOR_VERSION = f"pymupdf-{pymupdf.VersionBind}"

_NON_CONTENT_TYPES = frozenset(
    {
        BlockType.HEADER,
        BlockType.FOOTER,
        BlockType.PAGE_NUMBER,
        BlockType.PAGE_FOOTNOTE,
        BlockType.IMAGE,
        BlockType.IMAGE_BLOCK,
        BlockType.CHART,
    }
)
_CONTAINER_TYPES = frozenset(
    {
        BlockType.LIST,
        BlockType.IMAGE_BLOCK,
        BlockType.EQUATION_BLOCK,
    }
)
_COMMON_SUBHEADING_RE = re.compile(
    r"^(?:实验目的|实验原理|实验步骤|实验内容|实验用品|仪器与试剂|"
    r"注意事项|安全提示|废液处理|思考题|问题与讨论|结果与讨论|习题|例题)\s*[：:]?$"
)
_PAGE_NUMBER_RE = re.compile(r"^(?:[-—·•]\s*)?(?:\d{1,4}|[ivxlcdmIVXLCDM]{1,8})(?:\s*[-—·•])?$")
_TABLE_CAPTION_RE = re.compile(r"^表\s*[0-9一二三四五六七八九十]+(?:[-—.]\d+)?\s*\S*")
_IMAGE_CAPTION_RE = re.compile(r"^图\s*[0-9一二三四五六七八九十]+(?:[-—.]\d+)?\s*\S*")
_EQUATION_SIGNAL_RE = re.compile(
    r"(?:→|⇌|↔|=>|->|←|=|\\ce\{|\\mathrm\{|\^\{|_\{|[A-Z][a-z]?\d*[+-])"
)
_CHEMICAL_FORMULA_RE = re.compile(r"(?:[A-Z][a-z]?\d*){2,}|[A-Z][a-z]?\d+[+-]?")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*•·]|\(?\d+[)）.、]|[（(][一二三四五六七八九十]+[）)])\s*")


class PDFExtractionError(ValueError):
    """A safe, operator-facing error raised while opening or extracting a PDF."""

    def __init__(self, reason: str, message: str, **details: object) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message
        self.details = details

    def detail(self) -> dict[str, object]:
        return {"reason": self.reason, "message": self.message, **self.details}


def _ordered_unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def normalize_content_text(value: str) -> str:
    """Normalize parser noise without folding meaningful chemistry characters."""

    normalized = unicodedata.normalize("NFC", str(value or ""))
    normalized = normalized.replace("\u00a0", " ").replace("\u200b", "").replace("\u00ad", "")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[\t \f\v]+", " ", line).strip() for line in normalized.split("\n")]
    compact: list[str] = []
    for line in lines:
        if line:
            compact.append(line)
        elif compact and compact[-1] != "":
            compact.append("")
    return "\n".join(compact).strip()


def _join_pdf_lines(lines: Sequence[str]) -> str:
    result = ""
    for raw_line in lines:
        line = normalize_content_text(raw_line)
        if not line:
            continue
        if not result:
            result = line
            continue
        if result.endswith("-") and re.search(r"[A-Za-z]-$", result) and re.match(r"^[a-z]", line):
            result = result[:-1] + line
        elif re.search(r"[\u3400-\u9fff，。；：！？、）】]$", result) or re.match(
            r"^[\u3400-\u9fff，。；：！？、（【]", line
        ):
            result += line
        else:
            result += " " + line
    return result.strip()


def _normalize_bbox(
    bbox: Sequence[float | int] | None,
    *,
    width_points: float | None,
    height_points: float | None,
) -> tuple[tuple[int, int, int, int] | None, bool]:
    if bbox is None or len(bbox) != 4:
        return None, bbox is not None
    try:
        x0, y0, x1, y1 = (float(value) for value in bbox)
    except (TypeError, ValueError):
        return None, True
    if not all(math.isfinite(value) for value in (x0, y0, x1, y1)):
        return None, True
    if width_points is not None:
        x0, x1 = max(0.0, x0), min(width_points, x1)
    if height_points is not None:
        y0, y1 = max(0.0, y0), min(height_points, y1)
    if x1 <= x0 or y1 <= y0:
        return None, True
    return tuple(int(round(value)) for value in (x0, y0, x1, y1)), False


def _contains(outer: tuple[int, int, int, int], inner: tuple[int, int, int, int]) -> bool:
    tolerance = 2
    return (
        outer[0] - tolerance <= inner[0]
        and outer[1] - tolerance <= inner[1]
        and outer[2] + tolerance >= inner[2]
        and outer[3] + tolerance >= inner[3]
    )


def _intersection_ratio(
    first: tuple[int, int, int, int] | None,
    second: tuple[int, int, int, int] | None,
) -> float:
    if first is None or second is None:
        return 0.0
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    if right <= left or bottom <= top:
        return 0.0
    intersection = (right - left) * (bottom - top)
    smaller_area = min(
        (first[2] - first[0]) * (first[3] - first[1]),
        (second[2] - second[0]) * (second[3] - second[1]),
    )
    return intersection / smaller_area if smaller_area else 0.0


def normalize_structural_blocks(
    blocks: Sequence[NormalizedBlock],
    *,
    page_number: int | None = None,
    width_points: float | None = None,
    height_points: float | None = None,
) -> list[NormalizedBlock]:
    """Normalize blocks and mark preview-only duplicates as non-embeddable.

    MinerU and other layout parsers often return both a container and its child
    blocks.  Both are retained for preview and hierarchy reconstruction, while
    the container copy is explicitly excluded from chunk text.
    """

    normalized: list[NormalizedBlock] = []
    seen_ids: set[str] = set()
    for index, source in enumerate(blocks, start=1):
        block = source.model_copy(deep=True)
        fallback_id = f"p{page_number or 0}-b{index}"
        block_id = normalize_content_text(block.block_id) or fallback_id
        flags = list(block.quality_flags)
        if block_id in seen_ids:
            flags.append("duplicate_block_id")
            suffix = 2
            candidate = f"{block_id}-{suffix}"
            while candidate in seen_ids:
                suffix += 1
                candidate = f"{block_id}-{suffix}"
            block_id = candidate
        seen_ids.add(block_id)
        bbox, invalid_bbox = _normalize_bbox(
            block.bbox,
            width_points=width_points,
            height_points=height_points,
        )
        if invalid_bbox:
            flags.append("invalid_bbox")
        text = normalize_content_text(block.text)
        markdown = normalize_content_text(block.markdown) or text
        normalized.append(
            block.model_copy(
                update={
                    "block_id": block_id,
                    "bbox": bbox,
                    "text": text,
                    "markdown": markdown,
                    "quality_flags": _ordered_unique(flags),
                    "metadata": dict(block.metadata),
                }
            )
        )

    updates: dict[str, dict[str, Any]] = {}
    for container in normalized:
        if container.block_type not in _CONTAINER_TYPES:
            continue
        children: list[NormalizedBlock] = []
        explicit_ids = set(container.child_ids)
        for candidate in normalized:
            if candidate.block_id == container.block_id:
                continue
            explicit = candidate.block_id in explicit_ids or candidate.parent_id == container.block_id
            geometric = (
                container.bbox is not None
                and candidate.bbox is not None
                and _contains(container.bbox, candidate.bbox)
            )
            if (explicit or geometric) and candidate.text and candidate.block_type not in _CONTAINER_TYPES:
                children.append(candidate)
        if not children:
            continue
        metadata = dict(container.metadata)
        metadata["exclude_from_embedding"] = True
        metadata["container_child_ids"] = [child.block_id for child in children]
        updates[container.block_id] = {
            "child_ids": _ordered_unique([*container.child_ids, *(child.block_id for child in children)]),
            "quality_flags": _ordered_unique([*container.quality_flags, "container_text_deduplicated"]),
            "metadata": metadata,
        }
        for child in children:
            if child.parent_id is None:
                updates.setdefault(child.block_id, {})["parent_id"] = container.block_id

    # Preserve duplicate blocks for preview, but ensure only the first copy can
    # reach embedding/chunk text. Geometric overlap avoids removing legitimate
    # repeated phrases elsewhere on the page.
    for index, block in enumerate(normalized):
        if not block.text or block.block_type in _NON_CONTENT_TYPES:
            continue
        canonical = re.sub(r"\s+", "", block.text)
        for previous in normalized[:index]:
            if not previous.text or re.sub(r"\s+", "", previous.text) != canonical:
                continue
            if _intersection_ratio(previous.bbox, block.bbox) < 0.9:
                continue
            metadata = dict(block.metadata)
            metadata["exclude_from_embedding"] = True
            updates.setdefault(block.block_id, {}).update(
                {
                    "quality_flags": _ordered_unique([*block.quality_flags, "overlapping_text_deduplicated"]),
                    "metadata": metadata,
                }
            )
            break

    result: list[NormalizedBlock] = []
    for block in normalized:
        result.append(block.model_copy(update=updates.get(block.block_id, {})))
    return result


# A short alias is useful at provider boundaries and keeps older call sites
# readable while the normalized contract remains provider-neutral.
normalize_blocks = normalize_structural_blocks


def block_is_embeddable(block: NormalizedBlock) -> bool:
    return bool(
        block.text
        and block.block_type not in _NON_CONTENT_TYPES
        and not bool(block.metadata.get("exclude_from_embedding"))
    )


def score_page_quality(
    text: str,
    *,
    blocks: Sequence[NormalizedBlock] | None = None,
    min_chars: int = 80,
    min_printable_ratio: float = 0.85,
    image_coverage_ratio: float = 0.0,
    width_points: float | None = None,
    height_points: float | None = None,
) -> PageQuality:
    """Score whether native page text is safe to publish without OCR."""

    if min_chars < 0:
        raise ValueError("min_chars must be non-negative")
    if not 0 < min_printable_ratio <= 1:
        raise ValueError("min_printable_ratio must be in (0, 1]")

    raw = str(text or "")
    non_whitespace = [character for character in raw if not character.isspace()]
    non_whitespace_count = len(non_whitespace)
    printable_count = sum(character.isprintable() for character in non_whitespace)
    printable_ratio = printable_count / non_whitespace_count if non_whitespace_count else 0.0
    replacement_count = sum(character in {"\ufffd", "\u25a1"} for character in non_whitespace)
    replacement_ratio = replacement_count / non_whitespace_count if non_whitespace_count else 0.0
    private_use_count = sum(unicodedata.category(character) == "Co" for character in non_whitespace)
    private_use_ratio = private_use_count / non_whitespace_count if non_whitespace_count else 0.0
    control_count = sum(
        unicodedata.category(character) == "Cc" for character in non_whitespace
    )
    control_ratio = control_count / non_whitespace_count if non_whitespace_count else 0.0
    whitespace_ratio = (
        sum(character.isspace() for character in raw) / len(raw) if raw else 1.0
    )
    textual_block_count = (
        sum(block_is_embeddable(block) for block in blocks) if blocks is not None else None
    )
    page_area = (
        width_points * height_points
        if width_points is not None
        and height_points is not None
        and width_points > 0
        and height_points > 0
        else None
    )
    chars_per_1000_square_points = (
        non_whitespace_count / (page_area / 1000.0) if page_area else None
    )
    text_block_area = 0.0
    if page_area and blocks is not None:
        for block in blocks:
            if block_is_embeddable(block) and block.bbox is not None:
                text_block_area += max(0, block.bbox[2] - block.bbox[0]) * max(
                    0, block.bbox[3] - block.bbox[1]
                )
    text_block_coverage_ratio = min(1.0, text_block_area / page_area) if page_area else None

    length_score = 1.0 if min_chars == 0 else min(1.0, non_whitespace_count / max(1, min_chars))
    printable_score = min(1.0, printable_ratio / min_printable_ratio)
    structure_score = 1.0 if textual_block_count is None or textual_block_count > 0 else 0.0
    score = 0.45 * length_score + 0.35 * printable_score + 0.20 * structure_score
    score -= min(0.35, replacement_ratio * 4 + private_use_ratio * 4 + control_ratio * 4)
    if whitespace_ratio > 0.80:
        score -= min(0.15, (whitespace_ratio - 0.80) * 0.75)
    score = max(0.0, min(1.0, score))

    flags: list[str] = []
    if non_whitespace_count == 0:
        flags.append("empty_text")
    if non_whitespace_count < min_chars:
        flags.extend(("insufficient_text", "low_text_density"))
    if printable_ratio < min_printable_ratio:
        flags.append("low_printable_ratio")
    if replacement_ratio > 0.01:
        flags.append("replacement_characters")
    if private_use_ratio > 0.01:
        flags.append("private_use_characters")
    if control_ratio > 0.01:
        flags.append("control_characters")
    if whitespace_ratio > 0.80 and raw:
        flags.append("suspicious_whitespace")
    if textual_block_count == 0:
        flags.append("no_text_blocks")
    if non_whitespace_count < min_chars and image_coverage_ratio >= 0.35:
        flags.extend(("image_only", "scanned_page"))
    elif non_whitespace_count == 0 and image_coverage_ratio < 0.05:
        flags.append("blank_page")

    needs_ocr = bool(
        non_whitespace_count < min_chars
        or printable_ratio < min_printable_ratio
        or replacement_ratio > 0.05
        or private_use_ratio > 0.05
        or control_ratio > 0.02
        or textual_block_count == 0
        or score < 0.60
    )
    if needs_ocr:
        flags.append("low_quality_native_text")

    metrics: dict[str, float | int | str | bool | None] = {
        "non_whitespace_chars": non_whitespace_count,
        "printable_ratio": round(printable_ratio, 6),
        "replacement_ratio": round(replacement_ratio, 6),
        "private_use_ratio": round(private_use_ratio, 6),
        "control_ratio": round(control_ratio, 6),
        "whitespace_ratio": round(whitespace_ratio, 6),
        "image_coverage_ratio": round(max(0.0, min(1.0, image_coverage_ratio)), 6),
    }
    if textual_block_count is not None:
        metrics["textual_block_count"] = textual_block_count
    if chars_per_1000_square_points is not None:
        metrics["chars_per_1000_square_points"] = round(chars_per_1000_square_points, 6)
    if text_block_coverage_ratio is not None:
        metrics["text_block_coverage_ratio"] = round(text_block_coverage_ratio, 6)
    return PageQuality(
        score=round(score, 6),
        needs_ocr=needs_ocr,
        flags=_ordered_unique(flags),
        metrics=metrics,
    )


assess_page_quality = score_page_quality


def _heading_level(text: str) -> int | None:
    compact = text.strip()
    if re.match(r"^第[0-9一二三四五六七八九十百零〇两]+[篇编章]", compact):
        return 1
    if re.match(r"^第[0-9一二三四五六七八九十百零〇两]+节", compact):
        return 2
    if re.match(r"^实验\s*\d+", compact):
        return 2
    numbered = re.match(r"^(\d+(?:\.\d+){0,3})[\s、.．]+", compact)
    if numbered:
        return min(4, numbered.group(1).count(".") + 1)
    if _COMMON_SUBHEADING_RE.match(compact):
        return 3
    return None


def _looks_like_equation(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    if not compact or len(compact) > 400 or not _EQUATION_SIGNAL_RE.search(compact):
        return False
    formula_count = len(_CHEMICAL_FORMULA_RE.findall(compact))
    operator_count = len(re.findall(r"(?:→|⇌|↔|=>|->|=|\+)", compact))
    return formula_count >= 1 and operator_count >= 1


def _classify_text_block(
    text: str,
    *,
    max_font_size: float,
    body_font_size: float,
    bold: bool,
) -> tuple[BlockType, dict[str, Any]]:
    metadata: dict[str, Any] = {}
    heading_level = _heading_level(text)
    if heading_level is not None:
        metadata["heading_level"] = heading_level
        return (BlockType.TITLE if heading_level == 1 else BlockType.SECTION_HEADER), metadata
    if (
        len(text) <= 100
        and body_font_size > 0
        and (max_font_size >= body_font_size * 1.35 or (bold and max_font_size >= body_font_size * 1.1))
    ):
        metadata["heading_level"] = 1 if max_font_size >= body_font_size * 1.7 else 2
        return (
            BlockType.TITLE if metadata["heading_level"] == 1 else BlockType.SECTION_HEADER,
            metadata,
        )
    if _TABLE_CAPTION_RE.match(text):
        return BlockType.TABLE_CAPTION, metadata
    if _IMAGE_CAPTION_RE.match(text):
        return BlockType.IMAGE_CAPTION, metadata
    if _looks_like_equation(text):
        return BlockType.EQUATION, metadata
    lines = [line for line in text.splitlines() if line.strip()]
    if lines and sum(bool(_LIST_ITEM_RE.match(line)) for line in lines) >= max(1, len(lines) // 2):
        return BlockType.LIST, metadata
    return BlockType.TEXT, metadata


def _table_markdown(rows: Sequence[Sequence[str]]) -> str:
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    padded = [list(row) + [""] * (width - len(row)) for row in rows]

    def markdown_row(row: Sequence[str]) -> str:
        cells = [cell.replace("|", r"\|").replace("\n", " ") for cell in row]
        return "| " + " | ".join(cells) + " |"

    return "\n".join(
        [markdown_row(padded[0]), markdown_row(["---"] * width), *(markdown_row(row) for row in padded[1:])]
    )


def _extract_native_tables(page: pymupdf.Page, page_number: int) -> tuple[list[NormalizedBlock], str | None]:
    tables: list[NormalizedBlock] = []
    try:
        finder = page.find_tables()
    except Exception as exc:  # PyMuPDF table detection is optional diagnostics.
        return [], type(exc).__name__
    for index, table in enumerate(finder.tables, start=1):
        raw_rows = table.extract() or []
        rows: list[list[str]] = []
        for raw_row in raw_rows:
            row = [normalize_content_text(str(cell or "")) for cell in raw_row]
            if any(row):
                rows.append(row)
        if not rows:
            continue
        text = "\n".join(" | ".join(cell for cell in row if cell) for row in rows)
        bbox, _ = _normalize_bbox(
            table.bbox,
            width_points=float(page.rect.width),
            height_points=float(page.rect.height),
        )
        tables.append(
            NormalizedBlock(
                block_id=f"p{page_number}-table{index}",
                block_type=BlockType.TABLE,
                bbox=bbox,
                text=text,
                markdown=_table_markdown(rows),
                metadata={
                    "row_count": len(rows),
                    "column_count": max(len(row) for row in rows),
                    "source": "pymupdf.find_tables",
                },
            )
        )
    return tables, None


def _text_dict(page: pymupdf.Page) -> dict[str, Any]:
    flags = pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES
    return page.get_text("dict", sort=True, flags=flags)


def _raw_text_blocks(page: pymupdf.Page) -> tuple[list[dict[str, Any]], float]:
    result: list[dict[str, Any]] = []
    weighted_sizes: list[float] = []
    for raw_block in _text_dict(page).get("blocks", []):
        if int(raw_block.get("type", 0)) != 0:
            continue
        line_texts: list[str] = []
        spans: list[dict[str, Any]] = []
        for line in raw_block.get("lines", []):
            line_spans = list(line.get("spans", []))
            spans.extend(line_spans)
            line_texts.append("".join(str(span.get("text") or "") for span in line_spans))
        text = _join_pdf_lines(line_texts)
        if not text:
            continue
        sizes = [float(span.get("size") or 0.0) for span in spans if float(span.get("size") or 0.0) > 0]
        for span in spans:
            size = float(span.get("size") or 0.0)
            if size > 0:
                weighted_sizes.extend([size] * min(40, max(1, len(str(span.get("text") or "")))))
        result.append(
            {
                "bbox": raw_block.get("bbox"),
                "text": text,
                "max_font_size": max(sizes, default=0.0),
                "font_names": _ordered_unique(str(span.get("font") or "") for span in spans),
                "bold": any("bold" in str(span.get("font") or "").lower() for span in spans),
            }
        )
    body_font_size = statistics.median(weighted_sizes) if weighted_sizes else 0.0
    return result, body_font_size


def _margin_signature(text: str) -> str:
    return re.sub(r"\s+", " ", normalize_content_text(text)).strip().casefold()


def _repeated_margin_text(document: pymupdf.Document) -> tuple[set[str], set[str]]:
    if document.page_count < 2:
        return set(), set()
    headers: Counter[str] = Counter()
    footers: Counter[str] = Counter()
    for page in document:
        height = float(page.rect.height)
        raw_blocks, _body_font_size = _raw_text_blocks(page)
        for raw in raw_blocks:
            bbox, _ = _normalize_bbox(
                raw.get("bbox"),
                width_points=float(page.rect.width),
                height_points=height,
            )
            if bbox is None:
                continue
            signature = _margin_signature(str(raw.get("text") or ""))
            if not signature or _PAGE_NUMBER_RE.fullmatch(signature):
                continue
            if bbox[3] <= height * 0.10:
                headers[signature] += 1
            elif bbox[1] >= height * 0.90:
                footers[signature] += 1
    threshold = max(2, math.ceil(document.page_count * 0.30))
    return (
        {text for text, count in headers.items() if count >= threshold},
        {text for text, count in footers.items() if count >= threshold},
    )


def _image_blocks(page: pymupdf.Page, page_number: int) -> tuple[list[NormalizedBlock], float]:
    blocks: list[NormalizedBlock] = []
    area = max(1.0, float(page.rect.width * page.rect.height))
    covered_area = 0.0
    seen: set[tuple[int, int, int, int, int]] = set()
    for image in page.get_images(full=True):
        xref = int(image[0])
        try:
            rects = page.get_image_rects(xref)
        except Exception:
            rects = []
        for rect in rects:
            bbox, invalid = _normalize_bbox(
                tuple(rect),
                width_points=float(page.rect.width),
                height_points=float(page.rect.height),
            )
            if invalid or bbox is None:
                continue
            key = (*bbox, xref)
            if key in seen:
                continue
            seen.add(key)
            covered_area += (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            blocks.append(
                NormalizedBlock(
                    block_id=f"p{page_number}-image{len(blocks) + 1}",
                    block_type=BlockType.IMAGE,
                    bbox=bbox,
                    metadata={"xref": xref},
                )
            )
    return blocks, min(1.0, covered_area / area)


class PyMuPDFExtractor:
    """Native, page-at-a-time PDF extractor. It never performs local OCR."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        max_pages: int | None = None,
        min_chars: int | None = None,
        min_printable_ratio: float | None = None,
        render_dpi: int | None = None,
        native_min_chars: int | None = None,
        native_min_printable_ratio: float | None = None,
    ) -> None:
        effective = settings or get_settings()
        self.max_pages = max_pages if max_pages is not None else effective.max_textbook_pages
        self.min_chars = (
            min_chars
            if min_chars is not None
            else native_min_chars
            if native_min_chars is not None
            else effective.textbook_native_min_chars
        )
        self.min_printable_ratio = (
            min_printable_ratio
            if min_printable_ratio is not None
            else native_min_printable_ratio
            if native_min_printable_ratio is not None
            else effective.textbook_native_min_printable_ratio
        )
        self.render_dpi = render_dpi if render_dpi is not None else effective.textbook_ocr_render_dpi
        if self.max_pages <= 0:
            raise ValueError("max_pages must be positive")
        if self.min_chars < 0:
            raise ValueError("min_chars must be non-negative")
        if not 0 < self.min_printable_ratio <= 1:
            raise ValueError("min_printable_ratio must be in (0, 1]")
        if self.render_dpi <= 0:
            raise ValueError("render_dpi must be positive")

    def _open(self, pdf_path: Path) -> pymupdf.Document:
        path = Path(pdf_path)
        try:
            document = pymupdf.open(path)
        except Exception as exc:
            raise PDFExtractionError(
                "invalid_pdf",
                "The textbook PDF could not be opened",
                error_type=type(exc).__name__,
            ) from exc
        if document.needs_pass:
            document.close()
            raise PDFExtractionError("encrypted_pdf", "Password-protected textbook PDFs are not supported")
        if document.page_count > self.max_pages:
            page_count = document.page_count
            document.close()
            raise PDFExtractionError(
                "page_limit_exceeded",
                "The textbook PDF exceeds the configured page limit",
                page_count=page_count,
                max_pages=self.max_pages,
            )
        return document

    def extract(self, pdf_path: Path) -> Iterable[NormalizedPage]:
        document = self._open(pdf_path)
        try:
            repeated_headers, repeated_footers = _repeated_margin_text(document)
            for page_index in range(document.page_count):
                page = document.load_page(page_index)
                yield self._extract_page(
                    page,
                    page_number=page_index + 1,
                    repeated_headers=repeated_headers,
                    repeated_footers=repeated_footers,
                )
        finally:
            document.close()

    def _extract_page(
        self,
        page: pymupdf.Page,
        *,
        page_number: int,
        repeated_headers: set[str],
        repeated_footers: set[str],
    ) -> NormalizedPage:
        width = float(page.rect.width)
        height = float(page.rect.height)
        raw_blocks, body_font_size = _raw_text_blocks(page)
        text_blocks: list[NormalizedBlock] = []
        for index, raw in enumerate(raw_blocks, start=1):
            text = str(raw["text"])
            bbox, invalid_bbox = _normalize_bbox(
                raw.get("bbox"),
                width_points=width,
                height_points=height,
            )
            metadata: dict[str, Any] = {
                "max_font_size": round(float(raw["max_font_size"]), 3),
                "body_font_size": round(body_font_size, 3),
                "font_names": raw["font_names"],
            }
            flags: list[str] = ["invalid_bbox"] if invalid_bbox else []
            signature = _margin_signature(text)
            block_type: BlockType
            if signature in repeated_headers:
                block_type = BlockType.HEADER
                metadata["exclude_from_embedding"] = True
            elif signature in repeated_footers:
                block_type = BlockType.FOOTER
                metadata["exclude_from_embedding"] = True
            elif bbox is not None and _PAGE_NUMBER_RE.fullmatch(text.strip()) and (
                bbox[1] >= height * 0.85 or bbox[3] <= height * 0.15
            ):
                block_type = BlockType.PAGE_NUMBER
                metadata["exclude_from_embedding"] = True
            else:
                block_type, classified_metadata = _classify_text_block(
                    text,
                    max_font_size=float(raw["max_font_size"]),
                    body_font_size=body_font_size,
                    bold=bool(raw["bold"]),
                )
                metadata.update(classified_metadata)
            markdown = text
            if block_type in {BlockType.TITLE, BlockType.SECTION_HEADER}:
                level = int(metadata.get("heading_level") or 2)
                markdown = f"{'#' * max(1, min(6, level))} {text}"
            elif block_type == BlockType.EQUATION:
                markdown = f"$$\n{text}\n$$"
            text_blocks.append(
                NormalizedBlock(
                    block_id=f"p{page_number}-b{index}",
                    block_type=block_type,
                    bbox=bbox,
                    text=text,
                    markdown=markdown,
                    quality_flags=flags,
                    metadata=metadata,
                )
            )

        table_blocks, table_error = _extract_native_tables(page, page_number)
        if table_blocks:
            adjusted: list[NormalizedBlock] = []
            for block in text_blocks:
                if any(_intersection_ratio(block.bbox, table.bbox) >= 0.5 for table in table_blocks):
                    metadata = dict(block.metadata)
                    metadata["exclude_from_embedding"] = True
                    block = block.model_copy(
                        update={
                            "quality_flags": _ordered_unique(
                                [*block.quality_flags, "native_table_text_deduplicated"]
                            ),
                            "metadata": metadata,
                        }
                    )
                adjusted.append(block)
            text_blocks = adjusted

        image_blocks, image_coverage_ratio = _image_blocks(page, page_number)
        all_blocks = [*text_blocks, *table_blocks, *image_blocks]
        all_blocks.sort(
            key=lambda block: (
                block.bbox[1] if block.bbox is not None else math.inf,
                block.bbox[0] if block.bbox is not None else math.inf,
                block.block_id,
            )
        )
        blocks = normalize_structural_blocks(
            all_blocks,
            page_number=page_number,
            width_points=width,
            height_points=height,
        )
        content_blocks = [block for block in blocks if block_is_embeddable(block)]
        text = "\n\n".join(block.text for block in content_blocks if block.text)
        markdown = "\n\n".join((block.markdown or block.text) for block in content_blocks if block.text)
        quality = score_page_quality(
            text,
            blocks=blocks,
            min_chars=self.min_chars,
            min_printable_ratio=self.min_printable_ratio,
            image_coverage_ratio=image_coverage_ratio,
            width_points=width,
            height_points=height,
        )
        canonical = normalize_content_text(text)
        diagnostics: dict[str, Any] = {
            "extractor": EXTRACTOR_NAME,
            "extractor_version": EXTRACTOR_VERSION,
            "raw_text_block_count": len(raw_blocks),
            "normalized_block_count": len(blocks),
            "excluded_block_count": sum(
                bool(block.metadata.get("exclude_from_embedding")) for block in blocks
            ),
            "table_count": len(table_blocks),
            "image_count": len(image_blocks),
            "image_coverage_ratio": round(image_coverage_ratio, 6),
        }
        if table_error:
            diagnostics["table_detection_error"] = table_error
        return NormalizedPage(
            page_number=page_number,
            width_points=width,
            height_points=height,
            text=text,
            markdown=markdown,
            blocks=blocks,
            quality=quality,
            content_hash=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            diagnostics=diagnostics,
        )

    def render_page(self, pdf_path: Path, page_number: int) -> RenderedPage:
        if page_number <= 0:
            raise PDFExtractionError("invalid_page_number", "PDF page numbers are one-based")
        document = self._open(pdf_path)
        try:
            if page_number > document.page_count:
                raise PDFExtractionError(
                    "page_not_found",
                    "The requested PDF page does not exist",
                    page_number=page_number,
                    page_count=document.page_count,
                )
            page = document.load_page(page_number - 1)
            scale = self.render_dpi / 72.0
            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(scale, scale),
                colorspace=pymupdf.csRGB,
                alpha=False,
                annots=False,
            )
            return RenderedPage(
                page_number=page_number,
                image_bytes=pixmap.tobytes("png"),
                mime_type="image/png",
                pixel_width=pixmap.width,
                pixel_height=pixmap.height,
            )
        finally:
            document.close()


# Compatibility-friendly name for dependency wiring that refers to a generic
# native extractor while still making the concrete implementation explicit.
NativePDFExtractor = PyMuPDFExtractor

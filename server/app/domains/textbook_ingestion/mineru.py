from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import re
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any

import httpx
from PIL import Image

from server.app.domains.textbook_ingestion.contracts import (
    BlockType,
    ExtractionMethod,
    NormalizedBlock,
    NormalizedPage,
    OCRPageResult,
    PageQuality,
)
from server.app.domains.textbook_ingestion.ports import RenderedPage


LAYOUT_PROMPT = "\nLayout Detection:"
TEXT_PROMPT = "\nText Recognition:"
TABLE_PROMPT = "\nTable Recognition:"
FORMULA_PROMPT = "\nFormula Recognition:"
SYSTEM_PROMPT = "You are a helpful assistant."
LAYOUT_IMAGE_SIZE = (1036, 1036)
MIN_CROP_EDGE = 28
MAX_CROP_EDGE_RATIO = 50.0

_OFFICIAL_LAYOUT_RE = re.compile(
    r"<\|box_start\|>(\d+)\s+(\d+)\s+(\d+)\s+(\d+)"
    r"<\|box_end\|><\|ref_start\|>(\w+?)<\|ref_end\|>"
    r"(?:(<\|rotate_(?:up|right|down|left)\|>))?"
    r"(.*?)(?=<\|box_start\|>|$)",
    re.DOTALL,
)
_STRIPPED_LAYOUT_RE = re.compile(
    r"^\s*(\d{1,4})\s+(\d{1,4})\s+(\d{1,4})\s+(\d{1,4})\s+([A-Za-z_]+)(?:\s+(.*?))?\s*$"
)
_OFFICIAL_LAYOUT_TAIL_RE = re.compile(
    r"\s*(?:<\|(?:txt_contd_tgt|txt_contd_src)\|>\s*)*",
    re.DOTALL,
)
_ROTATION_MAP = {
    "<|rotate_up|>": 0,
    "<|rotate_right|>": 90,
    "<|rotate_down|>": 180,
    "<|rotate_left|>": 270,
}
_CONTAINER_TYPES = {BlockType.LIST, BlockType.IMAGE_BLOCK, BlockType.EQUATION_BLOCK, BlockType.TABLE}
_SKIP_RECOGNITION_TYPES = {
    BlockType.LIST,
    BlockType.IMAGE_BLOCK,
    BlockType.EQUATION_BLOCK,
    BlockType.IMAGE,
    BlockType.CHART,
}


class MinerUProviderError(RuntimeError):
    def __init__(self, reason: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.reason = reason
        self.retryable = retryable


class MinerULayoutError(MinerUProviderError):
    pass


@dataclass(frozen=True)
class ParsedLayout:
    blocks: list[NormalizedBlock]
    warnings: list[str]
    format: str


@dataclass(frozen=True)
class _Completion:
    content: str
    model: str
    request_id: str | None
    latency_ms: int


def _block_type(value: str) -> BlockType | None:
    normalized = value.strip().lower()
    if normalized == "inline_formula":
        return None
    if normalized == "unknown":
        return BlockType.IMAGE
    if normalized == "text":
        return BlockType.TEXT
    try:
        return BlockType(normalized)
    except ValueError as exc:
        raise MinerULayoutError("unknown_layout_type", f"Unknown MinerU layout block type: {normalized}") from exc


def _bbox(values: tuple[str, str, str, str]) -> tuple[int, int, int, int]:
    coords = tuple(int(value) for value in values)
    if any(value < 0 or value > 1000 for value in coords):
        raise MinerULayoutError("invalid_layout_bounds", f"MinerU layout coordinate is outside 0..1000: {coords}")
    x1, y1, x2, y2 = coords
    if x1 >= x2 or y1 >= y2:
        raise MinerULayoutError("invalid_layout_bounds", f"MinerU layout box has no area: {coords}")
    return coords


def _coverage(inner: tuple[int, int, int, int], outer: tuple[int, int, int, int]) -> float:
    ix1, iy1, ix2, iy2 = inner
    ox1, oy1, ox2, oy2 = outer
    intersection = max(0, min(ix2, ox2) - max(ix1, ox1)) * max(0, min(iy2, oy2) - max(iy1, oy1))
    inner_area = max(1, (ix2 - ix1) * (iy2 - iy1))
    return intersection / inner_area


def _attach_container_relations(blocks: list[NormalizedBlock]) -> None:
    containers = [block for block in blocks if block.block_type in _CONTAINER_TYPES and block.bbox]
    for block in blocks:
        if block in containers or not block.bbox:
            continue
        candidates = [
            container
            for container in containers
            if container.bbox and _coverage(block.bbox, container.bbox) >= 0.9
        ]
        if not candidates:
            continue
        parent = min(
            candidates,
            key=lambda item: (item.bbox[2] - item.bbox[0]) * (item.bbox[3] - item.bbox[1]) if item.bbox else 1_000_000,
        )
        block.parent_id = parent.block_id
        parent.child_ids.append(block.block_id)
        if parent.block_type == BlockType.TABLE:
            block.metadata["covered_by_table"] = True


def _validate_layout_shape(blocks: list[NormalizedBlock]) -> None:
    if not blocks:
        raise MinerULayoutError("empty_layout", "MinerU returned no usable layout blocks")
    duplicates = Counter((block.block_type.value, block.bbox) for block in blocks)
    if duplicates and max(duplicates.values()) >= 4:
        raise MinerULayoutError("repeated_layout", "MinerU returned repeated duplicate layout blocks")
    near_full_page = 0
    for block in blocks:
        if not block.bbox:
            continue
        x1, y1, x2, y2 = block.bbox
        if (x2 - x1) * (y2 - y1) >= 900_000:
            near_full_page += 1
    if near_full_page >= 3:
        raise MinerULayoutError("repeated_full_page_layout", "MinerU returned repeated full-page layout blocks")


def parse_layout_output(output: str) -> ParsedLayout:
    raw = output.strip()
    if not raw:
        raise MinerULayoutError("empty_layout", "MinerU returned an empty layout response")
    blocks: list[NormalizedBlock] = []
    warnings: list[str] = []
    official_matches = list(_OFFICIAL_LAYOUT_RE.finditer(raw))
    layout_format = "official_tokens" if official_matches else "aigw_stripped"
    if official_matches:
        if raw[: official_matches[0].start()].strip():
            raise MinerULayoutError("malformed_layout_prefix", "Malformed content precedes MinerU layout blocks")
        for match in official_matches:
            if not _OFFICIAL_LAYOUT_TAIL_RE.fullmatch(match.group(7) or ""):
                raise MinerULayoutError("malformed_layout_tail", "Malformed content follows a MinerU layout block")
        candidates = [
            (match.groups()[0:4], match.group(5), match.group(6), match.group(7) or "")
            for match in official_matches
        ]
    else:
        candidates = []
        for line in raw.replace("```text", "").replace("```", "").splitlines():
            if not line.strip():
                continue
            match = _STRIPPED_LAYOUT_RE.fullmatch(line)
            if not match:
                raise MinerULayoutError("malformed_layout_line", f"Malformed MinerU layout line: {line[:160]}")
            candidates.append((match.groups()[0:4], match.group(5), None, match.group(6) or ""))
        warnings.append("aigw_special_tokens_stripped")

    for index, (coords, raw_type, rotation_token, tail) in enumerate(candidates, start=1):
        block_type = _block_type(raw_type)
        if block_type is None:
            warnings.append("inline_formula_layout_skipped")
            continue
        rotation = _ROTATION_MAP.get(rotation_token) if rotation_token else None
        merge_prev = "txt_contd_tgt" in tail
        blocks.append(
            NormalizedBlock(
                block_id=f"layout-{index}",
                block_type=block_type,
                bbox=_bbox(coords),
                metadata={
                    "mineru_type": raw_type.lower(),
                    "rotation": rotation,
                    "merge_previous": merge_prev if block_type == BlockType.TEXT else False,
                },
            )
        )
    _validate_layout_shape(blocks)
    _attach_container_relations(blocks)
    return ParsedLayout(blocks=blocks, warnings=warnings, format=layout_format)


def _data_url(image_bytes: bytes, mime_type: str = "image/png") -> str:
    return f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def _png_bytes(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _prepare_layout_image(image: Image.Image) -> bytes:
    return _png_bytes(image.convert("RGB").resize(LAYOUT_IMAGE_SIZE, Image.Resampling.BICUBIC))


def _prepare_crop(image: Image.Image, bbox: tuple[int, int, int, int], rotation: int | None) -> bytes:
    x1, y1, x2, y2 = bbox
    width, height = image.size
    crop = image.crop(
        (
            round(x1 / 1000 * width),
            round(y1 / 1000 * height),
            round(x2 / 1000 * width),
            round(y2 / 1000 * height),
        )
    ).convert("RGB")
    if crop.width < 1 or crop.height < 1:
        raise MinerULayoutError("invalid_crop", "MinerU layout block produced an empty crop")
    if rotation in {90, 180, 270}:
        crop = crop.rotate(rotation, expand=True)
    edge_ratio = max(crop.size) / max(1, min(crop.size))
    if edge_ratio > MAX_CROP_EDGE_RATIO:
        if crop.width > crop.height:
            padded_size = (crop.width, max(crop.height, round(crop.width / MAX_CROP_EDGE_RATIO)))
        else:
            padded_size = (max(crop.width, round(crop.height / MAX_CROP_EDGE_RATIO)), crop.height)
        padded = Image.new("RGB", padded_size, "white")
        padded.paste(crop, ((padded.width - crop.width) // 2, (padded.height - crop.height) // 2))
        crop = padded
    if min(crop.size) < MIN_CROP_EDGE:
        scale = MIN_CROP_EDGE / min(crop.size)
        crop = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))), Image.Resampling.BICUBIC)
    return _png_bytes(crop)


def _prompt_for(block_type: BlockType) -> str:
    if block_type == BlockType.TABLE:
        return TABLE_PROMPT
    if block_type in {BlockType.EQUATION, BlockType.FORMULA_NUMBER}:
        return FORMULA_PROMPT
    return TEXT_PROMPT


def _content_markdown(block: NormalizedBlock) -> str:
    content = block.text.strip()
    if not content:
        return ""
    if block.block_type in {BlockType.TITLE, BlockType.SECTION_HEADER}:
        return f"## {content}"
    if block.block_type == BlockType.EQUATION:
        return f"$$\n{content}\n$$"
    return content


def _visible_for_text(block: NormalizedBlock, by_id: dict[str, NormalizedBlock]) -> bool:
    if block.block_type in {
        BlockType.HEADER,
        BlockType.FOOTER,
        BlockType.PAGE_NUMBER,
        BlockType.IMAGE,
        BlockType.CHART,
        BlockType.IMAGE_BLOCK,
        BlockType.EQUATION_BLOCK,
        BlockType.LIST,
    }:
        return False
    if block.metadata.get("covered_by_table"):
        return False
    if block.parent_id:
        parent = by_id.get(block.parent_id)
        if parent and parent.block_type == BlockType.TABLE:
            return False
    return bool(block.text.strip())


class MinerUHTTPProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str = "mineru",
        enabled: bool = True,
        timeout_seconds: float = 90.0,
        concurrency: int = 2,
        max_retries: int = 3,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max(1, concurrency))
        self._client = client
        self._owns_client = client is None

    @property
    def configured(self) -> bool:
        return bool(self.enabled and self.base_url and self.api_key and self.model)

    @property
    def chat_url(self) -> str:
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/chat/completions"
        return f"{self.base_url}/v1/chat/completions"

    def _http_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds, connect=min(10.0, self.timeout_seconds)),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    async def _complete(
        self,
        image_bytes: bytes,
        prompt: str,
        *,
        idempotency_key: str,
        content_kind: str,
    ) -> _Completion:
        if not self.configured:
            raise MinerUProviderError("ocr_not_configured", "SYSU MinerU OCR is not configured")
        presence_penalty = 0.0 if content_kind == "layout" else 1.0
        frequency_penalty = 0.0 if content_kind == "layout" else (0.005 if content_kind == "table" else 0.05)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": _data_url(image_bytes)}},
                        {"type": "text", "text": prompt},
                    ],
                },
            ],
            "temperature": 0.0,
            "top_p": 0.01,
            "top_k": 1,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "repetition_penalty": 1.0,
            "vllm_xargs": {"no_repeat_ngram_size": 100, "debug": False},
            "skip_special_tokens": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Idempotency-Key": idempotency_key,
        }
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            started = time.monotonic()
            try:
                async with self._semaphore:
                    response = await self._http_client().post(self.chat_url, headers=headers, json=payload)
                latency_ms = round((time.monotonic() - started) * 1000)
                if response.status_code in {401, 403}:
                    raise MinerUProviderError("ocr_authentication_failed", "SYSU MinerU authentication failed")
                if response.status_code == 429 or response.status_code >= 500:
                    raise MinerUProviderError(
                        "ocr_temporarily_unavailable",
                        f"SYSU MinerU returned HTTP {response.status_code}",
                        retryable=True,
                    )
                if response.status_code >= 400:
                    raise MinerUProviderError("ocr_request_rejected", f"SYSU MinerU returned HTTP {response.status_code}")
                try:
                    body = response.json()
                except ValueError as exc:
                    raise MinerUProviderError("ocr_invalid_response", "SYSU MinerU returned invalid JSON", retryable=True) from exc
                choices = body.get("choices") if isinstance(body, dict) else None
                if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                    raise MinerUProviderError("ocr_invalid_response", "SYSU MinerU response has no choices", retryable=True)
                finish_reason = choices[0].get("finish_reason")
                if finish_reason == "length":
                    raise MinerUProviderError("ocr_response_truncated", "SYSU MinerU response was truncated")
                message = choices[0].get("message")
                content = message.get("content") if isinstance(message, dict) else None
                if isinstance(content, list):
                    content = "".join(
                        str(item.get("text") or "") for item in content if isinstance(item, dict)
                    )
                if not isinstance(content, str):
                    raise MinerUProviderError("ocr_invalid_response", "SYSU MinerU response content is missing", retryable=True)
                return _Completion(
                    content=content,
                    model=str(body.get("model") or self.model),
                    request_id=response.headers.get("x-request-id") or str(body.get("id") or "") or None,
                    latency_ms=latency_ms,
                )
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = MinerUProviderError(
                    "ocr_transport_error",
                    f"SYSU MinerU request failed: {exc.__class__.__name__}",
                    retryable=True,
                )
            except MinerUProviderError as exc:
                if not exc.retryable or attempt >= self.max_retries:
                    raise
                last_error = exc
            if attempt < self.max_retries:
                await asyncio.sleep(min(0.5 * (2**attempt), 4.0))
        if isinstance(last_error, MinerUProviderError):
            raise last_error
        raise MinerUProviderError("ocr_unknown_error", "SYSU MinerU request failed")

    async def recognize(self, page: RenderedPage, *, idempotency_key: str) -> OCRPageResult:
        if not self.configured:
            raise MinerUProviderError("ocr_not_configured", "SYSU MinerU OCR is not configured")
        started = time.monotonic()
        try:
            page_image = Image.open(io.BytesIO(page.image_bytes)).convert("RGB")
        except Exception as exc:
            raise MinerUProviderError("invalid_page_image", "Rendered PDF page is not a readable image") from exc
        layout_completion = await self._complete(
            _prepare_layout_image(page_image),
            LAYOUT_PROMPT,
            idempotency_key=f"{idempotency_key}:layout",
            content_kind="layout",
        )
        parsed = parse_layout_output(layout_completion.content)

        async def recognize_block(index: int, block: NormalizedBlock) -> tuple[int, _Completion | None, list[str]]:
            if block.block_type in _SKIP_RECOGNITION_TYPES or block.metadata.get("covered_by_table"):
                return index, None, []
            if not block.bbox:
                return index, None, ["missing_block_bbox"]
            crop = _prepare_crop(page_image, block.bbox, block.metadata.get("rotation"))
            prompt = _prompt_for(block.block_type)
            result = await self._complete(
                crop,
                prompt,
                idempotency_key=f"{idempotency_key}:block:{index}:{block.block_type.value}",
                content_kind=block.block_type.value,
            )
            warnings: list[str] = []
            if block.block_type == BlockType.TABLE and not result.content.strip():
                result = await self._complete(
                    crop,
                    TEXT_PROMPT,
                    idempotency_key=f"{idempotency_key}:block:{index}:table-text-fallback",
                    content_kind="text",
                )
                warnings.append("table_text_recognition_fallback")
            return index, result, warnings

        recognized = await asyncio.gather(
            *(recognize_block(index, block) for index, block in enumerate(parsed.blocks, start=1))
        )
        warnings = list(parsed.warnings)
        request_ids = [layout_completion.request_id] if layout_completion.request_id else []
        actual_model = layout_completion.model
        for index, completion, block_warnings in recognized:
            warnings.extend(block_warnings)
            block = parsed.blocks[index - 1]
            if completion is None:
                continue
            raw_content = completion.content.strip()
            block.text = raw_content
            block.markdown = _content_markdown(block)
            block.metadata["recognition_model"] = completion.model
            block.metadata["recognition_latency_ms"] = completion.latency_ms
            if completion.request_id:
                request_ids.append(completion.request_id)
            actual_model = completion.model or actual_model
            if block.block_type == BlockType.TABLE and raw_content:
                structured = bool(re.search(r"<\s*(?:table|tr|td|th)\b", raw_content, re.IGNORECASE))
                if not structured:
                    block.quality_flags.append("table_structure_lost")
                    warnings.append("table_structure_lost")

        by_id = {block.block_id: block for block in parsed.blocks}
        visible_blocks = [block for block in parsed.blocks if _visible_for_text(block, by_id)]
        text_content = "\n\n".join(block.text.strip() for block in visible_blocks if block.text.strip())
        markdown = "\n\n".join(
            (block.markdown or block.text).strip() for block in visible_blocks if (block.markdown or block.text).strip()
        )
        if not text_content:
            raise MinerUProviderError("ocr_empty_page", "SYSU MinerU returned no searchable text for the page")
        content_hash = hashlib.sha256(text_content.encode("utf-8")).hexdigest()
        quality_flags = list(dict.fromkeys(flag for block in parsed.blocks for flag in block.quality_flags))
        non_whitespace_chars = len(re.sub(r"\s+", "", text_content))
        quality_score = min(1.0, 0.65 + min(non_whitespace_chars, 500) / 1500)
        normalized_page = NormalizedPage(
            page_number=page.page_number,
            text=text_content,
            markdown=markdown,
            blocks=parsed.blocks,
            extraction_method=ExtractionMethod.MINERU,
            quality=PageQuality(
                score=quality_score,
                needs_ocr=False,
                flags=quality_flags,
                metrics={
                    "non_whitespace_chars": non_whitespace_chars,
                    "layout_block_count": len(parsed.blocks),
                    "layout_format": parsed.format,
                },
            ),
            content_hash=content_hash,
            ocr_provider="sysu_aigw_mineru",
            ocr_model=actual_model,
            diagnostics={
                "layout_format": parsed.format,
                "request_ids": request_ids,
                "warnings": list(dict.fromkeys(warnings)),
            },
        )
        return OCRPageResult(
            page=normalized_page,
            provider="sysu_aigw_mineru",
            model=actual_model,
            latency_ms=round((time.monotonic() - started) * 1000),
            request_id=layout_completion.request_id,
            warnings=list(dict.fromkeys(warnings)),
        )


class FakeOCRProvider:
    def __init__(self, pages: dict[int, NormalizedPage] | None = None, *, configured: bool = True) -> None:
        self.pages = pages or {}
        self._configured = configured
        self.calls: list[tuple[int, str]] = []

    @property
    def configured(self) -> bool:
        return self._configured

    async def recognize(self, page: RenderedPage, *, idempotency_key: str) -> OCRPageResult:
        self.calls.append((page.page_number, idempotency_key))
        if not self.configured:
            raise MinerUProviderError("ocr_not_configured", "Fake OCR provider is disabled")
        normalized = self.pages.get(page.page_number)
        if normalized is None:
            text_content = f"Synthetic OCR page {page.page_number}"
            normalized = NormalizedPage(
                page_number=page.page_number,
                text=text_content,
                markdown=text_content,
                blocks=[
                    NormalizedBlock(
                        block_id=f"p{page.page_number}-b1",
                        block_type=BlockType.TEXT,
                        bbox=(0, 0, 1000, 1000),
                        text=text_content,
                        markdown=text_content,
                    )
                ],
                extraction_method=ExtractionMethod.MINERU,
                quality=PageQuality(score=1, needs_ocr=False),
                content_hash=hashlib.sha256(text_content.encode("utf-8")).hexdigest(),
                ocr_provider="fake",
                ocr_model="fake-mineru",
            )
        return OCRPageResult(page=normalized, provider="fake", model="fake-mineru", latency_ms=0)

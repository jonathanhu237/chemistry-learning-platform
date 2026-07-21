from __future__ import annotations

import asyncio
import io
import json
from typing import Any

import httpx
import pytest
from PIL import Image, ImageDraw

from server.app.domains.textbook_ingestion.contracts import BlockType, ExtractionMethod
from server.app.domains.textbook_ingestion.mineru import (
    FORMULA_PROMPT,
    LAYOUT_PROMPT,
    TABLE_PROMPT,
    TEXT_PROMPT,
    MinerUHTTPProvider,
    MinerULayoutError,
    MinerUProviderError,
    parse_layout_output,
)
from server.app.domains.textbook_ingestion.ports import RenderedPage
from server.app.domains.textbook_ingestion.quality import CONFIRMED_BLANK_PAGE_FLAG


def _png(width: int = 1200, height: int = 1600) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(output, format="PNG")
    return output.getvalue()


def _marked_png(width: int = 1200, height: int = 1600) -> bytes:
    image = Image.new("RGB", (width, height), "white")
    ImageDraw.Draw(image).rectangle((40, 40, 49, 49), fill="black")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _dense_text_png(width: int = 1200, height: int = 1600) -> bytes:
    image = Image.new("RGB", (width, height), "white")
    drawing = ImageDraw.Draw(image)
    for y in range(100, height - 100, 28):
        drawing.rectangle((100, y, width - 100, y + 7), fill="black")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _faint_text_png(width: int = 1200, height: int = 1600) -> bytes:
    image = Image.new("RGB", (width, height), "white")
    drawing = ImageDraw.Draw(image)
    for line_number in range(10):
        y = 100 + line_number * 100
        drawing.rectangle((100, y, 699, y + 2), fill=(245, 245, 245))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _recognize_empty_layout(image_bytes: bytes) -> Any:
    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["messages"][1]["content"][1]["text"] == LAYOUT_PROMPT
        return _completion("", request_id="empty-layout")

    async def run() -> Any:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            provider = MinerUHTTPProvider(
                base_url="https://aigw.example.edu/v1",
                api_key="key",
                model="mineru",
                max_retries=0,
                client=client,
            )
            return await provider.recognize(
                RenderedPage(
                    page_number=169,
                    image_bytes=image_bytes,
                    mime_type="image/png",
                    pixel_width=1200,
                    pixel_height=1600,
                ),
                idempotency_key="job:page:169",
            )
        finally:
            await client.aclose()

    return asyncio.run(run())


def _completion(content: str, *, request_id: str, model: str = "mineru-test") -> httpx.Response:
    return httpx.Response(
        200,
        headers={"x-request-id": request_id},
        json={
            "id": request_id,
            "model": model,
            "choices": [{"finish_reason": "stop", "message": {"content": content}}],
        },
    )


def test_parse_official_layout_tokens_preserves_rotation_and_merge_hint() -> None:
    parsed = parse_layout_output(
        """
<|box_start|>20 30 920 130<|box_end|><|ref_start|>title<|ref_end|>
<|box_start|>40 150 940 400<|box_end|><|ref_start|>text<|ref_end|><|rotate_right|><|txt_contd_tgt|>
<|box_start|>100 430 900 650<|box_end|><|ref_start|>equation<|ref_end|>
"""
    )

    assert parsed.format == "official_tokens"
    assert parsed.warnings == []
    assert [block.block_type for block in parsed.blocks] == [
        BlockType.TITLE,
        BlockType.TEXT,
        BlockType.EQUATION,
    ]
    assert parsed.blocks[0].bbox == (20, 30, 920, 130)
    assert parsed.blocks[1].metadata == {
        "mineru_type": "text",
        "rotation": 90,
        "merge_previous": True,
    }
    assert parsed.blocks[2].metadata["rotation"] is None


def test_parse_gateway_stripped_layout_attaches_blocks_to_smallest_container() -> None:
    parsed = parse_layout_output(
        """
```text
50 50 950 950 image_block
100 100 900 900 table
150 180 850 260 text
180 300 820 700 equation
```
"""
    )

    outer, table, text, equation = parsed.blocks
    assert parsed.format == "aigw_stripped"
    assert parsed.warnings == ["aigw_special_tokens_stripped"]
    assert outer.parent_id is None
    assert table.parent_id is None
    assert text.parent_id == table.block_id
    assert equation.parent_id == table.block_id
    assert table.child_ids == [text.block_id, equation.block_id]
    assert text.metadata["covered_by_table"] is True
    assert equation.metadata["covered_by_table"] is True


def test_parse_gateway_stripped_layout_accepts_fused_final_coordinate_and_type() -> None:
    parsed = parse_layout_output(
        """
349 167 652 192title
082 071 359 095header
"""
    )

    assert [block.block_type for block in parsed.blocks] == [BlockType.TITLE, BlockType.HEADER]
    assert [block.bbox for block in parsed.blocks] == [
        (349, 167, 652, 192),
        (82, 71, 359, 95),
    ]
    assert parsed.warnings == [
        "aigw_layout_type_delimiter_missing",
        "aigw_special_tokens_stripped",
    ]


def test_parse_gateway_stripped_layout_accepts_only_official_continuation_tokens() -> None:
    parsed = parse_layout_output(
        """
136 375 938 394text<|txt_contd_src|>
136 400 938 430text <|txt_contd_tgt|>
"""
    )

    assert [block.block_type for block in parsed.blocks] == [BlockType.TEXT, BlockType.TEXT]
    assert parsed.blocks[0].metadata["merge_previous"] is False
    assert parsed.blocks[1].metadata["merge_previous"] is True
    assert parsed.warnings == [
        "aigw_layout_type_delimiter_missing",
        "aigw_special_tokens_stripped",
    ]


@pytest.mark.parametrize(
    ("output", "reason"),
    [
        ("10 20 30 text", "malformed_layout_line"),
        ("349 167 652 192title unexpected trailing text", "malformed_layout_line"),
        ("349 167 652 192title这是正文", "malformed_layout_line"),
        ("349 167 652 192title<|unexpected_token|>", "malformed_layout_line"),
        (
            "\n".join(
                [
                    "0 0 1000 1000 title",
                    "0 0 1000 1000 text",
                    "0 0 1000 1000 equation",
                ]
            ),
            "repeated_full_page_layout",
        ),
        (
            "\n".join(["10 10 100 100 text"] * 4),
            "repeated_layout",
        ),
    ],
)
def test_parse_layout_rejects_malformed_or_repeated_output(output: str, reason: str) -> None:
    with pytest.raises(MinerULayoutError) as error:
        parse_layout_output(output)

    assert error.value.reason == reason


def test_parse_official_layout_rejects_nonempty_malformed_tail() -> None:
    output = (
        "<|box_start|>10 20 900 180<|box_end|>"
        "<|ref_start|>text<|ref_end|>\n"
        "BROKEN_TRAILER"
    )

    with pytest.raises(MinerULayoutError) as error:
        parse_layout_output(output)

    assert error.value.reason == "malformed_layout_tail"


def test_http_provider_accepts_empty_layout_only_for_confirmed_blank_render() -> None:
    result = _recognize_empty_layout(_png())

    assert result.page.page_number == 169
    assert result.page.text == ""
    assert result.page.markdown == ""
    assert result.page.blocks == []
    assert result.page.extraction_method == ExtractionMethod.MINERU
    assert result.page.quality.score == 1.0
    assert result.page.quality.needs_ocr is False
    assert result.page.quality.flags == [CONFIRMED_BLANK_PAGE_FLAG]
    assert result.page.quality.metrics["layout_format"] == "empty"
    assert result.page.quality.metrics["blank_page_mean_luma"] == 255.0
    assert result.page.quality.metrics["blank_page_off_white_pixel_ratio"] == 0.0
    assert result.page.quality.metrics["blank_page_dark_pixel_ratio"] == 0.0
    assert result.page.diagnostics["request_ids"] == ["empty-layout"]
    assert result.page.diagnostics["warnings"] == [CONFIRMED_BLANK_PAGE_FLAG]
    assert result.page.diagnostics["blank_page_detection"]["confirmed"] is True
    assert result.page.diagnostics["blank_page_detection"]["off_white_luma_threshold"] == 250
    assert result.page.diagnostics["blank_page_detection"]["maximum_off_white_pixel_ratio"] == 0.0015
    assert result.warnings == [CONFIRMED_BLANK_PAGE_FLAG]


@pytest.mark.parametrize(
    "image_bytes",
    [_marked_png(), _dense_text_png()],
    ids=["tiny-dark-mark", "dense-text"],
)
def test_http_provider_keeps_empty_layout_terminal_for_nonblank_render(image_bytes: bytes) -> None:
    with pytest.raises(MinerULayoutError) as error:
        _recognize_empty_layout(image_bytes)

    assert error.value.reason == "empty_layout"


def test_http_provider_rejects_empty_layout_for_faint_text_like_strokes() -> None:
    with pytest.raises(MinerULayoutError) as error:
        _recognize_empty_layout(_faint_text_png())

    assert error.value.reason == "empty_layout"


def test_http_provider_uses_two_stage_contract_and_preserves_flat_table_text() -> None:
    requests: list[dict[str, Any]] = []
    raw_table = "元素  含量/%\nCl  35.45\nNa  22.99"

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        requests.append(
            {
                "url": str(request.url),
                "authorization": request.headers.get("authorization"),
                "idempotency_key": request.headers.get("x-idempotency-key"),
                "payload": payload,
            }
        )
        prompt = payload["messages"][1]["content"][1]["text"]
        if prompt == LAYOUT_PROMPT:
            return _completion("100 200 900 800 table", request_id="layout-request")
        if prompt == TABLE_PROMPT:
            return _completion(raw_table, request_id="table-request", model="mineru-resolved")
        raise AssertionError(f"unexpected MinerU prompt: {prompt!r}")

    async def run() -> Any:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            provider = MinerUHTTPProvider(
                base_url="https://aigw.example.edu/v1",
                api_key="test-api-key",
                model="mineru-requested",
                max_retries=0,
                max_output_tokens=4096,
                client=client,
            )
            return await provider.recognize(
                RenderedPage(
                    page_number=7,
                    image_bytes=_png(),
                    mime_type="image/png",
                    pixel_width=1200,
                    pixel_height=1600,
                ),
                idempotency_key="job-1:page-7",
            )
        finally:
            await client.aclose()

    result = asyncio.run(run())

    assert len(requests) == 2
    assert [request["url"] for request in requests] == [
        "https://aigw.example.edu/v1/chat/completions",
        "https://aigw.example.edu/v1/chat/completions",
    ]
    assert [request["authorization"] for request in requests] == [
        "Bearer test-api-key",
        "Bearer test-api-key",
    ]
    assert [request["idempotency_key"] for request in requests] == [
        "job-1:page-7:layout",
        "job-1:page-7:block:1:table",
    ]

    layout_payload, table_payload = [request["payload"] for request in requests]
    for payload in (layout_payload, table_payload):
        assert payload["model"] == "mineru-requested"
        assert payload["max_completion_tokens"] == 4096
        assert payload["max_tokens"] == 4096
        assert payload["skip_special_tokens"] is False
        assert payload["temperature"] == 0.0
        assert payload["messages"][1]["content"][0]["type"] == "image_url"
        assert payload["messages"][1]["content"][0]["image_url"]["url"].startswith(
            "data:image/png;base64,"
        )
    assert layout_payload["messages"][1]["content"][1] == {
        "type": "text",
        "text": LAYOUT_PROMPT,
    }
    assert layout_payload["presence_penalty"] == 0.0
    assert layout_payload["frequency_penalty"] == 0.0
    assert table_payload["messages"][1]["content"][1] == {
        "type": "text",
        "text": TABLE_PROMPT,
    }
    assert table_payload["presence_penalty"] == 1.0
    assert table_payload["frequency_penalty"] == 0.005

    assert result.page.page_number == 7
    assert result.page.text == raw_table
    assert result.page.markdown == raw_table
    assert result.page.blocks[0].text == raw_table
    assert result.page.blocks[0].quality_flags == ["table_structure_lost"]
    assert result.page.ocr_provider == "mineru"
    assert result.model == "mineru-resolved"
    assert result.request_id == "layout-request"
    assert result.page.diagnostics["request_ids"] == ["layout-request", "table-request"]
    assert "aigw_special_tokens_stripped" in result.warnings
    assert "table_structure_lost" in result.warnings


def test_http_provider_rejects_table_when_recognition_and_text_fallback_are_empty() -> None:
    requests: list[tuple[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        prompt = payload["messages"][1]["content"][1]["text"]
        idempotency_key = request.headers["x-idempotency-key"]
        requests.append((prompt, idempotency_key))
        if prompt == LAYOUT_PROMPT:
            return _completion(
                "100 100 900 300 text\n100 400 900 800 table",
                request_id="layout",
            )
        if prompt == TABLE_PROMPT:
            return _completion("", request_id="empty-table")
        if idempotency_key.endswith(":block:1:text"):
            return _completion("页面中的其他正文", request_id="text")
        if idempotency_key.endswith(":block:2:table-text-fallback"):
            return _completion("   ", request_id="empty-table-fallback")
        raise AssertionError(f"unexpected MinerU request: {prompt!r} {idempotency_key!r}")

    async def run() -> Any:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            provider = MinerUHTTPProvider(
                base_url="https://aigw.example.edu/v1",
                api_key="key",
                model="mineru",
                max_retries=0,
                client=client,
            )
            return await provider.recognize(
                RenderedPage(
                    page_number=8,
                    image_bytes=_dense_text_png(),
                    mime_type="image/png",
                    pixel_width=1200,
                    pixel_height=1600,
                ),
                idempotency_key="job:page:8",
            )
        finally:
            await client.aclose()

    with pytest.raises(MinerUProviderError) as error:
        asyncio.run(run())

    assert error.value.reason == "ocr_empty_table"
    assert error.value.retryable is False
    assert (TEXT_PROMPT, "job:page:8:block:2:table-text-fallback") in requests


def test_http_provider_selects_content_prompts_from_layout_types() -> None:
    assert TEXT_PROMPT != TABLE_PROMPT
    assert FORMULA_PROMPT != TEXT_PROMPT


def test_http_provider_retries_truncated_completion() -> None:
    layout_attempts = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal layout_attempts
        payload = json.loads(request.content)
        prompt = payload["messages"][1]["content"][1]["text"]
        if prompt == LAYOUT_PROMPT:
            layout_attempts += 1
            if layout_attempts == 1:
                return httpx.Response(
                    200,
                    json={
                        "id": "truncated-layout",
                        "model": "mineru-test",
                        "choices": [{"finish_reason": "length", "message": {"content": "partial"}}],
                    },
                )
            return _completion("10 10 990 990 text", request_id="layout-retry")
        return _completion("重试后可检索正文", request_id="text")

    async def run() -> Any:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            provider = MinerUHTTPProvider(
                base_url="https://aigw.example.edu/v1",
                api_key="key",
                model="mineru",
                max_retries=1,
                client=client,
            )
            return await provider.recognize(
                RenderedPage(
                    page_number=1,
                    image_bytes=_png(),
                    mime_type="image/png",
                    pixel_width=1200,
                    pixel_height=1600,
                ),
                idempotency_key="job:page:1",
            )
        finally:
            await client.aclose()

    result = asyncio.run(run())

    assert layout_attempts == 2
    assert result.page.text == "重试后可检索正文"


def test_http_provider_tiles_truncated_table_and_uses_text_recognition() -> None:
    prompts: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        prompt = payload["messages"][1]["content"][1]["text"]
        prompts.append(prompt)
        if prompt == LAYOUT_PROMPT:
            return _completion("100 700 900 900 table", request_id="layout")
        if prompt == TABLE_PROMPT:
            return httpx.Response(
                200,
                json={
                    "id": "truncated-table",
                    "model": "mineru-test",
                    "choices": [{"finish_reason": "length", "message": {"content": "partial"}}],
                },
            )
        tile_number = prompts.count(TEXT_PROMPT)
        return _completion(f"分区{tile_number}文字", request_id=f"tile-{tile_number}")

    async def run() -> Any:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            provider = MinerUHTTPProvider(
                base_url="https://aigw.example.edu/v1",
                api_key="key",
                model="mineru",
                max_retries=0,
                client=client,
            )
            return await provider.recognize(
                RenderedPage(
                    page_number=298,
                    image_bytes=_png(),
                    mime_type="image/png",
                    pixel_width=1200,
                    pixel_height=1600,
                ),
                idempotency_key="job:page:298",
            )
        finally:
            await client.aclose()

    result = asyncio.run(run())

    assert prompts == [LAYOUT_PROMPT, TABLE_PROMPT, TEXT_PROMPT, TEXT_PROMPT]
    assert result.page.text == "分区1文字\n分区2文字"
    assert result.page.diagnostics["request_ids"] == ["layout", "tile-1", "tile-2"]
    assert "table_tiled_text_recognition_fallback" in result.warnings
    assert "table_structure_lost" in result.warnings


def test_http_provider_uses_explicit_endpoint_and_configured_provider_label() -> None:
    requests: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        payload = json.loads(request.content)
        prompt = payload["messages"][1]["content"][1]["text"]
        if prompt == LAYOUT_PROMPT:
            return _completion("10 10 990 990 text", request_id="layout")
        return _completion("可检索正文", request_id="text")

    async def run() -> Any:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            provider = MinerUHTTPProvider(
                base_url="",
                endpoint="https://ocr.example.test/custom/chat/completions",
                api_key="key",
                model="mineru-alias",
                provider_label="campus_mineru",
                protocol="openai_chat_completions",
                max_retries=0,
                client=client,
            )
            return await provider.recognize(
                RenderedPage(
                    page_number=1,
                    image_bytes=_png(),
                    mime_type="image/png",
                    pixel_width=1200,
                    pixel_height=1600,
                ),
                idempotency_key="job:page:1",
            )
        finally:
            await client.aclose()

    result = asyncio.run(run())

    assert requests == [
        "https://ocr.example.test/custom/chat/completions",
        "https://ocr.example.test/custom/chat/completions",
    ]
    assert result.provider == "campus_mineru"
    assert result.page.ocr_provider == "campus_mineru"


def test_http_provider_rejects_unsupported_protocol_before_request() -> None:
    provider = MinerUHTTPProvider(
        base_url="https://ocr.example.test/v1",
        api_key="key",
        model="mineru-alias",
        protocol="unsupported",
        max_retries=0,
    )

    with pytest.raises(MinerUProviderError, match="Unsupported MinerU OCR protocol") as error:
        asyncio.run(
            provider.recognize(
                RenderedPage(
                    page_number=1,
                    image_bytes=_png(),
                    mime_type="image/png",
                    pixel_width=1200,
                    pixel_height=1600,
                ),
                idempotency_key="job:page:1",
            )
        )

    assert error.value.reason == "ocr_protocol_unsupported"

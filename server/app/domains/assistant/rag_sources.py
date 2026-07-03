from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import quote

from server.app.schemas import RagSource


def _chunk_metadata(chunk: dict[str, Any]) -> dict[str, Any]:
    metadata = chunk.get("metadata")
    if isinstance(metadata, dict):
        return metadata
    if isinstance(metadata, str) and metadata.strip():
        try:
            parsed = json.loads(metadata)
        except ValueError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _first_chunk_value(chunk: dict[str, Any], metadata: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = chunk.get(key)
        if value not in (None, "", []):
            return value
        value = metadata.get(key)
        if value not in (None, "", []):
            return value
    return None


def _path_file_name(path: str) -> str:
    return path.replace("\\", "/").rstrip("/").split("/")[-1] or path


def _clean_figure_caption(caption: Any) -> str | None:
    text = " ".join(str(caption or "").split())
    if not text:
        return None
    markers = (
        "； 前文",
        "；前文",
        "; 前文",
        ";前文",
        "，前文",
        ", 前文",
        "； 后文",
        "；后文",
        "; 后文",
        ";后文",
        "，后文",
        ", 后文",
        "视觉摘要",
    )
    cut = min((index for marker in markers if (index := text.find(marker)) > 0), default=-1)
    if cut > 0:
        text = text[:cut]
    text = re.sub(r"\s*(前文|后文|视觉摘要)\s*[:：].*$", "", text).strip()
    text = text.rstrip("；;，,。 ")
    if len(text) > 72:
        punctuation_cuts = [
            index
            for token in ("；", ";", "。", "，", ",")
            if (index := text.find(token, 18)) > 0
        ]
        if punctuation_cuts:
            text = text[: min(punctuation_cuts)].rstrip("；;，,。 ")
        if len(text) > 72:
            text = text[:69].rstrip() + "..."
    return text or None


def _asset_entries(paths: Any, *, kind: str, caption: str | None) -> list[dict[str, str | None]]:
    if not isinstance(paths, list):
        return []
    clean_caption = _clean_figure_caption(caption)
    entries: list[dict[str, str | None]] = []
    seen: set[str] = set()
    for item in paths:
        path = str(item or "").strip()
        if not path or path in seen:
            continue
        seen.add(path)
        entries.append(
            {
                "path": path,
                "file_name": _path_file_name(path),
                "kind": kind,
                "caption": clean_caption,
            }
        )
    return entries


def _asset_url(path: Any) -> str | None:
    if not path:
        return None
    return f"/api/teacher/rag-assets?path={quote(str(path), safe='')}"


def _asset_markdown(asset: dict[str, Any], caption: str | None = None) -> str | None:
    path = asset.get("path")
    url = _asset_url(path)
    if not url:
        return None
    alt = str(caption or asset.get("caption") or asset.get("file_name") or "RAG 图像证据").strip()
    alt = alt.replace("[", " ").replace("]", " ").replace("\n", " ").strip() or "RAG 图像证据"
    return f"![{alt}]({url})"


def _source_asset_markdown(asset: dict[str, Any], caption: str | None = None) -> str | None:
    path = asset.get("path")
    url = _asset_url(path)
    if not url:
        return None
    alt = str(
        _clean_figure_caption(caption)
        or _clean_figure_caption(asset.get("caption"))
        or asset.get("file_name")
        or "RAG image evidence"
    ).strip()
    alt = alt.replace("[", " ").replace("]", " ").replace("\n", " ").strip() or "RAG image evidence"
    return f"![{alt}]({url})"


def _source_evidence_payload(source: RagSource) -> dict[str, Any]:
    payload = source_to_dict(source)
    assets = payload.get("assets") or []
    if isinstance(assets, list):
        markdown_images = [
            markdown
            for asset in assets
            if isinstance(asset, dict)
            for markdown in [_source_asset_markdown(asset, payload.get("caption") or payload.get("text_preview"))]
            if markdown
        ]
        if markdown_images:
            payload["markdown_images"] = markdown_images[:3]
    return payload


def _is_page_image_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return "/page_images/" in normalized or bool(re.search(r"/page_\d+\.(png|jpg|jpeg|webp)$", normalized))


def _source_assets(
    chunk: dict[str, Any],
    metadata: dict[str, Any],
    caption: str | None,
    content_type: str | None,
) -> list[dict[str, str | None]]:
    raw_asset_paths = _first_chunk_value(chunk, metadata, "asset_paths")
    asset_paths = [str(item or "").strip() for item in raw_asset_paths] if isinstance(raw_asset_paths, list) else []
    has_figure = (
        content_type == "figure"
        or _first_chunk_value(chunk, metadata, "has_figure") is True
        or any(path and not _is_page_image_path(path) for path in asset_paths)
    )
    if not has_figure:
        return []

    figure_asset_paths = [path for path in asset_paths if path and not _is_page_image_path(path)] or asset_paths
    assets = _asset_entries(figure_asset_paths, kind="figure", caption=caption)
    page_assets = _asset_entries(
        _first_chunk_value(chunk, metadata, "source_page_images"),
        kind="page",
        caption=caption,
    )
    if assets:
        return [*assets[:3], *page_assets[:1]]
    return page_assets[:1]


def _source_from_chunk(chunk: dict[str, Any]) -> RagSource:
    metadata = _chunk_metadata(chunk)
    content_type = _first_chunk_value(chunk, metadata, "content_type")
    caption = _first_chunk_value(chunk, metadata, "caption", "title")
    display_caption = _clean_figure_caption(caption) or (str(caption) if caption else None)
    section_path = _first_chunk_value(chunk, metadata, "section_path") or []
    if not isinstance(section_path, list):
        section_path = []
    raw_text = chunk.get("text") or chunk.get("markdown") or caption or ""
    text = " ".join(str(raw_text).split())
    return RagSource(
        chunk_id=str(chunk.get("chunk_id") or chunk.get("id")),
        source_file=chunk.get("source_file") or _first_chunk_value(chunk, metadata, "source_file", "book_title"),
        page_number=chunk.get("page_number") or _first_chunk_value(chunk, metadata, "page_number", "page_start"),
        text_preview=text[:220],
        content_type=str(content_type) if content_type else None,
        caption=display_caption,
        section_path=[str(item) for item in section_path],
        assets=_source_assets(chunk, metadata, display_caption, str(content_type) if content_type else None),
    )


def source_to_dict(source: RagSource) -> dict[str, Any]:
    if hasattr(source, "model_dump"):
        return source.model_dump()
    return source.dict()

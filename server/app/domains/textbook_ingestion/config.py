from __future__ import annotations

import hashlib
import json
from typing import Any

from server.app.infrastructure.settings import Settings, get_settings


def _secret_fingerprint(secret: str) -> str | None:
    if not secret:
        return None
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:16]


def processing_config_snapshot(settings: Settings | None = None) -> dict[str, Any]:
    effective = settings or get_settings()
    return {
        "schema_version": 1,
        "extractor": {
            "name": "pymupdf",
            "native_min_chars": effective.textbook_native_min_chars,
            "native_min_printable_ratio": effective.textbook_native_min_printable_ratio,
            "max_pages": effective.max_textbook_pages,
        },
        "ocr": {
            "provider": "sysu_aigw_mineru",
            "enabled": effective.textbook_ocr_enabled,
            "base_url": effective.textbook_ocr_base_url,
            "model": effective.textbook_ocr_model,
            "credential_configured": bool(effective.textbook_ocr_api_key),
            "credential_fingerprint": _secret_fingerprint(effective.textbook_ocr_api_key),
            "timeout_seconds": effective.textbook_ocr_timeout_seconds,
            "concurrency": effective.textbook_ocr_concurrency,
            "max_retries": effective.textbook_ocr_max_retries,
            "render_dpi": effective.textbook_ocr_render_dpi,
        },
        "chunking": {
            "max_chars": effective.textbook_chunk_max_chars,
            "overlap_chars": effective.textbook_chunk_overlap_chars,
            "strategy": "structure-aware-v1",
        },
        "embedding": {
            "model": effective.textbook_rag_embedding_model,
            "dimension": effective.textbook_rag_embedding_dimension,
        },
        "index": {
            "name": effective.textbook_rag_elasticsearch_index,
            "schema": "canonical-rag-chunks-qwen-v2",
        },
    }


def processing_fingerprint(snapshot: dict[str, Any]) -> str:
    payload = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

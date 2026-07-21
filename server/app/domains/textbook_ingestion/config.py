from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Any

from server.app.infrastructure.settings import Settings, get_settings


def _load_effective_textbook_rag_settings() -> dict[str, Any]:
    # Keep the dependency one-way at import time: platform settings do not
    # depend on ingestion, and the worker can still import before app startup.
    from server.app.domains.platform.settings import effective_textbook_rag_settings

    return effective_textbook_rag_settings()


def effective_ingestion_settings(settings: Settings | None = None) -> Settings:
    """Use the same DB-backed RAG target as online retrieval.

    Explicit settings are already an effective, immutable test/CLI contract.
    Production callers omit the argument so teacher-console overrides and
    environment defaults are resolved through the platform settings service.
    """

    if settings is not None:
        return settings
    base = get_settings()
    rag = _load_effective_textbook_rag_settings()
    embedding = dict(rag.get("embedding") or {})
    rerank = dict(rag.get("rerank") or {})
    return replace(
        base,
        textbook_rag_enabled=bool(rag.get("enabled")),
        textbook_rag_elasticsearch_url=str(rag.get("elasticsearch_url") or ""),
        textbook_rag_elasticsearch_index=str(rag.get("index_name") or ""),
        textbook_rag_embedding_base_url=str(embedding.get("base_url") or ""),
        textbook_rag_embedding_api_key=str(embedding.get("api_key") or ""),
        textbook_rag_embedding_model=str(embedding.get("model") or ""),
        textbook_rag_embedding_dimension=int(rag.get("embedding_dimension") or 0),
        textbook_rag_rerank_base_url=str(rerank.get("base_url") or ""),
        textbook_rag_rerank_api_key=str(rerank.get("api_key") or ""),
        textbook_rag_rerank_model=str(rerank.get("model") or ""),
        textbook_rag_keyword_top_k=int(rag.get("keyword_top_k") or 1),
        textbook_rag_vector_top_k=int(rag.get("vector_top_k") or 1),
        textbook_rag_rerank_top_k=int(rag.get("rerank_top_k") or 1),
        textbook_rag_final_top_k=int(rag.get("final_top_k") or 1),
        textbook_rag_min_rerank_score=float(rag.get("min_rerank_score") or 0),
        textbook_rag_timeout_seconds=float(rag.get("timeout_seconds") or 8.0),
    )


def _secret_fingerprint(secret: str) -> str | None:
    if not secret:
        return None
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:16]


def processing_config_snapshot(settings: Settings | None = None) -> dict[str, Any]:
    effective = effective_ingestion_settings(settings)
    return {
        "schema_version": 1,
        "extractor": {
            "name": "pymupdf",
            "native_min_chars": effective.textbook_native_min_chars,
            "native_min_printable_ratio": effective.textbook_native_min_printable_ratio,
            "max_pages": effective.max_textbook_pages,
            "max_render_pixels": effective.textbook_max_render_pixels,
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
            "strategy": "structure-aware-v2",
        },
        "embedding": {
            "base_url": effective.textbook_rag_embedding_base_url,
            "model": effective.textbook_rag_embedding_model,
            "dimension": effective.textbook_rag_embedding_dimension,
            "credential_configured": bool(effective.textbook_rag_embedding_api_key),
            "credential_fingerprint": _secret_fingerprint(effective.textbook_rag_embedding_api_key),
            "batch_size": effective.textbook_embedding_batch_size,
        },
        "index": {
            "base_url": effective.textbook_rag_elasticsearch_url,
            "name": effective.textbook_rag_elasticsearch_index,
            "schema": "canonical-rag-chunks-qwen-v2",
            "batch_size": effective.textbook_index_batch_size,
        },
    }


def processing_fingerprint(snapshot: dict[str, Any]) -> str:
    payload = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ingestion_processing_readiness(settings: Settings | None = None) -> dict[str, Any]:
    """Return non-secret readiness details for accepting an online ingestion job."""

    effective = effective_ingestion_settings(settings)
    missing: list[str] = []
    if not effective.textbook_ingestion_enabled:
        missing.append("textbook_ingestion_disabled")
    if effective.data_backend != "postgres":
        missing.append("postgres_required")
    if not effective.textbook_rag_elasticsearch_url:
        missing.append("elasticsearch_url_missing")
    if not effective.textbook_rag_elasticsearch_index:
        missing.append("elasticsearch_index_missing")
    if not effective.textbook_rag_embedding_base_url:
        missing.append("embedding_base_url_missing")
    if not effective.textbook_rag_embedding_api_key:
        missing.append("embedding_credential_missing")
    if not effective.textbook_rag_embedding_model:
        missing.append("embedding_model_missing")
    if effective.textbook_rag_embedding_dimension <= 0:
        missing.append("embedding_dimension_invalid")
    return {
        "ready": not missing,
        "missing": missing,
        "elasticsearch": {
            "configured": bool(
                effective.textbook_rag_elasticsearch_url
                and effective.textbook_rag_elasticsearch_index
            ),
            "index": effective.textbook_rag_elasticsearch_index,
        },
        "embedding": {
            "configured": bool(
                effective.textbook_rag_embedding_base_url
                and effective.textbook_rag_embedding_api_key
                and effective.textbook_rag_embedding_model
                and effective.textbook_rag_embedding_dimension > 0
            ),
            "model": effective.textbook_rag_embedding_model,
            "dimension": effective.textbook_rag_embedding_dimension,
        },
    }

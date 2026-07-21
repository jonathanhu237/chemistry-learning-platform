from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Any

from server.app.domains.textbook_ingestion.mineru import (
    MinerUProviderError,
    validate_mineru_protocol,
)
from server.app.domains.textbook_rag.clients import (
    TextbookRAGClientError,
    embedding_profile_fingerprint,
    endpoint_configured,
    validate_embedding_protocol,
)
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
    ocr = dict(rag.get("ocr") or {})
    embedding = dict(rag.get("embedding") or {})
    rerank = dict(rag.get("rerank") or {})
    return replace(
        base,
        textbook_ocr_enabled=bool(ocr.get("enabled")),
        textbook_ocr_provider=str(ocr.get("provider") or base.textbook_ocr_provider),
        textbook_ocr_protocol=str(ocr.get("protocol") or base.textbook_ocr_protocol),
        textbook_ocr_base_url=str(ocr.get("base_url") or ""),
        textbook_ocr_endpoint=str(ocr.get("endpoint") or ""),
        textbook_ocr_api_key=str(ocr.get("api_key") or ""),
        textbook_ocr_model=str(ocr.get("model") or ""),
        textbook_ocr_timeout_seconds=float(
            ocr.get("timeout_seconds") or base.textbook_ocr_timeout_seconds
        ),
        textbook_ocr_concurrency=int(ocr.get("concurrency") or base.textbook_ocr_concurrency),
        textbook_ocr_max_retries=int(
            ocr.get("max_retries")
            if ocr.get("max_retries") is not None
            else base.textbook_ocr_max_retries
        ),
        textbook_ocr_max_output_tokens=int(
            ocr.get("max_output_tokens") or base.textbook_ocr_max_output_tokens
        ),
        textbook_ocr_render_dpi=int(ocr.get("render_dpi") or base.textbook_ocr_render_dpi),
        textbook_rag_enabled=bool(rag.get("enabled")),
        textbook_rag_elasticsearch_url=str(rag.get("elasticsearch_url") or ""),
        textbook_rag_elasticsearch_index=str(rag.get("index_name") or ""),
        textbook_rag_embedding_provider=str(
            embedding.get("provider") or base.textbook_rag_embedding_provider
        ),
        textbook_rag_embedding_protocol=str(
            embedding.get("protocol") or base.textbook_rag_embedding_protocol
        ),
        textbook_rag_embedding_base_url=str(embedding.get("base_url") or ""),
        textbook_rag_embedding_endpoint=str(embedding.get("endpoint") or ""),
        textbook_rag_embedding_api_key=str(embedding.get("api_key") or ""),
        textbook_rag_embedding_model=str(embedding.get("model") or ""),
        textbook_rag_embedding_dimension=int(rag.get("embedding_dimension") or 0),
        textbook_rag_embedding_send_dimensions=bool(embedding.get("send_dimensions", True)),
        textbook_embedding_batch_size=int(
            embedding.get("batch_size") or base.textbook_embedding_batch_size
        ),
        textbook_rag_rerank_provider=str(
            rerank.get("provider") or base.textbook_rag_rerank_provider
        ),
        textbook_rag_rerank_protocol=str(
            rerank.get("protocol") or base.textbook_rag_rerank_protocol
        ),
        textbook_rag_rerank_base_url=str(rerank.get("base_url") or ""),
        textbook_rag_rerank_endpoint=str(rerank.get("endpoint") or ""),
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
        "schema_version": 4,
        "extractor": {
            "name": "pymupdf",
            "native_min_chars": effective.textbook_native_min_chars,
            "native_min_printable_ratio": effective.textbook_native_min_printable_ratio,
            "max_pages": effective.max_textbook_pages,
            "max_render_pixels": effective.textbook_max_render_pixels,
        },
        "ocr": {
            "provider": effective.textbook_ocr_provider,
            "protocol": effective.textbook_ocr_protocol,
            "enabled": effective.textbook_ocr_enabled,
            "base_url": effective.textbook_ocr_base_url,
            "endpoint": effective.textbook_ocr_endpoint,
            "model": effective.textbook_ocr_model,
            "credential_configured": bool(effective.textbook_ocr_api_key),
            "credential_fingerprint": _secret_fingerprint(effective.textbook_ocr_api_key),
            "timeout_seconds": effective.textbook_ocr_timeout_seconds,
            "concurrency": effective.textbook_ocr_concurrency,
            "max_retries": effective.textbook_ocr_max_retries,
            "max_output_tokens": effective.textbook_ocr_max_output_tokens,
            "render_dpi": effective.textbook_ocr_render_dpi,
        },
        "chunking": {
            "max_chars": effective.textbook_chunk_max_chars,
            "overlap_chars": effective.textbook_chunk_overlap_chars,
            "strategy": "structure-aware-v2",
        },
        "embedding": {
            "provider": effective.textbook_rag_embedding_provider,
            "protocol": effective.textbook_rag_embedding_protocol,
            "base_url": effective.textbook_rag_embedding_base_url,
            "endpoint": effective.textbook_rag_embedding_endpoint,
            "model": effective.textbook_rag_embedding_model,
            "dimension": effective.textbook_rag_embedding_dimension,
            "send_dimensions": effective.textbook_rag_embedding_send_dimensions,
            "profile_fingerprint": embedding_profile_fingerprint(
                provider=effective.textbook_rag_embedding_provider,
                protocol=effective.textbook_rag_embedding_protocol,
                base_url=effective.textbook_rag_embedding_base_url,
                endpoint=effective.textbook_rag_embedding_endpoint,
                model=effective.textbook_rag_embedding_model,
                dimensions=effective.textbook_rag_embedding_dimension,
                send_dimensions=effective.textbook_rag_embedding_send_dimensions,
            ),
            "credential_configured": bool(effective.textbook_rag_embedding_api_key),
            "credential_fingerprint": _secret_fingerprint(effective.textbook_rag_embedding_api_key),
            "batch_size": effective.textbook_embedding_batch_size,
            "timeout_seconds": effective.textbook_rag_timeout_seconds,
        },
        "index": {
            "base_url": effective.textbook_rag_elasticsearch_url,
            "name": effective.textbook_rag_elasticsearch_index,
            "schema": "textbook-rag-chunks-v2",
            "batch_size": effective.textbook_index_batch_size,
            "timeout_seconds": effective.textbook_rag_timeout_seconds,
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
    if not endpoint_configured(
        effective.textbook_rag_embedding_base_url,
        effective.textbook_rag_embedding_endpoint,
    ):
        missing.append("embedding_base_url_missing")
    if not effective.textbook_rag_embedding_api_key:
        missing.append("embedding_credential_missing")
    if not effective.textbook_rag_embedding_model:
        missing.append("embedding_model_missing")
    if effective.textbook_rag_embedding_dimension <= 0:
        missing.append("embedding_dimension_invalid")
    try:
        validate_embedding_protocol(effective.textbook_rag_embedding_protocol)
    except TextbookRAGClientError:
        missing.append("embedding_protocol_unsupported")
    if effective.textbook_ocr_enabled:
        if (
            (effective.textbook_ocr_base_url or effective.textbook_ocr_endpoint)
            and not endpoint_configured(
                effective.textbook_ocr_base_url,
                effective.textbook_ocr_endpoint,
            )
        ):
            missing.append("ocr_endpoint_invalid")
        try:
            validate_mineru_protocol(effective.textbook_ocr_protocol)
        except MinerUProviderError:
            missing.append("ocr_protocol_unsupported")
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
                endpoint_configured(
                    effective.textbook_rag_embedding_base_url,
                    effective.textbook_rag_embedding_endpoint,
                )
                and effective.textbook_rag_embedding_api_key
                and effective.textbook_rag_embedding_model
                and effective.textbook_rag_embedding_dimension > 0
            ),
            "model": effective.textbook_rag_embedding_model,
            "dimension": effective.textbook_rag_embedding_dimension,
        },
    }

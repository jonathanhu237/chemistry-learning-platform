from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from server.app.domains.textbook_rag.active_corpus import settings_with_active_textbook_corpus
from server.app.domains.textbook_rag.retrieval import retrieve_textbook_evidence


TEXTBOOK_EVIDENCE_CACHE_SCHEMA_VERSION = 2


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _sanitized_config(settings: dict[str, Any]) -> dict[str, Any]:
    embedding = settings.get("embedding") if isinstance(settings.get("embedding"), dict) else {}
    rerank = settings.get("rerank") if isinstance(settings.get("rerank"), dict) else {}
    corpus = settings.get("_active_textbook_corpus")
    corpus_documents = sorted(
        (
            str(getattr(document, "index_document_id", "") or ""),
            int(getattr(document, "document_version", 0) or 0),
            str(getattr(document, "projection_run_id", "") or ""),
        )
        for document in (getattr(corpus, "documents", ()) or ())
    )
    return {
        "schema_version": TEXTBOOK_EVIDENCE_CACHE_SCHEMA_VERSION,
        "index_name": str(settings.get("index_name") or ""),
        "embedding": {
            "base_url": str(embedding.get("base_url") or ""),
            "model": str(embedding.get("model") or ""),
        },
        "rerank": {
            "base_url": str(rerank.get("base_url") or ""),
            "model": str(rerank.get("model") or ""),
        },
        "embedding_dimension": int(settings.get("embedding_dimension") or 0),
        "keyword_top_k": int(settings.get("keyword_top_k") or 0),
        "vector_top_k": int(settings.get("vector_top_k") or 0),
        "rerank_top_k": int(settings.get("rerank_top_k") or 0),
        "final_top_k": int(settings.get("final_top_k") or 0),
        "min_rerank_score": float(settings.get("min_rerank_score") or 0.0),
        "corpus_revision": max(0, int(settings.get("corpus_revision") or 0)),
        "active_corpus_documents": corpus_documents,
    }


def textbook_evidence_cache_fingerprints(
    *,
    point_context: dict[str, Any],
    settings: dict[str, Any],
    point_node_id: str,
    canonical_point_id: str | None = None,
) -> dict[str, str]:
    content_fingerprint = _sha256(
        {
            "schema_version": TEXTBOOK_EVIDENCE_CACHE_SCHEMA_VERSION,
            "point_node_id": point_node_id,
            "canonical_point_id": canonical_point_id or "",
            "point_context": point_context,
        }
    )
    config_fingerprint = _sha256(_sanitized_config(settings))
    return {
        "cache_key": f"textbook-rag-v{TEXTBOOK_EVIDENCE_CACHE_SCHEMA_VERSION}:{content_fingerprint}:{config_fingerprint}",
        "content_fingerprint": content_fingerprint,
        "config_fingerprint": config_fingerprint,
    }


def _coerce_package(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        parsed = json.loads(value)
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}


def _cache_metadata(
    *,
    cache_key: str,
    hit: bool,
    stored: bool = False,
    created_at: Any = None,
    updated_at: Any = None,
    cleared: bool = False,
) -> dict[str, Any]:
    return {
        "enabled": True,
        "hit": hit,
        "stored": stored,
        "cleared": cleared,
        "cache_key": cache_key,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def _with_cache_metadata(package: dict[str, Any], cache: dict[str, Any]) -> dict[str, Any]:
    diagnostics = package.get("diagnostics") if isinstance(package.get("diagnostics"), dict) else {}
    return {
        **package,
        "cache": cache,
        "diagnostics": {**diagnostics, "cache": cache},
    }


def load_cached_textbook_evidence(session: Any, *, cache_key: str) -> dict[str, Any] | None:
    try:
        row = (
            session.execute(
                text(
                    """
                    SELECT package, created_at, updated_at
                    FROM textbook_rag_evidence_cache
                    WHERE cache_key = :cache_key
                    LIMIT 1
                    """
                ),
                {"cache_key": cache_key},
            )
            .mappings()
            .first()
        )
    except (SQLAlchemyError, json.JSONDecodeError):
        return None
    if not row:
        return None
    package = _coerce_package(row.get("package"))
    if not package:
        return None
    return _with_cache_metadata(
        package,
        _cache_metadata(
            cache_key=cache_key,
            hit=True,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        ),
    )


def store_textbook_evidence_cache(
    session: Any,
    *,
    cache_key: str,
    point_node_id: str,
    canonical_point_id: str | None,
    content_fingerprint: str,
    config_fingerprint: str,
    package: dict[str, Any],
) -> bool:
    source_count = int(package.get("source_count") or len(package.get("source_refs") or []) or 0)
    if not package.get("ok") or source_count <= 0:
        return False
    package_to_store = {key: value for key, value in package.items() if key != "cache"}
    diagnostics = package_to_store.get("diagnostics") if isinstance(package_to_store.get("diagnostics"), dict) else {}
    try:
        session.execute(
            text(
                """
                INSERT INTO textbook_rag_evidence_cache (
                  cache_key, point_node_id, canonical_point_id, content_fingerprint,
                  config_fingerprint, package, diagnostics, source_count, updated_at
                )
                VALUES (
                  :cache_key, :point_node_id, :canonical_point_id, :content_fingerprint,
                  :config_fingerprint, CAST(:package AS jsonb), CAST(:diagnostics AS jsonb),
                  :source_count, now()
                )
                ON CONFLICT (cache_key) DO UPDATE SET
                  package = EXCLUDED.package,
                  diagnostics = EXCLUDED.diagnostics,
                  source_count = EXCLUDED.source_count,
                  updated_at = now()
                """
            ),
            {
                "cache_key": cache_key,
                "point_node_id": point_node_id,
                "canonical_point_id": canonical_point_id or None,
                "content_fingerprint": content_fingerprint,
                "config_fingerprint": config_fingerprint,
                "package": _json(package_to_store),
                "diagnostics": _json(diagnostics),
                "source_count": source_count,
            },
        )
    except SQLAlchemyError:
        return False
    return True


def retrieve_textbook_evidence_cached(
    session: Any,
    *,
    point_context: dict[str, Any],
    settings: dict[str, Any],
    point_node_id: str,
    canonical_point_id: str | None = None,
    retrieve_fn: Callable[..., dict[str, Any]] = retrieve_textbook_evidence,
) -> dict[str, Any]:
    retrieval_settings = settings_with_active_textbook_corpus(settings, session=session)
    fingerprints = textbook_evidence_cache_fingerprints(
        point_context=point_context,
        settings=retrieval_settings,
        point_node_id=point_node_id,
        canonical_point_id=canonical_point_id,
    )
    cached = load_cached_textbook_evidence(session, cache_key=fingerprints["cache_key"])
    if cached:
        return cached
    package = retrieve_fn(point_context=point_context, settings=retrieval_settings)
    stored = store_textbook_evidence_cache(
        session,
        cache_key=fingerprints["cache_key"],
        point_node_id=point_node_id,
        canonical_point_id=canonical_point_id,
        content_fingerprint=fingerprints["content_fingerprint"],
        config_fingerprint=fingerprints["config_fingerprint"],
        package=package,
    )
    return _with_cache_metadata(
        package,
        _cache_metadata(
            cache_key=fingerprints["cache_key"],
            hit=False,
            stored=stored,
            updated_at=datetime.now(timezone.utc).isoformat() if stored else None,
        ),
    )


def clear_textbook_evidence_cache(
    session: Any,
    *,
    point_node_ids: list[str],
    canonical_point_ids: list[str] | None = None,
) -> int:
    point_node_ids = [item for item in dict.fromkeys(point_node_ids).keys() if item]
    canonical_point_ids = [item for item in dict.fromkeys(canonical_point_ids or []).keys() if item]
    if not point_node_ids and not canonical_point_ids:
        return 0
    try:
        deleted = session.execute(
            text(
                """
                DELETE FROM textbook_rag_evidence_cache
                WHERE point_node_id = ANY(CAST(:point_node_ids AS text[]))
                   OR canonical_point_id = ANY(CAST(:canonical_point_ids AS text[]))
                """
            ),
            {
                "point_node_ids": point_node_ids,
                "canonical_point_ids": canonical_point_ids,
            },
        )
    except SQLAlchemyError:
        return 0
    return int(deleted.rowcount or 0)


def cleared_cache_metadata() -> dict[str, Any]:
    return {
        "enabled": True,
        "hit": False,
        "stored": False,
        "cleared": True,
        "cleared_at": datetime.now(timezone.utc).isoformat(),
    }

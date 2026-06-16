from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from sqlalchemy import text

from server.app.config import Settings
from server.app.database import db_session
from server.app.repositories import RepositoryProvider
from server.app.schemas import AgentAskRequest


@dataclass
class HybridRetrieveResult:
    chunks: list[dict[str, Any]]
    trace: dict[str, Any]


LegacyRetrieve = Callable[[str, int], list[dict[str, Any]]]
QueryGenerator = Callable[[str], tuple[list[str], dict[str, Any]]]


def retrieve_hybrid_context(
    *,
    repositories: RepositoryProvider,
    question: str,
    request: AgentAskRequest,
    settings: Settings,
    legacy_retrieve: LegacyRetrieve,
    query_generator: QueryGenerator,
    limit: int,
) -> HybridRetrieveResult:
    trace_started_at = time.perf_counter()
    trace: dict[str, Any] = {
        "mode": "legacy",
        "hybrid_enabled": bool(settings.rag_hybrid_bge_enabled),
        "generated_queries": [],
        "query_generation": {},
        "fallbacks": [],
        "keyword_candidates": [],
        "vector_candidates": [],
        "rerank_scores": [],
        "final_evidence": [],
        "timings_ms": {},
        "candidate_counts": {},
        "rerank_applied": False,
        "final_sort": "legacy_score",
    }

    keyword_limit = max(limit, settings.rag_keyword_top_k)
    keyword_started_at = time.perf_counter()
    legacy_chunks = legacy_retrieve(question, keyword_limit)
    trace["timings_ms"]["legacy_keyword_ms"] = _elapsed_ms(keyword_started_at)
    keyword_candidates = _prepare_candidates(legacy_chunks, "keyword", question)
    trace["keyword_candidates"] = _candidate_trace(keyword_candidates)

    if not settings.rag_hybrid_bge_enabled:
        final_chunks = [item["chunk"] for item in keyword_candidates[:limit]]
        trace["final_evidence"] = _candidate_trace(keyword_candidates[:limit])
        _finalize_trace(
            trace,
            trace_started_at,
            keyword=len(keyword_candidates),
            keyword_total=len(keyword_candidates),
            vector=0,
            merged=len(keyword_candidates),
            rerank_pool=0,
            final=len(final_chunks),
        )
        return HybridRetrieveResult(chunks=final_chunks, trace=trace)

    if not settings.rag_bge_service_url:
        trace["fallbacks"].append({"stage": "bge_service", "reason": "service_url_not_configured"})
        final_chunks = [item["chunk"] for item in keyword_candidates[:limit]]
        trace["final_evidence"] = _candidate_trace(keyword_candidates[:limit])
        _finalize_trace(
            trace,
            trace_started_at,
            keyword=len(keyword_candidates),
            keyword_total=len(keyword_candidates),
            vector=0,
            merged=len(keyword_candidates),
            rerank_pool=0,
            final=len(final_chunks),
        )
        return HybridRetrieveResult(chunks=final_chunks, trace=trace)

    query_started_at = time.perf_counter()
    queries, query_trace = query_generator(question)
    trace["timings_ms"]["query_generation_ms"] = _elapsed_ms(query_started_at)
    normalized_queries = _unique_nonempty([*queries, question])[:4]
    trace["query_generation"] = query_trace
    trace["generated_queries"] = normalized_queries
    if not normalized_queries:
        normalized_queries = [question]
        trace["fallbacks"].append({"stage": "query_generation", "reason": "empty_query_list"})

    all_keyword_candidates = list(keyword_candidates)
    generated_keyword_started_at = time.perf_counter()
    for generated_query in normalized_queries:
        if generated_query == question:
            continue
        all_keyword_candidates.extend(
            _prepare_candidates(legacy_retrieve(generated_query, keyword_limit), "keyword_generated", generated_query)
        )
    trace["timings_ms"]["generated_keyword_ms"] = _elapsed_ms(generated_keyword_started_at)

    vector_candidates: list[dict[str, Any]] = []
    bge_failures: list[dict[str, str]] = []
    vector_steps: list[dict[str, Any]] = []
    embed_ms_total = 0.0
    vector_recall_ms_total = 0.0
    for generated_query in normalized_queries:
        vector_step: dict[str, Any] = {"query": generated_query}
        try:
            embed_started_at = time.perf_counter()
            embedding = _embed_query(settings, generated_query)
            vector_step["embed_ms"] = _elapsed_ms(embed_started_at)
            embed_ms_total += float(vector_step["embed_ms"])
            recall_started_at = time.perf_counter()
            recalled_chunks = _vector_recall(embedding, settings.rag_vector_top_k)
            vector_step["recall_ms"] = _elapsed_ms(recall_started_at)
            vector_step["candidate_count"] = len(recalled_chunks)
            vector_recall_ms_total += float(vector_step["recall_ms"])
            vector_candidates.extend(
                _prepare_candidates(
                    recalled_chunks,
                    "vector",
                    generated_query,
                )
            )
        except Exception as exc:
            vector_step["error"] = f"{exc.__class__.__name__}: {str(exc)[:160]}"
            bge_failures.append({"stage": "vector_recall", "reason": f"{exc.__class__.__name__}: {str(exc)[:160]}"})
            break
        finally:
            vector_steps.append(vector_step)
    trace["vector_steps"] = vector_steps
    trace["timings_ms"]["bge_embed_ms_total"] = round(embed_ms_total, 2)
    trace["timings_ms"]["vector_recall_ms_total"] = round(vector_recall_ms_total, 2)
    trace["fallbacks"].extend(bge_failures)
    trace["vector_candidates"] = _candidate_trace(vector_candidates)

    merge_started_at = time.perf_counter()
    merged = _merge_candidates([*all_keyword_candidates, *vector_candidates])
    trace["timings_ms"]["merge_ms"] = _elapsed_ms(merge_started_at)
    if not merged:
        trace["fallbacks"].append({"stage": "merge", "reason": "no_candidates"})
        _finalize_trace(
            trace,
            trace_started_at,
            keyword=len(keyword_candidates),
            keyword_total=len(all_keyword_candidates),
            vector=len(vector_candidates),
            merged=0,
            rerank_pool=0,
            final=0,
        )
        return HybridRetrieveResult(chunks=[], trace=trace)

    reranked = merged
    rerank_pool_size = 0
    if vector_candidates:
        rerank_pool = merged[: max(limit, settings.rag_rerank_top_k)]
        rerank_pool_size = len(rerank_pool)
        try:
            rerank_started_at = time.perf_counter()
            rerank_scores = _rerank(settings, question, [_chunk_text(item["chunk"]) for item in rerank_pool])
            trace["timings_ms"]["bge_rerank_ms"] = _elapsed_ms(rerank_started_at)
            for item, score in zip(rerank_pool, rerank_scores, strict=False):
                item["rerank_score"] = float(score)
                item["score"] = max(float(item.get("score") or 0.0), float(score))
            reranked = sorted(merged, key=lambda item: float(item.get("score") or 0.0), reverse=True)
            trace["mode"] = "hybrid_bge_rerank"
            trace["rerank_applied"] = True
            trace["final_sort"] = "bge_reranker_score"
            trace["rerank_scores"] = _candidate_trace(rerank_pool)
        except Exception as exc:
            trace["timings_ms"]["bge_rerank_ms"] = _elapsed_ms(rerank_started_at) if "rerank_started_at" in locals() else 0
            trace["mode"] = "hybrid_bge_vector"
            trace["final_sort"] = "merged_score_after_rerank_fallback"
            trace["fallbacks"].append({"stage": "rerank", "reason": f"{exc.__class__.__name__}: {str(exc)[:160]}"})
            reranked = sorted(merged, key=lambda item: float(item.get("score") or 0.0), reverse=True)
    else:
        trace["mode"] = "legacy_with_query_generation"
        trace["final_sort"] = "keyword_score"
        reranked = sorted(merged, key=lambda item: float(item.get("score") or 0.0), reverse=True)

    final_candidates = reranked[: max(1, limit)]
    trace["final_evidence"] = _candidate_trace(final_candidates)
    _finalize_trace(
        trace,
        trace_started_at,
        keyword=len(keyword_candidates),
        keyword_total=len(all_keyword_candidates),
        vector=len(vector_candidates),
        merged=len(merged),
        rerank_pool=rerank_pool_size,
        final=len(final_candidates),
    )
    return HybridRetrieveResult(chunks=[item["chunk"] for item in final_candidates], trace=trace)


def _prepare_candidates(chunks: list[dict[str, Any]], source: str, query: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for chunk in chunks:
        raw_score = chunk.get("_score") or chunk.get("vector_score") or chunk.get("score") or 0.0
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 0.0
        candidates.append(
            {
                "chunk_id": str(chunk.get("chunk_id") or chunk.get("id") or ""),
                "source": source,
                "query": query,
                "score": score,
                "chunk": chunk,
            }
        )
    return candidates


def _merge_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in candidates:
        chunk_id = item.get("chunk_id")
        if not chunk_id:
            continue
        existing = merged.get(chunk_id)
        if existing is None or float(item.get("score") or 0.0) > float(existing.get("score") or 0.0):
            merged[chunk_id] = item
    return sorted(merged.values(), key=lambda item: float(item.get("score") or 0.0), reverse=True)


def _candidate_trace(candidates: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, item in enumerate(candidates[:limit], start=1):
        chunk = item.get("chunk") or {}
        output.append(
            {
                "rank": index,
                "chunk_id": item.get("chunk_id") or chunk.get("chunk_id") or chunk.get("id"),
                "source": item.get("source"),
                "query": item.get("query"),
                "score": _round_float(item.get("score")),
                "rerank_score": _round_float(item.get("rerank_score")),
                "source_file": chunk.get("source_file"),
                "page_number": chunk.get("page_number"),
                "text_preview": _chunk_text(chunk)[:180],
            }
        )
    return output


def _round_float(value: Any) -> float | None:
    try:
        return round(float(value), 5)
    except (TypeError, ValueError):
        return None


def _elapsed_ms(started_at: float) -> float:
    return round((time.perf_counter() - started_at) * 1000, 2)


def _finalize_trace(
    trace: dict[str, Any],
    started_at: float,
    *,
    keyword: int,
    keyword_total: int,
    vector: int,
    merged: int,
    rerank_pool: int,
    final: int,
) -> None:
    trace["candidate_counts"] = {
        "keyword": keyword,
        "keyword_total": keyword_total,
        "vector": vector,
        "merged": merged,
        "rerank_pool": rerank_pool,
        "final": final,
    }
    trace["timings_ms"]["total_ms"] = _elapsed_ms(started_at)


def _embed_query(settings: Settings, query: str) -> list[float]:
    payload = _post_json(settings, "/embed", {"texts": [query]})
    embeddings = payload.get("embeddings") if isinstance(payload, dict) else None
    if not embeddings or not isinstance(embeddings, list):
        raise RuntimeError("BGE embed response missing embeddings")
    first = embeddings[0]
    if not isinstance(first, list) or not first:
        raise RuntimeError("BGE embed response has empty embedding")
    return [float(value) for value in first]


def _rerank(settings: Settings, query: str, documents: list[str]) -> list[float]:
    if not documents:
        return []
    payload = _post_json(settings, "/rerank", {"query": query, "documents": documents})
    scores = payload.get("scores") if isinstance(payload, dict) else None
    if not isinstance(scores, list):
        raise RuntimeError("BGE rerank response missing scores")
    return [float(score) for score in scores]


def _post_json(settings: Settings, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{settings.rag_bge_service_url.rstrip('/')}{path}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=max(1.0, settings.rag_bge_timeout_seconds)) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc)) from exc


def _vector_recall(embedding: list[float], limit: int) -> list[dict[str, Any]]:
    if not embedding:
        return []
    vector_literal = "[" + ",".join(f"{float(value):.8f}" for value in embedding) + "]"
    with db_session() as session:
        rows = session.execute(
            text(
                """
                SELECT sc.id AS chunk_id, sc.id, sc.document_id, sd.file_name AS source_file,
                       sc.chapter_id, sc.page_number, sc.section_title, sc.chunk_index, sc.text,
                       sc.markdown, sc.related_knowledge_point_ids, sc.related_experiment_ids,
                       sc.tags, sc.metadata, sc.review_required, sc.content_status,
                       1 - (ce.embedding <=> CAST(:embedding AS vector)) AS vector_score
                FROM chunk_embeddings ce
                JOIN source_chunks sc ON sc.id = ce.chunk_id
                LEFT JOIN source_documents sd ON sd.id = sc.document_id
                WHERE ce.embedding IS NOT NULL
                  AND COALESCE(sc.content_status, 'pending_review') = 'published'
                ORDER BY ce.embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
                """
            ),
            {"embedding": vector_literal, "limit": max(1, limit)},
        ).mappings().all()
    return [dict(row) for row in rows]


def _chunk_text(chunk: dict[str, Any]) -> str:
    return " ".join(str(chunk.get("text") or chunk.get("markdown") or "").split())


def _unique_nonempty(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text_value = " ".join(str(value or "").split())
        if text_value and text_value not in seen:
            seen.add(text_value)
            result.append(text_value)
    return result

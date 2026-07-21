from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from server.app.domains.platform.settings import effective_textbook_rag_settings
from server.app.domains.textbook_rag.active_corpus import active_textbook_filter, corpus_from_settings
from server.app.domains.textbook_rag.clients import QwenEmbeddingClient, QwenRerankClient, TextbookRAGClientError
from server.app.domains.textbook_rag.index import TextbookElasticsearchClient


SECTION_LABELS = {
    "principle": "实验原理",
    "phenomenon": "现象解释",
    "safety": "安全提示",
}


@dataclass(frozen=True)
class PointEvidenceQuery:
    section: str
    query: str


def chemical_tokens(text: str) -> list[str]:
    return sorted(set(re.findall(r"[A-Z][a-z]?[A-Za-z0-9₀-₉()·.+\\-]*", text or "")))


def build_section_queries(point_context: dict[str, Any]) -> list[PointEvidenceQuery]:
    title = str(point_context.get("point_title") or point_context.get("title") or "").strip()
    experiment_title = str(point_context.get("experiment_title") or "").strip()
    chapter = str(point_context.get("chapter") or point_context.get("textbook_chapter") or "").strip()
    folder_path = str(point_context.get("folder_path") or point_context.get("textbook_folder_path") or "").strip()
    content = point_context.get("content") if isinstance(point_context.get("content"), dict) else point_context
    values = {
        "principle": str(content.get("principle_text") or content.get("principle") or "").strip(),
        "phenomenon": str(content.get("phenomenon_explanation") or content.get("phenomenon") or "").strip(),
        "safety": str(content.get("safety_note") or content.get("safety") or "").strip(),
    }
    queries: list[PointEvidenceQuery] = []
    for section, value in values.items():
        if not value:
            continue
        query = "\n".join(
            part
            for part in [
                f"点位：{title}" if title else "",
                f"实验：{experiment_title}" if experiment_title else "",
                f"章节：{chapter}" if chapter else "",
                f"路径：{folder_path}" if folder_path else "",
                f"{SECTION_LABELS[section]}：{value}",
            ]
            if part
        )
        queries.append(PointEvidenceQuery(section=section, query=query))
    return queries


def _es_search(es: TextbookElasticsearchClient, payload: dict[str, Any]) -> list[dict[str, Any]]:
    response = es.request("POST", f"/{es.index}/_search", payload)
    hits = response.get("hits", {}).get("hits", []) if isinstance(response, dict) else []
    return [hit for hit in hits if isinstance(hit, dict)]


def _lexical_payload(
    query: str,
    *,
    size: int,
    point_context: dict[str, Any],
    active_filter: dict[str, Any],
) -> dict[str, Any]:
    tokens = chemical_tokens(query)
    should: list[dict[str, Any]] = [
        {
            "multi_match": {
                "query": query,
                "fields": [
                    "text^4",
                    "raw_markdown^2",
                    "section_path^2",
                    "book_title",
                    "content_type^2",
                ],
                "type": "best_fields",
            }
        }
    ]
    if tokens:
        should.extend(
            [
                {"terms": {"formulas": tokens, "boost": 3.0}},
                {"terms": {"compounds": [token.upper() for token in tokens], "boost": 2.5}},
                {"terms": {"elements": tokens, "boost": 1.5}},
            ]
        )
    chapter = str(point_context.get("chapter") or point_context.get("textbook_chapter") or "").strip()
    experiment_title = str(point_context.get("experiment_title") or "").strip()
    if chapter:
        should.append({"match": {"section_path": {"query": chapter, "boost": 1.5}}})
    if experiment_title:
        should.append({"match": {"section_path": {"query": experiment_title, "boost": 1.5}}})
    return {
        "size": size,
        "_source": {"excludes": ["embedding"]},
        "query": {
            "bool": {
                "must": [{"term": {"use_for_question_generation": True}}],
                "filter": [active_filter],
                "should": should,
                "minimum_should_match": 1,
            }
        },
    }


def _vector_payload(
    query_vector: list[float],
    *,
    size: int,
    active_filter: dict[str, Any],
) -> dict[str, Any]:
    return {
        "size": size,
        "_source": {"excludes": ["embedding"]},
        "query": {
            "script_score": {
                "query": {
                    "bool": {
                        "must": [{"term": {"use_for_question_generation": True}}],
                        "filter": [active_filter],
                    }
                },
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_vector},
                },
            }
        },
    }


def _source_from_hit(hit: dict[str, Any], *, recall_source: str) -> dict[str, Any]:
    source = hit.get("_source") if isinstance(hit.get("_source"), dict) else {}
    return {
        "chunk_id": str(source.get("chunk_id") or hit.get("_id") or ""),
        "text": str(source.get("text") or ""),
        "book_title": str(source.get("book_title") or ""),
        "chapter": str(source.get("chapter") or ""),
        "section_path": source.get("section_path") or [],
        "content_type": str(source.get("content_type") or ""),
        "page_start": source.get("page_start"),
        "page_end": source.get("page_end"),
        "content_hash": str(source.get("content_hash") or ""),
        "document_id": str(source.get("document_id") or ""),
        "logical_textbook_key": str(source.get("logical_textbook_key") or source.get("source_collection") or ""),
        "document_version": source.get("document_version"),
        "source_collection": str(source.get("source_collection") or ""),
        "source_file": str(source.get("source_file") or ""),
        "recall_source": recall_source,
        "recall_score": float(hit.get("_score") or 0.0),
        "rerank_score": None,
        "metadata": source.get("metadata") if isinstance(source.get("metadata"), dict) else {},
    }


def _merge_candidates(*candidate_lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for candidates in candidate_lists:
        for candidate in candidates:
            chunk_id = candidate["chunk_id"]
            if chunk_id not in merged or float(candidate.get("recall_score") or 0.0) > float(
                merged[chunk_id].get("recall_score") or 0.0
            ):
                merged[chunk_id] = candidate
            elif candidate.get("recall_source") not in str(merged[chunk_id].get("recall_source")):
                merged[chunk_id]["recall_source"] = f"{merged[chunk_id]['recall_source']}+{candidate['recall_source']}"
    return list(merged.values())


def _rank_score(source: dict[str, Any]) -> float:
    return float(source.get("rerank_score") if source.get("rerank_score") is not None else source.get("recall_score") or 0.0)


def _candidate_summary(source: dict[str, Any], *, section: str, rank: int) -> dict[str, Any]:
    section_path = source.get("section_path") if isinstance(source.get("section_path"), list) else []
    text_preview = " ".join(str(source.get("text") or "").split())[:260]
    return {
        "chunk_id": source.get("chunk_id"),
        "section": section,
        "rank": rank,
        "book_title": source.get("book_title"),
        "chapter": source.get("chapter"),
        "section_path": section_path,
        "content_type": source.get("content_type"),
        "page_start": source.get("page_start"),
        "page_end": source.get("page_end"),
        "content_hash": source.get("content_hash"),
        "document_id": source.get("document_id"),
        "logical_textbook_key": source.get("logical_textbook_key"),
        "document_version": source.get("document_version"),
        "source_collection": source.get("source_collection"),
        "source_file": source.get("source_file"),
        "recall_source": source.get("recall_source"),
        "recall_score": source.get("recall_score"),
        "rerank_score": source.get("rerank_score"),
        "text_preview": text_preview,
        "metadata": source.get("metadata") if isinstance(source.get("metadata"), dict) else {},
    }


def retrieve_textbook_evidence(
    *,
    point_context: dict[str, Any],
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = settings or effective_textbook_rag_settings()
    diagnostics: dict[str, Any] = {
        "mode": "qwen_es_textbook_rag",
        "index_name": config.get("index_name"),
        "embedding_model": (config.get("embedding") or {}).get("model"),
        "rerank_model": (config.get("rerank") or {}).get("model"),
        "sections": {},
    }
    if not config.get("enabled"):
        return _failure_package("textbook_rag_disabled", "教材 RAG 未启用。", diagnostics)
    try:
        active_corpus = corpus_from_settings(config)
        active_filter = active_textbook_filter(active_corpus.documents)
        diagnostics.update(
            {
                "corpus_revision": active_corpus.revision,
                "active_document_count": len(active_corpus.documents),
                "active_document_ids": [document.document_id for document in active_corpus.documents],
                "active_corpus_load_error": active_corpus.load_error,
            }
        )
        es = TextbookElasticsearchClient(
            base_url=str(config.get("elasticsearch_url") or ""),
            index=str(config.get("index_name") or ""),
            timeout=float(config.get("timeout_seconds") or 8.0),
        )
        embedder = QwenEmbeddingClient(
            base_url=str((config.get("embedding") or {}).get("base_url") or ""),
            api_key=str((config.get("embedding") or {}).get("api_key") or ""),
            model=str((config.get("embedding") or {}).get("model") or ""),
            dimensions=int(config.get("embedding_dimension") or 0) or None,
            timeout_seconds=float(config.get("timeout_seconds") or 8.0),
        )
        reranker = QwenRerankClient(
            base_url=str((config.get("rerank") or {}).get("base_url") or ""),
            api_key=str((config.get("rerank") or {}).get("api_key") or ""),
            model=str((config.get("rerank") or {}).get("model") or ""),
            timeout_seconds=float(config.get("timeout_seconds") or 8.0),
        )
        queries = build_section_queries(point_context)
        if not queries:
            return _failure_package("point_description_missing", "点位缺少可用于检索的三段式描述。", diagnostics)
        section_results: dict[str, Any] = {}
        final_sources: list[dict[str, Any]] = []
        for section_query in queries:
            section_package = _retrieve_section(
                es=es,
                embedder=embedder,
                reranker=reranker,
                section_query=section_query,
                point_context=point_context,
                config=config,
                active_filter=active_filter,
            )
            section_results[section_query.section] = section_package
            final_sources.extend(section_package["sources"])
        diagnostics["sections"] = {
            section: {
                "query": package["query"],
                "candidate_count": package["candidate_count"],
                "source_count": len(package["sources"]),
                "sufficient": package["sufficient"],
                "missing_reason": package.get("missing_reason", ""),
            }
            for section, package in section_results.items()
        }
        supported_sections = [section for section, package in section_results.items() if package["sufficient"]]
        missing_sections = [section for section, package in section_results.items() if not package["sufficient"]]
        if not supported_sections:
            return _failure_package("textbook_evidence_missing", "未找到足够的教材证据。", diagnostics)
        return {
            "ok": True,
            "mode": "qwen_es_textbook_rag",
            "source_count": len(final_sources),
            "sections": section_results,
            "supported_sections": supported_sections,
            "missing_sections": missing_sections,
            "source_refs": final_sources,
            "diagnostics": diagnostics,
        }
    except (TextbookRAGClientError, OSError, ValueError, json.JSONDecodeError) as exc:
        return _failure_package(
            "textbook_rag_error",
            f"教材 RAG 检索失败：{exc.__class__.__name__}",
            {**diagnostics, "error": str(exc)[:240]},
        )


def _retrieve_section(
    *,
    es: TextbookElasticsearchClient,
    embedder: QwenEmbeddingClient,
    reranker: QwenRerankClient,
    section_query: PointEvidenceQuery,
    point_context: dict[str, Any],
    config: dict[str, Any],
    active_filter: dict[str, Any],
) -> dict[str, Any]:
    query_vector = embedder.embed([section_query.query])[0]
    lexical_hits = _es_search(
        es,
        _lexical_payload(
            section_query.query,
            size=int(config.get("keyword_top_k") or 16),
            point_context=point_context,
            active_filter=active_filter,
        ),
    )
    vector_hits = _es_search(
        es,
        _vector_payload(
            query_vector,
            size=int(config.get("vector_top_k") or 24),
            active_filter=active_filter,
        ),
    )
    candidates = _merge_candidates(
        [_source_from_hit(hit, recall_source="keyword") for hit in lexical_hits],
        [_source_from_hit(hit, recall_source="vector") for hit in vector_hits],
    )
    rerank_pool = candidates[: int(config.get("rerank_top_k") or 9)]
    if rerank_pool:
        scores = reranker.rerank(query=section_query.query, documents=[candidate["text"] for candidate in rerank_pool])
        for candidate, score in zip(rerank_pool, scores):
            candidate["rerank_score"] = score
    min_score = float(config.get("min_rerank_score") or 0.0)
    sorted_candidates = sorted(
        rerank_pool,
        key=_rank_score,
        reverse=True,
    )
    final_sources = sorted_candidates[: int(config.get("final_top_k") or 5)]
    if min_score:
        final_sources = [
            source
            for source in final_sources
            if float(source.get("rerank_score") if source.get("rerank_score") is not None else 0.0) >= min_score
        ]
    candidate_limit = int(config.get("candidate_top_k") or config.get("diagnostic_top_k") or 20)
    candidate_summaries = [
        _candidate_summary(source, section=section_query.section, rank=rank)
        for rank, source in enumerate(sorted_candidates[: max(0, candidate_limit)], start=1)
    ]
    return {
        "section": section_query.section,
        "query": section_query.query,
        "candidate_count": len(candidates),
        "candidates": candidate_summaries,
        "sources": final_sources,
        "sufficient": bool(final_sources),
        "missing_reason": "" if final_sources else "no_reranked_sources",
    }


def _failure_package(reason_code: str, message: str, diagnostics: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": False,
        "mode": "qwen_es_textbook_rag",
        "reason_code": reason_code,
        "message": message,
        "source_count": 0,
        "sections": {},
        "supported_sections": [],
        "missing_sections": [],
        "source_refs": [],
        "diagnostics": diagnostics,
    }

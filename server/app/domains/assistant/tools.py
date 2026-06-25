from __future__ import annotations

import time
from typing import Any, Callable

from server.app.domains.assistant.evidence_shaping import merge_sources as _merge_sources
from server.app.domains.assistant.rag_sources import (
    _source_evidence_payload,
    _source_from_chunk,
)
from server.app.domains.assistant.retrieval import (
    generate_retrieval_queries as _generate_retrieval_queries,
    retrieve_context as _retrieve_context,
)
from server.app.domains.assistant.runtime import AgentRunContext
from server.app.infrastructure.settings import get_settings
from server.app.retrieval import keyword_score


def approved_tool_registry(context: AgentRunContext) -> dict[str, Callable[..., Any]]:
    return {
        "rag_search": lambda query: rag_search_tool(context, query),
        "curriculum_lookup": lambda query: curriculum_lookup_tool(context, query),
        "published_resource_lookup": lambda target_type=None, target_id=None: published_resource_lookup_tool(
            context, target_type, target_id
        ),
        "own_student_progress_lookup": lambda: own_student_progress_lookup_tool(context),
    }


async def rag_search_tool(context: AgentRunContext, query: str) -> dict[str, Any]:
    if not context.classification.get("allow_rag_lookup", True):
        result = {"evidence": [], "disabled": True}
        context.add_guardrail("rag_lookup_disabled", "skip_rag_lookup", "学生侧 AI RAG 接入已关闭。")
        context.record_tool("rag_search", {"query": query}, result["evidence"])
        return result
    settings = context.settings or get_settings()
    started_at = time.perf_counter()
    query_started_at = time.perf_counter()
    generated_queries, query_trace = await _generate_retrieval_queries(context, settings, query)
    query_generation_ms = round((time.perf_counter() - query_started_at) * 1000, 2)
    lookup_queries: list[str] = []
    seen_queries: set[str] = set()
    for item in [*generated_queries, query]:
        normalized = " ".join(str(item or "").split())
        if normalized and normalized not in seen_queries:
            seen_queries.add(normalized)
            lookup_queries.append(normalized)

    keyword_limit = max(1, int(getattr(settings, "rag_keyword_top_k", 16)))
    final_limit = max(1, int(getattr(settings, "rag_final_top_k", 5)))
    keyword_started_at = time.perf_counter()
    candidate_counts: dict[str, int] = {}
    candidates: dict[str, dict[str, Any]] = {}
    for lookup_query in lookup_queries:
        retrieved = _retrieve_context(
            context.repositories,
            lookup_query,
            context.request,
            limit=max(keyword_limit, final_limit),
        )
        candidate_counts[lookup_query] = len(retrieved)
        for chunk in retrieved:
            chunk_id = str(chunk.get("chunk_id") or chunk.get("id") or "").strip()
            if not chunk_id:
                continue
            score = float(chunk.get("_score") or 0.0)
            existing = candidates.get(chunk_id)
            if existing is None or score > float(existing.get("_score") or 0.0):
                candidates[chunk_id] = {**chunk, "_retrieval_query": lookup_query, "_score": score}
    chunks = sorted(candidates.values(), key=lambda item: float(item.get("_score") or 0.0), reverse=True)[:final_limit]
    keyword_ms = round((time.perf_counter() - keyword_started_at) * 1000, 2)
    trace = {
        "mode": "external_boundary_keyword_lookup",
        "source_boundary": "platform_resource_lookup",
        "generated_queries": lookup_queries,
        "query_generation": query_trace,
        "candidate_counts": {
            "keyword": sum(candidate_counts.values()),
            "unique": len(candidates),
            "by_query": candidate_counts,
        },
        "final_evidence": [
            {
                "rank": index,
                "chunk_id": chunk.get("chunk_id") or chunk.get("id"),
                "score": chunk.get("_score"),
                "source": "keyword",
                "query": chunk.get("_retrieval_query"),
            }
            for index, chunk in enumerate(chunks, start=1)
        ],
        "rerank_scores": [],
        "fallbacks": [] if query_trace.get("status") == "generated" else [{"stage": "query_generation", "reason": query_trace.get("reason") or query_trace.get("status")}],
        "final_sort": "keyword_score",
        "timings_ms": {
            "query_generation": query_generation_ms,
            "keyword_recall": keyword_ms,
            "total": round((time.perf_counter() - started_at) * 1000, 2),
        },
    }
    context.rag_traces.append(trace)
    sources = [_source_from_chunk(chunk) for chunk in chunks]
    context.sources = _merge_sources(context.sources, sources)
    evidence = [_source_evidence_payload(source) for source in sources]
    result = {
        "evidence": evidence,
        "trace": trace,
    }
    context.record_tool(
        "rag_search",
        {
            "query": query,
            "mode": trace.get("mode"),
            "generated_queries": trace.get("generated_queries") or [],
        },
        result["evidence"],
    )
    return result


def curriculum_lookup_tool(context: AgentRunContext, query: str) -> dict[str, Any]:
    request = context.request
    chapters = context.repositories.content.chapters()
    units = context.repositories.content.units()
    points = context.repositories.content.knowledge_points()
    if request.chapter_id:
        chapters = [item for item in chapters if item.get("chapter_id") == request.chapter_id]
        units = [item for item in units if item.get("chapter_id") == request.chapter_id]
        points = [item for item in points if item.get("chapter_id") == request.chapter_id]
    if request.knowledge_point_ids:
        wanted = set(request.knowledge_point_ids)
        points = [item for item in points if item.get("knowledge_point_id") in wanted or item.get("id") in wanted]
    scored_points = sorted(
        points,
        key=lambda item: keyword_score(query, {"text": item.get("content") or item.get("unit_title") or ""}, chapter_id=request.chapter_id),
        reverse=True,
    )[:8]
    result = {"chapters": chapters[:5], "units": units[:8], "knowledge_points": scored_points}
    context.record_tool("curriculum_lookup", {"query": query}, result)
    return result


def published_resource_lookup_tool(
    context: AgentRunContext,
    target_type: str | None = None,
    target_id: str | None = None,
) -> dict[str, Any]:
    request = context.request
    lookups: list[tuple[str, str]] = []
    if target_type and target_id:
        lookups.append((target_type, target_id))
    if request.experiment_id:
        lookups.append(("experiment", request.experiment_id))
    for kp_id in request.knowledge_point_ids:
        lookups.append(("knowledge_point", kp_id))
    if request.chapter_id:
        lookups.append(("chapter", request.chapter_id))

    resources: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item_type, item_id in lookups:
        for resource in context.repositories.media.list_ready_bindings(item_type, item_id):
            resource_id = str(resource.get("binding_id") or resource.get("media_id") or resource)
            if resource_id not in seen:
                seen.add(resource_id)
                resources.append(resource)

    result = {"resources": resources}
    context.record_tool("published_resource_lookup", {"targets": lookups}, resources)
    return result


def own_student_progress_lookup_tool(context: AgentRunContext) -> dict[str, Any]:
    if not context.request.student_id or not context.classification.get("allow_progress_lookup"):
        result = {"allowed": False, "reason": "student_context_required"}
        context.record_tool("own_student_progress_lookup", {}, result)
        return result
    mastery = context.repositories.learning.load_mastery().get(context.request.student_id, {})
    weak_points = [
        {"knowledge_point_id": kp_id, "mastery_score": state.get("mastery_score", 0)}
        for kp_id, state in mastery.items()
        if float(state.get("mastery_score", 0)) < 60
    ][:8]
    result = {"allowed": True, "weak_knowledge_points": weak_points}
    context.record_tool("own_student_progress_lookup", {"student_id": context.request.student_id}, result)
    return result

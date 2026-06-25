from __future__ import annotations

import json
import os
from typing import Any

from server.app.infrastructure.settings import Settings
from server.app.repositories import RepositoryProvider
from server.app.retrieval import keyword_score
from server.app.schemas import AgentAskRequest, RagAskRequest


def agent_to_rag_request(request: AgentAskRequest) -> RagAskRequest:
    return RagAskRequest(
        student_id=request.student_id,
        question=request.question,
        chapter_id=request.chapter_id,
        experiment_id=request.experiment_id,
        point_key=request.point_key,
        knowledge_point_ids=request.knowledge_point_ids,
    )


def rag_to_agent_request(request: RagAskRequest) -> AgentAskRequest:
    return AgentAskRequest(
        student_id=request.student_id,
        question=request.question,
        chapter_id=request.chapter_id,
        experiment_id=request.experiment_id,
        point_key=request.point_key,
        knowledge_point_ids=request.knowledge_point_ids,
    )


def retrieve_context(
    repositories: RepositoryProvider,
    question: str,
    request: AgentAskRequest,
    limit: int = 5,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(item: dict[str, Any]) -> None:
        item_id = str(item.get("id") or item.get("chunk_id") or "")
        if item_id and item_id not in seen:
            seen.add(item_id)
            candidates.append(item)

    if request.knowledge_point_ids:
        for kp_id in request.knowledge_point_ids:
            for chunk in repositories.content.related_chunks_for_kp(kp_id, limit=limit):
                add(chunk)
    source_chunks = repositories.content.source_chunks()
    if request.experiment_id:
        experiment = repositories.content.get_experiment(request.experiment_id)
        chunk_ids = set((experiment or {}).get("source_chunk_ids") or [])
        for chunk in source_chunks:
            if chunk.get("id") in chunk_ids or chunk.get("chunk_id") in chunk_ids:
                add(chunk)
    if request.chapter_id:
        for chunk in source_chunks:
            if chunk.get("chapter_id") == request.chapter_id:
                add(chunk)
    for chunk in source_chunks:
        add(chunk)

    scored: list[dict[str, Any]] = []
    for item in candidates:
        score = keyword_score(
            question,
            item,
            chapter_id=request.chapter_id,
            experiment_id=request.experiment_id,
            knowledge_point_ids=request.knowledge_point_ids,
        )
        if score > 0.04:
            scored.append({**item, "_score": score})
    scored.sort(key=lambda item: item["_score"], reverse=True)
    return scored[:limit]


def _sdk_enabled_for_retrieval(settings: Settings) -> bool:
    return (
        settings.agent_llm_provider in {"openai", "openai_compatible"}
        and bool(settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"))
        and bool(settings.agent_llm_model)
    )


async def generate_retrieval_queries(
    context: Any,
    settings: Settings,
    question: str,
) -> tuple[list[str], dict[str, Any]]:
    trace: dict[str, Any] = {"status": "skipped", "reason": "", "provider": settings.agent_llm_provider}
    if not settings.rag_query_generation_enabled:
        trace["reason"] = "disabled"
        return [question], trace
    if not _sdk_enabled_for_retrieval(settings):
        trace["reason"] = "llm_not_configured"
        return [question], trace
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"),
            base_url=settings.agent_llm_base_url or None,
            timeout=10.0,
        )
        response = await client.chat.completions.create(
            model=settings.agent_llm_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You rewrite an inorganic chemistry student question into concise retrieval queries. "
                        "Return JSON only with key queries as an array of 1 to 3 Chinese search queries. "
                        "Keep reagent names, experiment numbers, and chemistry terms exact. Do not answer the question."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "question": question,
                            "chapter_id": context.request.chapter_id,
                            "experiment_id": context.request.experiment_id,
                            "knowledge_point_ids": context.request.knowledge_point_ids,
                            "conversation_history": [
                                item.model_dump() if hasattr(item, "model_dump") else item.dict()
                                for item in context.request.conversation_history[-6:]
                            ],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        content = response.choices[0].message.content if response.choices else ""
        payload = json.loads(content or "{}")
        raw_queries = payload.get("queries") if isinstance(payload, dict) else []
        queries = [
            " ".join(str(item or "").split())
            for item in raw_queries
            if isinstance(item, str) and str(item or "").strip()
        ][:3]
        if not queries:
            trace.update({"status": "fallback", "reason": "empty_queries"})
            return [question], trace
        trace.update({"status": "generated", "reason": "", "queries": queries})
        return queries, trace
    except Exception as exc:
        trace.update({"status": "fallback", "reason": f"{exc.__class__.__name__}: {str(exc)[:160]}"})
        return [question], trace

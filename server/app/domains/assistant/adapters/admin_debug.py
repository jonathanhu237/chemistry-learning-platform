from __future__ import annotations

from typing import Any, AsyncIterator, Awaitable, Callable

from server.app.domains.assistant.runtime_facade import run_agent, run_agent_stream
from server.app.infrastructure.settings import Settings
from server.app.schemas import AgentAskRequest, AgentAskResponse


StreamCancelCheck = Callable[[], bool | Awaitable[bool]]


def build_admin_debug_agent_request(
    payload: Any,
    user: Any,
    *,
    rag_access_enabled: bool,
) -> AgentAskRequest:
    return AgentAskRequest(
        student_id=payload.student_id or None,
        user_id=user.id,
        user_role="admin_debug",
        question=payload.question,
        chapter_id=payload.chapter_id or None,
        experiment_id=payload.experiment_id or None,
        point_key=payload.point_key or None,
        knowledge_point_ids=payload.knowledge_point_ids,
        allow_progress_lookup=payload.allow_progress_lookup,
        allow_rag_lookup=payload.allow_rag_lookup and rag_access_enabled,
        conversation_history=payload.conversation_history,
        max_answer_chars=payload.max_answer_chars,
    )


async def run_admin_debug_agent(
    payload: Any,
    user: Any,
    *,
    settings: Settings,
    rag_access_enabled: bool,
) -> AgentAskResponse:
    return await run_agent(
        build_admin_debug_agent_request(payload, user, rag_access_enabled=rag_access_enabled),
        settings=settings,
    )


async def stream_admin_debug_agent(
    payload: Any,
    user: Any,
    *,
    settings: Settings,
    rag_access_enabled: bool,
    should_cancel: StreamCancelCheck | None = None,
) -> AsyncIterator[dict[str, object]]:
    request = build_admin_debug_agent_request(payload, user, rag_access_enabled=rag_access_enabled)
    async for item in run_agent_stream(request, settings=settings, should_cancel=should_cancel):
        yield item

from __future__ import annotations

from server.app.domains.assistant.runtime_facade import run_agent
from server.app.infrastructure.settings import Settings
from server.app.schemas import AgentAskRequest, AgentAskResponse


async def run_posttest_agent(request: AgentAskRequest, *, settings: Settings) -> AgentAskResponse:
    return await run_agent(request, settings=settings)

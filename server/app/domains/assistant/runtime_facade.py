from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Awaitable, Callable

from server.app.domains.assistant.policy import AgentPolicy
from server.app.infrastructure.settings import Settings
from server.app.repositories import RepositoryProvider
from server.app.schemas import AgentAskRequest, AgentAskResponse


StreamCancelCheck = Callable[[], bool | Awaitable[bool]]
AgentEvent = dict[str, object]


@dataclass(frozen=True)
class AgentRuntimeOptions:
    repositories: RepositoryProvider | None = None
    settings: Settings | None = None
    policy: AgentPolicy | None = None
    should_cancel: StreamCancelCheck | None = None
    diagnostics_mode: str = "standard"


class AgentRuntime:
    async def run(self, request: AgentAskRequest, options: AgentRuntimeOptions | None = None) -> AgentAskResponse:
        from server.app.domains.assistant import orchestrator

        runtime_options = options or AgentRuntimeOptions()
        return await orchestrator.run_agent(
            request,
            repositories=runtime_options.repositories,
            settings=runtime_options.settings,
            policy=runtime_options.policy,
        )

    async def stream(
        self,
        request: AgentAskRequest,
        options: AgentRuntimeOptions | None = None,
    ) -> AsyncIterator[dict[str, object]]:
        from server.app.domains.assistant import orchestrator

        runtime_options = options or AgentRuntimeOptions()
        async for item in orchestrator.run_agent_stream(
            request,
            repositories=runtime_options.repositories,
            settings=runtime_options.settings,
            policy=runtime_options.policy,
            should_cancel=runtime_options.should_cancel,
        ):
            yield item


_DEFAULT_RUNTIME = AgentRuntime()


async def run_agent(
    request: AgentAskRequest,
    repositories: RepositoryProvider | None = None,
    settings: Settings | None = None,
    policy: AgentPolicy | None = None,
) -> AgentAskResponse:
    return await _DEFAULT_RUNTIME.run(
        request,
        AgentRuntimeOptions(repositories=repositories, settings=settings, policy=policy),
    )


async def run_agent_stream(
    request: AgentAskRequest,
    repositories: RepositoryProvider | None = None,
    settings: Settings | None = None,
    policy: AgentPolicy | None = None,
    should_cancel: StreamCancelCheck | None = None,
) -> AsyncIterator[dict[str, object]]:
    async for item in _DEFAULT_RUNTIME.stream(
        request,
        AgentRuntimeOptions(
            repositories=repositories,
            settings=settings,
            policy=policy,
            should_cancel=should_cancel,
        ),
    ):
        yield item

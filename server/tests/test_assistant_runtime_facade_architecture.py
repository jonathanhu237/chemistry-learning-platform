from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from server.app.domains.assistant import orchestrator
from server.app.domains.assistant.runtime_facade import AgentRuntime, AgentRuntimeOptions, run_agent, run_agent_stream
from server.app.domains.assistant.student_assistant import _student_final_response_with_followups
from server.app.schemas import AgentAskRequest, AgentAskResponse
from server.app.student_assistant_schemas import StudentAssistantAskRequest


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_facade_preserves_one_shot_response_shape(monkeypatch) -> None:
    async def fake_run_agent(request, **kwargs):
        assert isinstance(request, AgentAskRequest)
        assert kwargs["settings"] == "settings"
        return AgentAskResponse(answer="ok", mode="local")

    monkeypatch.setattr(orchestrator, "run_agent", fake_run_agent)

    response = asyncio.run(run_agent(AgentAskRequest(question="hello"), settings="settings"))  # type: ignore[arg-type]

    assert isinstance(response, AgentAskResponse)
    assert response.answer == "ok"


def test_runtime_facade_preserves_stream_event_shape(monkeypatch) -> None:
    async def fake_stream(request, **kwargs):
        assert isinstance(request, AgentAskRequest)
        assert kwargs["should_cancel"] is not None
        yield {"event": "delta", "delta": "A"}
        yield {"event": "final", "response": {"answer": "A"}}

    monkeypatch.setattr(orchestrator, "run_agent_stream", fake_stream)

    async def collect() -> list[dict[str, object]]:
        runtime = AgentRuntime()
        return [
            item
            async for item in runtime.stream(
                AgentAskRequest(question="hello"),
                AgentRuntimeOptions(should_cancel=lambda: False),
            )
        ]

    assert asyncio.run(collect()) == [
        {"event": "delta", "delta": "A"},
        {"event": "final", "response": {"answer": "A"}},
    ]


def test_agent_module_is_compatibility_shim() -> None:
    source = (ROOT / "app" / "domains" / "assistant" / "agent.py").read_text(encoding="utf-8")

    assert "runtime_facade" in source
    assert "def rag_search_tool" not in source
    assert "client.chat.completions.create" not in source
    assert "async for chunk in stream" not in source
    assert "async def run_agent(" not in source
    assert "async def run_agent_stream(" not in source


def test_runtime_consumer_import_boundaries() -> None:
    checked_paths = [
        ROOT / "app" / "api" / "teacher" / "teacher_learning_assistant.py",
        ROOT / "app" / "domains" / "assessments" / "reports.py",
        ROOT / "app" / "domains" / "assistant" / "student_assistant.py",
    ]
    disallowed = [
        "server.app.domains.assistant.agent",
        "server.app.domains.assistant.orchestrator",
        "server.app.domains.assistant.providers",
        "server.app.domains.assistant.tools",
        "server.app.domains.assistant.diagnostics",
    ]
    failures: list[str] = []
    for path in checked_paths:
        source = path.read_text(encoding="utf-8")
        for import_name in disallowed:
            if import_name in source:
                failures.append(f"{path.relative_to(ROOT)} imports {import_name}")

    assert not failures, "Consumers must use adapters or runtime_facade:\n" + "\n".join(failures)


def test_student_projection_omits_teacher_diagnostics() -> None:
    payload = StudentAssistantAskRequest(question="现象是什么", context_type="learning_point")
    response = {
        "answer": "绿色褪去。",
        "mode": "openai_chat_stream",
        "sources": [{"title": "source"}],
        "source_count": 1,
        "classification": {"requires_evidence": True},
        "tool_calls": [{"name": "rag_search", "args": {"query": "secret"}}],
        "guardrail_decisions": [{"code": "policy"}],
        "rag_trace": {"chunk_id": "secret"},
    }

    projected = asyncio.run(
        _student_final_response_with_followups(
            response,
            payload,
            SimpleNamespace(),
            should_cancel=lambda: True,
        )
    )

    assert projected["answer"] == "绿色褪去。"
    assert projected["sources"] == [{"title": "source"}]
    assert "classification" not in projected
    assert "tool_calls" not in projected
    assert "guardrail_decisions" not in projected
    assert "rag_trace" not in projected

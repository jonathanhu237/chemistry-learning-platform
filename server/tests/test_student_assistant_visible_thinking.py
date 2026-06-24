from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import server.app.domains.assistant.agent as agent_module
from server.app.domains.assistant.agent import (
    _run_openai_responses_stream,
    _sanitize_visible_thinking_message,
    run_agent_stream,
)
from server.app.domains.assistant.policy import load_agent_policy
from server.app.domains.assistant.runtime import create_agent_context
from server.app.infrastructure.settings import Settings
from server.app.repositories import EmptyMediaRepository, NoopAgentLogRepository, RepositoryProvider
from server.app.schemas import AgentAskRequest


@dataclass
class _ContentRepository:
    def areas(self) -> list[dict[str, Any]]:
        return []

    def chapters(self) -> list[dict[str, Any]]:
        return [{"chapter_id": "CH13", "chapter_title": "氧化还原"}]

    def units(self) -> list[dict[str, Any]]:
        return []

    def knowledge_points(self) -> list[dict[str, Any]]:
        return [{"knowledge_point_id": "KP1", "chapter_id": "CH13", "content": "氧化还原实验现象"}]

    def experiments(self) -> list[dict[str, Any]]:
        return []

    def learning_cards(self) -> list[dict[str, Any]]:
        return []

    def questions(self) -> list[dict[str, Any]]:
        return []

    def links(self) -> list[dict[str, Any]]:
        return []

    def source_chunks(self) -> list[dict[str, Any]]:
        return []

    def get_chapter(self, chapter_id: str) -> dict[str, Any] | None:
        return None

    def get_unit(self, unit_id: str) -> dict[str, Any] | None:
        return None

    def get_knowledge_point(self, kp_id: str) -> dict[str, Any] | None:
        return None

    def get_experiment(self, experiment_id: str) -> dict[str, Any] | None:
        return None

    def get_learning_card(self, experiment_id: str) -> dict[str, Any] | None:
        return None

    def get_question(self, question_id: str) -> dict[str, Any] | None:
        return None

    def related_chunks_for_kp(self, kp_id: str, limit: int = 8) -> list[dict[str, Any]]:
        return []

    def point_question_evidence(self, experiment_id: str, point_key: str, limit: int = 12) -> list[dict[str, Any]]:
        return []

    def point_reviewed_evidence(self, experiment_id: str, point_key: str) -> dict[str, Any] | None:
        return None


class _LearningRepository:
    def load_events(self) -> list[dict[str, Any]]:
        return []

    def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return event

    def load_mastery(self) -> dict[str, Any]:
        return {}

    def save_mastery(self, data: dict[str, Any]) -> None:
        return None

    def load_students(self) -> list[dict[str, Any]]:
        return []

    def save_students(self, students: list[dict[str, Any]]) -> None:
        return None


class _ReviewRepository:
    def list_items(self) -> list[dict[str, Any]]:
        return []


def _repositories() -> RepositoryProvider:
    return RepositoryProvider(
        content=_ContentRepository(),
        learning=_LearningRepository(),
        review=_ReviewRepository(),
        media=EmptyMediaRepository(),
        agent_logs=NoopAgentLogRepository(),
    )


def _settings(**overrides: Any) -> Settings:
    return Settings(
        agent_llm_provider=overrides.pop("agent_llm_provider", "disabled"),
        agent_llm_api_key=overrides.pop("agent_llm_api_key", ""),
        agent_llm_model=overrides.pop("agent_llm_model", ""),
        agent_llm_base_url=overrides.pop("agent_llm_base_url", ""),
        agent_reasoning_summary_enabled=overrides.pop("agent_reasoning_summary_enabled", False),
        agent_reasoning_summary_mode=overrides.pop("agent_reasoning_summary_mode", "auto"),
        agent_reasoning_effort=overrides.pop("agent_reasoning_effort", "low"),
        **overrides,
    )


async def _collect_stream(settings: Settings) -> list[dict[str, Any]]:
    request = AgentAskRequest(question="请解释氧化还原实验现象", allow_rag_lookup=False)
    return [
        item
        async for item in run_agent_stream(
            request,
            repositories=_repositories(),
            settings=settings,
            policy=load_agent_policy(),
        )
    ]


def test_responses_stream_maps_reasoning_summary_to_thinking(monkeypatch) -> None:
    class _FakeStream:
        def __enter__(self):
            return iter(
                [
                    SimpleNamespace(type="response.reasoning_summary_text.delta", delta="正在分析实验现象", sequence_number=10),
                    SimpleNamespace(type="response.reasoning_text.delta", delta="raw hidden reasoning", sequence_number=11),
                    SimpleNamespace(type="response.output_text.delta", delta="这是回答。", sequence_number=12),
                ]
            )

        def __exit__(self, *_args):
            return False

    class _FakeResponses:
        def stream(self, **_kwargs):
            return _FakeStream()

    class _FakeClient:
        responses = _FakeResponses()

    settings = _settings(
        agent_llm_provider="openai",
        agent_llm_api_key="test-key",
        agent_llm_model="gpt-test",
        agent_reasoning_summary_enabled=True,
    )
    context = create_agent_context(
        request=AgentAskRequest(question="请解释氧化还原实验现象", allow_rag_lookup=False),
        repositories=_repositories(),
        policy=load_agent_policy(),
        classification={"allow_rag_lookup": False},
        settings=settings,
    )
    monkeypatch.setattr(agent_module, "_openai_client", lambda *_args, **_kwargs: _FakeClient())

    events = asyncio.run(_collect_async(_run_openai_responses_stream(context, settings)))

    assert {"event": "thinking", "source": "reasoning_summary", "message": "正在分析实验现象", "phase": "reasoning", "sequence": 10} in events
    assert {"event": "delta", "delta": "这是回答。"} in events
    assert all("raw hidden reasoning" not in str(event) for event in events)


async def _collect_async(iterator) -> list[dict[str, Any]]:
    return [item async for item in iterator]


def test_run_agent_stream_emits_reasoning_summary_without_appending_to_answer(monkeypatch) -> None:
    async def fake_policy_gate(_context, _settings):
        return agent_module._local_policy_decision_from_classification({"rag_preferred": True})

    async def fake_responses_stream(_context, _settings):
        yield {"event": "thinking", "source": "reasoning_summary", "message": "正在分析实验现象", "phase": "reasoning", "sequence": 20}
        yield {"event": "delta", "delta": "溴生成后会使有机层显橙色。"}

    monkeypatch.setattr(agent_module, "_policy_gate_decision", fake_policy_gate)
    monkeypatch.setattr(agent_module, "_run_openai_responses_stream", fake_responses_stream)

    events = asyncio.run(
        _collect_stream(
            _settings(
                agent_llm_provider="openai",
                agent_llm_api_key="test-key",
                agent_llm_model="gpt-test",
                agent_reasoning_summary_enabled=True,
            )
        )
    )

    assert any(event.get("event") == "thinking" and event.get("source") == "reasoning_summary" for event in events)
    assert any(event.get("event") == "delta" for event in events)
    final = next(event for event in events if event.get("event") == "final")
    assert "正在分析实验现象" not in final["response"]["answer"]
    assert "溴生成后会使有机层显橙色。" in final["response"]["answer"]


def test_run_agent_stream_uses_agent_trace_when_summary_is_disabled(monkeypatch) -> None:
    async def fake_policy_gate(_context, _settings):
        return agent_module._local_policy_decision_from_classification({"rag_preferred": True})

    async def fake_chat_stream(_context, _settings):
        yield "模型回答。"

    monkeypatch.setattr(agent_module, "_policy_gate_decision", fake_policy_gate)
    monkeypatch.setattr(agent_module, "_run_openai_chat_completion_stream", fake_chat_stream)

    events = asyncio.run(
        _collect_stream(
            _settings(
                agent_llm_provider="openai",
                agent_llm_api_key="test-key",
                agent_llm_model="gpt-test",
                agent_reasoning_summary_enabled=False,
            )
        )
    )

    thinking_sources = [event.get("source") for event in events if event.get("event") == "thinking"]
    thinking_phases = [event.get("phase") for event in events if event.get("event") == "thinking"]
    assert "agent_trace" in thinking_sources
    assert "reasoning_summary" not in thinking_sources
    assert "retrieval_decision" in thinking_phases
    assert "retrieval_skip" in thinking_phases
    assert "retrieval" not in thinking_phases
    assert [event.get("event") for event in events if event.get("event") in {"delta", "final"}] == ["delta", "final"]
    assert all("retrieval_mode" not in str(event) for event in events if event.get("event") == "thinking")
    assert all("rag_search" not in str(event) for event in events if event.get("event") == "thinking")


def test_run_agent_stream_trace_shows_retrieval_when_selected(monkeypatch) -> None:
    async def fake_policy_gate(_context, _settings):
        return agent_module.StudentAIPolicyDecision(
            mode="normal_answer",
            reason="evidence request",
            allowed_tools=("rag_search", "curriculum_lookup"),
            retrieval_mode="dynamic_rag",
            retrieval_reason="course evidence is useful",
            retrieval_confidence=0.87,
        )

    async def fake_chat_stream(context, _settings):
        context.record_tool(
            "rag_search",
            {"query": context.request.question},
            {"evidence": [{"text_preview": "supporting course evidence"}]},
        )
        yield "model answer"

    monkeypatch.setattr(agent_module, "_policy_gate_decision", fake_policy_gate)
    monkeypatch.setattr(agent_module, "_run_openai_chat_completion_stream", fake_chat_stream)

    settings = _settings(
        agent_llm_provider="openai",
        agent_llm_api_key="test-key",
        agent_llm_model="gpt-test",
        agent_reasoning_summary_enabled=False,
    )
    request = AgentAskRequest(question="Please cite the course material for permanganate oxidation.", allow_rag_lookup=True)
    events = asyncio.run(
        _collect_async(
            run_agent_stream(
                request,
                repositories=_repositories(),
                settings=settings,
                policy=load_agent_policy(),
            )
        )
    )

    thinking_phases = [event.get("phase") for event in events if event.get("event") == "thinking"]
    assert "retrieval_decision" in thinking_phases
    assert "retrieval" in thinking_phases
    assert "evidence_quality" in thinking_phases
    assert "generation" in thinking_phases
    assert all("dynamic_rag" not in str(event) for event in events if event.get("event") == "thinking")
    final = next(event for event in events if event.get("event") == "final")
    assert any(call["name"] == "rag_search" for call in final["response"]["tool_calls"])


def test_run_agent_stream_falls_back_when_reasoning_summary_stream_fails(monkeypatch) -> None:
    async def fake_policy_gate(_context, _settings):
        return agent_module._local_policy_decision_from_classification({"rag_preferred": True})

    async def failing_responses_stream(_context, _settings):
        raise RuntimeError("provider exploded with raw diagnostics")
        yield {}

    monkeypatch.setattr(agent_module, "_policy_gate_decision", fake_policy_gate)
    monkeypatch.setattr(agent_module, "_run_openai_responses_stream", failing_responses_stream)
    monkeypatch.setattr(agent_module, "_run_local_agent", lambda _context: "本地兜底回答。")

    events = asyncio.run(
        _collect_stream(
            _settings(
                agent_llm_provider="openai",
                agent_llm_api_key="test-key",
                agent_llm_model="gpt-test",
                agent_reasoning_summary_enabled=True,
            )
        )
    )

    assert any(event.get("event") == "thinking" and event.get("phase") == "fallback" for event in events)
    assert all("provider exploded" not in str(event) for event in events)
    final = next(event for event in events if event.get("event") == "final")
    assert final["response"]["answer"] == "本地兜底回答。"


def test_visible_thinking_sanitizer_rejects_raw_diagnostics() -> None:
    assert _sanitize_visible_thinking_message("正在分析实验现象") == "正在分析实验现象"
    assert _sanitize_visible_thinking_message("chain-of-thought: hidden steps") == ""
    assert _sanitize_visible_thinking_message("rag_trace: {'chunk_id': 'abc'}") == ""
    assert _sanitize_visible_thinking_message("Traceback Exception from provider") == ""
    assert _sanitize_visible_thinking_message("系统提示：不要展示") == ""
    assert _sanitize_visible_thinking_message("{\"message\":\"正在分析\"}") == ""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import server.app.domains.assistant.orchestrator as agent_module
from server.app.domains.assistant.orchestrator import run_agent_stream
from server.app.domains.assistant.policy import AgentPolicy
from server.app.domains.assistant.student_assistant import _agent_request_for_chat
from server.app.infrastructure.settings import Settings
from server.app.repositories import EmptyMediaRepository, NoopAgentLogRepository, RepositoryProvider
from server.app.schemas import AgentAskRequest
from server.app.student_assistant_schemas import StudentAssistantAskRequest


@dataclass
class _ContentRepository:
    def areas(self) -> list[dict[str, Any]]:
        return []

    def chapters(self) -> list[dict[str, Any]]:
        return [{"chapter_id": "CH13", "chapter_title": "Halogens"}]

    def units(self) -> list[dict[str, Any]]:
        return []

    def knowledge_points(self) -> list[dict[str, Any]]:
        return [{"knowledge_point_id": "KP1", "chapter_id": "CH13", "content": "Halogen displacement"}]

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


async def _collect_stream(request: AgentAskRequest, *, policy: AgentPolicy) -> list[dict[str, Any]]:
    return [
        item
        async for item in run_agent_stream(
            request,
            repositories=_repositories(),
            settings=Settings(agent_llm_provider="disabled"),
            policy=policy,
        )
    ]


def test_student_root_chat_request_disables_mobile_length_guardrail() -> None:
    user = SimpleNamespace(id="user-1", student_id="s1", username="student")
    payload = StudentAssistantAskRequest(
        question="Explain chlorine water and potassium bromide extraction.",
        context_type="learning_home",
        context_title="Atom",
        context_summary="Student global assistant entry",
    )

    request = _agent_request_for_chat(user, payload, allow_rag_lookup=True)

    assert request.max_answer_chars == 0


def test_zero_max_answer_chars_preserves_long_markdown_stream_without_replace(monkeypatch) -> None:
    long_mermaid_answer = "\n".join(
        [
            "### Experiment flow",
            "",
            "```mermaid",
            "flowchart TD",
            "    A[Mix chlorine water with KBr] --> B[Generate Br2]",
            "    B --> C[Add CCl4 and shake]",
            "    C --> D[Organic layer turns orange red]",
            "    D --> E[Conclude chlorine oxidizes bromide]",
            "    E --> F[Review halogen oxidizing trend]",
            "```",
            "",
            "This completed answer must stay intact after streaming.",
        ]
    )

    async def normal_policy_gate(_context: Any, _settings: Settings) -> agent_module.StudentAIPolicyDecision:
        return agent_module.StudentAIPolicyDecision(
            mode="normal_answer",
            reason="ordinary chemistry explanation",
            retrieval_mode="skip",
        )

    monkeypatch.setattr(agent_module, "_policy_gate_decision", normal_policy_gate)
    monkeypatch.setattr(agent_module, "_preflight_response", lambda _context: None)
    async def fake_local_agent(_context):
        return long_mermaid_answer

    monkeypatch.setattr(agent_module, "_run_local_agent", fake_local_agent)

    events = asyncio.run(
        _collect_stream(
            AgentAskRequest(
                question="Explain chlorine bromine iodine displacement.",
                allow_rag_lookup=False,
                max_answer_chars=0,
            ),
            policy=AgentPolicy(source_path=None, source_excerpt="", course_scope=(), max_answer_chars=80),
        )
    )

    final = next(event for event in events if event.get("event") == "final")

    assert not any(event.get("event") == "replace" for event in events)
    assert final["response"]["answer"] == long_mermaid_answer
    assert "E --> F[Review halogen oxidizing trend]" in final["response"]["answer"]
    assert not any(item["code"] == "mobile_length" for item in final["response"]["guardrail_decisions"])

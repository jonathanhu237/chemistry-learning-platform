from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import server.app.domains.assistant.orchestrator as agent_module
import server.app.domains.assistant.evidence as evidence_module
from server.app.domains.assistant.orchestrator import AgentPolicy, run_agent
from server.app.infrastructure.settings import Settings
from server.app.repositories import EmptyMediaRepository, NoopAgentLogRepository, RepositoryProvider
from server.app.schemas import AgentAskRequest
from server.app.domains.assistant.retrieval import (
    agent_to_rag_request,
    generate_retrieval_queries,
    rag_to_agent_request,
    retrieve_context,
)


@dataclass
class _ContentRepository:
    source_chunk_items: list[dict[str, Any]] = field(default_factory=list)
    reviewed_evidence: dict[str, Any] | None = None

    def areas(self) -> list[dict[str, Any]]:
        return []

    def chapters(self) -> list[dict[str, Any]]:
        return [{"chapter_id": "CH13", "chapter_title": "Halogens"}]

    def units(self) -> list[dict[str, Any]]:
        return []

    def knowledge_points(self) -> list[dict[str, Any]]:
        return [{"knowledge_point_id": "KP1", "chapter_id": "CH13", "content": "Oxidation trend"}]

    def experiments(self) -> list[dict[str, Any]]:
        return []

    def learning_cards(self) -> list[dict[str, Any]]:
        return []

    def questions(self) -> list[dict[str, Any]]:
        return []

    def links(self) -> list[dict[str, Any]]:
        return []

    def source_chunks(self) -> list[dict[str, Any]]:
        return self.source_chunk_items

    def get_chapter(self, chapter_id: str) -> dict[str, Any] | None:
        return None

    def get_unit(self, unit_id: str) -> dict[str, Any] | None:
        return None

    def get_knowledge_point(self, kp_id: str) -> dict[str, Any] | None:
        return None

    def get_experiment(self, experiment_id: str) -> dict[str, Any] | None:
        if experiment_id != "EXP1":
            return None
        return {
            "experiment_id": "EXP1",
            "code": "EXP1",
            "title": "Silver chloride precipitation",
            "chapter_id": "CH13",
            "metadata": {"video_candidates": ["Observation point"]},
        }

    def get_learning_card(self, experiment_id: str) -> dict[str, Any] | None:
        return None

    def get_question(self, question_id: str) -> dict[str, Any] | None:
        return None

    def related_chunks_for_kp(self, kp_id: str, limit: int = 8) -> list[dict[str, Any]]:
        return self.source_chunk_items[:limit]

    def point_question_evidence(self, experiment_id: str, point_key: str, limit: int = 12) -> list[dict[str, Any]]:
        return []

    def point_reviewed_evidence(self, experiment_id: str, point_key: str) -> dict[str, Any] | None:
        return self.reviewed_evidence


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


def _repositories(content: _ContentRepository) -> RepositoryProvider:
    return RepositoryProvider(
        content=content,
        learning=_LearningRepository(),
        review=_ReviewRepository(),
        media=EmptyMediaRepository(),
        agent_logs=NoopAgentLogRepository(),
    )


def _settings() -> Settings:
    return Settings(agent_llm_provider="disabled", rag_query_generation_enabled=False)


def _policy() -> AgentPolicy:
    return AgentPolicy(source_path=None, source_excerpt="", course_scope=(), max_answer_chars=20000)


def test_run_agent_uses_fixed_point_evidence_before_supplemental_rag():
    content = _ContentRepository(
        source_chunk_items=[
            {
                "chunk_id": "experiment-chunk",
                "source_file": "experiment.md",
                "text": "Silver chloride precipitate forms as a white solid.",
                "metadata": {"content_type": "text", "caption": "Experiment evidence"},
            },
            {
                "chunk_id": "theory-chunk",
                "source_file": "theory.md",
                "text": "Halide precipitation reflects solubility product differences.",
                "metadata": {"content_type": "text", "caption": "Theory evidence"},
            },
        ],
        reviewed_evidence={
            "manual_reviewed": True,
            "review_grade": "A",
            "source_label": "manual fixture",
            "experiment_chunk_ids": ["experiment-chunk"],
            "theory_chunk_ids": ["theory-chunk"],
        },
    )
    request = AgentAskRequest(
        question="Explain the observation for this point.",
        chapter_id="CH13",
        experiment_id="EXP1",
        point_key="Observation point",
        allow_rag_lookup=False,
    )

    response = asyncio.run(run_agent(request, repositories=_repositories(content), settings=_settings(), policy=_policy()))

    assert response.mode == "point_context_local"
    assert "Silver chloride precipitate" in response.answer
    assert [source.chunk_id for source in response.sources] == ["experiment-chunk", "theory-chunk"]
    assert response.rag_trace["point_context"]["manual_reviewed"] is True
    assert response.rag_trace["point_context"]["source_count"] == 2
    assert any(item["code"] == "point_context_fixed" for item in response.guardrail_decisions)


def test_run_agent_uses_catalog_node_static_evidence_before_supplemental_rag(monkeypatch):
    content = _ContentRepository(
        source_chunk_items=[
            {
                "chunk_id": "catalog-chunk",
                "source_file": "catalog-source.md",
                "text": "Catalog-node evidence explains chlorine water bleaching dyed solution.",
                "metadata": {"content_type": "text"},
            }
        ],
    )
    monkeypatch.setattr(
        evidence_module,
        "catalog_point_static_evidence_package",
        lambda point_node_id: {
            "enabled": True,
            "evidence_source": "catalog_node_static_evidence",
            "static_evidence_role": "fallback_or_supplemental",
            "point_node_id": point_node_id,
            "point_title": "Chlorine bleaching",
            "catalog_path": ["Chapter", "Chlorine"],
            "chunk_ids": ["catalog-chunk"],
            "chunk_roles": {"catalog-chunk": "fallback"},
            "static_fallback_missing": False,
            "static_evidence_status": "available_static_fallback",
            "source_count": 1,
            "bindings": [{"chunk_id": "catalog-chunk", "evidence_role": "fallback", "freshness_status": "fresh"}],
            "dynamic_rag_available": True,
        },
    )
    request = AgentAskRequest(
        question="Explain this point.",
        chapter_id="CH13",
        point_node_id="cat-point-bleaching",
        allow_rag_lookup=False,
    )

    response = asyncio.run(run_agent(request, repositories=_repositories(content), settings=_settings(), policy=_policy()))

    assert response.mode == "point_context_local"
    assert "chlorine water bleaching" in response.answer
    point_context = response.rag_trace["point_context"]
    assert point_context["evidence_source"] == "catalog_node_static_evidence"
    assert point_context["static_evidence_role"] == "fallback_or_supplemental"
    assert point_context["sources"][0]["source_boundary"] == "catalog_node_static_evidence"
    assert point_context["sources"][0]["evidence_kind"] == "fallback"
    assert any(item["code"] == "catalog_node_static_evidence_loaded" for item in response.guardrail_decisions)


def test_run_agent_marks_missing_catalog_node_static_evidence_as_dynamic_rag_eligible(monkeypatch):
    monkeypatch.setattr(
        evidence_module,
        "catalog_point_static_evidence_package",
        lambda point_node_id: {
            "enabled": True,
            "evidence_source": "catalog_node_static_evidence",
            "static_evidence_role": "fallback_or_supplemental",
            "point_node_id": point_node_id,
            "chunk_ids": [],
            "chunk_roles": {},
            "static_fallback_missing": True,
            "static_evidence_status": "missing_fallback_evidence",
            "source_count": 0,
            "bindings": [],
            "dynamic_rag_available": True,
        },
    )
    request = AgentAskRequest(
        question="Explain this new point.",
        chapter_id="CH13",
        point_node_id="cat-point-new",
        allow_rag_lookup=True,
    )

    response = asyncio.run(run_agent(request, repositories=_repositories(_ContentRepository()), settings=_settings(), policy=_policy()))

    point_context = response.rag_trace["point_context"]
    assert point_context["evidence_source"] == "catalog_node_static_evidence"
    assert point_context["static_fallback_missing"] is True
    assert point_context["supplemental_dynamic_rag_allowed"] is True
    assert any(item["code"] == "catalog_node_static_evidence_missing" for item in response.guardrail_decisions)


def test_run_agent_respects_disabled_rag_and_uses_curriculum_context():
    content = _ContentRepository()
    request = AgentAskRequest(
        question="Explain the oxidation trend.",
        chapter_id="CH13",
        allow_rag_lookup=False,
    )

    response = asyncio.run(run_agent(request, repositories=_repositories(content), settings=_settings(), policy=_policy()))

    assert response.mode == "local"
    assert "Oxidation trend" in response.answer
    assert [call["name"] for call in response.tool_calls] == ["curriculum_lookup"]
    assert not response.sources
    assert any(item["code"] == "rag_lookup_disabled" for item in response.guardrail_decisions)


def test_retrieval_helpers_preserve_request_shape_and_disabled_query_fallback():
    content = _ContentRepository(
        source_chunk_items=[
            {
                "chunk_id": "low",
                "chapter_id": "CH13",
                "text": "Unrelated halogen note.",
            },
            {
                "chunk_id": "high",
                "chapter_id": "CH13",
                "text": "Oxidation trend oxidation trend chlorine bromine iodine.",
            },
        ]
    )
    repositories = _repositories(content)
    request = AgentAskRequest(
        student_id="S1",
        question="oxidation trend chlorine",
        chapter_id="CH13",
        knowledge_point_ids=["KP1"],
    )

    rag_request = agent_to_rag_request(request)
    round_trip = rag_to_agent_request(rag_request)
    retrieved = retrieve_context(repositories, request.question, request, limit=1)
    queries, trace = asyncio.run(
        generate_retrieval_queries(
            type("Context", (), {"request": request})(),
            Settings(agent_llm_provider="disabled", rag_query_generation_enabled=False),
            request.question,
        )
    )

    assert round_trip.question == request.question
    assert round_trip.chapter_id == request.chapter_id
    assert round_trip.knowledge_point_ids == request.knowledge_point_ids
    assert [item["chunk_id"] for item in retrieved] == ["high"]
    assert queries == [request.question]
    assert trace == {"status": "skipped", "reason": "disabled", "provider": "disabled"}

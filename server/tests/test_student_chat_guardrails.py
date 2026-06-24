from __future__ import annotations

import asyncio

import server.app.domains.assistant.agent as agent_module
from server.app.domains.assistant.agent import (
    AgentPolicy,
    AgentRunContext,
    StudentAIPolicyDecision,
    _apply_policy_decision_to_classification,
    classify_agent_request,
    run_agent,
)
from server.app.infrastructure.settings import Settings
from server.app.repositories import EmptyMediaRepository, NoopAgentLogRepository, RepositoryProvider, get_repositories
from server.app.schemas import AgentAskRequest, AgentChatMessage
from server.app.schemas import RagSource, RagSourceAsset


class _FakeContentRepository:
    point_title = "Observe permanganate color change"
    point_key = agent_module._candidate_point_key(0, point_title)

    def areas(self):
        return []

    def chapters(self):
        return [{"chapter_id": "CH13", "chapter_title": "Chapter 13"}]

    def units(self):
        return []

    def knowledge_points(self):
        return [{"knowledge_point_id": "KP_TEST", "chapter_id": "CH13", "content": "Permanganate oxidation state changes"}]

    def experiments(self):
        return [self.get_experiment("EXP_TEST")]

    def learning_cards(self):
        return []

    def questions(self):
        return []

    def links(self):
        return []

    def source_chunks(self):
        return [
            {
                "chunk_id": "chunk-point-1",
                "source_file": "test-source.md",
                "page_number": 12,
                "text": "Permanganate color fading is evidence that Mn(VII) is reduced while oxidizing the substrate.",
                "metadata": {"content_type": "text", "section_path": ["Experiment", "Permanganate"]},
            },
            {
                "chunk_id": "chunk-theory-1",
                "source_file": "test-source.md",
                "page_number": 13,
                "text": "High oxidation-state manganese species are strong oxidants and are reduced in redox reactions.",
                "metadata": {"content_type": "text", "section_path": ["Theory", "Redox"]},
            }
        ]

    def get_chapter(self, chapter_id):
        return {"chapter_id": chapter_id, "chapter_title": "Chapter 13"} if chapter_id == "CH13" else None

    def get_unit(self, unit_id):
        return None

    def get_knowledge_point(self, kp_id):
        return None

    def get_experiment(self, experiment_id):
        if experiment_id != "EXP_TEST":
            return None
        return {
            "id": "EXP_TEST",
            "experiment_id": "EXP_TEST",
            "code": "T-1",
            "title": "Permanganate test",
            "chapter_id": "CH13",
            "video_candidates": [self.point_title],
        }

    def get_learning_card(self, experiment_id):
        return None

    def get_question(self, question_id):
        return None

    def related_chunks_for_kp(self, kp_id, limit=8):
        return []

    def point_question_evidence(self, experiment_id, point_key, limit=12):
        raise AssertionError("student assistant point evidence must not query question-bank source_audit")

    def point_reviewed_evidence(self, experiment_id, point_key):
        if experiment_id != "EXP_TEST" or point_key != self.point_key:
            return None
        return {
            "experiment_id": experiment_id,
            "point_key": point_key,
            "point_title": self.point_title,
            "experiment_chunk_ids": ["chunk-point-1"],
            "theory_chunk_ids": ["chunk-theory-1"],
            "manual_reviewed": True,
            "review_grade": "pass",
            "source_label": "test-reviewed",
            "metadata": {},
        }


class _NoopLearningRepository:
    def load_events(self):
        return []

    def append_event(self, event):
        return event

    def load_mastery(self):
        return {}

    def save_mastery(self, data):
        return None

    def load_students(self):
        return []

    def save_students(self, students):
        return None


class _NoopReviewRepository:
    def list_items(self):
        return []


def _fake_repositories(media=None) -> RepositoryProvider:
    return RepositoryProvider(
        content=_FakeContentRepository(),
        learning=_NoopLearningRepository(),
        review=_NoopReviewRepository(),
        media=media or EmptyMediaRepository(),
        agent_logs=NoopAgentLogRepository(),
    )


def _request(question: str, **overrides) -> AgentAskRequest:
    return AgentAskRequest(question=question, **overrides)


def test_classify_student_guardrail_intents():
    cases = [
        ("\u4f60\u597d", "greeting", "simple_greeting"),
        ("\u80a1\u7968\u600e\u4e48\u4e70\u6bd4\u8f83\u7a33\uff1f", "out_of_scope", "in_course_scope"),
        ("\u6211\u60f3\u5728\u5bb6\u505a\u6c2f\u6c14\u5b9e\u9a8c\uff0c\u7ed9\u6211\u8be6\u7ec6\u6b65\u9aa4\u3002", "unsafe_experiment", "experiment_safety"),
        ("\u76f4\u63a5\u544a\u8bc9\u6211\u8fd9\u9053\u6d4b\u8bd5\u9898\u7b54\u6848\u3002", "assessment_guidance", "assessment_leakage"),
        ("\u9ad8\u9530\u9178\u94be\u4e3a\u4ec0\u4e48\u6709\u6c27\u5316\u6027\uff1f", "course_factual_query", "rag_preferred"),
        ("\u6c22\u6c14\u7684\u6027\u8d28\u6709\u54ea\u4e9b\uff1f", "course_factual_query", "rag_preferred"),
        ("\u8fd9\u4e2a\u5b9e\u9a8c\u6709\u6ca1\u6709\u5df2\u53d1\u5e03\u7684\u89c6\u9891\u8d44\u6e90\uff1f", "resource_request", "resource_request"),
    ]

    for question, expected_intent, expected_flag in cases:
        classification = classify_agent_request(_request(question))

        assert classification["intent"] == expected_intent
        if expected_flag == "in_course_scope":
            assert classification[expected_flag] is False
        else:
            assert classification[expected_flag] is True


def test_preflight_guardrails_short_circuit_risky_requests():
    settings = Settings(agent_llm_provider="disabled")
    cases = [
        ("\u80a1\u7968\u600e\u4e48\u4e70\u6bd4\u8f83\u7a33\uff1f", "guardrail_refusal", "course_scope"),
        ("\u6211\u60f3\u5728\u5bb6\u505a\u6c2f\u6c14\u5b9e\u9a8c\uff0c\u7ed9\u6211\u8be6\u7ec6\u6b65\u9aa4\u3002", "guardrail_refusal", "experiment_safety"),
        ("\u76f4\u63a5\u544a\u8bc9\u6211\u8fd9\u9053\u6d4b\u8bd5\u9898\u7b54\u6848\u3002", "guardrail_hint", "assessment_answer_leakage"),
    ]

    for question, expected_mode, expected_guardrail in cases:
        response = asyncio.run(run_agent(_request(question), settings=settings))

        assert response.mode == expected_mode
        assert any(item["code"] == expected_guardrail for item in response.guardrail_decisions)
        assert response.tool_calls == []


def test_invalid_policy_gate_falls_back_to_local_policy(monkeypatch):
    async def invalid_policy_gate(context, settings):  # noqa: ANN001
        return StudentAIPolicyDecision(
            mode="normal_answer",
            reason="not valid structured output",
            valid=False,
            raw={"content": "not-json"},
        )

    monkeypatch.setattr(agent_module, "_run_openai_policy_gate", invalid_policy_gate)
    request = _request("\u80a1\u7968\u600e\u4e48\u4e70\u6bd4\u8f83\u7a33\uff1f")
    context = AgentRunContext(
        request=request,
        repositories=get_repositories(),
        policy=AgentPolicy(source_path=None, source_excerpt="", course_scope=()),
        classification=classify_agent_request(request),
    )

    decision = asyncio.run(
        agent_module._policy_gate_decision(
            context,
            Settings(agent_llm_provider="openai", agent_llm_api_key="test-key", agent_llm_model="test-model"),
        )
    )
    context.policy_decision = decision
    _apply_policy_decision_to_classification(context)
    agent_module._apply_retrieval_decision(context)

    assert decision.valid is True
    assert decision.mode == "refuse_out_of_scope"
    assert context.classification["intent"] == "refuse_out_of_scope"
    assert context.retrieval_decision.mode == "skip"
    assert context.retrieval_decision.source == "hard_rule"
    assert context.retrieval_decision.should_call_rag is False
    assert any(
        item["code"] == "policy_decision_invalid" and item["action"] == "continue_with_local_policy"
        for item in context.guardrail_decisions
    )


def test_agent_sdk_failure_uses_plain_llm_fallback_for_course_facts(monkeypatch):
    async def normal_policy_gate(context, settings):  # noqa: ANN001
        return StudentAIPolicyDecision(
            mode="normal_answer",
            reason="ordinary course fact",
            allowed_tools=("rag_search", "curriculum_lookup"),
        )

    async def failing_sdk(context, settings):  # noqa: ANN001
        raise RuntimeError("sdk unavailable")

    async def plain_chat(context, settings):  # noqa: ANN001
        context.mode = "openai_chat_fallback"
        return "\u9ad8\u9530\u9178\u94be\u4e2d\u9530\u5904\u4e8e+7\u4ef7\uff0c\u5bb9\u6613\u63a5\u53d7\u7535\u5b50\uff0c\u56e0\u6b64\u8868\u73b0\u5f3a\u6c27\u5316\u6027\u3002"

    monkeypatch.setattr(agent_module, "_run_openai_policy_gate", normal_policy_gate)
    monkeypatch.setattr(agent_module, "_run_openai_agents_sdk", failing_sdk)
    monkeypatch.setattr(agent_module, "_run_openai_chat_completion", plain_chat)

    response = asyncio.run(
        run_agent(
            _request("\u9ad8\u9530\u9178\u94be\u4e3a\u4ec0\u4e48\u6709\u6c27\u5316\u6027\uff1f", allow_rag_lookup=False),
            settings=Settings(agent_llm_provider="openai", agent_llm_api_key="test-key", agent_llm_model="test-model"),
        )
    )

    assert response.mode == "openai_chat_fallback"
    assert "\u9530\u5904\u4e8e+7\u4ef7" in response.answer
    assert response.classification["requires_evidence"] is False
    assert any(item["code"] == "agent_sdk_fallback" for item in response.guardrail_decisions)
    assert not any(item["code"] == "source_grounding" for item in response.guardrail_decisions)


def test_rag_disabled_point_request_uses_fixed_point_evidence():
    response = asyncio.run(
        run_agent(
            _request(
                "Please explain why this experiment point fades.",
                chapter_id="CH13",
                experiment_id="EXP_TEST",
                point_key=_FakeContentRepository.point_title,
                allow_rag_lookup=False,
            ),
            repositories=_fake_repositories(),
            settings=Settings(agent_llm_provider="disabled"),
        )
    )

    point_context = response.rag_trace["point_context"]
    assert response.mode == "point_context_local"
    assert response.classification["resource_request"] is False
    assert point_context["requested_point_key"] == _FakeContentRepository.point_title
    assert point_context["point_key"] == _FakeContentRepository.point_key
    assert point_context["resolved"] is True
    assert point_context["evidence_source"] == "manual_reviewed_point_evidence"
    assert point_context["manual_reviewed"] is True
    assert point_context["review_grade"] == "pass"
    assert "question_count" not in point_context
    assert point_context["experiment_chunk_ids"] == ["chunk-point-1"]
    assert point_context["theory_chunk_ids"] == ["chunk-theory-1"]
    assert point_context["experiment_source_count"] == 1
    assert point_context["theory_source_count"] == 1
    assert point_context["source_count"] == 2
    assert response.sources[0].chunk_id == "chunk-point-1"
    assert any(item["code"] == "point_context_fixed" for item in response.guardrail_decisions)
    assert not any(call["name"] == "rag_search" for call in response.tool_calls)


def test_resource_availability_miss_returns_unavailable_without_scope_refusal():
    response = asyncio.run(
        run_agent(
            _request(
                "\u8fd9\u4e2a\u5b9e\u9a8c\u6709\u6ca1\u6709\u5df2\u53d1\u5e03\u7684\u89c6\u9891\u8d44\u6e90\uff1f",
                chapter_id="CH13",
                experiment_id="EXP_TEST",
                allow_rag_lookup=False,
            ),
            repositories=_fake_repositories(),
            settings=Settings(agent_llm_provider="disabled"),
        )
    )

    assert response.mode == "local"
    assert response.classification["resource_request"] is True
    assert response.classification["in_course_scope"] is True
    retrieval = response.classification["retrieval_decision"]
    assert retrieval["mode"] == "resource_lookup"
    assert retrieval["source"] == "hard_rule"
    assert retrieval["strict_evidence"] is True
    assert retrieval["should_call_resource_lookup"] is True
    assert retrieval["should_call_rag"] is False
    assert any(call["name"] == "published_resource_lookup" and call["result_count"] == 0 for call in response.tool_calls)
    assert any(item["code"] == "no_fabricated_resource" for item in response.guardrail_decisions)
    assert not any(item["code"] == "course_scope" for item in response.guardrail_decisions)
    assert response.answer


def test_ordinary_explanation_skips_dynamic_rag_when_rag_is_enabled(monkeypatch):
    def forbidden_rag_search(_context, _query):  # noqa: ANN001
        raise AssertionError("ordinary explanations must not call dynamic RAG by default")

    monkeypatch.setattr(agent_module, "rag_search_tool", forbidden_rag_search)

    response = asyncio.run(
        run_agent(
            _request("\u9ad8\u9530\u9178\u94be\u4e3a\u4ec0\u4e48\u6709\u5f3a\u6c27\u5316\u6027\uff1f", allow_rag_lookup=True),
            repositories=_fake_repositories(),
            settings=Settings(agent_llm_provider="disabled"),
        )
    )

    retrieval = response.classification["retrieval_decision"]
    assert response.answer
    assert retrieval["mode"] == "skip"
    assert retrieval["source"] == "local_fallback"
    assert retrieval["should_call_rag"] is False
    assert retrieval["should_call_resource_lookup"] is False
    assert not any(call["name"] == "rag_search" for call in response.tool_calls)


def test_llm_over_retrieval_for_ordinary_explanation_is_forced_to_skip(monkeypatch):
    async def over_eager_policy_gate(context, settings):  # noqa: ANN001
        return StudentAIPolicyDecision(
            mode="normal_answer",
            reason="over-eager router wanted textbook evidence",
            allowed_tools=("rag_search", "curriculum_lookup"),
            retrieval_mode="dynamic_rag",
            retrieval_reason="model guessed course evidence may help",
            retrieval_confidence=0.91,
        )

    def forbidden_rag_search(_context, _query):  # noqa: ANN001
        raise AssertionError("ordinary explanation must override over-eager dynamic RAG")

    monkeypatch.setattr(agent_module, "_policy_gate_decision", over_eager_policy_gate)
    monkeypatch.setattr(agent_module, "rag_search_tool", forbidden_rag_search)

    response = asyncio.run(
        run_agent(
            _request("\u5982\u4f55\u7528\u5409\u5e03\u65af\u81ea\u7531\u80fd\u89e3\u91ca\u6c27\u5316\u6027\uff1f", allow_rag_lookup=True),
            repositories=_fake_repositories(),
            settings=Settings(agent_llm_provider="openai", agent_llm_api_key="test-key", agent_llm_model="test-model"),
        )
    )

    retrieval = response.classification["retrieval_decision"]
    assert response.answer
    assert response.sources == []
    assert retrieval["mode"] == "skip"
    assert retrieval["source"] == "hard_rule"
    assert retrieval["override_reason"] == "deterministic_ordinary_learning_skip"
    assert retrieval["should_call_rag"] is False
    assert not any(call["name"] == "rag_search" for call in response.tool_calls)


def test_rag_disabled_ordinary_question_answers_without_dynamic_rag(monkeypatch):
    def forbidden_rag_search(_context, _query):  # noqa: ANN001
        raise AssertionError("RAG-disabled turns must not call dynamic RAG")

    monkeypatch.setattr(agent_module, "rag_search_tool", forbidden_rag_search)

    response = asyncio.run(
        run_agent(
            _request("\u8bf7\u89e3\u91ca\u6c27\u5316\u6001\u548c\u6c27\u5316\u6027\u7684\u5173\u7cfb\u3002", allow_rag_lookup=False),
            repositories=_fake_repositories(),
            settings=Settings(agent_llm_provider="disabled"),
        )
    )

    retrieval = response.classification["retrieval_decision"]
    assert response.answer
    assert retrieval["mode"] == "skip"
    assert retrieval["should_call_rag"] is False
    assert not any(call["name"] == "rag_search" for call in response.tool_calls)


def test_explicit_course_evidence_request_requires_evidence_and_fails_closed(monkeypatch):
    rag_queries: list[str] = []

    def empty_rag_search(context, query):  # noqa: ANN001
        rag_queries.append(query)
        result = {"evidence": [], "queries": [query]}
        context.record_tool("rag_search", {"query": query}, result)
        return result

    monkeypatch.setattr(agent_module, "rag_search_tool", empty_rag_search)

    response = asyncio.run(
        run_agent(
            _request(
                "\u8bf7\u5f15\u7528\u8bfe\u672c\u8d44\u6599\u8bf4\u660e\u9ad8\u9530\u9178\u94be\u7684\u6c27\u5316\u6027\u3002",
                allow_rag_lookup=True,
            ),
            repositories=_fake_repositories(),
            settings=Settings(agent_llm_provider="disabled"),
        )
    )

    retrieval = response.classification["retrieval_decision"]
    assert rag_queries
    assert retrieval["mode"] == "strict_evidence"
    assert retrieval["source"] == "hard_rule"
    assert retrieval["strict_evidence"] is True
    assert retrieval["should_call_rag"] is True
    assert response.sources == []
    assert any(call["name"] == "rag_search" and call["result_count"] == 0 for call in response.tool_calls)
    assert any(item["code"] in {"missing_evidence", "source_grounding"} for item in response.guardrail_decisions)


def test_policy_resource_false_positive_does_not_override_point_explanation(monkeypatch):
    async def false_positive_policy_gate(context, settings):  # noqa: ANN001
        return StudentAIPolicyDecision(
            mode="needs_platform_evidence",
            reason="mistook video point explanation for platform resource availability",
            evidence_required=True,
            allowed_tools=("published_resource_lookup", "rag_search", "curriculum_lookup"),
        )

    monkeypatch.setattr(agent_module, "_policy_gate_decision", false_positive_policy_gate)

    response = asyncio.run(
        run_agent(
            _request(
                "I am viewing EXP_19_1_01 chlorine bromine iodine displacement, "
                "please use the experiment evidence to explain what to observe and why.",
                chapter_id="CH13",
                allow_rag_lookup=False,
            ),
            repositories=_fake_repositories(),
            settings=Settings(agent_llm_provider="disabled"),
        )
    )

    assert response.classification["policy_decision_mode"] == "normal_answer"
    assert response.classification["resource_request"] is False
    assert response.classification["requires_evidence"] is True
    assert response.classification["retrieval_decision"]["mode"] == "strict_evidence"
    assert not any(call["name"] == "published_resource_lookup" for call in response.tool_calls)
    assert any(item["code"] == "policy_resource_veto" for item in response.guardrail_decisions)
    assert not any(item["code"] == "no_fabricated_resource" for item in response.guardrail_decisions)


def test_short_follow_up_policy_question_includes_recent_context():
    request = _request(
        "Why?",
        chapter_id="CH13",
        experiment_id="EXP_TEST",
        conversation_history=[
            AgentChatMessage(role="user", content="Why is potassium permanganate oxidizing?"),
            AgentChatMessage(role="assistant", content="Because manganese is in a high oxidation state and can accept electrons."),
        ],
    )
    context = AgentRunContext(
        request=request,
        repositories=_fake_repositories(),
        policy=AgentPolicy(source_path=None, source_excerpt="", course_scope=()),
        classification=classify_agent_request(request),
    )

    resolved = agent_module._resolved_policy_question(context)

    assert "Why?" in resolved
    assert "Why is potassium permanganate oxidizing?" in resolved
    assert "high oxidation state" in resolved

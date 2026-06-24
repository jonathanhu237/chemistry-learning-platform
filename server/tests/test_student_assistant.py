from __future__ import annotations

import asyncio
from types import SimpleNamespace

from server.app.domains.assistant import student_assistant as student_assistant_module
from server.app.domains.assistant.agent import classify_agent_request
from server.app.domains.assistant.student_assistant import _agent_request_for_chat, _sanitize_followup_prompts
from server.app.schemas import AgentAskRequest, AgentChatMessage
from server.app.student_assistant_schemas import StudentAssistantAskRequest
from server.tests.route_helpers import assert_route


def test_student_assistant_routes_are_registered() -> None:
    assert_route("/api/student/assistant/ask/stream", "POST")
    assert_route("/api/student/assistant/posttest-summary", "POST")
    assert_route("/api/student/assistant/posttest-mistakes", "POST")


def test_student_assistant_chat_forwards_catalog_context_to_agent_request() -> None:
    request = _agent_request_for_chat(
        SimpleNamespace(student_id="s-1", username="student-1", id="user-1"),
        StudentAssistantAskRequest(
            question="Why does the organic layer turn orange?",
            context_type="learning_point",
            context_title="Orange layer observation",
            context_summary="Chlorine displaces bromide.",
            chapter_id="CH17",
            point_key="legacy-point",
            point_node_id="cat-point-halogen",
            source_node_id="cat-source-halogen",
            catalog_path=["Halogen displacement catalog", "Orange layer observation"],
            conversation_history=[AgentChatMessage(role="user", content="Previous question")],
        ),
        allow_rag_lookup=True,
    )

    assert request.point_key == "legacy-point"
    assert request.point_node_id == "cat-point-halogen"
    assert request.source_node_id == "cat-source-halogen"
    assert request.catalog_path == ["Halogen displacement catalog", "Orange layer observation"]
    assert request.conversation_history == [AgentChatMessage(role="user", content="Previous question")]


async def _collect_student_stream(payload: StudentAssistantAskRequest) -> list[dict]:
    user = SimpleNamespace(student_id="s-1", username="student-1", id="user-1")
    return [item async for item in student_assistant_module.stream_student_assistant_answer(user, payload)]


def test_student_assistant_stream_attaches_suggested_prompts(monkeypatch) -> None:
    payload = StudentAssistantAskRequest(
        question="Why does the organic layer turn orange?",
        context_type="learning_point",
        context_title="Orange layer observation",
        context_summary="Chlorine displaces bromide.",
        conversation_history=[AgentChatMessage(role="assistant", content="It is a displacement reaction.")],
    )
    settings = SimpleNamespace(agent_llm_provider="openai", agent_llm_api_key="test-key", agent_llm_model="test-model", agent_llm_base_url=None)

    async def fake_stream(_request, settings=None):
        yield {"event": "delta", "delta": "Bromide is oxidized."}
        yield {"event": "final", "response": {"answer": "Bromide is oxidized.", "mode": "openai_chat_stream"}}

    async def fake_suggestions(suggestion_payload, answer, suggestion_settings):
        assert suggestion_payload.question == payload.question
        assert suggestion_payload.conversation_history == payload.conversation_history
        assert answer == "Bromide is oxidized."
        assert suggestion_settings is settings
        return ["这个现象如何判断？", "相关反应式是什么？"]

    monkeypatch.setattr(student_assistant_module, "_ai_enabled", lambda: (True, True))
    monkeypatch.setattr(student_assistant_module, "get_settings", lambda: settings)
    monkeypatch.setattr(student_assistant_module, "effective_ai_settings", lambda _settings: settings)
    monkeypatch.setattr(student_assistant_module, "run_agent_stream", fake_stream)
    monkeypatch.setattr(student_assistant_module, "_generate_followup_prompts", fake_suggestions)

    events = asyncio.run(_collect_student_stream(payload))

    assert events[-1]["event"] == "final"
    assert events[-1]["response"]["suggested_prompts"] == ["这个现象如何判断？", "相关反应式是什么？"]


def test_student_assistant_stream_keeps_final_when_suggestion_generation_fails(monkeypatch) -> None:
    payload = StudentAssistantAskRequest(
        question="Explain the color change.",
        context_type="learning_home",
        context_title="Home",
        context_summary="",
    )
    settings = SimpleNamespace(agent_llm_provider="openai", agent_llm_api_key="test-key", agent_llm_model="test-model", agent_llm_base_url=None)

    async def fake_stream(_request, settings=None):
        yield {"event": "final", "response": {"answer": "The color comes from bromine.", "mode": "openai_chat_stream"}}

    async def failing_suggestions(_payload, _answer, _settings):
        raise RuntimeError("suggestion model unavailable")

    monkeypatch.setattr(student_assistant_module, "_ai_enabled", lambda: (True, True))
    monkeypatch.setattr(student_assistant_module, "get_settings", lambda: settings)
    monkeypatch.setattr(student_assistant_module, "effective_ai_settings", lambda _settings: settings)
    monkeypatch.setattr(student_assistant_module, "run_agent_stream", fake_stream)
    monkeypatch.setattr(student_assistant_module, "_generate_followup_prompts", failing_suggestions)

    events = asyncio.run(_collect_student_stream(payload))

    assert events == [
        {
            "event": "final",
            "response": {
                "answer": "The color comes from bromine.",
                "mode": "openai_chat_stream",
                "suggested_prompts": [],
            },
        }
    ]


def test_student_assistant_followup_sanitizer_filters_guardrails_and_allows_partial_results() -> None:
    result = _sanitize_followup_prompts(
        {
            "suggested_prompts": [
                " 1. 这个现象如何判断？ ",
                "这个现象如何判断？",
                "短？",
                "这是一条明显超过二十四个可见字符并且非常冗长的追问建议",
                42,
                "",
                "RAG trace 怎么看？",
                "请在家具体步骤怎么做？",
                "正确答案选哪个？",
                "想了解 Ellingham 图的判读方法？",
                "需要解析 Frost 图分析反应？",
                "要不要继续看方程式？",
                "Ellingham 图怎么判读？",
                "Frost 图怎么分析？",
                "相关反应式是什么？",
            ]
        }
    )

    assert result == ["这个现象如何判断？", "Ellingham 图怎么判读？", "Frost 图怎么分析？", "相关反应式是什么？"]


def test_student_assistant_followup_prompt_locks_student_question_voice() -> None:
    prompt = student_assistant_module._FOLLOWUP_SYSTEM_PROMPT

    assert "sent verbatim as the student's next message" in prompt
    assert "written in the student's voice" in prompt
    assert "Ellingham图怎么判读？" in prompt
    assert "想了解...？" in prompt
    assert "需要解析...？" in prompt


def test_posttest_review_context_allows_submitted_answer_explanation() -> None:
    classification = classify_agent_request(
        AgentAskRequest(
            question="请解释我这道课后测试题为什么选错了，参考答案是什么思路。",
            assessment_review=True,
        )
    )

    assert classification["assessment_leakage"] is False
    assert classification["intent"] == "course_factual_query"


def test_live_assessment_answer_request_still_gets_guarded() -> None:
    classification = classify_agent_request(
        AgentAskRequest(
            question="直接告诉我这道测试题答案选哪个。",
            assessment_review=False,
        )
    )

    assert classification["assessment_leakage"] is True
    assert classification["intent"] == "assessment_guidance"

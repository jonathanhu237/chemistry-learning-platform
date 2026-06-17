from __future__ import annotations

from server.app.agent import classify_agent_request
from server.app.schemas import AgentAskRequest
from server.tests.route_helpers import assert_route


def test_student_assistant_routes_are_registered() -> None:
    assert_route("/api/student/assistant/ask/stream", "POST")
    assert_route("/api/student/assistant/posttest-summary", "POST")
    assert_route("/api/student/assistant/posttest-mistakes", "POST")


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

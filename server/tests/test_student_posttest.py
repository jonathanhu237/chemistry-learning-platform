from __future__ import annotations

from fastapi import HTTPException

from server.app.services.student_posttest_service import (
    PosttestQuestionCandidate,
    _balanced_posttest_sample,
    _public_question,
    _validate_submitted_answers,
)
from server.app.student_posttest_schemas import StudentPosttestSubmitRequest
from server.tests.route_helpers import assert_route


def _candidate(question_id: str, *, experiment_id: str) -> PosttestQuestionCandidate:
    return PosttestQuestionCandidate(
        id=question_id,
        experiment_id=experiment_id,
        experiment_title=f"Experiment {experiment_id}",
        question_type="single_choice",
        stem=f"Question {question_id}",
        options=[{"label": "A", "text": "A"}, {"label": "B", "text": "B"}],
        answer={"value": "A"},
        explanation="Because A",
        difficulty="basic",
        related_chapter_ids=["CH13"],
        related_knowledge_point_ids=[f"kp_{question_id}"],
    )


def test_student_posttest_routes_are_registered() -> None:
    assert_route("/api/student/posttest/start", "POST")
    assert_route("/api/student/posttest/submit", "POST")


def test_public_posttest_question_does_not_expose_answer_or_explanation() -> None:
    public = _public_question(_candidate("q1", experiment_id="EXP_19_1"))
    payload = public.model_dump()

    assert "answer" not in payload
    assert "explanation" not in payload
    assert payload["experiment_id"] == "EXP_19_1"


def test_posttest_sample_balances_across_learned_experiments() -> None:
    candidates = [
        _candidate("q1", experiment_id="EXP_19_1"),
        _candidate("q2", experiment_id="EXP_19_1"),
        _candidate("q3", experiment_id="EXP_19_1"),
        _candidate("q4", experiment_id="EXP_20_2"),
        _candidate("q5", experiment_id="EXP_20_2"),
    ]

    selected = _balanced_posttest_sample(
        candidates,
        experiment_ids=["EXP_19_1", "EXP_20_2"],
        student_id="20240001",
        count=4,
    )

    assert len(selected) == 4
    assert [item.experiment_id for item in selected].count("EXP_19_1") == 2
    assert [item.experiment_id for item in selected].count("EXP_20_2") == 2


def test_posttest_answers_must_match_session_questions() -> None:
    payload = StudentPosttestSubmitRequest(
        session_id="00000000-0000-0000-0000-000000000001",
        answers=[
            {"question_id": "q1", "answer": "A"},
            {"question_id": "q1", "answer": "B"},
        ],
    )

    try:
        _validate_submitted_answers(["q1", "q2"], payload)
    except HTTPException as exc:
        assert exc.status_code == 400
    else:
        raise AssertionError("duplicate question ids should be rejected")

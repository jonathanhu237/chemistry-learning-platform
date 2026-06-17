from __future__ import annotations

from fastapi import HTTPException

from server.app.services.student_pretest_service import (
    QuestionCandidate,
    _public_question,
    _select_stage1_questions,
    _select_stage2_questions,
    _validate_submitted_answers,
    _weakest_area,
)
from server.app.student_pretest_schemas import StudentPretestSubmitRequest
from server.tests.route_helpers import assert_route


def _candidate(
    question_id: str,
    *,
    area: str,
    chapter_id: str = "ch_13",
    experiment_id: str = "EXP_19_1_01",
    parent_code: str = "19-1",
    kp_id: str | None = None,
) -> QuestionCandidate:
    return QuestionCandidate(
        id=question_id,
        experiment_id=experiment_id,
        question_type="single_choice",
        stem=f"Question {question_id}",
        options=[{"label": "A", "text": "A"}, {"label": "B", "text": "B"}],
        answer={"value": "A"},
        difficulty="basic",
        parent_code=parent_code,
        display_order=1,
        related_chapter_ids=[chapter_id],
        related_knowledge_point_ids=[kp_id or f"kp_{question_id}"],
        areas=(area,),
    )


def test_student_pretest_routes_are_registered() -> None:
    assert_route("/api/student/pretest/start", "POST")
    assert_route("/api/student/pretest/submit", "POST")


def test_public_pretest_question_does_not_expose_answer_or_explanation() -> None:
    public = _public_question(_candidate("00000000-0000-0000-0000-000000000001", area="p区"))
    payload = public.model_dump()

    assert "answer" not in payload
    assert "explanation" not in payload
    assert payload["area"] == "p区"


def test_stage1_selects_two_per_available_area_and_records_underfilled() -> None:
    candidates = [
        _candidate("00000000-0000-0000-0000-000000000001", area="s区"),
        _candidate("00000000-0000-0000-0000-000000000002", area="p区"),
        _candidate("00000000-0000-0000-0000-000000000003", area="p区"),
        _candidate("00000000-0000-0000-0000-000000000004", area="p区"),
        _candidate("00000000-0000-0000-0000-000000000005", area="d区"),
        _candidate("00000000-0000-0000-0000-000000000006", area="d区"),
    ]

    selected, area_map, warnings = _select_stage1_questions(candidates, student_id="20240001")

    assert len(selected) == 5
    assert list(area_map.values()).count("p区") == 2
    assert list(area_map.values()).count("d区") == 2
    assert warnings["underfilled_areas"] == {"s区": 1}
    assert warnings["missing_areas"] == ["ds区", "f区"]


def test_weakest_area_uses_demo_tie_breaking_priority() -> None:
    assert _weakest_area({"s区": 0, "p区": 0, "d区": 0.5, "ds区": None, "f区": None}) == "p区"
    assert _weakest_area({"s区": 0.5, "p区": 1, "d区": 0.5, "ds区": 0.5, "f区": 0.5}) == "d区"


def test_stage2_balances_questions_per_experiment_in_weak_area() -> None:
    candidates: list[QuestionCandidate] = []
    for exp_index, chapter_id in enumerate(["ch_13", "ch_14", "ch_15", "ch_16", "ch_17"], start=1):
        for index in range(3):
            suffix = chapter_id.replace("ch_", "")
            candidates.append(
                _candidate(
                    f"00000000-0000-0000-0000-{suffix}{index:09d}",
                    area="p区",
                    chapter_id=chapter_id,
                    experiment_id=f"EXP_19_1_{exp_index:02d}",
                    kp_id=f"kp_{chapter_id}_{index}",
                )
            )

    selected, area_map, warnings = _select_stage2_questions(candidates, student_id="20240001", weakest_area="p区")
    selected_experiments = [item.experiment_id for item in selected]

    assert len(selected) == 10
    assert warnings == {}
    assert set(area_map.values()) == {"p区"}
    assert all(selected_experiments.count(f"EXP_19_1_{index:02d}") == 2 for index in range(1, 6))


def test_submitted_answers_reject_duplicate_question_ids() -> None:
    payload = StudentPretestSubmitRequest(
        stage=1,
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

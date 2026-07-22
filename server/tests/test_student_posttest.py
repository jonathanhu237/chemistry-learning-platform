from __future__ import annotations

import json
from types import SimpleNamespace

from server.app.domains.errors import DomainHTTPException
from server.app.domains.assessments import posttest as posttest_module
from server.app.domains.assessments.posttest import (
    PosttestQuestionCandidate,
    _balanced_posttest_sample,
    _candidate_from_question_snapshot,
    _insert_attempts,
    _load_locked_session_questions,
    _public_question,
    _question_snapshots,
    _session_experiment_summaries,
    _validate_submitted_answers,
)
from server.app.domains.assessments.student_experiment import _grade_answer
from server.app.domains.assessments.student_context import SMART_BASELINE_REQUIRED_DETAIL
from server.app.student_posttest_schemas import StudentPosttestResponse, StudentPosttestSubmitRequest
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
        primary_point_node_ids=[f"cat-point-{question_id}"],
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
    except DomainHTTPException as exc:
        assert exc.status_code == 400
    else:
        raise AssertionError("duplicate question ids should be rejected")


def test_posttest_resume_and_submit_keep_original_question_snapshot() -> None:
    original = _candidate("q1", experiment_id="EXP_19_1")
    row = {
        "question_ids": [original.id],
        "experiment_ids": [original.experiment_id],
        "metadata": {"question_snapshots": _question_snapshots([original])},
    }

    class NoDatabaseReadSession:
        def execute(self, *_args: object, **_kwargs: object) -> object:
            raise AssertionError("posttest snapshot must be used after source withdrawal")

    resumed = _load_locked_session_questions(
        NoDatabaseReadSession(),
        row,
        changed_detail="Posttest question bank has changed",
    )

    assert resumed[0].stem == original.stem
    assert resumed[0].answer == {"value": "A"}
    assert _grade_answer(resumed[0].question_type, resumed[0].answer, "A") is True


def test_question_snapshot_rejects_unknown_version_and_question_type() -> None:
    original = _candidate("q1", experiment_id="EXP_19_1")
    snapshot = _question_snapshots([original])[0]

    assert _candidate_from_question_snapshot(snapshot) == original

    future_snapshot = {**snapshot, "version": 2}
    invalid_type_snapshot = {**snapshot, "question_type": "unsupported"}

    assert _candidate_from_question_snapshot(future_snapshot) is None
    assert _candidate_from_question_snapshot(invalid_type_snapshot) is None


def test_session_experiment_summary_uses_snapshot_after_experiment_changes() -> None:
    summaries = _session_experiment_summaries(
        object(),
        {
            "experiment_ids": ["EXP_19_1"],
            "metadata": {
                "experiments": [
                    {
                        "id": "EXP_19_1",
                        "code": "19-1",
                        "title": "Original experiment title",
                        "parent_code": "19",
                        "parent_title": "Original chapter title",
                    }
                ]
            },
        },
    )

    assert len(summaries) == 1
    assert summaries[0].title == "Original experiment title"
    assert summaries[0].parent_title == "Original chapter title"


def test_legacy_open_posttest_can_load_its_locked_disabled_question_without_resampling() -> None:
    statements: list[str] = []

    class RowsResult:
        def mappings(self) -> "RowsResult":
            return self

        def __iter__(self):
            return iter(
                [
                    {
                        "id": "q1",
                        "experiment_id": "EXP_19_1",
                        "experiment_title": "Experiment EXP_19_1",
                        "question_type": "single_choice",
                        "stem": "Original disabled question",
                        "options": [{"label": "A", "text": "A"}, {"label": "B", "text": "B"}],
                        "answer": {"value": "A"},
                        "explanation": "Original explanation",
                        "difficulty": "basic",
                        "related_chapter_ids": ["CH13"],
                        "related_knowledge_point_ids": ["kp_q1"],
                        "primary_point_node_ids": ["cat-point-q1"],
                        "primary_canonical_point_ids": ["canon-q1"],
                        "source_placement_node_ids": ["cat-point-q1"],
                    }
                ]
            )

    class FakeSession:
        def execute(self, statement: object, params: dict[str, object]) -> RowsResult:
            statements.append(str(statement))
            assert params == {"question_ids": ["q1"]}
            return RowsResult()

    locked = _load_locked_session_questions(
        FakeSession(),
        {"question_ids": ["q1"], "experiment_ids": ["EXP_19_1"], "metadata": {}},
        changed_detail="Posttest question bank has changed",
    )

    assert [question.id for question in locked] == ["q1"]
    assert "q.status = 'published'" not in statements[0]


def test_posttest_attempt_metadata_keeps_snapshot_and_lineage() -> None:
    question = _candidate("q1", experiment_id="EXP_19_1")
    captured: list[dict[str, object]] = []

    class FakeSession:
        def execute(self, _statement: object, params: dict[str, object]) -> None:
            captured.append(params)

    graded = _insert_attempts(
        FakeSession(),
        student_id="20249999",
        class_id="CLS_1",
        posttest_session_id="session-1",
        questions=[question],
        answers={question.id: "A"},
    )
    metadata = json.loads(str(captured[0]["metadata"]))

    assert graded[0]["correct"] is True
    assert metadata["question_snapshot"]["answer"] == {"value": "A"}
    assert metadata["question_snapshot"]["primary_point_node_ids"] == ["cat-point-q1"]
    assert metadata["source_placement_node_ids"] == ["cat-point-q1"]


def test_posttest_start_resumes_open_session_even_after_setting_is_disabled(monkeypatch) -> None:
    response = StudentPosttestResponse(
        status="in_progress",
        session_id="open-posttest-session",
        experiments=[],
        questions=[],
    )

    class SessionContext:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, *_exc: object) -> bool:
            return False

    monkeypatch.setattr(
        posttest_module,
        "get_learning_behavior_settings",
        lambda: SimpleNamespace(assessment=SimpleNamespace(posttest_enabled=False)),
    )
    monkeypatch.setattr(posttest_module, "db_session", SessionContext)
    monkeypatch.setattr(
        posttest_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(posttest_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(posttest_module, "_require_completed_smart_baseline", lambda _session, _student_id: None)
    monkeypatch.setattr(
        posttest_module,
        "_load_open_session",
        lambda _session, _student_id: {"id": "open-posttest-session"},
    )
    monkeypatch.setattr(posttest_module, "_response_for_session", lambda _session, _row: response)

    result = posttest_module.start_student_posttest(SimpleNamespace(id="u1", role="student"))

    assert result.session_id == "open-posttest-session"


def test_posttest_start_cannot_bypass_required_smart_baseline(monkeypatch) -> None:
    class ScalarResult:
        def scalar_one_or_none(self) -> None:
            return None

    class NoBaselineSession:
        def execute(self, statement: object, params: dict[str, object] | None = None) -> ScalarResult:
            assert "assessment_mode = 'smart'" in str(statement)
            assert params == {"student_id": "20249999"}
            return ScalarResult()

    class SessionContext:
        def __enter__(self) -> NoBaselineSession:
            return NoBaselineSession()

        def __exit__(self, *_exc: object) -> bool:
            return False

    monkeypatch.setattr(
        posttest_module,
        "get_learning_behavior_settings",
        lambda: SimpleNamespace(assessment=SimpleNamespace(posttest_enabled=True)),
    )
    monkeypatch.setattr(posttest_module, "db_session", SessionContext)
    monkeypatch.setattr(
        posttest_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(posttest_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(
        posttest_module,
        "_load_open_session",
        lambda _session, _student_id: (_ for _ in ()).throw(AssertionError("baseline gate must run first")),
    )

    try:
        posttest_module.start_student_posttest(SimpleNamespace(id="u1", role="student"))
    except DomainHTTPException as exc:
        assert exc.status_code == 409
        assert exc.detail == SMART_BASELINE_REQUIRED_DETAIL
    else:
        raise AssertionError("posttest must require the completed smart baseline")

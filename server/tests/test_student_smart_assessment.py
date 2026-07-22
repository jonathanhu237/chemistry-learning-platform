from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from server.app.app_runtime.main import app
from server.app.domains.assessments.posttest import (
    PosttestQuestionCandidate,
    _load_locked_session_questions,
    _question_snapshots,
)
from server.app.domains.assessments import smart_assessment as smart_assessment_module
from server.app.domains.assessments.smart_assessment import (
    _build_class_smart_assessment_preview,
    _compose_custom_questions,
    _compose_point_questions,
    _compose_questions,
    _custom_settings_from_value,
    _draw_tickets,
    _point_ids_for_scope_nodes,
    _public_question,
    _scope_leaf_point_ids,
    _strategy_from_value,
    _validate_submitted_answers,
)
from server.app.domains.assessments.student_experiment import _grade_answer
from server.app.domains.assessments.student_context import SMART_BASELINE_REQUIRED_DETAIL
from server.app.domains.errors import DomainHTTPException
from server.app.domains.platform.settings import CustomAssessmentSettings, SmartAssessmentSettings
from server.app.student_smart_assessment_schemas import (
    CustomAssessmentScopeNode,
    SmartAssessmentCompositionSummary,
    StudentCustomAssessmentStartRequest,
    StudentPointAssessmentStartRequest,
    StudentSmartAssessmentReport,
    StudentSmartAssessmentResponse,
    StudentSmartAssessmentSubmitRequest,
)
from server.tests.route_helpers import assert_route


def _candidate(question_id: str, *, experiment_id: str, point_id: str | None = None) -> PosttestQuestionCandidate:
    point_id = point_id or f"point-{question_id}"
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
        primary_point_node_ids=[point_id],
        primary_canonical_point_ids=[f"canon-{question_id}"],
        source_placement_node_ids=[point_id],
    )


class _ScalarResult:
    def __init__(self, value: object = None):
        self.value = value

    def scalar_one_or_none(self) -> object:
        return self.value


class _FakeSessionContext:
    def __init__(self, session: object):
        self.session = session

    def __enter__(self) -> object:
        return self.session

    def __exit__(self, *_exc: object) -> bool:
        return False


def test_student_smart_assessment_routes_are_registered() -> None:
    assert_route("/api/student/assessment/status", "GET")
    assert "/api/student/assessment/baseline-prompt-dismiss" not in app.openapi()["paths"]
    assert_route("/api/student/smart-assessment/start", "POST")
    assert_route("/api/student/point-assessment/start", "POST")
    assert_route("/api/student/smart-assessment/submit", "POST")
    assert_route("/api/student/custom-assessment/options", "GET")
    assert_route("/api/student/custom-assessment/start", "POST")
    assert_route("/api/admin/classes/{class_id}/smart-assessment-strategy", "GET")
    assert_route("/api/admin/classes/{class_id}/smart-assessment-strategy", "PUT")
    assert_route("/api/admin/classes/{class_id}/smart-assessment-strategy", "DELETE")
    assert_route("/api/admin/classes/{class_id}/smart-assessment-preview", "GET")
    assert_route("/api/admin/classes/{class_id}/custom-assessment-settings", "GET")
    assert_route("/api/admin/classes/{class_id}/custom-assessment-settings", "PUT")
    assert_route("/api/admin/classes/{class_id}/custom-assessment-settings", "DELETE")


def test_public_smart_assessment_question_does_not_expose_answer_or_explanation() -> None:
    public = _public_question(_candidate("q1", experiment_id="EXP_19_1"))
    payload = public.model_dump()

    assert "answer" not in payload
    assert "explanation" not in payload
    assert payload["experiment_id"] == "EXP_19_1"


def test_custom_assessment_start_schema_accepts_only_nonempty_scope_and_exact_per_point_count() -> None:
    payload = StudentCustomAssessmentStartRequest(
        scope_node_ids=[" chapter:CH13 ", "point-a", "point-a"],
        questions_per_point=2,
    )

    assert payload.scope_node_ids == ["chapter:CH13", "point-a"]
    assert payload.questions_per_point == 2

    with pytest.raises(ValidationError):
        StudentCustomAssessmentStartRequest.model_validate(
            {"scope_node_ids": ["point-a"], "questions_per_point": 2, "question_count": 10}
        )
    with pytest.raises(ValidationError):
        StudentCustomAssessmentStartRequest.model_validate(
            {"scope_node_ids": ["point-a"], "questions_per_point": 4}
        )
    with pytest.raises(ValidationError):
        StudentCustomAssessmentStartRequest.model_validate(
            {"scope_node_ids": ["  "], "questions_per_point": 1}
        )


def test_custom_scope_expansion_recurses_and_deduplicates_overlapping_parents() -> None:
    point_a = CustomAssessmentScopeNode(id="point-a", title="A", kind="point", parent_id="dir-1", question_count=2)
    point_b = CustomAssessmentScopeNode(id="point-b", title="B", kind="point", parent_id="dir-1", question_count=1)
    directory = CustomAssessmentScopeNode(
        id="dir-1",
        title="Directory",
        kind="directory",
        parent_id="chapter:CH13",
        question_count=3,
        children=[point_a, point_b],
    )
    chapter = CustomAssessmentScopeNode(
        id="chapter:CH13",
        title="Chapter",
        kind="chapter",
        question_count=3,
        children=[directory],
    )

    assert _scope_leaf_point_ids(chapter) == ["point-a", "point-b"]
    selected, invalid = _point_ids_for_scope_nodes(
        [chapter],
        ["chapter:CH13", "dir-1", "point-a", "missing"],
    )

    assert selected == ["point-a", "point-b"]
    assert invalid == ["missing"]


def test_custom_scope_tree_contains_only_published_question_bearing_paths() -> None:
    statements: list[str] = []

    class RowsResult:
        def __init__(self, rows: list[dict[str, object]]) -> None:
            self.rows = rows

        def mappings(self) -> "RowsResult":
            return self

        def __iter__(self):
            return iter(self.rows)

    class FakeSession:
        def execute(self, statement: object, params: dict[str, object] | None = None) -> RowsResult:
            statements.append(str(statement))
            assert params == {"point_ids": ["point-a", "point-b"]}
            return RowsResult(
                [
                    {
                        "id": "dir-root",
                        "parent_id": None,
                        "node_kind": "directory",
                        "title": "Root",
                        "chapter_id": "CH13",
                        "display_order": 1,
                        "chapter_number": 13,
                        "chapter_title": "Chapter 13",
                    },
                    {
                        "id": "point-a",
                        "parent_id": "dir-root",
                        "node_kind": "point",
                        "title": "Point A",
                        "chapter_id": "CH13",
                        "display_order": 1,
                        "chapter_number": 13,
                        "chapter_title": "Chapter 13",
                    },
                    {
                        "id": "point-b",
                        "parent_id": "dir-root",
                        "node_kind": "point",
                        "title": "Point B",
                        "chapter_id": "CH13",
                        "display_order": 2,
                        "chapter_number": 13,
                        "chapter_title": "Chapter 13",
                    },
                ]
            )

    tree = smart_assessment_module._custom_scope_tree_from_candidates(
        FakeSession(),
        [
            _candidate("q-a", experiment_id="EXP_A", point_id="point-a"),
            _candidate("q-b", experiment_id="EXP_B", point_id="point-b"),
        ],
    )

    assert [node.id for node in tree] == ["chapter:CH13"]
    assert tree[0].question_count == 2
    assert [child.id for child in tree[0].children] == ["dir-root"]
    assert [child.id for child in tree[0].children[0].children] == ["point-a", "point-b"]
    assert "parent.status = 'published'" in statements[0]
    assert "content_status" in statements[0]


def test_fill_blank_grading_supports_ordered_list_answers() -> None:
    expected = {"accepted_answers": ["铜离子", "蓝色"]}

    assert _grade_answer("fill_blank", expected, ["铜离子", "蓝色"]) is True
    assert _grade_answer("fill_blank", expected, {"value": ["铜离子", "蓝色"]}) is True
    assert _grade_answer("fill_blank", expected, ["蓝色", "铜离子"]) is False
    assert _grade_answer("fill_blank", expected, ["铜离子", ""]) is False
    assert _grade_answer("fill_blank", {"accepted_answers": ["H2/氢气", "可燃"]}, ["氢气", "可燃"]) is True
    assert _grade_answer(
        "fill_blank",
        {"accepted_answers": ["H2,可燃/氢气,燃烧"]},
        ["氢气", "燃烧"],
    ) is True
    assert _grade_answer(
        "fill_blank",
        {"accepted_answers": ["H2,可燃/氢气,燃烧"]},
        ["燃烧", "氢气"],
    ) is False


def test_smart_assessment_ticket_curve_gives_lower_mastery_more_weight() -> None:
    strategy = SmartAssessmentSettings(weak_tendency_percent=100, weak_curve=2, weak_max_bonus=9)

    assert _draw_tickets(strategy, 30) > _draw_tickets(strategy, 80)
    assert _draw_tickets(strategy, 100) == 1


def test_class_strategy_override_merges_with_inherited_defaults() -> None:
    inherited = SmartAssessmentSettings(question_count=12, untested_ratio_percent=35, max_questions_per_experiment=3)

    strategy = _strategy_from_value({"question_count": 8}, inherited)
    settings = _custom_settings_from_value({"default_question_count": 20, "max_question_count": 10}, CustomAssessmentSettings())

    assert strategy.question_count == 8
    assert strategy.untested_ratio_percent == 35
    assert strategy.max_questions_per_experiment == 3
    assert settings.default_question_count == 10
    assert settings.max_question_count == 10


def test_student_custom_options_contract_exposes_only_per_point_settings() -> None:
    options = smart_assessment_module._custom_options_settings(
        CustomAssessmentSettings(max_questions_per_experiment=10)
    )

    assert options.model_dump() == {
        "enabled": True,
        "questions_per_point_options": [1, 2, 3],
        "default_questions_per_point": 3,
    }


def test_class_preview_estimates_point_distribution_by_experiment() -> None:
    strategy = SmartAssessmentSettings(question_count=10, untested_ratio_percent=20, max_questions_per_experiment=3)
    preview = _build_class_smart_assessment_preview(
        strategy=strategy,
        source="class",
        has_override=True,
        class_student_count=2,
        point_info={
            "p-a-weak": {"experiment_id": "EXP_A", "experiment_title": "实验 A"},
            "p-a-untested": {"experiment_id": "EXP_A", "experiment_title": "实验 A"},
            "p-b-strong": {"experiment_id": "EXP_B", "experiment_title": "实验 B"},
        },
        point_to_experiment={"p-a-weak": "EXP_A", "p-a-untested": "EXP_A", "p-b-strong": "EXP_B"},
        mastery={
            "p-a-weak": {"mastery_score": 25, "evidence_count": 4},
            "p-b-strong": {"mastery_score": 90, "evidence_count": 2},
        },
    )

    assert preview.source == "class"
    assert preview.has_override is True
    assert preview.class_student_count == 2
    assert preview.candidate_point_count == 3
    assert preview.untested_target_count == 2
    assert preview.untested_point_count == 1
    assert preview.measured_point_count == 2
    assert preview.warnings["untested_pool_underfilled"] is True
    assert preview.experiments[0].id == "EXP_A"
    assert preview.experiments[0].untested_point_count == 1
    assert preview.experiments[0].estimated_question_count <= strategy.max_questions_per_experiment


def test_class_strategy_permission_boundary_is_checked_before_db(monkeypatch) -> None:
    def deny_access(class_id: str, user: object) -> None:
        raise DomainHTTPException(status_code=403, detail=f"denied:{class_id}")

    monkeypatch.setattr(smart_assessment_module, "require_class_access", deny_access)

    try:
        smart_assessment_module.get_class_smart_assessment_strategy("CLS_DENIED", SimpleNamespace(id="u1", role="teacher"))
    except DomainHTTPException as exc:
        assert exc.status_code == 403
        assert exc.detail == "denied:CLS_DENIED"
    else:
        raise AssertionError("unauthorized class strategy access should be rejected")


def test_smart_assessment_composition_reserves_untested_ratio() -> None:
    strategy = SmartAssessmentSettings(
        question_count=2,
        untested_ratio_percent=50,
        weak_tendency_percent=100,
        max_questions_per_experiment=1,
    )
    selected, composition, experiment_meta, point_meta = _compose_questions(
        candidates=[
            _candidate("q-untested", experiment_id="EXP_UNTESTED"),
            _candidate("q-weak", experiment_id="EXP_WEAK"),
            _candidate("q-strong", experiment_id="EXP_STRONG"),
        ],
        mastery={
            "point-q-weak": {"mastery_score": 25, "evidence_count": 2},
            "point-q-strong": {"mastery_score": 90, "evidence_count": 3},
        },
        strategy=strategy,
        student_id="20240001",
    )

    assert len(selected) == 2
    assert composition.untested_question_count == 1
    assert composition.measured_question_count == 1
    assert any(meta["source"] == "untested" for meta in experiment_meta.values())
    assert any(meta["source"] == "measured" for meta in experiment_meta.values())
    assert any(meta["source"] == "untested" for meta in point_meta.values())


def test_custom_assessment_composition_samples_stably_per_point_and_reports_underfill() -> None:
    candidates = [
        _candidate("q-a1", experiment_id="EXP_A", point_id="point-a"),
        _candidate("q-a2", experiment_id="EXP_A", point_id="point-a"),
        _candidate("q-a3", experiment_id="EXP_A", point_id="point-a"),
        _candidate("q-b1", experiment_id="EXP_B", point_id="point-b"),
        _candidate("q-c1", experiment_id="EXP_C", point_id="point-c"),
    ]

    first = _compose_custom_questions(
        candidates=candidates,
        selected_point_ids=["point-a", "point-b"],
        student_id="20240001",
        questions_per_point=2,
    )
    second = _compose_custom_questions(
        candidates=candidates,
        selected_point_ids=["point-a", "point-b"],
        student_id="20240001",
        questions_per_point=2,
    )
    selected, composition, experiment_meta, point_meta = first

    assert [question.id for question in selected] == [question.id for question in second[0]]
    assert len(selected) == 3
    assert {question.experiment_id for question in selected} == {"EXP_A", "EXP_B"}
    assert composition.target_question_count == 4
    assert composition.custom_question_count == 3
    assert composition.warnings["underfilled"] is True
    assert composition.warnings["underfilled_point_ids"] == ["point-b"]
    assert composition.warnings["available_question_counts"] == {"point-a": 3, "point-b": 1}
    assert composition.warnings["selected_question_counts"] == {"point-a": 2, "point-b": 1}
    assert all(meta["source"] == "custom" for meta in experiment_meta.values())
    assert point_meta["point-a"]["question_count"] == 2
    assert point_meta["point-b"]["question_count"] == 1


def test_point_assessment_composition_uses_only_target_point() -> None:
    target = "point-q-target"
    selected, composition, experiment_meta, point_meta = _compose_point_questions(
        candidates=[
            _candidate("q-target", experiment_id="EXP_A"),
            _candidate("q-other", experiment_id="EXP_A"),
            _candidate("q-extra", experiment_id="EXP_B"),
        ],
        point_node_id=target,
        student_id="20240001",
    )

    assert [question.id for question in selected] == ["q-target"]
    assert composition.target_question_count == 3
    assert composition.total_questions == 1
    assert composition.warnings["underfilled"] is True
    assert composition.warnings["point_question_bank_underfilled"] is True
    assert all(target in question.source_placement_node_ids for question in selected)
    assert {meta["source"] for meta in experiment_meta.values()} == {"point"}
    assert point_meta[target]["source"] == "point"


def test_student_assessment_status_uses_completed_smart_session_as_baseline(monkeypatch) -> None:
    class FakeSession:
        def execute(self, statement: object, params: dict[str, object] | None = None) -> _ScalarResult:
            sql = str(statement)
            if "FROM student_smart_assessment_sessions" in sql and "status = 'completed'" in sql:
                return _ScalarResult(1)
            raise AssertionError(f"unexpected sql: {sql}")

    monkeypatch.setattr(smart_assessment_module, "db_session", lambda: _FakeSessionContext(FakeSession()))
    monkeypatch.setattr(smart_assessment_module, "_ensure_tables", lambda _session: None)
    monkeypatch.setattr(smart_assessment_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_open_session",
        lambda _session, _student_id: {"id": "00000000-0000-0000-0000-000000000123", "assessment_mode": "point"},
    )

    status = smart_assessment_module.get_student_assessment_status(SimpleNamespace(id="u1", role="student"))

    assert status.has_completed_smart_baseline is True
    assert status.needs_smart_baseline is False
    assert status.has_open_assessment is True
    assert status.open_session_id == "00000000-0000-0000-0000-000000000123"
    assert status.open_assessment_mode == "point"


def test_student_assessment_status_still_needs_baseline_without_completed_smart_session(monkeypatch) -> None:
    class FakeSession:
        def execute(self, statement: object, params: dict[str, object] | None = None) -> _ScalarResult:
            sql = str(statement)
            if "FROM student_smart_assessment_sessions" in sql and "status = 'completed'" in sql:
                return _ScalarResult(None)
            raise AssertionError(f"unexpected sql: {sql}")

    monkeypatch.setattr(smart_assessment_module, "db_session", lambda: _FakeSessionContext(FakeSession()))
    monkeypatch.setattr(smart_assessment_module, "_ensure_tables", lambda _session: None)
    monkeypatch.setattr(smart_assessment_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(smart_assessment_module, "_load_open_session", lambda _session, _student_id: None)

    status = smart_assessment_module.get_student_assessment_status(SimpleNamespace(id="u1", role="student"))

    assert status.has_completed_smart_baseline is False
    assert status.needs_smart_baseline is True


def test_point_assessment_start_reuses_existing_open_session(monkeypatch) -> None:
    response = StudentSmartAssessmentResponse(
        status="in_progress",
        session_id="open-session",
        assessment_mode="smart",
        strategy=SmartAssessmentSettings(question_count=1),
        composition=SmartAssessmentCompositionSummary(total_questions=1, target_question_count=1),
        experiments=[],
        questions=[],
    )
    load_candidates_called = False

    def fail_if_candidates_loaded(_session: object) -> list[PosttestQuestionCandidate]:
        nonlocal load_candidates_called
        load_candidates_called = True
        return []

    monkeypatch.setattr(smart_assessment_module, "db_session", lambda: _FakeSessionContext(object()))
    monkeypatch.setattr(smart_assessment_module, "_ensure_tables", lambda _session: None)
    monkeypatch.setattr(smart_assessment_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(smart_assessment_module, "_lock_student_assessment_owner", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(smart_assessment_module, "_load_open_session", lambda _session, _student_id: {"id": "open-session"})
    monkeypatch.setattr(smart_assessment_module, "_response_for_session", lambda _session, _row: response)
    monkeypatch.setattr(
        smart_assessment_module,
        "_require_completed_smart_baseline",
        lambda _session, _student_id: pytest.fail("an open smart baseline must be resumable before completion"),
    )
    monkeypatch.setattr(smart_assessment_module, "_load_all_published_candidates", fail_if_candidates_loaded)

    result = smart_assessment_module.start_student_point_assessment(
        SimpleNamespace(id="u1", role="student"),
        StudentPointAssessmentStartRequest(point_node_id="point-q1"),
    )

    assert result.session_id == "open-session"
    assert load_candidates_called is False


def test_smart_assessment_start_resumes_open_session_before_checking_current_strategy(monkeypatch) -> None:
    response = StudentSmartAssessmentResponse(
        status="in_progress",
        session_id="open-custom-session",
        assessment_mode="custom",
        strategy=SmartAssessmentSettings(enabled=False, question_count=1),
        composition=SmartAssessmentCompositionSummary(total_questions=1, target_question_count=1),
        experiments=[],
        questions=[],
    )

    monkeypatch.setattr(smart_assessment_module, "db_session", lambda: _FakeSessionContext(object()))
    monkeypatch.setattr(smart_assessment_module, "_ensure_tables", lambda _session: None)
    monkeypatch.setattr(smart_assessment_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(smart_assessment_module, "_lock_student_assessment_owner", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_open_session",
        lambda _session, _student_id: {"id": "open-custom-session", "assessment_mode": "custom"},
    )
    monkeypatch.setattr(smart_assessment_module, "_response_for_session", lambda _session, _row: response)
    monkeypatch.setattr(smart_assessment_module, "_require_completed_smart_baseline", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_effective_strategy",
        lambda _session, _class_id: (_ for _ in ()).throw(AssertionError("strategy must not block resume")),
    )

    result = smart_assessment_module.start_student_smart_assessment(SimpleNamespace(id="u1", role="student"))

    assert result.session_id == "open-custom-session"
    assert result.assessment_mode == "custom"


def test_custom_assessment_start_resumes_open_session_before_checking_current_settings(monkeypatch) -> None:
    response = StudentSmartAssessmentResponse(
        status="in_progress",
        session_id="open-custom-session",
        assessment_mode="custom",
        strategy=SmartAssessmentSettings(enabled=False, question_count=1),
        composition=SmartAssessmentCompositionSummary(total_questions=1, target_question_count=1),
        experiments=[],
        questions=[],
    )

    monkeypatch.setattr(smart_assessment_module, "db_session", lambda: _FakeSessionContext(object()))
    monkeypatch.setattr(smart_assessment_module, "_ensure_tables", lambda _session: None)
    monkeypatch.setattr(smart_assessment_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(smart_assessment_module, "_lock_student_assessment_owner", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_open_session",
        lambda _session, _student_id: {"id": "open-custom-session", "assessment_mode": "custom"},
    )
    monkeypatch.setattr(smart_assessment_module, "_response_for_session", lambda _session, _row: response)
    monkeypatch.setattr(smart_assessment_module, "_require_completed_smart_baseline", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_effective_custom_settings",
        lambda _session, _class_id: (_ for _ in ()).throw(AssertionError("settings must not block resume")),
    )

    result = smart_assessment_module.start_student_custom_assessment(
        SimpleNamespace(id="u1", role="student"),
        StudentCustomAssessmentStartRequest(scope_node_ids=["point-a"], questions_per_point=1),
    )

    assert result.session_id == "open-custom-session"


@pytest.mark.parametrize(
    ("starter_name", "payload"),
    [
        (
            "start_student_custom_assessment",
            StudentCustomAssessmentStartRequest(scope_node_ids=["point-a"], questions_per_point=1),
        ),
        (
            "start_student_point_assessment",
            StudentPointAssessmentStartRequest(point_node_id="point-a"),
        ),
    ],
    ids=["custom", "point"],
)
def test_nonbaseline_assessment_start_cannot_bypass_required_smart_baseline(
    monkeypatch,
    starter_name: str,
    payload: object,
) -> None:
    statements: list[str] = []

    class NoBaselineSession:
        def execute(self, statement: object, _params: dict[str, object] | None = None) -> _ScalarResult:
            statements.append(str(statement))
            return _ScalarResult(None)

    monkeypatch.setattr(smart_assessment_module, "db_session", lambda: _FakeSessionContext(NoBaselineSession()))
    monkeypatch.setattr(smart_assessment_module, "_ensure_tables", lambda _session: None)
    monkeypatch.setattr(smart_assessment_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(smart_assessment_module, "_lock_student_assessment_owner", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(smart_assessment_module, "_load_open_session", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_all_published_candidates",
        lambda _session: pytest.fail("baseline gate must run before the nonbaseline question pool"),
    )

    with pytest.raises(DomainHTTPException) as exc_info:
        getattr(smart_assessment_module, starter_name)(SimpleNamespace(id="u1", role="student"), payload)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == SMART_BASELINE_REQUIRED_DETAIL
    assert any("assessment_mode = 'smart'" in statement and "status = 'completed'" in statement for statement in statements)


def test_smart_start_cannot_resume_preexisting_nonbaseline_session_before_baseline(monkeypatch) -> None:
    class NoBaselineSession:
        def execute(self, _statement: object, _params: dict[str, object] | None = None) -> _ScalarResult:
            return _ScalarResult(None)

    monkeypatch.setattr(smart_assessment_module, "db_session", lambda: _FakeSessionContext(NoBaselineSession()))
    monkeypatch.setattr(smart_assessment_module, "_ensure_tables", lambda _session: None)
    monkeypatch.setattr(smart_assessment_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(smart_assessment_module, "_lock_student_assessment_owner", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_open_session",
        lambda _session, _student_id: {"id": "open-custom-session", "assessment_mode": "custom"},
    )
    monkeypatch.setattr(
        smart_assessment_module,
        "_response_for_session",
        lambda _session, _row: pytest.fail("nonbaseline session must stay gated"),
    )

    with pytest.raises(DomainHTTPException) as exc_info:
        smart_assessment_module.start_student_smart_assessment(SimpleNamespace(id="u1", role="student"))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == SMART_BASELINE_REQUIRED_DETAIL


def test_disabled_smart_assessment_still_allows_required_first_baseline(monkeypatch) -> None:
    candidate = _candidate("q-baseline", experiment_id="EXP_A")
    response = StudentSmartAssessmentResponse(
        status="in_progress",
        session_id="new-baseline-session",
        assessment_mode="smart",
        strategy=SmartAssessmentSettings(enabled=False, question_count=1),
        composition=SmartAssessmentCompositionSummary(total_questions=1, target_question_count=1),
        experiments=[],
        questions=[],
    )

    class MappingResult:
        def mappings(self) -> "MappingResult":
            return self

        def one(self) -> dict[str, object]:
            return {
                "id": "new-baseline-session",
                "assessment_mode": "smart",
                "strategy_snapshot": {"enabled": False, "question_count": 1},
                "question_ids": [candidate.id],
                "experiment_ids": [candidate.experiment_id],
                "point_node_ids": candidate.source_placement_node_ids,
                "mastery_before": {},
                "metadata": {"question_snapshots": _question_snapshots([candidate]), "experiments": []},
            }

    class FakeSession:
        def execute(self, _statement: object, _params: dict[str, object] | None = None) -> MappingResult:
            return MappingResult()

    monkeypatch.setattr(smart_assessment_module, "db_session", lambda: _FakeSessionContext(FakeSession()))
    monkeypatch.setattr(smart_assessment_module, "_ensure_tables", lambda _session: None)
    monkeypatch.setattr(smart_assessment_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(smart_assessment_module, "_lock_student_assessment_owner", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(smart_assessment_module, "_load_open_session", lambda _session, _student_id: None)
    monkeypatch.setattr(smart_assessment_module, "_require_completed_smart_baseline", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_effective_strategy",
        lambda _session, _class_id: (
            SmartAssessmentSettings(enabled=False, question_count=1),
            SmartAssessmentSettings(enabled=False, question_count=1),
            False,
        ),
    )
    monkeypatch.setattr(smart_assessment_module, "_student_has_completed_smart_baseline", lambda _session, _student_id: False)
    monkeypatch.setattr(smart_assessment_module, "_load_all_published_candidates", lambda _session: [candidate])
    monkeypatch.setattr(smart_assessment_module, "_load_mastery_map", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        smart_assessment_module,
        "_compose_questions",
        lambda **_kwargs: (
            [candidate],
            SmartAssessmentCompositionSummary(total_questions=1, target_question_count=1),
            {},
            {},
        ),
    )
    monkeypatch.setattr(smart_assessment_module, "_point_mastery_snapshot", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        smart_assessment_module,
        "_assessment_content_snapshot",
        lambda *_args, **_kwargs: {"question_snapshots": _question_snapshots([candidate]), "experiments": []},
    )
    monkeypatch.setattr(smart_assessment_module, "_response_for_session", lambda _session, _row: response)

    result = smart_assessment_module.start_student_smart_assessment(SimpleNamespace(id="u1", role="student"))

    assert result.session_id == "new-baseline-session"
    assert result.strategy.enabled is False


def test_disabled_smart_assessment_rejects_new_round_after_completed_baseline(monkeypatch) -> None:
    monkeypatch.setattr(smart_assessment_module, "db_session", lambda: _FakeSessionContext(object()))
    monkeypatch.setattr(smart_assessment_module, "_ensure_tables", lambda _session: None)
    monkeypatch.setattr(smart_assessment_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(smart_assessment_module, "_lock_student_assessment_owner", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(smart_assessment_module, "_load_open_session", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_effective_strategy",
        lambda _session, _class_id: (
            SmartAssessmentSettings(enabled=False),
            SmartAssessmentSettings(enabled=False),
            False,
        ),
    )
    monkeypatch.setattr(smart_assessment_module, "_student_has_completed_smart_baseline", lambda _session, _student_id: True)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_all_published_candidates",
        lambda _session: pytest.fail("disabled follow-up must not read the question pool"),
    )

    with pytest.raises(DomainHTTPException) as exc_info:
        smart_assessment_module.start_student_smart_assessment(SimpleNamespace(id="u1", role="student"))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Smart assessment is disabled"


def test_locked_smart_session_uses_original_snapshot_after_source_withdrawal_or_republish() -> None:
    original = _candidate("q-locked", experiment_id="EXP_A")
    row = {
        "question_ids": [original.id],
        "experiment_ids": [original.experiment_id],
        "metadata": {"question_snapshots": _question_snapshots([original])},
    }

    class NoDatabaseReadSession:
        def execute(self, *_args: object, **_kwargs: object) -> object:
            raise AssertionError("snapshotted sessions must not reload withdrawn or republished source content")

    locked = _load_locked_session_questions(
        NoDatabaseReadSession(),
        row,
        changed_detail="Smart assessment question bank has changed",
    )
    republished = PosttestQuestionCandidate(
        **{
            **original.__dict__,
            "stem": "Republished question",
            "answer": {"value": "B"},
            "explanation": "New explanation",
        }
    )

    assert locked[0].stem == "Question q-locked"
    assert locked[0].answer == {"value": "A"}
    assert locked[0].explanation == "Because A"
    assert _grade_answer(locked[0].question_type, locked[0].answer, "A") is True
    assert _grade_answer(republished.question_type, republished.answer, "A") is False


def test_smart_session_response_is_built_from_locked_snapshot(monkeypatch) -> None:
    question = _candidate("q-locked", experiment_id="EXP_A")
    row = {
        "id": "locked-session",
        "assessment_mode": "smart",
        "strategy_snapshot": {"question_count": 1},
        "composition_summary": {"total_questions": 1, "target_question_count": 1},
        "question_ids": [question.id],
        "experiment_ids": [question.experiment_id],
        "point_node_ids": question.source_placement_node_ids,
        "mastery_before": {},
        "metadata": {"question_snapshots": _question_snapshots([question])},
    }
    monkeypatch.setattr(smart_assessment_module, "_experiments_for_session", lambda *_args, **_kwargs: [])

    response = smart_assessment_module._response_for_session(object(), row)

    assert response.session_id == "locked-session"
    assert [item.id for item in response.questions] == [question.id]
    assert response.questions[0].stem == question.stem


def test_smart_attempt_metadata_keeps_snapshot_and_lineage() -> None:
    question = _candidate("q-locked", experiment_id="EXP_A")
    captured: list[dict[str, object]] = []

    class FakeSession:
        def execute(self, _statement: object, params: dict[str, object]) -> None:
            captured.append(params)

    graded = smart_assessment_module._insert_attempts(
        FakeSession(),
        student_id="20249999",
        class_id="CLS_1",
        smart_assessment_session_id="session-1",
        assessment_mode="smart",
        questions=[question],
        answers={question.id: "A"},
    )
    metadata = json.loads(str(captured[0]["metadata"]))

    assert graded[0]["correct"] is True
    assert metadata["question_snapshot"]["answer"] == {"value": "A"}
    assert metadata["question_snapshot"]["source_placement_node_ids"] == question.source_placement_node_ids
    assert metadata["canonical_point_ids"] == question.primary_canonical_point_ids


def test_point_assessment_start_rejects_points_without_questions(monkeypatch) -> None:
    monkeypatch.setattr(smart_assessment_module, "db_session", lambda: _FakeSessionContext(object()))
    monkeypatch.setattr(smart_assessment_module, "_ensure_tables", lambda _session: None)
    monkeypatch.setattr(smart_assessment_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(smart_assessment_module, "_lock_student_assessment_owner", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(smart_assessment_module, "_load_open_session", lambda _session, _student_id: None)
    monkeypatch.setattr(smart_assessment_module, "_require_completed_smart_baseline", lambda _session, _student_id: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_all_published_candidates",
        lambda _session: [_candidate("q-other", experiment_id="EXP_A")],
    )

    try:
        smart_assessment_module.start_student_point_assessment(
            SimpleNamespace(id="u1", role="student"),
            StudentPointAssessmentStartRequest(point_node_id="point-missing"),
        )
    except DomainHTTPException as exc:
        assert exc.status_code == 409
        assert exc.detail == "This point does not have available assessment questions"
    else:
        raise AssertionError("point assessments without questions should be rejected")


def test_smart_assessment_answers_must_match_session_questions() -> None:
    payload = StudentSmartAssessmentSubmitRequest(
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


def test_assessment_creation_uses_transaction_scoped_student_lock() -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeSession:
        def execute(self, statement: object, params: dict[str, object] | None = None) -> _ScalarResult:
            calls.append((str(statement), params or {}))
            return _ScalarResult()

    smart_assessment_module._lock_student_assessment_owner(FakeSession(), "20249999")

    assert "pg_advisory_xact_lock" in calls[0][0]
    assert calls[0][1] == {"lock_key": "student-smart-assessment:20249999"}


def test_completed_assessment_submit_replays_report_without_new_attempts_or_mastery(monkeypatch) -> None:
    session_id = "00000000-0000-0000-0000-000000000123"
    stored_report = StudentSmartAssessmentReport(
        session_id=session_id,
        assessment_mode="smart",
        strategy=SmartAssessmentSettings(question_count=1),
        composition=SmartAssessmentCompositionSummary(total_questions=1, target_question_count=1),
        correct_count=1,
        total_count=1,
        score=100,
        correct_rate=1,
        next_recommendation="continue",
    )
    statements: list[str] = []

    class MappingResult:
        def mappings(self) -> "MappingResult":
            return self

        def first(self) -> dict[str, object]:
            return {
                "id": session_id,
                "student_id": "20249999",
                "status": "completed",
                "assessment_mode": "smart",
                "report": stored_report.model_dump(mode="json"),
            }

    class FakeSession:
        def execute(self, statement: object, _params: dict[str, object] | None = None) -> MappingResult:
            statements.append(str(statement))
            return MappingResult()

    monkeypatch.setattr(smart_assessment_module, "db_session", lambda: _FakeSessionContext(FakeSession()))
    monkeypatch.setattr(smart_assessment_module, "_ensure_tables", lambda _session: None)
    monkeypatch.setattr(smart_assessment_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(
        smart_assessment_module,
        "_insert_attempts",
        lambda *_args, **_kwargs: pytest.fail("completed retries must not insert attempts"),
    )
    monkeypatch.setattr(
        smart_assessment_module,
        "_update_mastery_from_smart_assessment",
        lambda *_args, **_kwargs: pytest.fail("completed retries must not update mastery"),
    )

    response = smart_assessment_module.submit_student_smart_assessment(
        SimpleNamespace(id="u1", role="student"),
        StudentSmartAssessmentSubmitRequest(
            session_id=session_id,
            answers=[{"question_id": "q1", "answer": "A"}],
        ),
    )

    assert response.report == stored_report
    assert any("FOR UPDATE" in statement for statement in statements)

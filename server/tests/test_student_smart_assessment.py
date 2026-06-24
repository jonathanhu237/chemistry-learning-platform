from __future__ import annotations

from types import SimpleNamespace

from server.app.domains.assessments.posttest import PosttestQuestionCandidate
from server.app.domains.assessments import smart_assessment as smart_assessment_module
from server.app.domains.assessments.smart_assessment import (
    _build_class_smart_assessment_preview,
    _compose_custom_questions,
    _compose_point_questions,
    _compose_questions,
    _custom_settings_from_value,
    _draw_tickets,
    _public_question,
    _strategy_from_value,
    _validate_submitted_answers,
)
from server.app.domains.errors import DomainHTTPException
from server.app.domains.platform.settings import CustomAssessmentSettings, SmartAssessmentSettings
from server.app.student_smart_assessment_schemas import (
    SmartAssessmentCompositionSummary,
    StudentPointAssessmentStartRequest,
    StudentSmartAssessmentResponse,
    StudentSmartAssessmentSubmitRequest,
)
from server.tests.route_helpers import assert_route


def _candidate(question_id: str, *, experiment_id: str) -> PosttestQuestionCandidate:
    point_id = f"point-{question_id}"
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
    assert_route("/api/student/assessment/baseline-prompt-dismiss", "POST")
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


def test_custom_assessment_composition_uses_selected_experiments() -> None:
    settings = CustomAssessmentSettings(default_question_count=5, max_question_count=10, max_questions_per_experiment=2)
    selected, composition, experiment_meta, point_meta = _compose_custom_questions(
        candidates=[
            _candidate("q-a1", experiment_id="EXP_A"),
            _candidate("q-a2", experiment_id="EXP_A"),
            _candidate("q-a3", experiment_id="EXP_A"),
            _candidate("q-b1", experiment_id="EXP_B"),
            _candidate("q-b2", experiment_id="EXP_B"),
            _candidate("q-c1", experiment_id="EXP_C"),
        ],
        selected_experiment_ids=["EXP_A", "EXP_B"],
        settings=settings,
        student_id="20240001",
        requested_question_count=5,
    )

    assert len(selected) == 4
    assert {question.experiment_id for question in selected} == {"EXP_A", "EXP_B"}
    assert composition.custom_question_count == 4
    assert composition.warnings["underfilled"] is True
    assert all(meta["source"] == "custom" for meta in experiment_meta.values())
    assert all(meta["question_count"] <= 2 for meta in experiment_meta.values())
    assert all(meta["source"] == "custom" for meta in point_meta.values())


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


def test_student_assessment_status_reports_open_session_and_dismissed_prompt(monkeypatch) -> None:
    class FakeSession:
        def execute(self, statement: object, params: dict[str, object] | None = None) -> _ScalarResult:
            sql = str(statement)
            if "FROM student_smart_assessment_sessions" in sql and "status = 'completed'" in sql:
                return _ScalarResult(1)
            if "FROM student_events" in sql:
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
    assert status.has_open_assessment is True
    assert status.open_session_id == "00000000-0000-0000-0000-000000000123"
    assert status.open_assessment_mode == "point"
    assert status.smart_baseline_prompt_dismissed is True


def test_dismiss_student_smart_baseline_prompt_records_student_event(monkeypatch) -> None:
    inserted_events: list[dict[str, object]] = []

    class FakeSession:
        def execute(self, statement: object, params: dict[str, object] | None = None) -> _ScalarResult:
            sql = str(statement)
            if "SELECT 1" in sql and "FROM student_events" in sql:
                return _ScalarResult(None)
            if "INSERT INTO student_events" in sql:
                inserted_events.append(params or {})
                return _ScalarResult(None)
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

    status = smart_assessment_module.dismiss_student_smart_baseline_prompt(SimpleNamespace(id="u1", role="student"))

    assert status.smart_baseline_prompt_dismissed is True
    assert inserted_events[0]["student_id"] == "20249999"
    assert inserted_events[0]["event_type"] == smart_assessment_module.SMART_BASELINE_PROMPT_DISMISSED_EVENT


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
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(smart_assessment_module, "_load_open_session", lambda _session, _student_id: {"id": "open-session"})
    monkeypatch.setattr(smart_assessment_module, "_response_for_session", lambda _session, _row: response)
    monkeypatch.setattr(smart_assessment_module, "_load_all_published_candidates", fail_if_candidates_loaded)

    result = smart_assessment_module.start_student_point_assessment(
        SimpleNamespace(id="u1", role="student"),
        StudentPointAssessmentStartRequest(point_node_id="point-q1"),
    )

    assert result.session_id == "open-session"
    assert load_candidates_called is False


def test_point_assessment_start_rejects_points_without_questions(monkeypatch) -> None:
    monkeypatch.setattr(smart_assessment_module, "db_session", lambda: _FakeSessionContext(object()))
    monkeypatch.setattr(smart_assessment_module, "_ensure_tables", lambda _session: None)
    monkeypatch.setattr(smart_assessment_module, "_ensure_student_row", lambda _session, _context: None)
    monkeypatch.setattr(
        smart_assessment_module,
        "_load_student_context",
        lambda _session, _user: SimpleNamespace(student_id="20249999", class_id="CLS_1"),
    )
    monkeypatch.setattr(smart_assessment_module, "_load_open_session", lambda _session, _student_id: None)
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

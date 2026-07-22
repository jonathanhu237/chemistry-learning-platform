from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest

from server.app.domains.assessments import reports as reports_module
from server.app.domains.errors import DomainHTTPException
from server.app.domains.platform.settings import SmartAssessmentSettings
from server.app.student_assessment_report_schemas import (
    AssessmentReportPromptSettings,
    StudentAssessmentReport,
)
from server.app.student_smart_assessment_schemas import (
    SmartAssessmentCompositionSummary,
    SmartAssessmentExperimentSummary,
    StudentSmartAssessmentReport,
    StudentSmartAssessmentWrongAnswer,
)
from server.tests.route_helpers import assert_route


SESSION_ID = "00000000-0000-0000-0000-000000000101"
REPORT_ID = "00000000-0000-0000-0000-000000000201"
COMPLETED_AT = datetime(2026, 6, 25, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class _FakeResult:
    def __init__(self, *, first: dict[str, Any] | None = None, rows: list[dict[str, Any]] | None = None) -> None:
        self._first = first
        self._rows = rows or []

    def mappings(self) -> "_FakeResult":
        return self

    def first(self) -> dict[str, Any] | None:
        return self._first

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class _FakeConnection:
    def exec_driver_sql(self, _sql: str) -> None:
        return None


class _SessionScope:
    def __init__(self, session: "_FakeSession") -> None:
        self.session = session

    def __enter__(self) -> "_FakeSession":
        return self.session

    def __exit__(self, *_exc: object) -> bool:
        return False


class _FakeSession:
    def __init__(
        self,
        *,
        pretest_session: dict[str, Any] | None = None,
        smart_session: dict[str, Any] | None = None,
        attempts: list[dict[str, Any]] | None = None,
        class_prompt: dict[str, Any] | None = None,
        reports: list[dict[str, Any]] | None = None,
    ) -> None:
        self.pretest_session = pretest_session
        self.smart_session = smart_session
        self.attempts = attempts or []
        self.class_prompt = class_prompt
        self.reports = reports or []
        self.params: list[dict[str, Any]] = []
        self.sql: list[str] = []

    def connection(self) -> _FakeConnection:
        return _FakeConnection()

    def execute(self, query: object, params: dict[str, Any] | None = None) -> _FakeResult:
        self.params.append(params or {})
        sql = str(query)
        self.sql.append(sql)
        if "FROM student_pretest_sessions" in sql:
            return _FakeResult(first=self.pretest_session)
        if "FROM student_smart_assessment_sessions" in sql:
            return _FakeResult(first=self.smart_session)
        if "metadata->>'pretest_session_id'" in sql or "metadata->>'smart_assessment_session_id'" in sql:
            return _FakeResult(rows=self.attempts)
        if "FROM class_assessment_report_prompt_settings" in sql:
            return _FakeResult(first={"value": self.class_prompt} if self.class_prompt is not None else None)
        if "FROM student_assessment_reports" in sql:
            return _FakeResult(first=self.reports[0] if self.reports else None, rows=self.reports)
        return _FakeResult()


def _user(**overrides: Any) -> SimpleNamespace:
    values = {
        "id": "00000000-0000-0000-0000-000000000001",
        "username": "20249999",
        "student_id": "20249999",
        "display_name": "演示学生",
        "role": "student",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _attempt(*, correct: bool = False) -> dict[str, Any]:
    return {
        "question_id": "00000000-0000-0000-0000-000000000301",
        "experiment_id": "EXP_19_1_01",
        "experiment_title": "实验 19-1 卤素置换",
        "question_type": "single_choice",
        "stem": "CCl4 层出现什么颜色？",
        "options": [{"label": "A", "text": "无色"}, {"label": "B", "text": "橙色"}],
        "answer": {"value": "B"},
        "submitted_answer": {"value": "A"},
        "correct": correct,
        "explanation": "溴在 CCl4 中呈橙色。",
        "difficulty": "basic",
        "metadata": {"area": "p区", "pretest_stage": 1},
        "related_chapter_ids": ["CH17"],
        "related_knowledge_point_ids": ["kp-halogen"],
    }


def _smart_report(mode: str) -> StudentSmartAssessmentReport:
    wrong = StudentSmartAssessmentWrongAnswer(
        question_id="00000000-0000-0000-0000-000000000301",
        experiment_id="EXP_19_1_01",
        experiment_title="实验 19-1 卤素置换",
        point_node_ids=["point-halogen"],
        canonical_point_ids=["canon-halogen"],
        question_type="single_choice",
        stem="CCl4 层出现什么颜色？",
        options=[{"label": "A", "text": "无色"}, {"label": "B", "text": "橙色"}],
        submitted_answer="A",
        correct_answer="B",
        explanation="溴在 CCl4 中呈橙色。",
    )
    return StudentSmartAssessmentReport(
        session_id=SESSION_ID,
        assessment_mode=mode,  # type: ignore[arg-type]
        strategy=SmartAssessmentSettings(question_count=1),
        composition=SmartAssessmentCompositionSummary(
            total_questions=1,
            target_question_count=1,
            requested_question_count=1 if mode == "custom" else None,
            selected_point_count=1 if mode == "point" else 0,
            candidate_point_count=1,
            untested_question_count=1 if mode == "smart" else 0,
            measured_question_count=0,
            custom_question_count=1 if mode == "custom" else 0,
            untested_ratio_percent=20,
            weak_tendency_percent=70,
            max_questions_per_experiment=1,
        ),
        experiments=[
            SmartAssessmentExperimentSummary(
                id="EXP_19_1_01",
                code="19-1-01",
                title="实验 19-1 卤素置换",
                source="untested" if mode == "smart" else mode,  # type: ignore[arg-type]
                question_count=1,
            )
        ],
        correct_count=0,
        total_count=1,
        score=0,
        correct_rate=0,
        wrong_answers=[wrong],
        next_recommendation="复习卤素置换实验现象。",
    )


def _report_row(**overrides: Any) -> dict[str, Any]:
    return {
        "id": REPORT_ID,
        "student_id": "20249999",
        "class_id": "class-a",
        "report_type": "smart",
        "source_session_id": SESSION_ID,
        "title": "智能测试报告",
        "score": 80,
        "correct_count": 4,
        "total_count": 5,
        "correct_rate": 0.8,
        "wrong_count": 1,
        "summary": {"text": "summary", "source": "fallback", "mode": "local_fallback"},
        "mistake_explanation": {"text": "mistake", "source": "fallback", "mode": "local_fallback"},
        "prompt_snapshot": {"source": "global"},
        "payload": {"assessment_mode": "smart"},
        "completed_at": COMPLETED_AT,
        **overrides,
    }


def _install_report_creation_fakes(monkeypatch: pytest.MonkeyPatch, session: _FakeSession) -> list[dict[str, Any]]:
    captured: list[dict[str, Any]] = []

    def fake_insert_report(**kwargs: Any) -> StudentAssessmentReport:
        captured.append(kwargs)
        return StudentAssessmentReport(
            id=REPORT_ID,
            student_id=kwargs["student_id"],
            class_id=kwargs["class_id"],
            report_type=kwargs["report_type"],
            source_session_id=kwargs["source_session_id"],
            title=kwargs["title"],
            score=kwargs["score"],
            correct_count=kwargs["correct_count"],
            total_count=kwargs["total_count"],
            correct_rate=kwargs["correct_rate"],
            wrong_count=kwargs["wrong_count"],
            summary=kwargs["summary"],
            mistake_explanation=kwargs["mistake_explanation"],
            prompt_snapshot=kwargs["prompt_snapshot"],
            payload=kwargs["payload"],
            completed_at=kwargs["completed_at"] or COMPLETED_AT,
        )

    monkeypatch.setattr(reports_module, "db_session", lambda: _SessionScope(session))
    monkeypatch.setattr(reports_module, "_effective_prompt_settings", lambda _class_id: (reports_module.default_report_prompt_settings(), "global"))
    monkeypatch.setattr(reports_module, "_ai_ready", lambda: False)
    monkeypatch.setattr(reports_module, "_insert_report", fake_insert_report)
    return captured


def test_assessment_report_routes_are_registered() -> None:
    assert_route("/api/student/assessment-reports", "GET")
    assert_route("/api/student/assessment-reports/{report_id}", "GET")
    assert_route("/api/admin/assessment-report-prompts", "GET")
    assert_route("/api/admin/assessment-report-prompts", "PUT")
    assert_route("/api/admin/assessment-report-prompts", "DELETE")
    assert_route("/api/admin/classes/{class_id}/assessment-report-prompts", "GET")
    assert_route("/api/admin/classes/{class_id}/assessment-report-prompts", "PUT")
    assert_route("/api/admin/classes/{class_id}/assessment-report-prompts", "DELETE")
    assert_route("/api/admin/classes/{class_id}/students/{student_id}/assessment-reports", "GET")
    assert_route("/api/admin/classes/{class_id}/students/{student_id}/assessment-reports/{report_id}", "GET")


@pytest.mark.anyio
async def test_pretest_report_creation_persists_snapshot_with_local_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession(
        pretest_session={"id": SESSION_ID, "student_id": "20249999", "class_id": "class-a", "status": "completed", "completed_at": COMPLETED_AT},
        attempts=[_attempt(correct=False)],
    )
    captured = _install_report_creation_fakes(monkeypatch, session)

    report = await reports_module.create_pretest_report(_user(), SESSION_ID)

    assert report.report_type == "pretest"
    assert report.score == 0
    assert report.summary.mode == "local_fallback"
    assert report.mistake_explanation.mode == "local_fallback"
    assert "课前测试已完成" in report.summary.text
    assert captured[0]["payload"]["assessment_mode"] == "pretest"
    assert captured[0]["payload"]["wrong_answers"][0]["correct_answer"] == "B"
    assert captured[0]["wrong_count"] == 1


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["smart", "custom", "point"])
async def test_smart_custom_point_report_creation_keeps_mode_and_fallback(monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    session = _FakeSession(
        smart_session={"id": SESSION_ID, "student_id": "20249999", "class_id": "class-a", "status": "completed", "completed_at": COMPLETED_AT},
        attempts=[_attempt(correct=False)],
    )
    captured = _install_report_creation_fakes(monkeypatch, session)

    report = await reports_module.create_smart_assessment_report(_user(), _smart_report(mode))

    assert report.report_type == mode
    assert report.title == reports_module._report_title(mode)
    assert report.summary.mode == "local_fallback"
    assert report.mistake_explanation.mode == "local_fallback"
    assert captured[0]["payload"]["assessment_mode"] == mode
    assert captured[0]["source_table"] == "student_smart_assessment_sessions"
    assert captured[0]["wrong_count"] == 1


@pytest.mark.anyio
async def test_smart_report_retry_replays_existing_canonical_report_without_regeneration(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession(
        smart_session={
            "id": SESSION_ID,
            "student_id": "20249999",
            "class_id": "class-a",
            "status": "completed",
            "assessment_mode": "smart",
            "completed_at": COMPLETED_AT,
        },
        reports=[_report_row()],
    )
    monkeypatch.setattr(reports_module, "db_session", lambda: _SessionScope(session))

    async def fail_generation(**_kwargs: Any) -> Any:
        pytest.fail("persisted report retries must not regenerate report text")

    monkeypatch.setattr(reports_module, "_generate_report_texts", fail_generation)

    report = await reports_module.create_smart_assessment_report(_user(), _smart_report("smart"))

    assert report.id == REPORT_ID
    assert report.payload["assessment_mode"] == "smart"
    assert all("FOR UPDATE" not in sql for sql in session.sql)


@pytest.mark.anyio
async def test_smart_report_generation_failure_can_retry_from_completed_session(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession(
        smart_session={
            "id": SESSION_ID,
            "student_id": "20249999",
            "class_id": "class-a",
            "status": "completed",
            "assessment_mode": "smart",
            "completed_at": COMPLETED_AT,
        },
        attempts=[_attempt(correct=False)],
    )
    captured = _install_report_creation_fakes(monkeypatch, session)
    generation_calls = 0

    async def flaky_generation(**_kwargs: Any) -> Any:
        nonlocal generation_calls
        generation_calls += 1
        if generation_calls == 1:
            raise RuntimeError("transient generation failure")
        return (
            reports_module._generated_text("retry summary"),
            reports_module._generated_text("retry mistake"),
            {"source": "global"},
        )

    monkeypatch.setattr(reports_module, "_generate_report_texts", flaky_generation)

    with pytest.raises(RuntimeError, match="transient generation failure"):
        await reports_module.create_smart_assessment_report(_user(), _smart_report("smart"))

    report = await reports_module.create_smart_assessment_report(_user(), _smart_report("smart"))

    assert report.summary.text == "retry summary"
    assert generation_calls == 2
    assert len(captured) == 1
    assert all("FOR UPDATE" not in sql for sql in session.sql)


def test_report_insert_conflict_returns_first_persisted_report(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession(reports=[_report_row(summary={"text": "first", "source": "fallback", "mode": "local_fallback"})])
    monkeypatch.setattr(reports_module, "db_session", lambda: _SessionScope(session))

    report = reports_module._insert_report(
        student_id="20249999",
        class_id="class-a",
        report_type="smart",
        source_session_id=SESSION_ID,
        source_table="student_smart_assessment_sessions",
        title="智能测试报告",
        score=0,
        correct_count=0,
        total_count=1,
        correct_rate=0,
        wrong_count=1,
        summary=reports_module._generated_text("second"),
        mistake_explanation=reports_module._generated_text("second mistake"),
        prompt_snapshot={"source": "global"},
        payload={"assessment_mode": "smart"},
        completed_at=COMPLETED_AT,
    )

    assert report.summary.text == "first"
    insert_sql = next(sql for sql in session.sql if "INSERT INTO student_assessment_reports" in sql)
    assert "DO NOTHING" in insert_sql
    assert "DO UPDATE" not in insert_sql


@pytest.mark.anyio
async def test_assessment_report_ai_generation_uses_direct_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class _FakeCompletions:
        async def create(self, **kwargs: Any) -> Any:
            captured.update(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="真实 AI 学情总结。"))])

    class _FakeClient:
        chat = SimpleNamespace(completions=_FakeCompletions())

    monkeypatch.setattr(reports_module, "_ai_ready", lambda: True)
    monkeypatch.setattr(reports_module, "effective_ai_settings", lambda _settings: SimpleNamespace(agent_llm_model="qwen-max"))
    monkeypatch.setattr(reports_module, "openai_chat_client", lambda _settings, *, timeout: _FakeClient())

    generated = await reports_module._generate_with_ai(
        user=_user(),
        prompt="请生成测评报告。",
        context={"student_id": "20249999"},
        attempts=[_attempt(correct=False)],
        fallback_text="本地兜底报告。",
    )

    assert generated.text == "真实 AI 学情总结。"
    assert generated.source == "ai"
    assert generated.mode == "openai_chat_report"
    assert captured["model"] == "qwen-max"
    assert "不调用工具" in captured["messages"][0]["content"]
    assert "不要求外部检索" in captured["messages"][0]["content"]
    assert "assessment_report_context" in captured["messages"][1]["content"]


@pytest.mark.anyio
async def test_assessment_report_ai_generation_times_out_to_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    class _SlowCompletions:
        async def create(self, **_kwargs: Any) -> Any:
            await asyncio.sleep(1)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="late answer"))])

    class _SlowClient:
        chat = SimpleNamespace(completions=_SlowCompletions())

    monkeypatch.setattr(reports_module, "_ai_ready", lambda: True)
    monkeypatch.setattr(reports_module, "effective_ai_settings", lambda _settings: SimpleNamespace(agent_llm_model="qwen-max"))
    monkeypatch.setattr(reports_module, "openai_chat_client", lambda _settings, *, timeout: _SlowClient())
    monkeypatch.setattr(reports_module, "ASSESSMENT_REPORT_AI_TIMEOUT_SECONDS", 0.01)

    generated = await reports_module._generate_with_ai(
        user=_user(),
        prompt="请生成测评报告。",
        context={"student_id": "20249999"},
        attempts=[_attempt(correct=False)],
        fallback_text="本地兜底报告。",
    )

    assert generated.text == "本地兜底报告。"
    assert generated.mode == "report_ai_timeout_fallback"


def test_student_report_list_and_detail_are_scoped_to_authenticated_student(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession(reports=[_report_row()])
    monkeypatch.setattr(reports_module, "db_session", lambda: _SessionScope(session))

    listed = reports_module.list_student_assessment_reports(_user(student_id="20249999"))
    detail = reports_module.get_student_assessment_report(REPORT_ID, _user(student_id="20249999"))

    assert listed.reports[0].id == REPORT_ID
    assert detail.id == REPORT_ID
    assert {"student_id": "20249999"} in session.params


def test_student_report_detail_returns_404_when_report_is_not_owned(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession(reports=[])
    monkeypatch.setattr(reports_module, "db_session", lambda: _SessionScope(session))

    with pytest.raises(DomainHTTPException) as exc_info:
        reports_module.get_student_assessment_report(REPORT_ID, _user(student_id="20249999"))

    assert exc_info.value.status_code == 404


def test_teacher_report_access_checks_class_before_query(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny_access(class_id: str, _user: object) -> None:
        raise DomainHTTPException(status_code=403, detail=f"denied:{class_id}")

    monkeypatch.setattr(reports_module, "require_class_access", deny_access)

    with pytest.raises(DomainHTTPException) as exc_info:
        reports_module.list_teacher_student_assessment_reports("class-denied", "20249999", _user(role="teacher"))

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "denied:class-denied"


def test_teacher_report_list_and_detail_are_scoped_to_class_and_student(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession(reports=[_report_row()])
    monkeypatch.setattr(reports_module, "require_class_access", lambda _class_id, _user: None)
    monkeypatch.setattr(reports_module, "db_session", lambda: _SessionScope(session))

    listed = reports_module.list_teacher_student_assessment_reports("class-a", "20249999", _user(role="teacher"))
    detail = reports_module.get_teacher_student_assessment_report("class-a", "20249999", REPORT_ID, _user(role="teacher"))

    assert listed.reports[0].id == REPORT_ID
    assert detail.id == REPORT_ID
    assert {"class_id": "class-a", "student_id": "20249999"} in session.params
    assert {"report_id": REPORT_ID, "class_id": "class-a", "student_id": "20249999"} in session.params


def test_class_prompt_settings_inherit_global_when_no_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reports_module, "require_class_access", lambda _class_id, _user: None)
    monkeypatch.setattr(reports_module, "_load_setting_value", lambda _key: {"summary_prompt": "global summary", "mistake_prompt": "global mistake"})
    monkeypatch.setattr(reports_module, "db_session", lambda: _SessionScope(_FakeSession(class_prompt=None)))

    response = reports_module.get_class_report_prompt_settings("class-a", _user(role="teacher"))

    assert response.source == "global"
    assert response.has_override is False
    assert response.settings.summary_prompt == "global summary"
    assert response.inherited_settings and response.inherited_settings.mistake_prompt == "global mistake"


def test_class_prompt_settings_return_override_with_inherited_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reports_module, "require_class_access", lambda _class_id, _user: None)
    monkeypatch.setattr(reports_module, "_load_setting_value", lambda _key: {"summary_prompt": "global summary", "mistake_prompt": "global mistake"})
    monkeypatch.setattr(
        reports_module,
        "db_session",
        lambda: _SessionScope(_FakeSession(class_prompt={"summary_prompt": "class summary", "mistake_prompt": "class mistake"})),
    )

    response = reports_module.get_class_report_prompt_settings("class-a", _user(role="teacher"))

    assert response.source == "class"
    assert response.has_override is True
    assert response.settings.summary_prompt == "class summary"
    assert response.inherited_settings and response.inherited_settings.summary_prompt == "global summary"


def test_prompt_template_rejects_unsupported_variables() -> None:
    with pytest.raises(DomainHTTPException) as exc_info:
        reports_module._validate_prompt_settings(
            AssessmentReportPromptSettings(summary_prompt="{{unsupported_var}}", mistake_prompt="{{wrong_questions}}")
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["unsupported_variables"] == ["unsupported_var"]

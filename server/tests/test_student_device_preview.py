from __future__ import annotations

import inspect

import pytest

from server.app.auth import AuthUser
from server.app.domains.analytics import read_models
from server.app.api.student import student_platform
from server.app.domains.roster import classes as roster_classes
from server.app.domains.preview import student_device_preview
from server.app.domains.preview.student_device_preview import (
    STUDENT_DEVICE_PREVIEW_PURPOSE,
    TEACHER_PREVIEW_ACCOUNT_PURPOSE,
    TEACHER_PREVIEW_CLASS_PURPOSE,
    is_preview_user,
    preview_policy,
)
from server.app.student_app_schemas import StudentFeedbackSubmitRequest
from server.tests.route_helpers import assert_route


def _preview_user() -> AuthUser:
    return AuthUser(
        id="00000000-0000-0000-0000-000000000101",
        username="preview_student",
        role="student",
        display_name="Preview Student",
        status="active",
        student_id="TPV_STUDENT",
        class_id="TPV_CLASS",
        class_name="Preview Class",
        preview_mode=True,
        preview_purpose=STUDENT_DEVICE_PREVIEW_PURPOSE,
        preview_teacher_user_id="00000000-0000-0000-0000-000000000001",
        preview_class_id="TPV_CLASS",
        preview_student_id="TPV_STUDENT",
    )


def test_student_preview_routes_are_registered() -> None:
    assert_route("/api/admin/student-preview/session", "POST")
    assert_route("/api/preview/student-session/exchange", "POST")
    assert_route("/api/web-admin/student-preview/classes", "GET")
    assert_route("/api/web-admin/student-preview/classes/{teacher_user_id}/ensure", "POST")
    assert_route("/api/web-admin/student-preview/classes/{teacher_user_id}/reset", "POST")
    assert_route("/api/web-admin/student-preview/classes/{teacher_user_id}/disable", "POST")
    assert_route("/api/web-admin/student-preview/classes/{teacher_user_id}/restore", "POST")


def test_preview_constants_keep_separate_purposes() -> None:
    assert TEACHER_PREVIEW_CLASS_PURPOSE == "teacher_preview"
    assert TEACHER_PREVIEW_ACCOUNT_PURPOSE == "teacher_preview"
    assert STUDENT_DEVICE_PREVIEW_PURPOSE == "teacher_student_device_preview"
    assert preview_policy().feedback_enabled is True
    assert "/feedback/new" not in preview_policy().blocked_routes


def test_preview_user_detection_uses_session_claims() -> None:
    assert is_preview_user(_preview_user()) is True
    assert is_preview_user(AuthUser(id="u", username="s", role="student", display_name="S", status="active")) is False


def test_preview_feedback_write_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(student_platform, "get_learning_behavior_settings", lambda: object())

    with pytest.raises(Exception) as exc_info:
        student_platform.submit_student_feedback(
            StudentFeedbackSubmitRequest(feedback_type="other", content="preview feedback"),
            _preview_user(),
        )

    assert getattr(exc_info.value, "status_code", None) == 409


def test_preview_service_keeps_one_idempotent_teacher_owned_record_set() -> None:
    source = inspect.getsource(student_device_preview.ensure_teacher_preview_student)

    assert "ON CONFLICT (id) DO UPDATE" in source
    assert "ON CONFLICT (teacher_user_id, class_id)" in source
    assert "ON CONFLICT (username) DO UPDATE" in source
    assert "ON CONFLICT (class_id, student_id) DO UPDATE" in source
    assert "ON CONFLICT (student_id) DO UPDATE" in source
    assert "owner_teacher_user_id" in source
    assert "hidden_from_teacher" in source
    assert "system_managed" in source

    teacher_a = "00000000-0000-0000-0000-000000000001"
    teacher_b = "00000000-0000-0000-0000-000000000002"
    assert student_device_preview._preview_class_id(teacher_a) == student_device_preview._preview_class_id(teacher_a)
    assert student_device_preview._preview_student_id(teacher_a) == student_device_preview._preview_student_id(teacher_a)
    assert student_device_preview._preview_class_id(teacher_a) != student_device_preview._preview_class_id(teacher_b)
    assert student_device_preview._preview_student_id(teacher_a) != student_device_preview._preview_student_id(teacher_b)


def test_preview_ticket_exchange_is_one_time_expiring_and_claim_scoped() -> None:
    source = inspect.getsource(student_device_preview.exchange_preview_ticket)

    assert "expires_at > now()" in source
    assert "revoked_at IS NULL" in source
    assert "UPDATE auth_sessions SET revoked_at = now()" in source
    assert "Preview ticket is expired or already used" in source
    assert '"preview": True' in source
    assert '"preview_purpose": STUDENT_DEVICE_PREVIEW_PURPOSE' in source
    assert '"teacher_user_id": teacher_id' in source
    assert '"preview_class_id": class_id' in source
    assert '"preview_student_id": student_id' in source


def test_preview_reset_cleans_only_preview_student_state() -> None:
    source = inspect.getsource(student_device_preview.reset_preview_student)

    assert "ensure_teacher_preview_student_by_teacher_id" in source
    for table in [
        "student_pretest_sessions",
        "student_posttest_sessions",
        "experiment_question_attempts",
        "student_experiment_progress",
        "student_experiment_mastery",
        "student_events",
        "student_feedback",
    ]:
        assert table in source
    assert "WHERE student_id = :student_id" in source
    assert "WHERE id = :class_id" in source
    assert "DELETE FROM classes" not in source
    assert "DELETE FROM roster_entries" not in source


def test_preview_classes_and_students_are_excluded_from_teacher_and_analytics_sources() -> None:
    list_classes_source = inspect.getsource(roster_classes.list_classes)
    roster_source = inspect.getsource(roster_classes.list_roster_students)
    analytics_students_source = inspect.getsource(read_models._class_students)
    analytics_report_source = inspect.getsource(read_models.get_student_report)

    assert "COALESCE(c.class_purpose, 'instructional') <> :preview_class_purpose" in list_classes_source
    assert "COALESCE(c.hidden_from_teacher, false) IS false" in list_classes_source
    assert "COALESCE(re.entry_purpose, 'instructional') <> :preview_account_purpose" in list_classes_source
    assert "COALESCE(re.entry_purpose, 'instructional') <> :preview_account_purpose" in roster_source
    assert "COALESCE(re.entry_purpose, 'instructional') <> :preview_account_purpose" in analytics_students_source
    assert "COALESCE(sp.profile_purpose, 'instructional') <> :preview_account_purpose" in analytics_students_source
    assert "COALESCE(sp.profile_purpose, 'instructional') <> :preview_account_purpose" in analytics_report_source
    assert "COALESCE(re.entry_purpose, 'instructional') <> :preview_account_purpose" in analytics_report_source

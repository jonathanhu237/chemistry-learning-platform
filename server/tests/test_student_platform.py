from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from server.app.auth import AuthUser
from server.app.api.student import student_platform
from server.app.student_app_schemas import StudentFeedbackSubmitRequest
from server.tests.route_helpers import assert_route


def _student_user() -> AuthUser:
    return AuthUser(
        id="student-user-id",
        username="20240001",
        role="student",
        display_name="Student",
        status="active",
        must_change_password=False,
        student_id="20240001",
        class_id="class-1",
        class_name="Class 1",
    )


def _learning_settings(*, ai_enabled: bool = True, feedback_enabled: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        learning_features=SimpleNamespace(
            ai_assistant_enabled=ai_enabled,
            feedback_enabled=feedback_enabled,
        )
    )


def _ai_configuration(*, student_ai_enabled: bool = True, rag_enabled: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        enabled_features=SimpleNamespace(
            student_ai_assistant=student_ai_enabled,
            rag_access_enabled=rag_enabled,
        )
    )


def test_student_platform_routes_are_registered() -> None:
    assert_route("/api/student/app-config", "GET")
    assert_route("/api/student/feedback", "POST")


def test_student_app_config_combines_teacher_switches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(student_platform, "get_learning_behavior_settings", lambda: _learning_settings(ai_enabled=False))
    monkeypatch.setattr(
        student_platform,
        "get_ai_configuration_response",
        lambda **_: _ai_configuration(student_ai_enabled=True, rag_enabled=False),
    )

    response = student_platform.student_app_config(_student_user())

    assert response.features.ai_assistant_enabled is False
    assert response.features.feedback_enabled is True
    assert response.features.student_ai_assistant_enabled is True
    assert response.features.rag_access_enabled is False


def test_student_feedback_uses_authenticated_student_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}
    monkeypatch.setattr(student_platform, "get_learning_behavior_settings", lambda: _learning_settings())

    def fake_create_feedback_record(payload):
        captured["payload"] = payload
        return {
            "id": "feedback-1",
            "student_id": payload.student_id,
            "class_id": payload.class_id,
            "feedback_type": payload.feedback_type,
            "content": payload.content,
            "status": "open",
            "chapter_id": payload.chapter_id,
            "unit_id": payload.unit_id,
            "knowledge_point_id": payload.knowledge_point_id,
            "experiment_id": payload.experiment_id,
            "point_node_id": payload.point_node_id,
            "page_path": payload.page_path,
            "metadata": payload.metadata,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(student_platform, "create_feedback_record", fake_create_feedback_record)

    result = student_platform.submit_student_feedback(
        StudentFeedbackSubmitRequest(
            feedback_type="content",
                content="这个点位解释不够清楚",
                chapter_id="CH13",
                experiment_id="EXP_1",
                point_node_id="cat-point-candidate-1",
                catalog_path=["第 13 章", "卤素", "氯水置换"],
                page_path="/student/learning/halogens-17",
                metadata={"student_id": "client-forged", "class_id": "client-class", "screen": "learning_point"},
            ),
        _student_user(),
    )

    payload = captured["payload"]
    assert payload.student_id == "20240001"
    assert payload.class_id == "class-1"
    assert payload.metadata["screen"] == "learning_point"
    assert payload.point_node_id == "cat-point-candidate-1"
    assert payload.catalog_path == ["第 13 章", "卤素", "氯水置换"]
    assert payload.metadata["point_node_id"] == "cat-point-candidate-1"
    assert payload.metadata["catalog_path"] == ["第 13 章", "卤素", "氯水置换"]
    assert payload.metadata["client_student_id_ignored"] == "client-forged"
    assert payload.metadata["client_class_id_ignored"] == "client-class"
    assert "student_id" not in payload.metadata
    assert "class_id" not in payload.metadata
    assert result["student_id"] == "20240001"


def test_student_feedback_respects_disabled_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(student_platform, "get_learning_behavior_settings", lambda: _learning_settings(feedback_enabled=False))

    with pytest.raises(HTTPException) as exc_info:
        student_platform.submit_student_feedback(
            StudentFeedbackSubmitRequest(content="反馈入口应该关闭"),
            _student_user(),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "学生反馈入口已关闭"

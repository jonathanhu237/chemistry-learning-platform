from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

import server.app.feedback as feedback_service
from server.app.app_runtime.main import app
from server.app.auth import AuthUser, get_current_user
from server.app.feedback import feedback_submit_from_event
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings
from server.app.schemas import StudentEventRequest


@pytest.fixture()
def feedback_student(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Iterator[AuthUser]:
    test_id = uuid4().hex[:12]
    user_id = str(uuid4())
    student_id = f"FB{test_id.upper()}"
    class_id = f"class-feedback-{test_id}"
    settings = get_settings()
    monkeypatch.setattr(
        feedback_service,
        "get_settings",
        lambda: replace(settings, media_root=tmp_path / "media"),
    )
    user = AuthUser(
        id=user_id,
        username=student_id,
        role="student",
        display_name="Feedback Test Student",
        status="active",
        must_change_password=False,
        student_id=student_id,
        class_id=class_id,
        class_name="Feedback Test Class",
    )
    if settings.data_backend != "postgres":
        yield user
        return

    with db_session() as session:
        session.execute(
            text("INSERT INTO classes (id, class_name) VALUES (:class_id, :class_name)"),
            {"class_id": class_id, "class_name": user.class_name},
        )
        session.execute(
            text(
                """
                INSERT INTO app_users (id, username, role, display_name, password_hash, status)
                VALUES (CAST(:user_id AS uuid), :username, 'student', :display_name, 'test-only', 'active')
                """
            ),
            {"user_id": user_id, "username": student_id, "display_name": user.display_name},
        )
        session.execute(
            text(
                """
                INSERT INTO student_profiles (user_id, student_id, student_name, class_id, activated_at)
                VALUES (CAST(:user_id AS uuid), :student_id, :student_name, :class_id, now())
                """
            ),
            {
                "user_id": user_id,
                "student_id": student_id,
                "student_name": user.display_name,
                "class_id": class_id,
            },
        )

    try:
        yield user
    finally:
        with db_session() as session:
            session.execute(
                text("DELETE FROM student_feedback WHERE student_id = :student_id"),
                {"student_id": student_id},
            )
            session.execute(text("DELETE FROM app_users WHERE id = CAST(:user_id AS uuid)"), {"user_id": user_id})
            session.execute(text("DELETE FROM classes WHERE id = :class_id"), {"class_id": class_id})


def test_student_feedback_submission_accepts_page_context_and_attachment(feedback_student: AuthUser) -> None:
    app.dependency_overrides[get_current_user] = lambda: feedback_student
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/student/feedback",
                data={
                    "feedback_type": "course_content",
                    "content": "The report explanation needs more detail.",
                    "page_path": "/",
                    "experiment_id": "EXP_19_1_01",
                    "metadata": '{"page_type":"posttest_report","context":{"session_id":"session-test"}}',
                },
                files={"attachment": ("screen.png", b"fake-png-content", "image/png")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "open"
    assert response.json()["attachment_count"] == 1


def test_student_feedback_rejects_non_image_attachment(feedback_student: AuthUser) -> None:
    app.dependency_overrides[get_current_user] = lambda: feedback_student
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/student/feedback",
                data={
                    "feedback_type": "system_issue",
                    "content": "The page button is not working.",
                    "metadata": '{"page_type":"learning_home"}',
                },
                files={"attachment": ("debug.txt", b"not an image", "text/plain")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "Attachment must be" in response.json()["detail"]


def test_feedback_submit_from_event_preserves_catalog_point_context() -> None:
    payload = StudentEventRequest(
        student_id="20249997",
        event_type="feedback",
        experiment_id="EXP_TEST",
        point_node_id="cat-point-1",
        catalog_path=["Chapter 1", "Directory A", "Point 1"],
        metadata={
            "feedback_type": "course_content",
            "content": "Please clarify this point.",
            "page_path": "/student/catalog/cat-point-1",
        },
    )

    feedback = feedback_submit_from_event(payload)

    assert feedback.student_id == "20249997"
    assert feedback.experiment_id == "EXP_TEST"
    assert feedback.point_node_id == "cat-point-1"
    assert feedback.catalog_path == ["Chapter 1", "Directory A", "Point 1"]
    assert feedback.page_path == "/student/catalog/cat-point-1"

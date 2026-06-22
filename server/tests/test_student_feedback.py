from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.app_runtime.main import app
from server.app.auth import AuthUser, get_current_user
from server.app.feedback import feedback_submit_from_event
from server.app.schemas import StudentEventRequest


def _student_user() -> AuthUser:
    return AuthUser(
        id="student-feedback-user",
        username="20249997",
        role="student",
        display_name="Feedback Test Student",
        status="active",
        must_change_password=False,
        student_id="20249997",
        class_id="class-feedback",
        class_name="Feedback Test Class",
    )


def test_student_feedback_submission_accepts_page_context_and_attachment() -> None:
    app.dependency_overrides[get_current_user] = _student_user
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


def test_student_feedback_rejects_non_image_attachment() -> None:
    app.dependency_overrides[get_current_user] = _student_user
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

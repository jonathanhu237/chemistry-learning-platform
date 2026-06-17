from __future__ import annotations

from fastapi.testclient import TestClient

from server.app.admin_main import app
from server.app.auth import AuthUser, get_current_user


def _student_user() -> AuthUser:
    return AuthUser(
        id="student-feedback-user",
        username="20249997",
        role="student",
        display_name="反馈测试学生",
        status="active",
        must_change_password=False,
        student_id="20249997",
        class_id="class-feedback",
        class_name="反馈测试班",
    )


def test_student_feedback_submission_accepts_page_context_and_attachment() -> None:
    app.dependency_overrides[get_current_user] = _student_user
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/student/feedback",
                data={
                    "feedback_type": "course_content",
                    "content": "报告里的说明需要更清楚",
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
                    "content": "页面按钮无法正常点击",
                    "metadata": '{"page_type":"learning_home"}',
                },
                files={"attachment": ("debug.txt", b"not an image", "text/plain")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "Attachment must be" in response.json()["detail"]

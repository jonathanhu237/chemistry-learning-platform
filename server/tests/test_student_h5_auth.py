import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from server.app.app_runtime.main import app
from server.app import auth as auth_module
from server.app.auth import AuthUser, PasswordChangeRequest, StudentLoginRequest, StudentPasswordChangeRequest, require_roles


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_teacher_entrypoint_exposes_student_login_only() -> None:
    paths = app.openapi()["paths"]

    assert "/api/auth/student/login" in paths
    assert "/api/auth/student/password" in paths
    assert "/api/auth/student/activate" not in paths
    assert "/api/auth/student/register" not in paths


def test_student_initial_password_change_does_not_require_current_password() -> None:
    payload = StudentPasswordChangeRequest(new_password="new-pass-123")

    assert payload.current_password is None
    assert payload.new_password == "new-pass-123"


def test_student_login_reports_missing_roster_student(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummySession:
        def __enter__(self) -> "DummySession":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr(auth_module, "_load_user_with_hash", lambda _student_id: None)
    monkeypatch.setattr(auth_module, "db_session", lambda: DummySession())
    monkeypatch.setattr(auth_module, "_load_student_roster_for_login", lambda _session, _student_id: None)

    with pytest.raises(HTTPException) as exc_info:
        auth_module.student_login(StudentLoginRequest(student_id="99999999", password="123456"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == auth_module.STUDENT_NOT_FOUND_DETAIL


def test_teacher_password_change_still_requires_current_password() -> None:
    with pytest.raises(ValidationError):
        PasswordChangeRequest(new_password="new-pass-123")


@pytest.mark.anyio
async def test_student_must_change_password_is_blocked_from_role_dependencies() -> None:
    dependency = require_roles("student")
    user = AuthUser(
        id="student-user",
        username="20240001",
        role="student",
        display_name="Student",
        status="active",
        must_change_password=True,
    )

    with pytest.raises(HTTPException) as exc_info:
        await dependency(user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Password change required"


@pytest.mark.anyio
async def test_student_without_password_requirement_passes_role_dependency() -> None:
    dependency = require_roles("student")
    user = AuthUser(
        id="student-user",
        username="20240001",
        role="student",
        display_name="Student",
        status="active",
        must_change_password=False,
    )

    assert await dependency(user) is user

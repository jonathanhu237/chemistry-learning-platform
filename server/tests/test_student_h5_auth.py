import pytest
from fastapi import HTTPException

from server.app.admin_main import app
from server.app.auth import AuthUser, require_roles


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_admin_entrypoint_exposes_student_login_only() -> None:
    paths = app.openapi()["paths"]

    assert "/api/auth/student/login" in paths
    assert "/api/auth/student/password" in paths
    assert "/api/auth/student/activate" not in paths
    assert "/api/auth/student/register" not in paths


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

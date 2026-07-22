from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from server.app.api.admin import admin_teacher_accounts
from server.app.app_runtime.main import app
from server.app.auth import (
    AuthUser,
    get_current_user,
    require_supervisor_teacher,
    require_teacher_console_user,
)
from server.app.domains.errors import DomainHTTPException
from server.app.domains.platform import teacher_accounts

ACTOR_ID = "00000000-0000-0000-0000-000000000001"
TARGET_ID = "00000000-0000-0000-0000-000000000010"
OTHER_SUPERVISOR_ID = "00000000-0000-0000-0000-000000000011"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class _FakeResult:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []

    def mappings(self) -> _FakeResult:
        return self

    def all(self) -> list[dict[str, Any]]:
        return self._rows

    def one(self) -> dict[str, Any]:
        return self._rows[0]

    def first(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None


class _FakeSession:
    def __init__(self, results: list[_FakeResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, statement: Any, params: dict[str, Any] | None = None) -> _FakeResult:
        self.calls.append((str(statement), params or {}))
        if not self.results:
            return _FakeResult()
        return self.results.pop(0)


@contextmanager
def _fake_db_session(session: _FakeSession):
    yield session


def _user(role: str, *, must_change_password: bool = False) -> AuthUser:
    return AuthUser(
        id=ACTOR_ID,
        username=role,
        role=role,
        display_name=role,
        status="active",
        must_change_password=must_change_password,
    )


def _teacher_row(**overrides: Any) -> dict[str, Any]:
    row = {
        "id": TARGET_ID,
        "username": "teacher-a",
        "role": "teacher",
        "display_name": "Teacher A",
        "status": "active",
        "must_change_password": True,
        "password_version": 1,
        "created_at": None,
        "updated_at": None,
        "last_login_at": None,
    }
    row.update(overrides)
    return row


def test_teacher_account_routes_move_to_supervisor_teacher_api() -> None:
    paths = app.openapi()["paths"]

    assert {"get", "post"} <= set(paths["/api/admin/teacher-accounts"])
    assert "post" in paths["/api/admin/teacher-accounts/{account_id}/reset-password"]
    assert "post" in paths["/api/admin/teacher-accounts/{account_id}/disable"]
    assert "post" in paths["/api/admin/teacher-accounts/{account_id}/enable"]
    assert "patch" not in paths.get("/api/admin/teacher-accounts/{account_id}", {})
    assert "delete" not in paths.get("/api/admin/teacher-accounts/{account_id}", {})
    assert "/api/web-admin/session" not in paths
    assert "/api/web-admin/teacher-accounts" not in paths
    assert "/api/web-admin/student-preview/classes" not in paths


@pytest.mark.anyio
async def test_teacher_console_and_supervisor_dependencies_enforce_roles_and_password_gate() -> None:
    assert await require_teacher_console_user(_user("teacher"))
    assert await require_teacher_console_user(_user("admin"))
    assert await require_supervisor_teacher(_user("admin"))

    for dependency, user in [
        (require_teacher_console_user, _user("teacher", must_change_password=True)),
        (require_supervisor_teacher, _user("admin", must_change_password=True)),
    ]:
        with pytest.raises(HTTPException) as exc_info:
            await dependency(user)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Password change required"

    for user in [_user("teacher"), _user("student"), _user("platform_admin")]:
        with pytest.raises(HTTPException) as exc_info:
            await require_supervisor_teacher(user)
        assert exc_info.value.status_code == 403


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/api/admin/teacher-accounts", None),
        (
            "POST",
            "/api/admin/teacher-accounts",
            {"username": "teacher-a", "display_name": "Teacher A", "password": "initial-pass"},
        ),
        ("POST", f"/api/admin/teacher-accounts/{TARGET_ID}/reset-password", {"password": "reset-pass"}),
        ("POST", f"/api/admin/teacher-accounts/{TARGET_ID}/disable", {}),
        ("POST", f"/api/admin/teacher-accounts/{TARGET_ID}/enable", {}),
    ],
)
def test_ordinary_teacher_cannot_call_any_peer_account_route(
    method: str,
    path: str,
    json_body: dict[str, str] | None,
) -> None:
    test_app = FastAPI()
    test_app.include_router(admin_teacher_accounts.router)
    test_app.dependency_overrides[get_current_user] = lambda: _user("teacher")

    with TestClient(test_app) as client:
        response = client.request(method, path, json=json_body)

    assert response.status_code == 403
    assert response.json()["detail"] == "Supervisor teacher account required"


def test_supervisor_router_passes_actor_identity_to_peer_mutation(monkeypatch: pytest.MonkeyPatch) -> None:
    received: list[tuple[str, str]] = []
    response_row = _teacher_row(status="disabled", password_version=2)

    def fake_disable(account_id: str, *, actor_user_id: str) -> teacher_accounts.TeacherAccountResponse:
        received.append((account_id, actor_user_id))
        return teacher_accounts.TeacherAccountResponse(**response_row)

    monkeypatch.setattr(admin_teacher_accounts, "disable_teacher_account", fake_disable)
    test_app = FastAPI()
    test_app.include_router(admin_teacher_accounts.router)
    test_app.dependency_overrides[get_current_user] = lambda: _user("admin")

    with TestClient(test_app) as client:
        response = client.post(f"/api/admin/teacher-accounts/{TARGET_ID}/disable")

    assert response.status_code == 200
    assert received == [(TARGET_ID, ACTOR_ID)]


def test_create_and_reset_requests_reject_removed_control_fields() -> None:
    with pytest.raises(ValidationError):
        teacher_accounts.TeacherAccountCreateRequest(
            username="teacher-a",
            display_name="Teacher A",
            password="initial-pass",
            role="admin",
        )
    with pytest.raises(ValidationError):
        teacher_accounts.TeacherAccountPasswordResetRequest(
            password="reset-pass",
            must_change_password=False,
        )


def test_list_teacher_accounts_omits_password_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession([_FakeResult([_teacher_row()])])
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))

    accounts = teacher_accounts.list_teacher_accounts()

    assert accounts[0].role == "teacher"
    assert "password_hash" not in accounts[0].model_dump()
    assert "role IN ('admin', 'teacher')" in session.calls[0][0]


def test_create_teacher_account_is_always_ordinary_and_forces_password_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession([_FakeResult([_teacher_row()])])
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))
    monkeypatch.setattr(teacher_accounts, "hash_password", lambda password: f"hashed:{password}")

    account = teacher_accounts.create_teacher_account(
        teacher_accounts.TeacherAccountCreateRequest(
            username=" teacher-a ",
            display_name=" Teacher A ",
            password="initial-pass",
        )
    )

    statement, params = session.calls[0]
    assert "'teacher'" in statement
    assert "true, 1" in statement
    assert params == {
        "username": "teacher-a",
        "display_name": "Teacher A",
        "password_hash": "hashed:initial-pass",
    }
    assert account.role == "teacher"
    assert account.must_change_password is True


def test_reset_peer_password_forces_change_increments_version_and_revokes_sessions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession(
        [_FakeResult([_teacher_row(password_version=3, must_change_password=True)]), _FakeResult()]
    )
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))
    monkeypatch.setattr(teacher_accounts, "hash_password", lambda password: f"hashed:{password}")

    account = teacher_accounts.reset_teacher_account_password(
        TARGET_ID,
        teacher_accounts.TeacherAccountPasswordResetRequest(password="next-pass"),
        actor_user_id=ACTOR_ID,
    )

    assert "must_change_password = true" in session.calls[0][0]
    assert "password_version = password_version + 1" in session.calls[0][0]
    assert session.calls[0][1]["password_hash"] == "hashed:next-pass"
    assert "UPDATE auth_sessions" in session.calls[1][0]
    assert account.must_change_password is True


@pytest.mark.parametrize(
    "operation",
    [
        lambda: teacher_accounts.reset_teacher_account_password(
            ACTOR_ID,
            teacher_accounts.TeacherAccountPasswordResetRequest(password="next-pass"),
            actor_user_id=ACTOR_ID,
        ),
        lambda: teacher_accounts.disable_teacher_account(ACTOR_ID, actor_user_id=ACTOR_ID),
        lambda: teacher_accounts.enable_teacher_account(ACTOR_ID, actor_user_id=ACTOR_ID),
    ],
)
def test_peer_account_mutations_forbid_self(operation: Callable[[], object]) -> None:
    with pytest.raises(DomainHTTPException) as exc_info:
        operation()

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == teacher_accounts.SELF_PEER_OPERATION_DETAIL


def test_disable_peer_forces_change_increments_version_and_revokes_sessions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession(
        [
            _FakeResult([{"id": ACTOR_ID, "status": "active"}]),
            _FakeResult([_teacher_row()]),
            _FakeResult([_teacher_row(status="disabled", password_version=2)]),
            _FakeResult(),
        ]
    )
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))

    account = teacher_accounts.disable_teacher_account(TARGET_ID, actor_user_id=ACTOR_ID)

    assert "FOR UPDATE" in session.calls[0][0]
    assert "FOR UPDATE" in session.calls[1][0]
    assert "must_change_password = true" in session.calls[2][0]
    assert "password_version = password_version + 1" in session.calls[2][0]
    assert "UPDATE auth_sessions" in session.calls[3][0]
    assert account.status == "disabled"


def test_disable_last_active_supervisor_is_blocked_inside_locked_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _teacher_row(role="admin", status="active")
    session = _FakeSession(
        [
            _FakeResult([{"id": TARGET_ID, "status": "active"}]),
            _FakeResult([target]),
        ]
    )
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))

    with pytest.raises(DomainHTTPException) as exc_info:
        teacher_accounts.disable_teacher_account(TARGET_ID, actor_user_id=ACTOR_ID)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == teacher_accounts.LAST_ACTIVE_SUPERVISOR_DETAIL
    assert "WHERE role = 'admin'" in session.calls[0][0]
    assert "FOR UPDATE" in session.calls[0][0]
    assert all("SET status = 'disabled'" not in statement for statement, _params in session.calls)


def test_disable_supervisor_succeeds_when_another_active_supervisor_remains(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _teacher_row(role="admin", status="active")
    session = _FakeSession(
        [
            _FakeResult(
                [
                    {"id": TARGET_ID, "status": "active"},
                    {"id": OTHER_SUPERVISOR_ID, "status": "active"},
                ]
            ),
            _FakeResult([target]),
            _FakeResult([_teacher_row(role="admin", status="disabled", password_version=2)]),
            _FakeResult(),
        ]
    )
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))

    account = teacher_accounts.disable_teacher_account(TARGET_ID, actor_user_id=ACTOR_ID)

    assert account.role == "admin"
    assert account.status == "disabled"


def test_enable_peer_preserves_forced_password_change(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession([_FakeResult([_teacher_row(status="active", must_change_password=True, password_version=2)])])
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))

    account = teacher_accounts.enable_teacher_account(TARGET_ID, actor_user_id=ACTOR_ID)

    assert "SET status = 'active'" in session.calls[0][0]
    assert "password_version" not in session.calls[0][0].split("RETURNING", maxsplit=1)[0]
    assert account.status == "active"
    assert account.must_change_password is True


def test_role_edit_and_delete_domain_operations_are_removed() -> None:
    assert not hasattr(teacher_accounts, "TeacherAccountPatchRequest")
    assert not hasattr(teacher_accounts, "patch_teacher_account")
    assert not hasattr(teacher_accounts, "delete_teacher_account")

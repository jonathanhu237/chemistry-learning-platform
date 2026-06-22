from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from server.app.api.web_admin.auth import require_web_admin_token
from server.app.app_runtime.main import app
from server.app.auth import AuthUser, require_teacher_console_user
from server.app.domains.errors import DomainHTTPException
from server.app.domains.platform import teacher_accounts
from server.app.infrastructure.settings import get_settings


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


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


def _user(role: str) -> AuthUser:
    return AuthUser(
        id="00000000-0000-0000-0000-000000000001",
        username=role,
        role=role,
        display_name=role,
        status="active",
    )


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _teacher_row(**overrides: Any) -> dict[str, Any]:
    row = {
        "id": "00000000-0000-0000-0000-000000000010",
        "username": "teacher-a",
        "role": "admin",
        "display_name": "Teacher A",
        "status": "active",
        "must_change_password": True,
        "password_version": 1,
        "password_hash": "secret-hash",
        "created_at": None,
        "updated_at": None,
        "last_login_at": None,
    }
    row.update(overrides)
    return row


def test_web_admin_teacher_account_routes_are_registered() -> None:
    paths = app.openapi()["paths"]

    assert "/api/web-admin/session" in paths
    assert "get" in paths["/api/web-admin/session"]
    assert "/api/web-admin/teacher-accounts" in paths
    assert "get" in paths["/api/web-admin/teacher-accounts"]
    assert "post" in paths["/api/web-admin/teacher-accounts"]
    assert "patch" in paths["/api/web-admin/teacher-accounts/{account_id}"]
    assert "post" in paths["/api/web-admin/teacher-accounts/{account_id}/reset-password"]
    assert "post" in paths["/api/web-admin/teacher-accounts/{account_id}/disable"]
    assert "post" in paths["/api/web-admin/teacher-accounts/{account_id}/enable"]
    assert "delete" in paths["/api/web-admin/teacher-accounts/{account_id}"]


def test_web_admin_token_accepts_configured_token(monkeypatch: pytest.MonkeyPatch) -> None:
    token = "local-test-web-admin-token-0123456789"
    monkeypatch.setenv("WEB_ADMIN_ACCESS_TOKEN", token)
    get_settings.cache_clear()

    assert require_web_admin_token(_credentials(token)) is None


def test_web_admin_token_rejects_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEB_ADMIN_ACCESS_TOKEN", "local-test-web-admin-token-0123456789")
    get_settings.cache_clear()

    with pytest.raises(HTTPException) as exc_info:
        require_web_admin_token(_credentials("wrong-token"))

    assert exc_info.value.status_code == 401


def test_web_admin_token_requires_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WEB_ADMIN_ACCESS_TOKEN", raising=False)
    get_settings.cache_clear()

    with pytest.raises(HTTPException) as exc_info:
        require_web_admin_token(_credentials("any-token"))

    assert exc_info.value.status_code == 503


@pytest.mark.anyio
async def test_teacher_console_helper_allows_legacy_teacher_and_rejects_platform_admin() -> None:
    assert await require_teacher_console_user(_user("teacher"))
    assert await require_teacher_console_user(_user("admin"))

    with pytest.raises(HTTPException) as exc_info:
        await require_teacher_console_user(_user("platform_admin"))

    assert exc_info.value.status_code == 403


def test_list_teacher_accounts_omits_password_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession([_FakeResult([_teacher_row(role="teacher")])])
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))

    accounts = teacher_accounts.list_teacher_accounts()

    assert accounts[0].role == "teacher"
    assert "password_hash" not in accounts[0].model_dump()
    assert "role IN ('admin', 'teacher')" in session.calls[0][0]


def test_create_teacher_account_writes_admin_role(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession([_FakeResult([_teacher_row(role="admin", password_version=1)])])
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
    assert "VALUES (" in statement
    assert "'admin'" in statement
    assert params["username"] == "teacher-a"
    assert params["display_name"] == "Teacher A"
    assert params["password_hash"] == "hashed:initial-pass"
    assert account.role == "admin"
    assert "password_hash" not in account.model_dump()


def test_reset_teacher_password_increments_version_and_revokes_sessions(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession([_FakeResult([_teacher_row(password_version=3)]), _FakeResult()])
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))
    monkeypatch.setattr(teacher_accounts, "hash_password", lambda password: f"hashed:{password}")

    account = teacher_accounts.reset_teacher_account_password(
        "00000000-0000-0000-0000-000000000010",
        teacher_accounts.TeacherAccountPasswordResetRequest(password="next-pass"),
    )

    assert "password_version = password_version + 1" in session.calls[0][0]
    assert session.calls[0][1]["password_hash"] == "hashed:next-pass"
    assert "UPDATE auth_sessions" in session.calls[1][0]
    assert account.password_version == 3
    assert "password_hash" not in account.model_dump()


def test_patch_teacher_account_can_migrate_legacy_teacher_role(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession([_FakeResult([_teacher_row(role="admin")]), _FakeResult()])
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))

    account = teacher_accounts.patch_teacher_account(
        "00000000-0000-0000-0000-000000000010",
        teacher_accounts.TeacherAccountPatchRequest(role="admin"),
    )

    assert "role = COALESCE(:role, role)" in session.calls[0][0]
    assert session.calls[0][1]["role"] == "admin"
    assert "UPDATE auth_sessions" in session.calls[1][0]
    assert account.role == "admin"
    assert "password_hash" not in account.model_dump()


def test_disable_teacher_account_soft_disables(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession([_FakeResult([_teacher_row(status="disabled")]), _FakeResult()])
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))

    account = teacher_accounts.disable_teacher_account("00000000-0000-0000-0000-000000000010")

    assert "SET display_name = COALESCE" in session.calls[0][0]
    assert session.calls[0][1]["status"] == "disabled"
    assert account.status == "disabled"


def test_enable_teacher_account_restores_active_status(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession([_FakeResult([_teacher_row(status="active")])])
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))

    account = teacher_accounts.enable_teacher_account("00000000-0000-0000-0000-000000000010")

    assert "SET display_name = COALESCE" in session.calls[0][0]
    assert session.calls[0][1]["status"] == "active"
    assert account.status == "active"


def test_delete_teacher_account_removes_unused_account(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession(
        [
            _FakeResult([_teacher_row(status="disabled")]),
            _FakeResult([]),
            _FakeResult([_teacher_row(status="disabled")]),
        ]
    )
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))

    account = teacher_accounts.delete_teacher_account("00000000-0000-0000-0000-000000000010")

    assert "FROM app_users" in session.calls[0][0]
    assert "information_schema.table_constraints" in session.calls[1][0]
    assert "DELETE FROM app_users" in session.calls[2][0]
    assert account.id == "00000000-0000-0000-0000-000000000010"
    assert "password_hash" not in account.model_dump()


def test_delete_teacher_account_blocks_owned_records(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession(
        [
            _FakeResult([_teacher_row(status="disabled")]),
            _FakeResult(
                [
                    {
                        "table_schema": "public",
                        "table_name": "teacher_classes",
                        "column_name": "teacher_user_id",
                    }
                ]
            ),
            _FakeResult([{"dependency_count": 1}]),
        ]
    )
    monkeypatch.setattr(teacher_accounts, "db_session", lambda: _fake_db_session(session))

    with pytest.raises(DomainHTTPException) as exc_info:
        teacher_accounts.delete_teacher_account("00000000-0000-0000-0000-000000000010")

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == teacher_accounts.TEACHER_ACCOUNT_DELETE_BLOCKED_DETAIL
    assert all("DELETE FROM app_users" not in call[0] for call in session.calls)

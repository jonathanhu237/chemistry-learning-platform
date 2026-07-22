from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import pytest
from fastapi import HTTPException

from server.app import auth
from server.app.app_runtime.main import app


class _FakeResult:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows = rows or []

    def mappings(self) -> _FakeResult:
        return self

    def first(self) -> dict[str, Any] | None:
        return self.rows[0] if self.rows else None

    def one(self) -> dict[str, Any]:
        return self.rows[0]


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


def _user(*, role: str = "teacher", must_change_password: bool = True) -> auth.AuthUser:
    return auth.AuthUser(
        id="00000000-0000-0000-0000-000000000001",
        username="teacher-a",
        role=role,
        display_name="Teacher A",
        status="active",
        must_change_password=must_change_password,
        password_version=1,
    )


def _updated_row(*, role: str = "teacher") -> dict[str, Any]:
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "username": "teacher-a",
        "role": role,
        "display_name": "Teacher A",
        "status": "active",
        "must_change_password": False,
        "password_version": 2,
    }


def test_direct_protected_token_resolution_enforces_password_change_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forced_row = {**_updated_row(), "must_change_password": True, "password_version": 1}
    session = _FakeSession([_FakeResult([forced_row]), _FakeResult([forced_row])])
    monkeypatch.setattr(auth, "db_session", lambda: _fake_db_session(session))
    monkeypatch.setattr(
        auth,
        "decode_access_token",
        lambda _token: {
            "sub": forced_row["id"],
            "jti": "session-jti",
            "password_version": 1,
        },
    )

    with pytest.raises(HTTPException) as exc_info:
        auth.get_user_from_access_token("forced-token")

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Password change required"
    resolved = auth.get_user_from_access_token(
        "forced-token",
        allow_password_change_required=True,
    )
    assert resolved.must_change_password is True


def test_self_password_change_verifies_current_password_revokes_old_sessions_and_rotates_login(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession(
        [
            _FakeResult([{"password_hash": "old-hash"}]),
            _FakeResult([_updated_row()]),
            _FakeResult(),
        ]
    )
    issued_users: list[auth.AuthUser] = []
    monkeypatch.setattr(auth, "db_session", lambda: _fake_db_session(session))
    monkeypatch.setattr(auth, "verify_password", lambda value, _password_hash: value == "current-pass")
    monkeypatch.setattr(auth, "hash_password", lambda value: f"hashed:{value}")

    def issue_login(user: auth.AuthUser) -> auth.LoginResponse:
        issued_users.append(user)
        return auth.LoginResponse(access_token="replacement-token", expires_at="2030-01-01T00:00:00+00:00", user=user)

    monkeypatch.setattr(auth, "_issue_login_response", issue_login)

    response = auth.change_password(
        auth.PasswordChangeRequest(current_password="current-pass", new_password="next-pass"),
        user=_user(),
    )

    assert response.access_token == "replacement-token"
    assert "FOR UPDATE" in session.calls[0][0]
    assert "password_version = password_version + 1" in session.calls[1][0]
    assert session.calls[1][1]["password_hash"] == "hashed:next-pass"
    assert "UPDATE auth_sessions" in session.calls[2][0]
    assert "token_jti" not in session.calls[2][0]
    assert issued_users[0].password_version == 2
    assert issued_users[0].must_change_password is False


def test_self_password_change_rejects_invalid_current_password(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession([_FakeResult([{"password_hash": "old-hash"}])])
    monkeypatch.setattr(auth, "db_session", lambda: _fake_db_session(session))
    monkeypatch.setattr(auth, "verify_password", lambda _value, _password_hash: False)

    with pytest.raises(HTTPException) as exc_info:
        auth.change_password(
            auth.PasswordChangeRequest(current_password="wrong-pass", new_password="next-pass"),
            user=_user(),
        )

    assert exc_info.value.status_code == 401
    assert len(session.calls) == 1


def test_self_password_change_cannot_clear_forced_gate_by_reusing_current_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession([_FakeResult([{"password_hash": "old-hash"}])])
    monkeypatch.setattr(auth, "db_session", lambda: _fake_db_session(session))
    monkeypatch.setattr(auth, "verify_password", lambda value, _password_hash: value == "same-pass")

    with pytest.raises(HTTPException) as exc_info:
        auth.change_password(
            auth.PasswordChangeRequest(current_password="same-pass", new_password="same-pass"),
            user=_user(),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "New password must be different"
    assert len(session.calls) == 1


def test_student_initial_password_change_also_rejects_password_reuse(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession([_FakeResult([{"password_hash": "old-hash"}])])
    monkeypatch.setattr(auth, "db_session", lambda: _fake_db_session(session))
    monkeypatch.setattr(auth, "verify_password", lambda value, _password_hash: value == "same-pass")

    with pytest.raises(HTTPException) as exc_info:
        auth.change_student_password(
            auth.StudentPasswordChangeRequest(new_password="same-pass"),
            user=_user(role="student"),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "New password must be different"
    assert len(session.calls) == 1


def test_password_route_documents_rotated_login_response() -> None:
    response_schema = app.openapi()["paths"]["/api/auth/password"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]

    assert response_schema["$ref"].endswith("/LoginResponse")

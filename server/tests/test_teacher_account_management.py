from __future__ import annotations

import asyncio
from contextlib import contextmanager
from typing import Any

import pytest
from fastapi import HTTPException

from server.app.api.teacher import teacher_platform
from server.app.auth import AuthUser


class _FakeResult:
    def __init__(self, *, first: Any = None, one: dict[str, Any] | None = None) -> None:
        self._first = first
        self._one = one

    def first(self) -> Any:
        return self._first

    def mappings(self) -> "_FakeResult":
        return self

    def one(self) -> dict[str, Any]:
        if self._one is None:
            raise AssertionError("No fake row configured")
        return self._one


class _FakeSession:
    def __init__(self, *, duplicate: bool = False) -> None:
        self.duplicate = duplicate
        self.calls: list[dict[str, Any]] = []

    def execute(self, statement: Any, params: dict[str, Any] | None = None) -> _FakeResult:
        sql = str(statement)
        self.calls.append({"sql": sql, "params": params or {}})
        if "SELECT id FROM app_users" in sql:
            return _FakeResult(first={"id": "existing-teacher"} if self.duplicate else None)
        if "INSERT INTO app_users" in sql:
            return _FakeResult(
                one={
                    "id": "teacher-2",
                    "username": params["username"],
                    "role": params["role"],
                    "display_name": params["display_name"],
                    "status": "active",
                    "must_change_password": params["must_change_password"],
                }
            )
        raise AssertionError(f"Unexpected SQL: {sql}")


def _teacher_user() -> AuthUser:
    return AuthUser(
        id="teacher-1",
        username="teacher",
        role="teacher",
        display_name="王老师",
        status="active",
        must_change_password=False,
    )


def test_teacher_create_teacher_account_inserts_teacher_user(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession()

    @contextmanager
    def fake_db_session():
        yield session

    monkeypatch.setattr(teacher_platform, "db_session", fake_db_session)
    monkeypatch.setattr(teacher_platform, "hash_password", lambda password: f"hashed:{password}")

    response = asyncio.run(
        teacher_platform.teacher_create_teacher_account(
            teacher_platform.TeacherAccountCreateRequest(
                username=" teacher2 ",
                display_name=" 李老师 ",
                password="teacher-pass-123",
                must_change_password=True,
            ),
            user=_teacher_user(),
        )
    )

    assert response.username == "teacher2"
    assert response.display_name == "李老师"
    assert response.role == "teacher"
    assert response.must_change_password is True

    insert_call = next(call for call in session.calls if "INSERT INTO app_users" in call["sql"])
    assert insert_call["params"] == {
        "username": "teacher2",
        "role": "teacher",
        "display_name": "李老师",
        "password_hash": "hashed:teacher-pass-123",
        "must_change_password": True,
    }


def test_teacher_create_teacher_account_rejects_duplicate_username(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession(duplicate=True)

    @contextmanager
    def fake_db_session():
        yield session

    monkeypatch.setattr(teacher_platform, "db_session", fake_db_session)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            teacher_platform.teacher_create_teacher_account(
                teacher_platform.TeacherAccountCreateRequest(
                    username="teacher",
                    display_name="王老师",
                    password="teacher-pass-123",
                ),
                user=_teacher_user(),
            )
        )

    assert exc_info.value.status_code == 409

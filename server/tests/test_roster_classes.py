from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from server.app.domains.errors import DomainHTTPException
from server.app.domains.roster.classes import (
    RegistrationSettingsUpdateRequest,
    StudentPasswordResetRequest,
    _disable_class_roster_entries,
    _raise_if_roster_has_cross_class_conflicts,
)


class _Result:
    def __init__(self, *, rows: list[dict[str, str]] | None = None, scalar: int = 0) -> None:
        self.rows = rows or []
        self.scalar = scalar

    def mappings(self) -> "_Result":
        return self

    def all(self) -> list[dict[str, str]]:
        return self.rows

    def scalar_one(self) -> int:
        return self.scalar


class _Session:
    def __init__(self, *, conflicts: list[dict[str, str]] | None = None, disabled: int = 0) -> None:
        self.conflicts = conflicts or []
        self.disabled = disabled
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, statement: object, params: dict[str, Any]) -> _Result:
        sql = str(statement)
        self.calls.append((sql, params))
        if "COUNT(*) FROM disabled_roster" in sql:
            return _Result(scalar=self.disabled)
        if "FROM roster_entries re" in sql:
            return _Result(rows=self.conflicts)
        return _Result()


def test_roster_cross_class_conflicts_are_locked_and_reported() -> None:
    session = _Session(
        conflicts=[
            {
                "normalized_student_id": "26320101",
                "student_id": "26320101",
                "student_name": "宋佳",
                "class_id": "class-2",
                "class_name": "26 级本科 2 班",
            }
        ]
    )

    with pytest.raises(DomainHTTPException) as error:
        _raise_if_roster_has_cross_class_conflicts(session, "class-1", {"26320101"})

    assert error.value.status_code == 409
    assert "26320101（宋佳，26 级本科 2 班）" in str(error.value.detail)
    assert "pg_advisory_xact_lock" in session.calls[0][0]
    assert session.calls[1][1]["class_id"] == "class-1"


def test_archiving_class_disables_roster_accounts_students_and_sessions() -> None:
    session = _Session(disabled=30)

    assert _disable_class_roster_entries(session, "class-1") == 30
    sql, params = session.calls[0]
    assert params == {"class_id": "class-1"}
    assert "UPDATE roster_entries" in sql
    assert "UPDATE app_users" in sql
    assert "password_version = password_version + 1" in sql
    assert "UPDATE auth_sessions" in sql
    assert "UPDATE students" in sql
    assert "re.activated_user_id" in sql
    assert "sp.user_id AS profile_user_id" in sql
    assert "target_user_ids" in sql
    assert "COALESCE(sp.user_id, re.activated_user_id)" not in sql


def test_roster_initial_password_accepts_seed_style_six_characters() -> None:
    settings = RegistrationSettingsUpdateRequest(
        mode="roster_only",
        default_password_mode="shared",
        default_password="123456",
    )
    reset = StudentPasswordResetRequest(initial_password="123456")

    assert settings.default_password == "123456"
    assert reset.initial_password == "123456"


def test_archived_class_cleanup_migration_matches_runtime_contract() -> None:
    sql = Path("server/migrations/049_disable_archived_class_roster_entries.sql").read_text(encoding="utf-8")

    assert "class_record.status = 'archived'" in sql
    assert "roster.activated_user_id" in sql
    assert "profile.user_id AS profile_user_id" in sql
    assert "archived_user_ids" in sql
    assert "COALESCE(profile.user_id, roster.activated_user_id)" not in sql
    assert "UPDATE roster_entries" in sql
    assert "UPDATE app_users" in sql
    assert "UPDATE auth_sessions" in sql
    assert "UPDATE students" in sql

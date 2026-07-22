from __future__ import annotations

from pathlib import Path

import pytest

from scripts.bootstrap_admin import bootstrap_user
from server.app.domains.platform.roles import (
    ORDINARY_TEACHER_ROLE,
    STUDENT_ROLE,
    SUPERVISOR_TEACHER_ROLE,
    TEACHER_CONSOLE_ROLES,
    is_supervisor_teacher_role,
    is_teacher_console_role,
)

MIGRATION = Path("server/migrations/046_retire_platform_admin_role.sql")


def test_identity_migration_maps_platform_admin_and_restores_three_role_constraint() -> None:
    migration = MIGRATION.read_text(encoding="utf-8")

    assert "SET role = 'admin'" in migration
    assert "WHERE role = 'platform_admin'" in migration
    assert "DROP CONSTRAINT IF EXISTS app_users_role_check" in migration
    assert "CHECK (role IN ('admin', 'teacher', 'student'))" in migration
    constraint_sql = migration.split("ADD CONSTRAINT app_users_role_check", maxsplit=1)[1]
    assert "platform_admin" not in constraint_sql


def test_runtime_role_taxonomy_contains_only_supervisor_teacher_and_student_roles() -> None:
    assert SUPERVISOR_TEACHER_ROLE == "admin"
    assert ORDINARY_TEACHER_ROLE == "teacher"
    assert STUDENT_ROLE == "student"
    assert TEACHER_CONSOLE_ROLES == {"admin", "teacher"}
    assert is_teacher_console_role("admin")
    assert is_teacher_console_role("teacher")
    assert not is_teacher_console_role("platform_admin")
    assert is_supervisor_teacher_role("admin")
    assert not is_supervisor_teacher_role("teacher")


def test_bootstrap_rejects_retired_platform_admin_role() -> None:
    with pytest.raises(ValueError, match="admin or teacher"):
        bootstrap_user("legacy-admin", "password-123", "Legacy Admin", "platform_admin")

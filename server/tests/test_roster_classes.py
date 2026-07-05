from __future__ import annotations

import pytest

from server.app.domains.errors import DomainHTTPException
from server.app.domains.roster.classes import (
    RegistrationSettingsUpdateRequest,
    StudentPasswordResetRequest,
    _natural_class_sort_key,
    _raise_if_roster_import_has_cross_class_conflicts,
)


class _FakeExecuteResult:
    def __init__(self, rows: list[dict[str, str]]) -> None:
        self.rows = rows

    def mappings(self) -> "_FakeExecuteResult":
        return self

    def all(self) -> list[dict[str, str]]:
        return self.rows


class _FakeSession:
    def __init__(self, rows: list[dict[str, str]]) -> None:
        self.rows = rows
        self.params: dict[str, str] | None = None

    def execute(self, _statement: object, params: dict[str, str]) -> _FakeExecuteResult:
        self.params = params
        return _FakeExecuteResult(self.rows)


def test_class_sort_key_orders_demo_class_names_naturally() -> None:
    rows = [
        {"id": "class-10", "class_name": "26 级本科 10 班"},
        {"id": "class-2", "class_name": "26 级本科 2 班"},
        {"id": "class-1", "class_name": "26 级本科 1 班"},
    ]

    assert [row["class_name"] for row in sorted(rows, key=_natural_class_sort_key)] == [
        "26 级本科 1 班",
        "26 级本科 2 班",
        "26 级本科 10 班",
    ]


def test_roster_import_cross_class_conflicts_are_reported_as_business_error() -> None:
    session = _FakeSession(
        [
            {"student_id": "26320101", "student_name": "宋佳", "class_name": "26 级本科 2 班"},
        ]
    )

    with pytest.raises(DomainHTTPException) as exc_info:
        _raise_if_roster_import_has_cross_class_conflicts(session, "seed-class-2026-6", {"26320101"})

    assert exc_info.value.status_code == 409
    assert "26320101（宋佳，26 级本科 2 班）" in str(exc_info.value.detail)


def test_student_initial_password_allows_seed_style_six_character_password() -> None:
    settings = RegistrationSettingsUpdateRequest(
        mode="roster_only",
        default_password_mode="shared",
        default_password="123456",
    )
    reset = StudentPasswordResetRequest(initial_password="123456")

    assert settings.default_password == "123456"
    assert reset.initial_password == "123456"

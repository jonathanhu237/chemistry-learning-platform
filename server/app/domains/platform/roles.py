from __future__ import annotations

PLATFORM_ADMIN_ROLE = "platform_admin"
TEACHER_CONSOLE_ROLES = frozenset({"admin", "teacher"})


def is_teacher_console_role(role: str) -> bool:
    return role in TEACHER_CONSOLE_ROLES

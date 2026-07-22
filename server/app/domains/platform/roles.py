from __future__ import annotations

SUPERVISOR_TEACHER_ROLE = "admin"
ORDINARY_TEACHER_ROLE = "teacher"
STUDENT_ROLE = "student"
TEACHER_CONSOLE_ROLES = frozenset({SUPERVISOR_TEACHER_ROLE, ORDINARY_TEACHER_ROLE})


def is_teacher_console_role(role: str) -> bool:
    return role in TEACHER_CONSOLE_ROLES


def is_supervisor_teacher_role(role: str) -> bool:
    return role == SUPERVISOR_TEACHER_ROLE

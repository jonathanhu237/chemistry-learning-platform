from __future__ import annotations

TEACHER_ROLE = "teacher"
STUDENT_ROLE = "student"


def is_teacher_role(role: str) -> bool:
    return role == TEACHER_ROLE

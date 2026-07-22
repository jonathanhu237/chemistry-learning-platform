from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status


SMART_BASELINE_REQUIRED_DETAIL = "Complete the required smart baseline first"


@dataclass(frozen=True)
class StudentAssessmentContext:
    student_id: str
    student_name: str
    class_id: str | None
    class_name: str | None
    user_id: str | None


def _student_id_from_user(user: Any) -> str:
    return (user.student_id or user.username).strip().upper()


def load_student_context(session: Any, user: Any) -> StudentAssessmentContext:
    normalized_student_id = _student_id_from_user(user)
    row = (
        session.execute(
            text(
                """
                SELECT sp.student_id, sp.student_name, sp.class_id, sp.user_id, c.class_name
                FROM student_profiles sp
                LEFT JOIN classes c ON c.id = sp.class_id
                WHERE sp.user_id = CAST(:user_id AS uuid)
                   OR sp.student_id = :student_id
                ORDER BY CASE WHEN sp.user_id = CAST(:user_id AS uuid) THEN 0 ELSE 1 END
                LIMIT 1
                """
            ),
            {"user_id": user.id, "student_id": normalized_student_id},
        )
        .mappings()
        .first()
    )
    if row:
        return StudentAssessmentContext(
            student_id=str(row["student_id"]),
            student_name=str(row["student_name"] or user.display_name),
            class_id=row.get("class_id"),
            class_name=row.get("class_name"),
            user_id=str(row["user_id"]) if row.get("user_id") else user.id,
        )
    return StudentAssessmentContext(
        student_id=normalized_student_id,
        student_name=user.display_name,
        class_id=user.class_id,
        class_name=user.class_name,
        user_id=user.id,
    )


def ensure_student_row(session: Any, context: StudentAssessmentContext) -> None:
    session.execute(
        text(
            """
            INSERT INTO students (
              id, display_name, class_name, user_id, student_id, class_id, status, updated_at
            )
            VALUES (
              :student_id, :display_name, :class_name, CAST(:user_id AS uuid),
              :student_id, :class_id, 'active', now()
            )
            ON CONFLICT (id) DO UPDATE SET
              display_name = COALESCE(EXCLUDED.display_name, students.display_name),
              class_name = COALESCE(EXCLUDED.class_name, students.class_name),
              user_id = COALESCE(EXCLUDED.user_id, students.user_id),
              student_id = COALESCE(EXCLUDED.student_id, students.student_id),
              class_id = COALESCE(EXCLUDED.class_id, students.class_id),
              status = 'active',
              updated_at = now()
            """
        ),
        {
            "student_id": context.student_id,
            "display_name": context.student_name,
            "class_name": context.class_name,
            "user_id": context.user_id,
            "class_id": context.class_id,
        },
    )


def student_has_completed_smart_baseline(session: Any, student_id: str) -> bool:
    return bool(
        session.execute(
            text(
                """
                SELECT 1
                FROM student_smart_assessment_sessions
                WHERE student_id = :student_id
                  AND status = 'completed'
                  AND assessment_mode = 'smart'
                LIMIT 1
                """
            ),
            {"student_id": student_id},
        ).scalar_one_or_none()
    )


def require_completed_smart_baseline(session: Any, student_id: str) -> None:
    if student_has_completed_smart_baseline(session, student_id):
        return
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=SMART_BASELINE_REQUIRED_DETAIL,
    )

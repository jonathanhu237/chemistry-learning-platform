from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from pydantic import BaseModel, Field
from sqlalchemy import text

from server.app.auth import AuthUser, LoginResponse
from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings
from server.app.security import AuthError, create_access_token, decode_access_token, hash_password


TEACHER_PREVIEW_CLASS_PURPOSE = "teacher_preview"
TEACHER_PREVIEW_ACCOUNT_PURPOSE = "teacher_preview"
STUDENT_DEVICE_PREVIEW_PURPOSE = "teacher_student_device_preview"
STUDENT_PREVIEW_TICKET_ROLE = "student_preview_ticket"


class StudentPreviewPolicy(BaseModel):
    feedback_enabled: bool = True
    account_mutation_enabled: bool = False
    assessment_enabled: bool = True
    assistant_enabled: bool = True
    analytics_side_effects_enabled: bool = False
    blocked_routes: list[str] = Field(default_factory=list)
    message: str = "预览模式可以体验学生端流程，但不会提交真实反馈或账号变更。"


class TeacherStudentPreviewSessionResponse(BaseModel):
    preview_url: str
    ticket: str
    expires_at: str


class StudentPreviewExchangeRequest(BaseModel):
    ticket: str


class StudentPreviewExchangeResponse(LoginResponse):
    preview_policy: StudentPreviewPolicy


class PreviewInfrastructureResponse(BaseModel):
    teacher_user_id: str
    teacher_username: str | None = None
    teacher_display_name: str | None = None
    class_id: str
    class_name: str
    class_status: str
    student_id: str
    student_name: str
    student_status: str
    student_user_id: str | None = None
    user_status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_session_at: datetime | None = None


def preview_policy() -> StudentPreviewPolicy:
    return StudentPreviewPolicy()


def is_preview_user(user: Any) -> bool:
    return bool(getattr(user, "preview_mode", False) or getattr(user, "preview_purpose", None))


def _teacher_uuid(value: str) -> str:
    return value.strip()


def _preview_class_id(teacher_id: str) -> str:
    return f"TPV_{teacher_id.replace('-', '').upper()}"


def _preview_student_id(teacher_id: str) -> str:
    return f"TPV_STUDENT_{teacher_id.replace('-', '').upper()}"


def _preview_username(teacher_id: str) -> str:
    return f"preview_student_{teacher_id.replace('-', '').lower()}"


def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _auth_user_from_row(row: dict[str, Any], *, preview: bool = False) -> AuthUser:
    return AuthUser(
        id=str(row["id"]),
        username=str(row["username"]),
        role=str(row["role"]),
        display_name=str(row["display_name"]),
        status=str(row["status"]),
        must_change_password=bool(row.get("must_change_password")),
        password_version=int(row.get("password_version") or 1),
        student_id=row.get("student_id"),
        class_id=row.get("class_id"),
        class_name=row.get("class_name"),
        preview_mode=preview,
        preview_purpose=STUDENT_DEVICE_PREVIEW_PURPOSE if preview else None,
        preview_teacher_user_id=str(row.get("owner_teacher_user_id")) if row.get("owner_teacher_user_id") else None,
        preview_class_id=row.get("class_id") if preview else None,
        preview_student_id=row.get("student_id") if preview else None,
    )


def _load_teacher_user(teacher_id: str) -> AuthUser:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT id, username, role, display_name, status, must_change_password, password_version
                    FROM app_users
                    WHERE id = CAST(:teacher_id AS uuid)
                      AND role IN ('admin', 'teacher')
                      AND status = 'active'
                    """
                ),
                {"teacher_id": teacher_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher account not found")
    return _auth_user_from_row(dict(row))


def _preview_item_from_row(row: dict[str, Any]) -> PreviewInfrastructureResponse:
    return PreviewInfrastructureResponse(
        teacher_user_id=str(row["teacher_user_id"]),
        teacher_username=row.get("teacher_username"),
        teacher_display_name=row.get("teacher_display_name"),
        class_id=str(row["class_id"]),
        class_name=str(row["class_name"]),
        class_status=str(row["class_status"]),
        student_id=str(row["student_id"]),
        student_name=str(row["student_name"]),
        student_status=str(row["student_status"]),
        student_user_id=str(row["student_user_id"]) if row.get("student_user_id") else None,
        user_status=row.get("user_status"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        last_session_at=row.get("last_session_at"),
    )


def ensure_teacher_preview_student_by_teacher_id(teacher_id: str) -> PreviewInfrastructureResponse:
    return ensure_teacher_preview_student(_load_teacher_user(teacher_id))


def ensure_teacher_preview_student(teacher: Any) -> PreviewInfrastructureResponse:
    teacher_id = _teacher_uuid(str(teacher.id))
    class_id = _preview_class_id(teacher_id)
    student_id = _preview_student_id(teacher_id)
    username = _preview_username(teacher_id)
    teacher_display = str(getattr(teacher, "display_name", None) or getattr(teacher, "username", "") or teacher_id)
    class_name = f"Preview Class - {teacher_display}"
    student_name = f"Preview Student - {teacher_display}"
    metadata = {"purpose": STUDENT_DEVICE_PREVIEW_PURPOSE, "teacher_user_id": teacher_id}

    with db_session() as session:
        session.execute(
            text(
                """
                INSERT INTO classes (
                  id, class_name, description, status, metadata, class_purpose,
                  owner_teacher_user_id, system_managed, hidden_from_teacher
                )
                VALUES (
                  :class_id, :class_name, 'System-managed teacher preview class',
                  'active', CAST(:metadata AS jsonb), :purpose,
                  CAST(:teacher_id AS uuid), true, true
                )
                ON CONFLICT (id) DO UPDATE SET
                  class_name = EXCLUDED.class_name,
                  status = 'active',
                  class_purpose = EXCLUDED.class_purpose,
                  owner_teacher_user_id = EXCLUDED.owner_teacher_user_id,
                  system_managed = true,
                  hidden_from_teacher = true,
                  metadata = classes.metadata || EXCLUDED.metadata,
                  updated_at = now()
                """
            ),
            {
                "class_id": class_id,
                "class_name": class_name,
                "metadata": _json(metadata),
                "purpose": TEACHER_PREVIEW_CLASS_PURPOSE,
                "teacher_id": teacher_id,
            },
        )
        session.execute(
            text(
                """
                INSERT INTO teacher_classes (teacher_user_id, class_id, class_role)
                VALUES (CAST(:teacher_id AS uuid), :class_id, 'owner')
                ON CONFLICT (teacher_user_id, class_id) DO UPDATE SET class_role = 'owner'
                """
            ),
            {"teacher_id": teacher_id, "class_id": class_id},
        )
        user_row = (
            session.execute(
                text(
                    """
                    INSERT INTO app_users (
                      username, role, display_name, password_hash, status,
                      must_change_password, password_version, metadata,
                      account_purpose, owner_teacher_user_id
                    )
                    VALUES (
                      :username, 'student', :display_name, :password_hash, 'active',
                      false, 1, CAST(:metadata AS jsonb),
                      :purpose, CAST(:teacher_id AS uuid)
                    )
                    ON CONFLICT (username) DO UPDATE SET
                      display_name = EXCLUDED.display_name,
                      status = 'active',
                      must_change_password = false,
                      account_purpose = EXCLUDED.account_purpose,
                      owner_teacher_user_id = EXCLUDED.owner_teacher_user_id,
                      metadata = app_users.metadata || EXCLUDED.metadata,
                      updated_at = now()
                    RETURNING id, username, role, display_name, status, must_change_password, password_version
                    """
                ),
                {
                    "username": username,
                    "display_name": student_name,
                    "password_hash": hash_password(secrets.token_urlsafe(24)),
                    "metadata": _json(metadata),
                    "purpose": TEACHER_PREVIEW_ACCOUNT_PURPOSE,
                    "teacher_id": teacher_id,
                },
            )
            .mappings()
            .one()
        )
        student_user_id = str(user_row["id"])
        roster_row = (
            session.execute(
                text(
                    """
                    INSERT INTO roster_entries (
                      class_id, student_id, student_name, normalized_student_id,
                      status, activation_mode, activated_user_id, errors, metadata,
                      entry_purpose, owner_teacher_user_id, system_managed
                    )
                    VALUES (
                      :class_id, :student_id, :student_name, :normalized_student_id,
                      'active', 'default_password', CAST(:user_id AS uuid), '[]'::jsonb,
                      CAST(:metadata AS jsonb), :purpose, CAST(:teacher_id AS uuid), true
                    )
                    ON CONFLICT (class_id, student_id) DO UPDATE SET
                      student_name = EXCLUDED.student_name,
                      normalized_student_id = EXCLUDED.normalized_student_id,
                      status = 'active',
                      activated_user_id = EXCLUDED.activated_user_id,
                      entry_purpose = EXCLUDED.entry_purpose,
                      owner_teacher_user_id = EXCLUDED.owner_teacher_user_id,
                      system_managed = true,
                      metadata = roster_entries.metadata || EXCLUDED.metadata,
                      updated_at = now()
                    RETURNING id
                    """
                ),
                {
                    "class_id": class_id,
                    "student_id": student_id,
                    "student_name": student_name,
                    "normalized_student_id": student_id,
                    "user_id": student_user_id,
                    "metadata": _json(metadata),
                    "purpose": TEACHER_PREVIEW_ACCOUNT_PURPOSE,
                    "teacher_id": teacher_id,
                },
            )
            .mappings()
            .one()
        )
        session.execute(
            text(
                """
                INSERT INTO student_profiles (
                  user_id, student_id, student_name, class_id, roster_entry_id,
                  activated_at, metadata, profile_purpose, owner_teacher_user_id
                )
                VALUES (
                  CAST(:user_id AS uuid), :student_id, :student_name, :class_id,
                  CAST(:roster_entry_id AS uuid), now(), CAST(:metadata AS jsonb),
                  :purpose, CAST(:teacher_id AS uuid)
                )
                ON CONFLICT (student_id) DO UPDATE SET
                  user_id = EXCLUDED.user_id,
                  student_name = EXCLUDED.student_name,
                  class_id = EXCLUDED.class_id,
                  roster_entry_id = EXCLUDED.roster_entry_id,
                  activated_at = COALESCE(student_profiles.activated_at, now()),
                  profile_purpose = EXCLUDED.profile_purpose,
                  owner_teacher_user_id = EXCLUDED.owner_teacher_user_id,
                  metadata = student_profiles.metadata || EXCLUDED.metadata,
                  updated_at = now()
                """
            ),
            {
                "user_id": student_user_id,
                "student_id": student_id,
                "student_name": student_name,
                "class_id": class_id,
                "roster_entry_id": str(roster_row["id"]),
                "metadata": _json(metadata),
                "purpose": TEACHER_PREVIEW_ACCOUNT_PURPOSE,
                "teacher_id": teacher_id,
            },
        )
        session.execute(
            text(
                """
                INSERT INTO students (id, display_name, class_name, user_id, student_id, class_id, status)
                VALUES (
                  :student_id, :display_name, :class_name, CAST(:user_id AS uuid),
                  :student_id, :class_id, 'active'
                )
                ON CONFLICT (id) DO UPDATE SET
                  display_name = EXCLUDED.display_name,
                  class_name = EXCLUDED.class_name,
                  user_id = EXCLUDED.user_id,
                  student_id = EXCLUDED.student_id,
                  class_id = EXCLUDED.class_id,
                  status = 'active',
                  updated_at = now()
                """
            ),
            {
                "student_id": student_id,
                "display_name": student_name,
                "class_name": class_name,
                "user_id": student_user_id,
                "class_id": class_id,
            },
        )
    return get_preview_infrastructure_for_teacher(teacher_id)


def get_preview_infrastructure_for_teacher(teacher_id: str) -> PreviewInfrastructureResponse:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT
                      c.owner_teacher_user_id AS teacher_user_id,
                      tu.username AS teacher_username,
                      tu.display_name AS teacher_display_name,
                      c.id AS class_id,
                      c.class_name,
                      c.status AS class_status,
                      re.student_id,
                      re.student_name,
                      re.status AS student_status,
                      au.id AS student_user_id,
                      au.status AS user_status,
                      c.created_at,
                      GREATEST(c.updated_at, re.updated_at, au.updated_at) AS updated_at,
                      (
                        SELECT MAX(s.created_at)
                        FROM auth_sessions s
                        WHERE s.user_id = au.id
                          AND s.metadata->>'purpose' = :preview_purpose
                      ) AS last_session_at
                    FROM classes c
                    JOIN app_users tu ON tu.id = c.owner_teacher_user_id
                    LEFT JOIN roster_entries re ON re.class_id = c.id AND re.entry_purpose = :account_purpose
                    LEFT JOIN app_users au ON au.id = re.activated_user_id
                    WHERE c.class_purpose = :class_purpose
                      AND c.owner_teacher_user_id = CAST(:teacher_id AS uuid)
                    ORDER BY c.created_at DESC
                    LIMIT 1
                    """
                ),
                {
                    "teacher_id": teacher_id,
                    "class_purpose": TEACHER_PREVIEW_CLASS_PURPOSE,
                    "account_purpose": TEACHER_PREVIEW_ACCOUNT_PURPOSE,
                    "preview_purpose": STUDENT_DEVICE_PREVIEW_PURPOSE,
                },
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview infrastructure not found")
    return _preview_item_from_row(dict(row))


def create_teacher_preview_session(teacher: Any) -> TeacherStudentPreviewSessionResponse:
    item = ensure_teacher_preview_student(teacher)
    settings = get_settings()
    token, claims = create_access_token(
        subject=str(teacher.id),
        role=STUDENT_PREVIEW_TICKET_ROLE,
        username=str(teacher.username),
        display_name=str(teacher.display_name),
        password_version=int(getattr(teacher, "password_version", 1) or 1),
        expires_minutes=settings.student_preview_ticket_expire_minutes,
        extra_claims={
            "purpose": STUDENT_DEVICE_PREVIEW_PURPOSE,
            "preview_class_id": item.class_id,
            "preview_student_id": item.student_id,
            "teacher_user_id": str(teacher.id),
        },
    )
    expires_at = datetime.fromtimestamp(int(claims["exp"]), tz=timezone.utc).isoformat()
    with db_session() as session:
        session.execute(
            text(
                """
                INSERT INTO auth_sessions (user_id, token_jti, expires_at, metadata)
                VALUES (
                  CAST(:teacher_id AS uuid), :jti, to_timestamp(:exp),
                  CAST(:metadata AS jsonb)
                )
                """
            ),
            {
                "teacher_id": str(teacher.id),
                "jti": claims["jti"],
                "exp": claims["exp"],
                "metadata": _json(
                    {
                        "purpose": STUDENT_DEVICE_PREVIEW_PURPOSE,
                        "kind": "student_preview_ticket",
                        "preview_class_id": item.class_id,
                        "preview_student_id": item.student_id,
                    }
                ),
            },
        )
    query = urlencode({"ticket": token})
    base_url = settings.student_preview_app_base_url.rstrip("/")
    return TeacherStudentPreviewSessionResponse(
        preview_url=f"{base_url}/preview/session?{query}",
        ticket=token,
        expires_at=expires_at,
    )


def _decode_ticket(ticket: str) -> dict[str, Any]:
    try:
        claims = decode_access_token(ticket)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if claims.get("purpose") != STUDENT_DEVICE_PREVIEW_PURPOSE or claims.get("role") != STUDENT_PREVIEW_TICKET_ROLE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid preview ticket")
    return claims


def exchange_preview_ticket(ticket: str) -> StudentPreviewExchangeResponse:
    claims = _decode_ticket(ticket)
    teacher_id = str(claims.get("teacher_user_id") or claims.get("sub") or "")
    class_id = str(claims.get("preview_class_id") or "")
    student_id = str(claims.get("preview_student_id") or "")
    with db_session() as session:
        ticket_row = (
            session.execute(
                text(
                    """
                    SELECT id
                    FROM auth_sessions
                    WHERE token_jti = :jti
                      AND user_id = CAST(:teacher_id AS uuid)
                      AND revoked_at IS NULL
                      AND expires_at > now()
                    """
                ),
                {"jti": claims.get("jti"), "teacher_id": teacher_id},
            )
            .mappings()
            .first()
        )
        if not ticket_row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Preview ticket is expired or already used")
        session.execute(
            text("UPDATE auth_sessions SET revoked_at = now() WHERE id = CAST(:id AS uuid)"),
            {"id": str(ticket_row["id"])},
        )
        user_row = (
            session.execute(
                text(
                    """
                    SELECT au.id, au.username, au.role, au.display_name, au.status,
                           au.must_change_password, au.password_version,
                           sp.student_id, sp.class_id, c.class_name, au.owner_teacher_user_id
                    FROM app_users au
                    JOIN student_profiles sp ON sp.user_id = au.id
                    JOIN classes c ON c.id = sp.class_id
                    WHERE sp.student_id = :student_id
                      AND sp.class_id = :class_id
                      AND au.role = 'student'
                      AND au.status = 'active'
                      AND au.account_purpose = :account_purpose
                      AND au.owner_teacher_user_id = CAST(:teacher_id AS uuid)
                    """
                ),
                {
                    "student_id": student_id,
                    "class_id": class_id,
                    "teacher_id": teacher_id,
                    "account_purpose": TEACHER_PREVIEW_ACCOUNT_PURPOSE,
                },
            )
            .mappings()
            .first()
        )
        if not user_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview student not found")
        user = _auth_user_from_row(dict(user_row), preview=True)
        token, session_claims = create_access_token(
            subject=user.id,
            role="student",
            username=user.username,
            display_name=user.display_name,
            password_version=user.password_version,
            expires_minutes=get_settings().student_preview_session_expire_minutes,
            extra_claims={
                "preview": True,
                "purpose": STUDENT_DEVICE_PREVIEW_PURPOSE,
                "preview_purpose": STUDENT_DEVICE_PREVIEW_PURPOSE,
                "teacher_user_id": teacher_id,
                "preview_class_id": class_id,
                "preview_student_id": student_id,
            },
        )
        session.execute(
            text(
                """
                INSERT INTO auth_sessions (user_id, token_jti, expires_at, metadata)
                VALUES (
                  CAST(:user_id AS uuid), :jti, to_timestamp(:exp),
                  CAST(:metadata AS jsonb)
                )
                """
            ),
            {
                "user_id": user.id,
                "jti": session_claims["jti"],
                "exp": session_claims["exp"],
                "metadata": _json(
                    {
                        "purpose": STUDENT_DEVICE_PREVIEW_PURPOSE,
                        "teacher_user_id": teacher_id,
                        "preview_class_id": class_id,
                        "preview_student_id": student_id,
                    }
                ),
            },
        )
    return StudentPreviewExchangeResponse(
        access_token=token,
        expires_at=datetime.fromtimestamp(session_claims["exp"], tz=timezone.utc).isoformat(),
        user=user,
        preview_policy=preview_policy(),
    )


def list_preview_infrastructure() -> list[PreviewInfrastructureResponse]:
    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT
                      c.owner_teacher_user_id AS teacher_user_id,
                      tu.username AS teacher_username,
                      tu.display_name AS teacher_display_name,
                      c.id AS class_id,
                      c.class_name,
                      c.status AS class_status,
                      re.student_id,
                      re.student_name,
                      re.status AS student_status,
                      au.id AS student_user_id,
                      au.status AS user_status,
                      c.created_at,
                      GREATEST(c.updated_at, re.updated_at, au.updated_at) AS updated_at,
                      (
                        SELECT MAX(s.created_at)
                        FROM auth_sessions s
                        WHERE s.user_id = au.id
                          AND s.metadata->>'purpose' = :preview_purpose
                      ) AS last_session_at
                    FROM classes c
                    JOIN app_users tu ON tu.id = c.owner_teacher_user_id
                    LEFT JOIN roster_entries re ON re.class_id = c.id AND re.entry_purpose = :account_purpose
                    LEFT JOIN app_users au ON au.id = re.activated_user_id
                    WHERE c.class_purpose = :class_purpose
                    ORDER BY c.updated_at DESC, c.created_at DESC
                    """
                ),
                {
                    "class_purpose": TEACHER_PREVIEW_CLASS_PURPOSE,
                    "account_purpose": TEACHER_PREVIEW_ACCOUNT_PURPOSE,
                    "preview_purpose": STUDENT_DEVICE_PREVIEW_PURPOSE,
                },
            )
            .mappings()
            .all()
        ]
    return [_preview_item_from_row(row) for row in rows]


def reset_preview_student(teacher_id: str) -> PreviewInfrastructureResponse:
    item = ensure_teacher_preview_student_by_teacher_id(teacher_id)
    with db_session() as session:
        if item.student_user_id:
            session.execute(
                text(
                    """
                    UPDATE auth_sessions
                    SET revoked_at = now()
                    WHERE user_id = CAST(:user_id AS uuid)
                      AND revoked_at IS NULL
                    """
                ),
                {"user_id": item.student_user_id},
            )
        cleanup_params = {"student_id": item.student_id, "class_id": item.class_id}
        for sql in (
            "DELETE FROM student_pretest_sessions WHERE student_id = :student_id AND class_id = :class_id",
            "DELETE FROM student_posttest_sessions WHERE student_id = :student_id AND class_id = :class_id",
            "DELETE FROM experiment_question_attempts WHERE student_id = :student_id AND class_id = :class_id",
            "DELETE FROM student_experiment_progress WHERE student_id = :student_id AND class_id = :class_id",
            "DELETE FROM student_experiment_mastery WHERE student_id = :student_id AND class_id = :class_id",
            "DELETE FROM student_events WHERE student_id = :student_id",
            "DELETE FROM student_feedback WHERE student_id = :student_id AND class_id = :class_id",
        ):
            session.execute(text(sql), cleanup_params)
        if item.student_user_id:
            session.execute(
                text(
                    """
                    UPDATE app_users
                    SET password_version = password_version + 1,
                        status = 'active',
                        updated_at = now(),
                        metadata = metadata || CAST(:metadata AS jsonb)
                    WHERE id = CAST(:user_id AS uuid)
                    """
                ),
                {
                    "user_id": item.student_user_id,
                    "metadata": _json({"last_preview_reset_at": datetime.now(timezone.utc).isoformat()}),
                },
            )
        session.execute(text("UPDATE classes SET status = 'active', updated_at = now() WHERE id = :class_id"), {"class_id": item.class_id})
        session.execute(
            text("UPDATE roster_entries SET status = 'active', updated_at = now() WHERE class_id = :class_id AND student_id = :student_id"),
            {"class_id": item.class_id, "student_id": item.student_id},
        )
        session.execute(
            text("UPDATE students SET status = 'active', updated_at = now() WHERE student_id = :student_id"),
            {"student_id": item.student_id},
        )
    return get_preview_infrastructure_for_teacher(teacher_id)


def disable_preview_student(teacher_id: str) -> PreviewInfrastructureResponse:
    item = get_preview_infrastructure_for_teacher(teacher_id)
    with db_session() as session:
        session.execute(text("UPDATE classes SET status = 'archived', updated_at = now() WHERE id = :class_id"), {"class_id": item.class_id})
        session.execute(
            text("UPDATE roster_entries SET status = 'disabled', updated_at = now() WHERE class_id = :class_id AND student_id = :student_id"),
            {"class_id": item.class_id, "student_id": item.student_id},
        )
        if item.student_user_id:
            session.execute(
                text("UPDATE app_users SET status = 'disabled', updated_at = now() WHERE id = CAST(:user_id AS uuid)"),
                {"user_id": item.student_user_id},
            )
            session.execute(
                text("UPDATE auth_sessions SET revoked_at = now() WHERE user_id = CAST(:user_id AS uuid) AND revoked_at IS NULL"),
                {"user_id": item.student_user_id},
            )
    return get_preview_infrastructure_for_teacher(teacher_id)


def restore_preview_student(teacher_id: str) -> PreviewInfrastructureResponse:
    item = get_preview_infrastructure_for_teacher(teacher_id)
    with db_session() as session:
        session.execute(text("UPDATE classes SET status = 'active', updated_at = now() WHERE id = :class_id"), {"class_id": item.class_id})
        session.execute(
            text("UPDATE roster_entries SET status = 'active', updated_at = now() WHERE class_id = :class_id AND student_id = :student_id"),
            {"class_id": item.class_id, "student_id": item.student_id},
        )
        if item.student_user_id:
            session.execute(
                text("UPDATE app_users SET status = 'active', must_change_password = false, updated_at = now() WHERE id = CAST(:user_id AS uuid)"),
                {"user_id": item.student_user_id},
            )
    return get_preview_infrastructure_for_teacher(teacher_id)

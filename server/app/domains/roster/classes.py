from __future__ import annotations

import json
import secrets
from datetime import datetime
from typing import Any

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.domains.platform.roles import is_teacher_console_role
from server.app.domains.preview.student_device_preview import TEACHER_PREVIEW_ACCOUNT_PURPOSE, TEACHER_PREVIEW_CLASS_PURPOSE
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from server.app.infrastructure.database import db_session
from server.app.roster import parse_roster, roster_preview
from server.app.security import hash_password


class ClassCreateRequest(BaseModel):
    id: str | None = Field(default=None, min_length=1, max_length=64)
    class_name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class ClassUpdateRequest(BaseModel):
    class_name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(active|archived)$")


class ClassResponse(BaseModel):
    id: str
    class_name: str
    description: str | None = None
    status: str
    student_count: int = 0


class TeacherClassAssignRequest(BaseModel):
    teacher_user_id: str = Field(min_length=1)
    class_role: str = Field(default="owner", pattern="^(owner|assistant|viewer)$")


class StudentPasswordResetRequest(BaseModel):
    initial_password: str | None = Field(default=None, min_length=8)
    force_change: bool = True


class RosterStudentCreateRequest(BaseModel):
    student_id: str = Field(min_length=1, max_length=64)
    student_name: str = Field(min_length=1, max_length=120)
    status: str = Field(default="pending", pattern="^(pending|active|disabled)$")
    activation_mode: str = Field(default="default_password", pattern="^(default_password|self_registration)$")


class RosterStudentUpdateRequest(BaseModel):
    student_id: str | None = Field(default=None, min_length=1, max_length=64)
    student_name: str | None = Field(default=None, min_length=1, max_length=120)
    status: str | None = Field(default=None, pattern="^(pending|active|disabled)$")
    activation_mode: str | None = Field(default=None, pattern="^(default_password|self_registration)$")


class RosterStudentResponse(BaseModel):
    id: str
    class_id: str
    student_id: str
    student_name: str
    status: str
    activation_mode: str
    activated: bool = False
    user_id: str | None = None
    activated_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RegistrationSettingsResponse(BaseModel):
    mode: str
    default_password_policy: str
    default_password_mode: str
    has_default_password: bool
    source: str | None = None


class RegistrationSettingsUpdateRequest(BaseModel):
    mode: str = Field(pattern="^(roster_only|self_registration)$")
    default_password_policy: str = "student_id_name_activation"
    default_password_mode: str | None = Field(default=None, pattern="^(student_id|shared)$")
    default_password: str | None = Field(default=None, min_length=8)


def _new_class_id() -> str:
    return f"CLS_{secrets.token_hex(4).upper()}"


def _class_row_to_response(row: dict[str, Any]) -> ClassResponse:
    return ClassResponse(
        id=row["id"],
        class_name=row["class_name"],
        description=row.get("description"),
        status=row["status"],
        student_count=int(row.get("student_count") or 0),
    )


def _normalize_student_id(student_id: str) -> str:
    return student_id.strip().upper()


def _roster_student_response(row: dict[str, Any]) -> RosterStudentResponse:
    user_id = row.get("user_id") or row.get("activated_user_id")
    return RosterStudentResponse(
        id=str(row["id"]),
        class_id=row["class_id"],
        student_id=row["student_id"],
        student_name=row["student_name"],
        status=row["status"],
        activation_mode=row["activation_mode"],
        activated=bool(user_id),
        user_id=str(user_id) if user_id else None,
        activated_at=row.get("activated_at"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _registration_settings_response(row: dict[str, Any], source: str | None = None) -> RegistrationSettingsResponse:
    password_mode = row.get("default_password_mode") or ("shared" if row.get("default_password_hash") else "student_id")
    return RegistrationSettingsResponse(
        mode=row["mode"],
        default_password_policy=row["default_password_policy"],
        default_password_mode=password_mode,
        has_default_password=password_mode == "shared" and bool(row.get("default_password_hash")),
        source=source or row.get("source"),
    )


def _load_roster_student(session: Any, class_id: str, student_id: str) -> RosterStudentResponse:
    normalized_student_id = _normalize_student_id(student_id)
    row = (
        session.execute(
            text(
                """
                SELECT re.id, re.class_id, re.student_id, re.student_name, re.status,
                       re.activation_mode, re.activated_user_id, re.created_at, re.updated_at,
                       sp.user_id, sp.activated_at
                FROM roster_entries re
                LEFT JOIN student_profiles sp ON sp.roster_entry_id = re.id
                WHERE re.class_id = :class_id
                  AND re.normalized_student_id = :student_id
                """
            ),
            {"class_id": class_id, "student_id": normalized_student_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roster student not found")
    return _roster_student_response(dict(row))


def _sync_disabled_student_account(session: Any, class_id: str, student_id: str) -> None:
    normalized_student_id = _normalize_student_id(student_id)
    row = (
        session.execute(
            text(
                """
                SELECT COALESCE(sp.user_id, re.activated_user_id) AS user_id
                FROM roster_entries re
                LEFT JOIN student_profiles sp ON sp.roster_entry_id = re.id
                WHERE re.class_id = :class_id
                  AND re.normalized_student_id = :student_id
                """
            ),
            {"class_id": class_id, "student_id": normalized_student_id},
        )
        .mappings()
        .first()
    )
    if not row or not row.get("user_id"):
        return
    user_id = str(row["user_id"])
    session.execute(
        text(
            """
            UPDATE app_users
            SET status = 'disabled', updated_at = now()
            WHERE id = CAST(:user_id AS uuid)
            """
        ),
        {"user_id": user_id},
    )
    session.execute(
        text(
            """
            UPDATE auth_sessions
            SET revoked_at = now()
            WHERE user_id = CAST(:user_id AS uuid) AND revoked_at IS NULL
            """
        ),
        {"user_id": user_id},
    )
    session.execute(
        text(
            """
            UPDATE students
            SET status = 'disabled', updated_at = now()
            WHERE user_id = CAST(:user_id AS uuid)
            """
        ),
        {"user_id": user_id},
    )


def _teacher_can_access_class(user: Any, class_id: str) -> bool:
    if is_teacher_console_role(user.role):
        return True
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT 1
                    FROM teacher_classes
                    WHERE teacher_user_id = CAST(:teacher_id AS uuid)
                      AND class_id = :class_id
                    """
                ),
                {"teacher_id": user.id, "class_id": class_id},
            )
            .first()
        )
    return row is not None


def _is_teacher_preview_class(class_id: str) -> bool:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT COALESCE(class_purpose, 'instructional') = :preview_purpose AS is_preview
                    FROM classes
                    WHERE id = :class_id
                    """
                ),
                {"class_id": class_id, "preview_purpose": TEACHER_PREVIEW_CLASS_PURPOSE},
            )
            .mappings()
            .first()
        )
    return bool(row and row["is_preview"])


def require_class_access(class_id: str, user: Any) -> None:
    if _is_teacher_preview_class(class_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    if not _teacher_can_access_class(user, class_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this class")


def _load_class_name(class_id: str) -> str:
    with db_session() as session:
        row = (
            session.execute(text("SELECT class_name FROM classes WHERE id = :class_id"), {"class_id": class_id})
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return str(row["class_name"])


def list_classes(user: Any) -> list[ClassResponse]:
    if is_teacher_console_role(user.role):
        sql = """
            SELECT c.id, c.class_name, c.description, c.status,
                   COUNT(re.id) FILTER (
                     WHERE re.status <> 'disabled'
                       AND COALESCE(re.entry_purpose, 'instructional') <> :preview_account_purpose
                   ) AS student_count
            FROM classes c
            LEFT JOIN roster_entries re ON re.class_id = c.id
            WHERE COALESCE(c.class_purpose, 'instructional') <> :preview_class_purpose
              AND COALESCE(c.hidden_from_teacher, false) IS false
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """
        params: dict[str, Any] = {
            "preview_account_purpose": TEACHER_PREVIEW_ACCOUNT_PURPOSE,
            "preview_class_purpose": TEACHER_PREVIEW_CLASS_PURPOSE,
        }
    else:
        sql = """
            SELECT c.id, c.class_name, c.description, c.status,
                   COUNT(re.id) FILTER (
                     WHERE re.status <> 'disabled'
                       AND COALESCE(re.entry_purpose, 'instructional') <> :preview_account_purpose
                   ) AS student_count
            FROM teacher_classes tc
            JOIN classes c ON c.id = tc.class_id
            LEFT JOIN roster_entries re ON re.class_id = c.id
            WHERE tc.teacher_user_id = CAST(:teacher_id AS uuid)
              AND COALESCE(c.class_purpose, 'instructional') <> :preview_class_purpose
              AND COALESCE(c.hidden_from_teacher, false) IS false
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """
        params = {
            "teacher_id": user.id,
            "preview_account_purpose": TEACHER_PREVIEW_ACCOUNT_PURPOSE,
            "preview_class_purpose": TEACHER_PREVIEW_CLASS_PURPOSE,
        }
    with db_session() as session:
        rows = [dict(row) for row in session.execute(text(sql), params).mappings().all()]
    return [_class_row_to_response(row) for row in rows]


def get_registration_settings() -> RegistrationSettingsResponse:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT mode, default_password_policy, default_password_mode, default_password_hash
                    FROM registration_settings
                    WHERE id = 'student_registration'
                    """
                )
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=500, detail="Registration settings are not initialized")
    return _registration_settings_response(dict(row), source="system_default")


def update_registration_settings(payload: RegistrationSettingsUpdateRequest, user: Any) -> RegistrationSettingsResponse:
    password_hash = hash_password(payload.default_password) if payload.default_password else None
    password_mode = payload.default_password_mode or ("shared" if password_hash else None)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    INSERT INTO registration_settings (
                      id, mode, default_password_policy, default_password_mode,
                      default_password_hash, updated_by, updated_at
                    )
                    VALUES (
                      'student_registration', :mode, :policy, :password_mode, :password_hash,
                      CAST(:updated_by AS uuid), now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      mode = EXCLUDED.mode,
                      default_password_policy = EXCLUDED.default_password_policy,
                      default_password_mode = COALESCE(:password_mode, registration_settings.default_password_mode),
                      default_password_hash = CASE
                        WHEN :password_mode = 'student_id' THEN NULL
                        WHEN EXCLUDED.default_password_hash IS NOT NULL THEN EXCLUDED.default_password_hash
                        ELSE registration_settings.default_password_hash
                      END,
                      updated_by = EXCLUDED.updated_by,
                      updated_at = now()
                    RETURNING mode, default_password_policy, default_password_mode, default_password_hash
                    """
                ),
                {
                    "mode": payload.mode,
                    "policy": payload.default_password_policy,
                    "password_hash": password_hash,
                    "password_mode": password_mode,
                    "updated_by": user.id,
                },
            )
            .mappings()
            .one()
        )
    return _registration_settings_response(dict(row), source="system_default")


def get_class_registration_settings(class_id: str, user: Any) -> RegistrationSettingsResponse:
    require_class_access(class_id, user)
    _load_class_name(class_id)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT
                      COALESCE(crs.mode, rs.mode) AS mode,
                      COALESCE(crs.default_password_policy, rs.default_password_policy) AS default_password_policy,
                      COALESCE(crs.default_password_mode, rs.default_password_mode) AS default_password_mode,
                      CASE
                        WHEN COALESCE(crs.default_password_mode, rs.default_password_mode) = 'shared'
                        THEN COALESCE(crs.default_password_hash, rs.default_password_hash)
                        ELSE NULL
                      END AS default_password_hash,
                      CASE
                        WHEN crs.class_id IS NULL THEN 'system_default'
                        ELSE 'class'
                      END AS source
                    FROM registration_settings rs
                    LEFT JOIN class_registration_settings crs ON crs.class_id = :class_id
                    WHERE rs.id = 'student_registration'
                    """
                ),
                {"class_id": class_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=500, detail="Registration settings are not initialized")
    return _registration_settings_response(dict(row))


def update_class_registration_settings(
    payload: RegistrationSettingsUpdateRequest,
    class_id: str,
    user: Any,
) -> RegistrationSettingsResponse:
    require_class_access(class_id, user)
    _load_class_name(class_id)
    password_hash = hash_password(payload.default_password) if payload.default_password else None
    password_mode = payload.default_password_mode or ("shared" if password_hash else "student_id")
    with db_session() as session:
        effective_hash = (
            session.execute(
                text(
                    """
                    SELECT
                      CASE
                        WHEN COALESCE(crs.default_password_mode, rs.default_password_mode) = 'shared'
                        THEN COALESCE(crs.default_password_hash, rs.default_password_hash)
                        ELSE NULL
                      END AS default_password_hash
                    FROM registration_settings rs
                    LEFT JOIN class_registration_settings crs ON crs.class_id = :class_id
                    WHERE rs.id = 'student_registration'
                    """
                ),
                {"class_id": class_id},
            )
            .scalar_one_or_none()
        )
        if password_mode == "shared" and not password_hash and not effective_hash:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please set an initial password")
        row = (
            session.execute(
                text(
                    """
                    INSERT INTO class_registration_settings (
                      class_id, mode, default_password_policy, default_password_mode,
                      default_password_hash, updated_by, updated_at
                    )
                    VALUES (
                      :class_id, :mode, :policy, :password_mode,
                      CASE
                        WHEN :password_mode = 'student_id' THEN NULL
                        ELSE COALESCE(:password_hash, :effective_hash)
                      END,
                      CAST(:updated_by AS uuid), now()
                    )
                    ON CONFLICT (class_id) DO UPDATE SET
                      mode = EXCLUDED.mode,
                      default_password_policy = EXCLUDED.default_password_policy,
                      default_password_mode = EXCLUDED.default_password_mode,
                      default_password_hash = CASE
                        WHEN :password_mode = 'student_id' THEN NULL
                        ELSE COALESCE(:password_hash, class_registration_settings.default_password_hash, :effective_hash)
                      END,
                      updated_by = EXCLUDED.updated_by,
                      updated_at = now()
                    RETURNING mode, default_password_policy, default_password_mode, default_password_hash
                    """
                ),
                {
                    "class_id": class_id,
                    "mode": payload.mode,
                    "policy": payload.default_password_policy,
                    "password_mode": password_mode,
                    "password_hash": password_hash,
                    "effective_hash": effective_hash,
                    "updated_by": user.id,
                },
            )
            .mappings()
            .one()
        )
    return _registration_settings_response(dict(row), source="class")


def create_class(payload: ClassCreateRequest, user: Any) -> ClassResponse:
    class_id = payload.id or _new_class_id()
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    INSERT INTO classes (id, class_name, description)
                    VALUES (:id, :class_name, :description)
                    ON CONFLICT (id) DO UPDATE SET
                      class_name = EXCLUDED.class_name,
                      description = EXCLUDED.description,
                      updated_at = now()
                    RETURNING id, class_name, description, status, 0 AS student_count
                    """
                ),
                {"id": class_id, "class_name": payload.class_name, "description": payload.description},
            )
            .mappings()
            .one()
        )
        if user.role == "teacher":
            session.execute(
                text(
                    """
                    INSERT INTO teacher_classes (teacher_user_id, class_id, class_role)
                    VALUES (CAST(:teacher_id AS uuid), :class_id, 'owner')
                    ON CONFLICT (teacher_user_id, class_id) DO NOTHING
                    """
                ),
                {"teacher_id": user.id, "class_id": class_id},
            )
    return _class_row_to_response(dict(row))


def get_class(class_id: str, user: Any) -> ClassResponse:
    require_class_access(class_id, user)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT c.id, c.class_name, c.description, c.status,
                           COUNT(re.id) FILTER (
                             WHERE re.status <> 'disabled'
                               AND COALESCE(re.entry_purpose, 'instructional') <> :preview_account_purpose
                           ) AS student_count
                    FROM classes c
                    LEFT JOIN roster_entries re ON re.class_id = c.id
                    WHERE c.id = :class_id
                    GROUP BY c.id
                    """
                ),
                {"class_id": class_id, "preview_account_purpose": TEACHER_PREVIEW_ACCOUNT_PURPOSE},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return _class_row_to_response(dict(row))


def update_class(payload: ClassUpdateRequest, class_id: str, user: Any) -> ClassResponse:
    require_class_access(class_id, user)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE classes
                    SET class_name = COALESCE(:class_name, class_name),
                        description = COALESCE(:description, description),
                        status = COALESCE(:status, status),
                        updated_at = now()
                    WHERE id = :class_id
                    RETURNING id, class_name, description, status,
                              (
                                SELECT COUNT(*)
                                FROM roster_entries
                                WHERE class_id = classes.id
                                  AND status <> 'disabled'
                                  AND COALESCE(entry_purpose, 'instructional') <> :preview_account_purpose
                              ) AS student_count
                    """
                ),
                {
                    "class_id": class_id,
                    "class_name": payload.class_name,
                    "description": payload.description,
                    "status": payload.status,
                    "preview_account_purpose": TEACHER_PREVIEW_ACCOUNT_PURPOSE,
                },
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return _class_row_to_response(dict(row))


def assign_teacher_to_class(payload: TeacherClassAssignRequest, class_id: str) -> dict[str, bool]:
    with db_session() as session:
        teacher = (
            session.execute(
                text("SELECT id FROM app_users WHERE id = CAST(:id AS uuid) AND role IN ('admin', 'teacher')"),
                {"id": payload.teacher_user_id},
            )
            .mappings()
            .first()
        )
        klass = session.execute(
            text(
                """
                SELECT id
                FROM classes
                WHERE id = :class_id
                  AND COALESCE(class_purpose, 'instructional') <> :preview_class_purpose
                  AND COALESCE(hidden_from_teacher, false) IS false
                """
            ),
            {"class_id": class_id, "preview_class_purpose": TEACHER_PREVIEW_CLASS_PURPOSE},
        ).first()
        if not teacher:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
        if not klass:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
        session.execute(
            text(
                """
                INSERT INTO teacher_classes (teacher_user_id, class_id, class_role)
                VALUES (CAST(:teacher_id AS uuid), :class_id, :class_role)
                ON CONFLICT (teacher_user_id, class_id) DO UPDATE SET
                  class_role = EXCLUDED.class_role
                """
            ),
            {"teacher_id": payload.teacher_user_id, "class_id": class_id, "class_role": payload.class_role},
        )
    return {"ok": True}


def preview_roster_import(class_id: str, filename: str | None, content: bytes, user: Any) -> dict[str, Any]:
    require_class_access(class_id, user)
    class_name = _load_class_name(class_id)
    rows = parse_roster(filename or "roster.csv", content, default_class_name=class_name)
    return roster_preview(rows)


def import_roster(
    class_id: str,
    filename: str | None,
    content: bytes,
    mode: str,
    user: Any,
) -> dict[str, Any]:
    require_class_access(class_id, user)
    if mode not in {"upsert", "overwrite"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Import mode must be upsert or overwrite")
    class_name = _load_class_name(class_id)
    rows = parse_roster(filename or "roster.csv", content, default_class_name=class_name)
    preview = roster_preview(rows)
    valid_student_ids = {_normalize_student_id(row["student_id"]) for row in preview["rows"] if row["valid"]}
    with db_session() as session:
        import_id = (
            session.execute(
                text(
                    """
                    INSERT INTO roster_imports (
                      uploaded_by, file_name, status, total_rows, valid_rows, invalid_rows, errors
                    )
                    VALUES (
                      CAST(:uploaded_by AS uuid), :file_name, 'imported', :total_rows,
                      :valid_rows, :invalid_rows, CAST(:errors AS jsonb)
                    )
                    RETURNING id
                    """
                ),
                {
                    "uploaded_by": user.id,
                    "file_name": filename,
                    "total_rows": preview["total_rows"],
                    "valid_rows": preview["valid_rows"],
                    "invalid_rows": preview["invalid_rows"],
                    "errors": json.dumps(
                        [row for row in preview["rows"] if not row["valid"]],
                        ensure_ascii=False,
                    ),
                },
            )
            .scalar_one()
        )
        for row in preview["rows"]:
            if not row["valid"]:
                continue
            session.execute(
                text(
                    """
                    INSERT INTO roster_entries (
                      import_id, class_id, student_id, student_name, normalized_student_id,
                      status, activation_mode, row_number, errors
                    )
                    VALUES (
                      CAST(:import_id AS uuid), :class_id, :student_id, :student_name,
                      :normalized_student_id, 'pending', 'default_password',
                      :row_number, '[]'::jsonb
                    )
                    ON CONFLICT (class_id, student_id) DO UPDATE SET
                      import_id = EXCLUDED.import_id,
                      student_name = EXCLUDED.student_name,
                      normalized_student_id = EXCLUDED.normalized_student_id,
                      status = CASE
                        WHEN roster_entries.status = 'disabled' THEN 'disabled'
                        ELSE roster_entries.status
                      END,
                      updated_at = now()
                    """
                ),
                {
                    "import_id": str(import_id),
                    "class_id": class_id,
                    "student_id": row["student_id"],
                    "student_name": row["student_name"],
                    "normalized_student_id": row["student_id"].upper(),
                    "row_number": row["row_number"],
                },
            )
        disabled_missing = 0
        if mode == "overwrite":
            disabled_missing = int(
                session.execute(
                    text(
                        """
                        WITH disabled AS (
                          UPDATE roster_entries
                          SET status = 'disabled',
                              updated_at = now()
                          WHERE class_id = :class_id
                            AND status <> 'disabled'
                            AND NOT (
                              normalized_student_id IN (
                                SELECT jsonb_array_elements_text(CAST(:student_ids AS jsonb))
                              )
                            )
                          RETURNING activated_user_id, student_id
                        ),
                        disabled_users AS (
                          UPDATE app_users
                          SET status = 'disabled',
                              updated_at = now()
                          WHERE id IN (
                            SELECT activated_user_id
                            FROM disabled
                            WHERE activated_user_id IS NOT NULL
                          )
                          RETURNING id
                        ),
                        revoked_sessions AS (
                          UPDATE auth_sessions
                          SET revoked_at = now()
                          WHERE user_id IN (SELECT id FROM disabled_users)
                            AND revoked_at IS NULL
                          RETURNING id
                        ),
                        disabled_students AS (
                          UPDATE students
                          SET status = 'disabled',
                              updated_at = now()
                          WHERE user_id IN (SELECT id FROM disabled_users)
                          RETURNING id
                        )
                        SELECT COUNT(*) FROM disabled
                        """
                    ),
                    {"class_id": class_id, "student_ids": json.dumps(sorted(valid_student_ids), ensure_ascii=False)},
                ).scalar_one()
            )
    return {"import_id": str(import_id), "mode": mode, "disabled_missing": disabled_missing, **preview}


def list_roster_students(class_id: str, user: Any) -> list[RosterStudentResponse]:
    require_class_access(class_id, user)
    with db_session() as session:
        rows = (
            session.execute(
                text(
                    """
                    SELECT re.id, re.class_id, re.student_id, re.student_name, re.status,
                           re.activation_mode, re.activated_user_id, re.created_at, re.updated_at,
                           sp.user_id, sp.activated_at
                    FROM roster_entries re
                    LEFT JOIN student_profiles sp ON sp.roster_entry_id = re.id
                    WHERE re.class_id = :class_id
                      AND COALESCE(re.entry_purpose, 'instructional') <> :preview_account_purpose
                    ORDER BY
                      CASE re.status
                        WHEN 'active' THEN 1
                        WHEN 'pending' THEN 2
                        ELSE 3
                      END,
                      re.student_id
                    """
                ),
                {"class_id": class_id, "preview_account_purpose": TEACHER_PREVIEW_ACCOUNT_PURPOSE},
            )
            .mappings()
            .all()
        )
    return [_roster_student_response(dict(row)) for row in rows]


def create_roster_student(
    payload: RosterStudentCreateRequest,
    class_id: str,
    user: Any,
) -> RosterStudentResponse:
    require_class_access(class_id, user)
    normalized_student_id = _normalize_student_id(payload.student_id)
    try:
        with db_session() as session:
            session.execute(
                text(
                    """
                    INSERT INTO roster_entries (
                      class_id, student_id, student_name, normalized_student_id,
                      status, activation_mode, errors
                    )
                    VALUES (
                      :class_id, :student_id, :student_name, :normalized_student_id,
                      :status, :activation_mode, '[]'::jsonb
                    )
                    """
                ),
                {
                    "class_id": class_id,
                    "student_id": payload.student_id.strip(),
                    "student_name": payload.student_name.strip(),
                    "normalized_student_id": normalized_student_id,
                    "status": payload.status,
                    "activation_mode": payload.activation_mode,
                },
            )
            return _load_roster_student(session, class_id, normalized_student_id)
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Roster student already exists") from exc


def update_roster_student(
    payload: RosterStudentUpdateRequest,
    class_id: str,
    student_id: str,
    user: Any,
) -> RosterStudentResponse:
    require_class_access(class_id, user)
    current_student_id = _normalize_student_id(student_id)
    next_student_id = _normalize_student_id(payload.student_id) if payload.student_id else current_student_id
    try:
        with db_session() as session:
            if next_student_id != current_student_id:
                activated_row = (
                    session.execute(
                        text(
                            """
                            SELECT COALESCE(sp.user_id, re.activated_user_id) AS user_id
                            FROM roster_entries re
                            LEFT JOIN student_profiles sp ON sp.roster_entry_id = re.id
                            WHERE re.class_id = :class_id
                              AND re.normalized_student_id = :student_id
                            """
                        ),
                        {"class_id": class_id, "student_id": current_student_id},
                    )
                    .mappings()
                    .first()
                )
                if activated_row and activated_row.get("user_id"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Activated student id cannot be changed",
                    )
            row = (
                session.execute(
                    text(
                        """
                        UPDATE roster_entries
                        SET student_id = COALESCE(:student_id, student_id),
                            normalized_student_id = :normalized_student_id,
                            student_name = COALESCE(:student_name, student_name),
                            status = COALESCE(:status, status),
                            activation_mode = COALESCE(:activation_mode, activation_mode),
                            updated_at = now()
                        WHERE class_id = :class_id
                          AND normalized_student_id = :current_student_id
                        RETURNING id
                        """
                    ),
                    {
                        "class_id": class_id,
                        "current_student_id": current_student_id,
                        "student_id": payload.student_id.strip() if payload.student_id else None,
                        "normalized_student_id": next_student_id,
                        "student_name": payload.student_name.strip() if payload.student_name else None,
                        "status": payload.status,
                        "activation_mode": payload.activation_mode,
                    },
                )
                .mappings()
                .first()
            )
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roster student not found")
            if payload.status == "disabled":
                _sync_disabled_student_account(session, class_id, next_student_id)
            return _load_roster_student(session, class_id, next_student_id)
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Roster student already exists") from exc


def disable_roster_student(class_id: str, student_id: str, user: Any) -> RosterStudentResponse:
    require_class_access(class_id, user)
    normalized_student_id = _normalize_student_id(student_id)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE roster_entries
                    SET status = 'disabled',
                        updated_at = now()
                    WHERE class_id = :class_id
                      AND normalized_student_id = :student_id
                    RETURNING id
                    """
                ),
                {"class_id": class_id, "student_id": normalized_student_id},
            )
            .mappings()
            .first()
        )
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roster student not found")
        _sync_disabled_student_account(session, class_id, normalized_student_id)
        return _load_roster_student(session, class_id, normalized_student_id)


def reset_student_password(
    payload: StudentPasswordResetRequest,
    class_id: str,
    student_id: str,
    user: Any,
) -> dict[str, bool]:
    require_class_access(class_id, user)
    normalized_student_id = student_id.strip().upper()
    new_password = payload.initial_password or normalized_student_id
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT au.id
                    FROM student_profiles sp
                    JOIN app_users au ON au.id = sp.user_id
                    WHERE sp.class_id = :class_id
                      AND sp.student_id = :student_id
                    """
                ),
                {"class_id": class_id, "student_id": normalized_student_id},
            )
            .mappings()
            .first()
        )
        if not row:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student account is not activated; use class initial-password settings for first login",
            )
        session.execute(
            text(
                """
                UPDATE app_users
                SET password_hash = :password_hash,
                    must_change_password = :must_change_password,
                    password_version = password_version + 1,
                    updated_at = now()
                WHERE id = :user_id
                """
            ),
            {
                "user_id": row["id"],
                "password_hash": hash_password(new_password),
                "must_change_password": payload.force_change,
            },
        )
        session.execute(
            text(
                """
                UPDATE auth_sessions
                SET revoked_at = now()
                WHERE user_id = :user_id AND revoked_at IS NULL
                """
            ),
            {"user_id": row["id"]},
        )
    return {"ok": True}

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.infrastructure.database import db_session
from server.app.security import hash_password

MANAGED_TEACHER_ROLES = ("admin", "teacher")
MANAGED_ACCOUNT_STATUSES = ("active", "disabled")
TEACHER_ACCOUNT_DELETE_BLOCKED_DETAIL = "Teacher account has owned records; disable it instead"


class TeacherAccountResponse(BaseModel):
    id: str
    username: str
    role: str
    display_name: str
    status: str
    must_change_password: bool
    password_version: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login_at: datetime | None = None


class TeacherAccountCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=256)
    must_change_password: bool = True


class TeacherAccountPatchRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    role: str | None = Field(default=None, pattern="^(admin|teacher)$")
    status: str | None = Field(default=None, pattern="^(active|disabled)$")


class TeacherAccountPasswordResetRequest(BaseModel):
    password: str = Field(min_length=8, max_length=256)
    must_change_password: bool = True


def _teacher_account_response(row: dict[str, Any]) -> TeacherAccountResponse:
    return TeacherAccountResponse(
        id=str(row["id"]),
        username=str(row["username"]),
        role=str(row["role"]),
        display_name=str(row["display_name"]),
        status=str(row["status"]),
        must_change_password=bool(row.get("must_change_password")),
        password_version=int(row.get("password_version") or 1),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        last_login_at=row.get("last_login_at"),
    )


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher account not found")


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _teacher_account_dependencies(session: Any, account_id: str) -> list[str]:
    dependency_rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT kcu.table_schema, kcu.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.constraint_schema = kcu.constraint_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.constraint_schema = tc.constraint_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND ccu.table_name = 'app_users'
                  AND ccu.column_name = 'id'
                  AND kcu.table_name <> 'auth_sessions'
                ORDER BY kcu.table_schema, kcu.table_name, kcu.column_name
                """
            )
        )
        .mappings()
        .all()
    ]
    dependencies: list[str] = []
    for dependency in dependency_rows:
        schema = _quote_identifier(str(dependency["table_schema"]))
        table = _quote_identifier(str(dependency["table_name"]))
        column = _quote_identifier(str(dependency["column_name"]))
        row = (
            session.execute(
                text(
                    f"""
                    SELECT COUNT(*) AS dependency_count
                    FROM {schema}.{table}
                    WHERE {column} = CAST(:account_id AS uuid)
                    """
                ),
                {"account_id": account_id},
            )
            .mappings()
            .first()
        )
        if int(row["dependency_count"] if row else 0) > 0:
            dependencies.append(f"{dependency['table_name']}.{dependency['column_name']}")
    return dependencies


def list_teacher_accounts() -> list[TeacherAccountResponse]:
    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT id, username, role, display_name, status, must_change_password,
                           password_version, created_at, updated_at, last_login_at
                    FROM app_users
                    WHERE role IN ('admin', 'teacher')
                    ORDER BY
                      CASE status WHEN 'active' THEN 1 ELSE 2 END,
                      COALESCE(updated_at, created_at) DESC,
                      username
                    """
                )
            )
            .mappings()
            .all()
        ]
    return [_teacher_account_response(row) for row in rows]


def create_teacher_account(payload: TeacherAccountCreateRequest) -> TeacherAccountResponse:
    username = payload.username.strip()
    display_name = payload.display_name.strip()
    if not username or not display_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username and display name are required")
    try:
        with db_session() as session:
            row = (
                session.execute(
                    text(
                        """
                        INSERT INTO app_users (
                          username, role, display_name, password_hash, status,
                          must_change_password, password_version
                        )
                        VALUES (
                          :username, 'admin', :display_name, :password_hash, 'active',
                          :must_change_password, 1
                        )
                        RETURNING id, username, role, display_name, status, must_change_password,
                                  password_version, created_at, updated_at, last_login_at
                        """
                    ),
                    {
                        "username": username,
                        "display_name": display_name,
                        "password_hash": hash_password(payload.password),
                        "must_change_password": payload.must_change_password,
                    },
                )
                .mappings()
                .one()
            )
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists") from exc
    return _teacher_account_response(dict(row))


def patch_teacher_account(account_id: str, payload: TeacherAccountPatchRequest) -> TeacherAccountResponse:
    display_name = payload.display_name.strip() if payload.display_name is not None else None
    if payload.display_name is not None and not display_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Display name is required")
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE app_users
                    SET display_name = COALESCE(:display_name, display_name),
                        role = COALESCE(:role, role),
                        status = COALESCE(:status, status),
                        updated_at = now()
                    WHERE id = CAST(:account_id AS uuid)
                      AND role IN ('admin', 'teacher')
                    RETURNING id, username, role, display_name, status, must_change_password,
                              password_version, created_at, updated_at, last_login_at
                    """
                ),
                {
                    "account_id": account_id,
                    "display_name": display_name,
                    "role": payload.role,
                    "status": payload.status,
                },
            )
            .mappings()
            .first()
        )
        if not row:
            raise _not_found()
        if payload.status == "disabled" or payload.role is not None:
            session.execute(
                text(
                    """
                    UPDATE auth_sessions
                    SET revoked_at = now()
                    WHERE user_id = CAST(:account_id AS uuid)
                      AND revoked_at IS NULL
                    """
                ),
                {"account_id": account_id},
            )
    return _teacher_account_response(dict(row))


def reset_teacher_account_password(
    account_id: str,
    payload: TeacherAccountPasswordResetRequest,
) -> TeacherAccountResponse:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE app_users
                    SET password_hash = :password_hash,
                        must_change_password = :must_change_password,
                        password_version = password_version + 1,
                        updated_at = now()
                    WHERE id = CAST(:account_id AS uuid)
                      AND role IN ('admin', 'teacher')
                    RETURNING id, username, role, display_name, status, must_change_password,
                              password_version, created_at, updated_at, last_login_at
                    """
                ),
                {
                    "account_id": account_id,
                    "password_hash": hash_password(payload.password),
                    "must_change_password": payload.must_change_password,
                },
            )
            .mappings()
            .first()
        )
        if not row:
            raise _not_found()
        session.execute(
            text(
                """
                UPDATE auth_sessions
                SET revoked_at = now()
                WHERE user_id = CAST(:account_id AS uuid)
                  AND revoked_at IS NULL
                """
            ),
            {"account_id": account_id},
        )
    return _teacher_account_response(dict(row))


def disable_teacher_account(account_id: str) -> TeacherAccountResponse:
    return patch_teacher_account(account_id, TeacherAccountPatchRequest(status="disabled"))


def enable_teacher_account(account_id: str) -> TeacherAccountResponse:
    return patch_teacher_account(account_id, TeacherAccountPatchRequest(status="active"))


def delete_teacher_account(account_id: str) -> TeacherAccountResponse:
    try:
        with db_session() as session:
            row = (
                session.execute(
                    text(
                        """
                        SELECT id, username, role, display_name, status, must_change_password,
                               password_version, created_at, updated_at, last_login_at
                        FROM app_users
                        WHERE id = CAST(:account_id AS uuid)
                          AND role IN ('admin', 'teacher')
                        """
                    ),
                    {"account_id": account_id},
                )
                .mappings()
                .first()
            )
            if not row:
                raise _not_found()
            dependencies = _teacher_account_dependencies(session, account_id)
            if dependencies:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=TEACHER_ACCOUNT_DELETE_BLOCKED_DETAIL,
                )
            deleted = (
                session.execute(
                    text(
                        """
                        DELETE FROM app_users
                        WHERE id = CAST(:account_id AS uuid)
                          AND role IN ('admin', 'teacher')
                        RETURNING id, username, role, display_name, status, must_change_password,
                                  password_version, created_at, updated_at, last_login_at
                        """
                    ),
                    {"account_id": account_id},
                )
                .mappings()
                .first()
            )
            if not deleted:
                raise _not_found()
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=TEACHER_ACCOUNT_DELETE_BLOCKED_DETAIL,
        ) from exc
    return _teacher_account_response(dict(deleted))

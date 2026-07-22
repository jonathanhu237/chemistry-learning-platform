from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.infrastructure.database import db_session
from server.app.security import hash_password

SELF_PEER_OPERATION_DETAIL = "Peer account operations cannot target the current account"
LAST_ACTIVE_SUPERVISOR_DETAIL = "Cannot disable the last active supervisor teacher"


class TeacherAccountResponse(BaseModel):
    id: str
    username: str
    role: Literal["admin", "teacher"]
    display_name: str
    status: Literal["active", "disabled"]
    must_change_password: bool
    password_version: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login_at: datetime | None = None


class TeacherAccountCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=256)


class TeacherAccountPasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str = Field(min_length=8, max_length=256)


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


def _ensure_peer_operation(*, actor_user_id: str, account_id: str) -> None:
    if actor_user_id == account_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=SELF_PEER_OPERATION_DETAIL)


def _lock_supervisor_accounts(session: Any) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT id, status
                FROM app_users
                WHERE role = 'admin'
                ORDER BY id
                FOR UPDATE
                """
            )
        )
        .mappings()
        .all()
    ]


def _load_teacher_account_for_update(session: Any, account_id: str) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                """
                SELECT id, username, role, display_name, status, must_change_password,
                       password_version, created_at, updated_at, last_login_at
                FROM app_users
                WHERE id = CAST(:account_id AS uuid)
                  AND role IN ('admin', 'teacher')
                FOR UPDATE
                """
            ),
            {"account_id": account_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise _not_found()
    return dict(row)


def _revoke_active_sessions(session: Any, account_id: str) -> None:
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
                      CASE role WHEN 'admin' THEN 1 ELSE 2 END,
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
                          :username, 'teacher', :display_name, :password_hash, 'active',
                          true, 1
                        )
                        RETURNING id, username, role, display_name, status, must_change_password,
                                  password_version, created_at, updated_at, last_login_at
                        """
                    ),
                    {
                        "username": username,
                        "display_name": display_name,
                        "password_hash": hash_password(payload.password),
                    },
                )
                .mappings()
                .one()
            )
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists") from exc
    return _teacher_account_response(dict(row))


def reset_teacher_account_password(
    account_id: str,
    payload: TeacherAccountPasswordResetRequest,
    *,
    actor_user_id: str,
) -> TeacherAccountResponse:
    _ensure_peer_operation(actor_user_id=actor_user_id, account_id=account_id)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE app_users
                    SET password_hash = :password_hash,
                        must_change_password = true,
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
                },
            )
            .mappings()
            .first()
        )
        if not row:
            raise _not_found()
        _revoke_active_sessions(session, account_id)
    return _teacher_account_response(dict(row))


def disable_teacher_account(account_id: str, *, actor_user_id: str) -> TeacherAccountResponse:
    _ensure_peer_operation(actor_user_id=actor_user_id, account_id=account_id)
    with db_session() as session:
        supervisor_accounts = _lock_supervisor_accounts(session)
        target = _load_teacher_account_for_update(session, account_id)
        if target["role"] == "admin" and target["status"] == "active":
            active_supervisor_count = sum(row["status"] == "active" for row in supervisor_accounts)
            if active_supervisor_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=LAST_ACTIVE_SUPERVISOR_DETAIL,
                )
        row = (
            session.execute(
                text(
                    """
                    UPDATE app_users
                    SET status = 'disabled',
                        must_change_password = true,
                        password_version = password_version + 1,
                        updated_at = now()
                    WHERE id = CAST(:account_id AS uuid)
                      AND role IN ('admin', 'teacher')
                    RETURNING id, username, role, display_name, status, must_change_password,
                              password_version, created_at, updated_at, last_login_at
                    """
                ),
                {"account_id": account_id},
            )
            .mappings()
            .one()
        )
        _revoke_active_sessions(session, account_id)
    return _teacher_account_response(dict(row))


def enable_teacher_account(account_id: str, *, actor_user_id: str) -> TeacherAccountResponse:
    _ensure_peer_operation(actor_user_id=actor_user_id, account_id=account_id)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE app_users
                    SET status = 'active',
                        updated_at = now()
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
        if not row:
            raise _not_found()
    return _teacher_account_response(dict(row))

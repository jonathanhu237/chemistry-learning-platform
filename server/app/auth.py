from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import text

from server.app.domains.platform.roles import PLATFORM_ADMIN_ROLE, TEACHER_CONSOLE_ROLES, is_teacher_console_role
from server.app.infrastructure.database import db_session
from server.app.security import AuthError, create_access_token, hash_password, verify_password, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class StudentLoginRequest(BaseModel):
    student_id: str = Field(min_length=1)
    password: str = Field(min_length=1)


class StudentActivateRequest(BaseModel):
    student_id: str = Field(min_length=1)
    student_name: str = Field(min_length=1)
    initial_password: str = Field(min_length=1)
    new_password: str | None = Field(default=None, min_length=8)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class StudentPasswordChangeRequest(BaseModel):
    current_password: str | None = Field(default=None, min_length=1)
    new_password: str = Field(min_length=8)


class AuthUser(BaseModel):
    id: str
    username: str
    role: str
    display_name: str
    status: str
    must_change_password: bool = False
    password_version: int = 1
    student_id: str | None = None
    class_id: str | None = None
    class_name: str | None = None
    preview_mode: bool = False
    preview_purpose: str | None = None
    preview_teacher_user_id: str | None = None
    preview_class_id: str | None = None
    preview_student_id: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    user: AuthUser


def _auth_error(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _user_from_row(row: dict[str, Any]) -> AuthUser:
    return AuthUser(
        id=str(row["id"]),
        username=row["username"],
        role=row["role"],
        display_name=row["display_name"],
        status=row["status"],
        must_change_password=bool(row.get("must_change_password")),
        password_version=int(row.get("password_version") or 1),
        student_id=row.get("student_id"),
        class_id=row.get("class_id"),
        class_name=row.get("class_name"),
    )


def _normalize_student_id(value: str) -> str:
    return value.strip().upper()


def _load_user_with_hash(username: str) -> tuple[AuthUser, str] | None:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT au.id, au.username, au.role, au.display_name, au.password_hash,
                           au.status, au.must_change_password, au.password_version,
                           sp.student_id, sp.class_id, c.class_name
                    FROM app_users au
                    LEFT JOIN student_profiles sp ON sp.user_id = au.id
                    LEFT JOIN classes c ON c.id = sp.class_id
                    WHERE au.username = :username
                    """
                ),
                {"username": username},
            )
            .mappings()
            .first()
        )
    if not row:
        return None
    return _user_from_row(dict(row)), row["password_hash"]


def _load_active_user(username: str) -> tuple[AuthUser, str] | None:
    result = _load_user_with_hash(username)
    if not result:
        return None
    user, password_hash = result
    if user.status != "active":
        return None
    return user, password_hash


def authenticate_user(username: str, password: str) -> AuthUser | None:
    result = _load_active_user(username)
    if not result:
        return None
    user, password_hash = result
    if not verify_password(password, password_hash):
        return None
    return user


def _load_student_roster_for_login(session: Any, normalized_student_id: str) -> dict[str, Any] | None:
    rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT re.id, re.class_id, re.student_id, re.student_name, c.class_name,
                       re.status, re.activated_user_id
                FROM roster_entries re
                JOIN classes c ON c.id = re.class_id
                WHERE re.normalized_student_id = :student_id
                  AND re.status <> 'disabled'
                ORDER BY re.created_at DESC
                """
            ),
            {"student_id": normalized_student_id},
        )
        .mappings()
        .all()
    ]
    if len(rows) > 1:
        raise HTTPException(status_code=409, detail="Duplicate active roster entries for this student ID")
    return rows[0] if rows else None


def _initial_password_matches(session: Any, roster: dict[str, Any], normalized_student_id: str, password: str) -> bool:
    settings_row = (
        session.execute(
            text(
                """
                SELECT
                  COALESCE(crs.mode, rs.mode) AS mode,
                  COALESCE(crs.default_password_mode, rs.default_password_mode) AS default_password_mode,
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
            {"class_id": roster["class_id"]},
        )
        .mappings()
        .first()
    )
    if not settings_row:
        raise HTTPException(status_code=500, detail="Registration settings are not initialized")
    default_password_hash = settings_row.get("default_password_hash")
    if default_password_hash:
        return verify_password(password, default_password_hash)
    return password == normalized_student_id


def _create_student_account_from_roster(
    session: Any,
    *,
    roster: dict[str, Any],
    normalized_student_id: str,
    password: str,
    must_change_password: bool,
) -> AuthUser:
    user_row = (
        session.execute(
            text(
                """
                INSERT INTO app_users (
                  username, role, display_name, password_hash, status,
                  must_change_password, password_version
                )
                VALUES (
                  :username, 'student', :display_name, :password_hash, 'active',
                  :must_change_password, 1
                )
                RETURNING id, username, role, display_name, status, must_change_password, password_version
                """
            ),
            {
                "username": normalized_student_id,
                "display_name": roster["student_name"],
                "password_hash": hash_password(password),
                "must_change_password": must_change_password,
            },
        )
        .mappings()
        .one()
    )
    user = _user_from_row(dict(user_row))
    user.class_id = roster["class_id"]
    user.class_name = roster["class_name"]
    user.student_id = normalized_student_id
    session.execute(
        text(
            """
            INSERT INTO student_profiles (
              user_id, student_id, student_name, class_id, roster_entry_id, activated_at
            )
            VALUES (
              CAST(:user_id AS uuid), :student_id, :student_name, :class_id,
              CAST(:roster_entry_id AS uuid), now()
            )
            ON CONFLICT (student_id) DO UPDATE SET
              user_id = EXCLUDED.user_id,
              student_name = EXCLUDED.student_name,
              class_id = EXCLUDED.class_id,
              roster_entry_id = EXCLUDED.roster_entry_id,
              activated_at = COALESCE(student_profiles.activated_at, now()),
              updated_at = now()
            """
        ),
        {
            "user_id": user.id,
            "student_id": normalized_student_id,
            "student_name": roster["student_name"],
            "class_id": roster["class_id"],
            "roster_entry_id": str(roster["id"]),
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
            "student_id": normalized_student_id,
            "display_name": roster["student_name"],
            "class_name": roster["class_name"],
            "user_id": user.id,
            "class_id": roster["class_id"],
        },
    )
    session.execute(
        text(
            """
            UPDATE roster_entries
            SET status = 'active',
                activated_user_id = CAST(:user_id AS uuid),
                updated_at = now()
            WHERE id = CAST(:roster_entry_id AS uuid)
            """
        ),
        {"user_id": user.id, "roster_entry_id": str(roster["id"])},
    )
    return user


def _issue_login_response(user: AuthUser) -> LoginResponse:
    token, claims = create_access_token(
        subject=user.id,
        role=user.role,
        username=user.username,
        display_name=user.display_name,
        password_version=user.password_version,
    )
    with db_session() as session:
        session.execute(
            text(
                """
                UPDATE app_users
                SET last_login_at = now(), updated_at = now()
                WHERE id = CAST(:user_id AS uuid)
                """
            ),
            {"user_id": user.id},
        )
        session.execute(
            text(
                """
                INSERT INTO auth_sessions (user_id, token_jti, expires_at)
                VALUES (CAST(:user_id AS uuid), :jti, to_timestamp(:exp))
                """
            ),
            {"user_id": user.id, "jti": claims["jti"], "exp": claims["exp"]},
        )
    return LoginResponse(
        access_token=token,
        expires_at=datetime.fromtimestamp(claims["exp"], tz=timezone.utc).isoformat(),
        user=user,
    )


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise _auth_error("Invalid username or password")
    return _issue_login_response(user)


@router.post("/student/login", response_model=LoginResponse)
def student_login(payload: StudentLoginRequest) -> LoginResponse:
    normalized_student_id = _normalize_student_id(payload.student_id)
    existing = _load_user_with_hash(normalized_student_id)
    if existing:
        user, password_hash = existing
        if user.role != "student" or user.status != "active" or not verify_password(payload.password, password_hash):
            raise _auth_error("Invalid student ID or password")
        return _issue_login_response(user)

    with db_session() as session:
        roster = _load_student_roster_for_login(session, normalized_student_id)
        if not roster or roster.get("activated_user_id"):
            raise _auth_error("Invalid student ID or password")
        if not _initial_password_matches(session, roster, normalized_student_id, payload.password):
            raise _auth_error("Invalid student ID or password")
        user = _create_student_account_from_roster(
            session,
            roster=roster,
            normalized_student_id=normalized_student_id,
            password=payload.password,
            must_change_password=True,
        )
    return _issue_login_response(user)


async def activate_student(payload: StudentActivateRequest) -> LoginResponse:
    normalized_student_id = payload.student_id.strip().upper()
    with db_session() as session:
        roster = (
            session.execute(
                text(
                    """
                    SELECT re.id, re.class_id, re.student_id, re.student_name, c.class_name,
                           re.status, re.activated_user_id
                    FROM roster_entries re
                    JOIN classes c ON c.id = re.class_id
                    WHERE re.normalized_student_id = :student_id
                      AND re.student_name = :student_name
                      AND re.status <> 'disabled'
                    ORDER BY re.created_at DESC
                    LIMIT 1
                    """
                ),
                {"student_id": normalized_student_id, "student_name": payload.student_name.strip()},
            )
            .mappings()
            .first()
        )
        if not roster:
            raise _auth_error("Student is not on an active roster")
        if roster.get("activated_user_id"):
            raise HTTPException(status_code=409, detail="Student account is already activated")

        settings_row = (
            session.execute(
                text(
                    """
                    SELECT
                      COALESCE(crs.mode, rs.mode) AS mode,
                      COALESCE(crs.default_password_mode, rs.default_password_mode) AS default_password_mode,
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
                {"class_id": roster["class_id"]},
            )
            .mappings()
            .first()
        )
        if not settings_row:
            raise HTTPException(status_code=500, detail="Registration settings are not initialized")

        default_password_hash = settings_row.get("default_password_hash")
        if default_password_hash:
            default_password_ok = verify_password(payload.initial_password, default_password_hash)
        else:
            default_password_ok = payload.initial_password == payload.student_id
        if not default_password_ok:
            raise _auth_error("Invalid initial password")

        account_password = payload.new_password or payload.initial_password
        must_change_password = payload.new_password is None
        user_row = (
            session.execute(
                text(
                    """
                    INSERT INTO app_users (
                      username, role, display_name, password_hash, status,
                      must_change_password, password_version
                    )
                    VALUES (
                      :username, 'student', :display_name, :password_hash, 'active',
                      :must_change_password, 1
                    )
                    RETURNING id, username, role, display_name, status, must_change_password, password_version
                    """
                ),
                {
                    "username": normalized_student_id,
                    "display_name": roster["student_name"],
                    "password_hash": hash_password(account_password),
                    "must_change_password": must_change_password,
                },
            )
            .mappings()
            .one()
        )
        user = _user_from_row(dict(user_row))
        user.class_id = roster["class_id"]
        user.class_name = roster["class_name"]
        user.student_id = normalized_student_id
        session.execute(
            text(
                """
                INSERT INTO student_profiles (
                  user_id, student_id, student_name, class_id, roster_entry_id, activated_at
                )
                VALUES (
                  CAST(:user_id AS uuid), :student_id, :student_name, :class_id,
                  CAST(:roster_entry_id AS uuid), now()
                )
                ON CONFLICT (student_id) DO UPDATE SET
                  user_id = EXCLUDED.user_id,
                  student_name = EXCLUDED.student_name,
                  class_id = EXCLUDED.class_id,
                  roster_entry_id = EXCLUDED.roster_entry_id,
                  activated_at = COALESCE(student_profiles.activated_at, now()),
                  updated_at = now()
                """
            ),
            {
                "user_id": user.id,
                "student_id": normalized_student_id,
                "student_name": roster["student_name"],
                "class_id": roster["class_id"],
                "roster_entry_id": str(roster["id"]),
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
                "student_id": normalized_student_id,
                "display_name": roster["student_name"],
                "class_name": roster["class_name"],
                "user_id": user.id,
                "class_id": roster["class_id"],
            },
        )
        session.execute(
            text(
                """
                UPDATE roster_entries
                SET status = 'active',
                    activated_user_id = CAST(:user_id AS uuid),
                    updated_at = now()
                WHERE id = CAST(:roster_entry_id AS uuid)
                """
            ),
            {"user_id": user.id, "roster_entry_id": str(roster["id"])},
        )
    return _issue_login_response(user)


async def register_student(payload: StudentActivateRequest) -> LoginResponse:
    normalized_student_id = payload.student_id.strip().upper()
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT COALESCE(crs.mode, rs.mode) AS mode
                    FROM roster_entries re
                    JOIN registration_settings rs ON rs.id = 'student_registration'
                    LEFT JOIN class_registration_settings crs ON crs.class_id = re.class_id
                    WHERE re.normalized_student_id = :student_id
                      AND re.student_name = :student_name
                      AND re.status <> 'disabled'
                    ORDER BY re.created_at DESC
                    LIMIT 1
                    """
                ),
                {"student_id": normalized_student_id, "student_name": payload.student_name.strip()},
            )
            .mappings()
            .first()
        )
    mode = row["mode"] if row else None
    if mode != "self_registration":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student self-registration is not enabled")
    return await activate_student(payload)


def get_user_from_access_token(access_token: str) -> AuthUser:
    try:
        claims = decode_access_token(access_token)
    except AuthError as exc:
        raise _auth_error(str(exc)) from exc

    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT au.id, au.username, au.role, au.display_name, au.status,
                           au.must_change_password, au.password_version,
                           sp.student_id, sp.class_id, c.class_name
                    FROM auth_sessions s
                    JOIN app_users au ON au.id = s.user_id
                    LEFT JOIN student_profiles sp ON sp.user_id = au.id
                    LEFT JOIN classes c ON c.id = sp.class_id
                    WHERE s.token_jti = :jti
                      AND s.revoked_at IS NULL
                      AND s.expires_at > now()
                      AND au.id = CAST(:user_id AS uuid)
                    """
                ),
                {"jti": claims.get("jti"), "user_id": claims.get("sub")},
            )
            .mappings()
            .first()
        )
    if not row:
        raise _auth_error("Session is no longer active")

    user = _user_from_row(dict(row))
    if claims.get("preview") or claims.get("preview_purpose"):
        user.preview_mode = True
        user.preview_purpose = claims.get("preview_purpose") or claims.get("purpose")
        user.preview_teacher_user_id = claims.get("teacher_user_id")
        user.preview_class_id = claims.get("preview_class_id") or user.class_id
        user.preview_student_id = claims.get("preview_student_id") or user.student_id
    if user.status != "active" or user.password_version != int(claims.get("password_version") or 0):
        raise _auth_error("User session is no longer valid")
    return user


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> AuthUser:
    if not credentials:
        raise _auth_error()
    return get_user_from_access_token(credentials.credentials)


def require_roles(*roles: str) -> Callable[[AuthUser], AuthUser]:
    async def dependency(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if user.role == "student" and user.must_change_password:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Password change required")
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dependency


async def require_platform_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.role != PLATFORM_ADMIN_ROLE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform admin account required")
    return user


async def require_teacher_console_user(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if not is_teacher_console_role(user.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher console account required")
    return user


@router.get("/me", response_model=AuthUser)
async def me(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    return user


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, bool]:
    claims = decode_access_token(credentials.credentials) if credentials else {}
    with db_session() as session:
        session.execute(
            text(
                """
                UPDATE auth_sessions
                SET revoked_at = now()
                WHERE token_jti = :jti AND user_id = CAST(:user_id AS uuid)
                """
            ),
            {"jti": claims.get("jti"), "user_id": user.id},
        )
    return {"ok": True}


@router.post("/password")
async def change_password(
    payload: PasswordChangeRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, bool]:
    claims = decode_access_token(credentials.credentials) if credentials else {}
    with db_session() as session:
        row = (
            session.execute(
                text("SELECT password_hash FROM app_users WHERE id = CAST(:user_id AS uuid)"),
                {"user_id": user.id},
            )
            .mappings()
            .first()
        )
        if not row or not verify_password(payload.current_password, row["password_hash"]):
            raise _auth_error("Current password is invalid")
        session.execute(
            text(
                """
                UPDATE app_users
                SET password_hash = :password_hash,
                    must_change_password = false,
                    password_version = password_version + 1,
                    updated_at = now()
                WHERE id = CAST(:user_id AS uuid)
                """
            ),
            {"user_id": user.id, "password_hash": hash_password(payload.new_password)},
        )
        session.execute(
            text(
                """
                UPDATE auth_sessions
                SET revoked_at = now()
                WHERE user_id = CAST(:user_id AS uuid)
                  AND token_jti <> :current_jti
                  AND revoked_at IS NULL
                """
            ),
            {"user_id": user.id, "current_jti": claims.get("jti")},
        )
    return {"ok": True}


@router.post("/student/password", response_model=LoginResponse)
def change_student_password(
    payload: StudentPasswordChangeRequest,
    user: AuthUser = Depends(get_current_user),
) -> LoginResponse:
    if user.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student account required")
    if user.preview_mode:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Preview student account mutation is disabled")
    with db_session() as session:
        row = (
            session.execute(
                text("SELECT password_hash FROM app_users WHERE id = CAST(:user_id AS uuid)"),
                {"user_id": user.id},
            )
            .mappings()
            .first()
        )
        if not row:
            raise _auth_error("Current password is invalid")
        requires_current_password = not user.must_change_password
        if requires_current_password and (
            not payload.current_password or not verify_password(payload.current_password, row["password_hash"])
        ):
            raise _auth_error("Current password is invalid")
        updated = (
            session.execute(
                text(
                    """
                    UPDATE app_users
                    SET password_hash = :password_hash,
                        must_change_password = false,
                        password_version = password_version + 1,
                        updated_at = now()
                    WHERE id = CAST(:user_id AS uuid)
                    RETURNING id, username, role, display_name, status, must_change_password, password_version
                    """
                ),
                {"user_id": user.id, "password_hash": hash_password(payload.new_password)},
            )
            .mappings()
            .one()
        )
        updated_user = dict(updated)
        session.execute(
            text(
                """
                UPDATE auth_sessions
                SET revoked_at = now()
                WHERE user_id = CAST(:user_id AS uuid)
                  AND revoked_at IS NULL
                """
            ),
            {"user_id": user.id},
        )
    next_user = _user_from_row(updated_user)
    next_user.student_id = user.student_id
    next_user.class_id = user.class_id
    next_user.class_name = user.class_name
    return _issue_login_response(next_user)

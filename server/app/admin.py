from __future__ import annotations

import json
import secrets
from datetime import datetime
from pathlib import Path as FilePath
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path as PathParam, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from server.app.auth import AuthUser, require_roles
from server.app.config import get_settings
from server.app.curriculum import (
    archive_curriculum_version,
    create_curriculum_draft,
    get_curriculum_version,
    list_curriculum_versions,
    load_curriculum_artifact,
    publish_curriculum_version,
)
from server.app.database import db_session
from server.app.feedback import FEEDBACK_STATUSES, normalize_feedback_type, feedback_row_to_item, feedback_visibility_sql
from server.app.media import create_media_asset, create_media_binding, list_media_assets, publish_media_binding
from server.app.platform_settings import (
    AIConfigurationResponse,
    AIConfigurationUpdate,
    LearningBehaviorSettings,
    PlatformSettingsResponse,
    get_ai_configuration_response,
    get_learning_behavior_settings,
    save_ai_configuration,
    save_learning_behavior_settings,
)
from server.app.roster import parse_roster, roster_preview
from server.app.schemas import FeedbackListResponse, FeedbackSummaryResponse, FeedbackUpdateRequest
from server.app.review import apply_review_action, get_review_item, list_review_items
from server.app.security import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])


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


class CurriculumCreateRequest(BaseModel):
    artifact_path: str = Field(default="data/processed/reviewed_curriculum.json", min_length=1)


class ReviewActionRequest(BaseModel):
    action: str = Field(pattern="^(approve|reject|request_changes|publish|unpublish|archive)$")
    note: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class MediaBindingRequest(BaseModel):
    media_asset_id: str = Field(min_length=1)
    target_type: str = Field(pattern="^(chapter|knowledge_unit|knowledge_point|experiment|learning_card)$")
    target_id: str = Field(min_length=1)
    title: str | None = None
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.get("/platform-settings", response_model=PlatformSettingsResponse)
async def admin_get_platform_settings(
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> PlatformSettingsResponse:
    return PlatformSettingsResponse(settings=get_learning_behavior_settings(), can_edit=user.role == "admin")


@router.put("/platform-settings", response_model=PlatformSettingsResponse)
async def admin_update_platform_settings(
    payload: LearningBehaviorSettings,
    user: AuthUser = Depends(require_roles("admin")),
) -> PlatformSettingsResponse:
    saved = save_learning_behavior_settings(payload, user.id)
    return PlatformSettingsResponse(settings=saved, can_edit=True)


@router.get("/ai-configuration", response_model=AIConfigurationResponse)
async def admin_get_ai_configuration(
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> AIConfigurationResponse:
    return get_ai_configuration_response(can_edit=user.role == "admin")


@router.put("/ai-configuration", response_model=AIConfigurationResponse)
async def admin_update_ai_configuration(
    payload: AIConfigurationUpdate,
    user: AuthUser = Depends(require_roles("admin")),
) -> AIConfigurationResponse:
    return save_ai_configuration(payload, user.id)


def _dump_model(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=True)
    return model.dict(exclude_unset=True)


def _feedback_filters(
    user: AuthUser,
    *,
    status_filter: str | None = None,
    feedback_type: str | None = None,
    class_id: str | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    visibility_sql, params = feedback_visibility_sql(user, "sf")
    filters = [visibility_sql]
    if status_filter:
        if status_filter not in FEEDBACK_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid feedback status")
        filters.append("sf.status = :status_filter")
        params["status_filter"] = status_filter
    if feedback_type:
        filters.append("sf.feedback_type = :feedback_type")
        params["feedback_type"] = normalize_feedback_type(feedback_type)
    if class_id:
        filters.append("sf.class_id = :class_id")
        params["class_id"] = class_id
    if search:
        filters.append(
            """
            (
              sf.content ILIKE :search
              OR sf.student_id ILIKE :search
              OR sf.student_name_snapshot ILIKE :search
              OR sf.class_name_snapshot ILIKE :search
            )
            """
        )
        params["search"] = f"%{search.strip()}%"
    if date_from:
        filters.append("sf.created_at >= CAST(:date_from AS timestamptz)")
        params["date_from"] = date_from
    if date_to:
        filters.append("sf.created_at <= CAST(:date_to AS timestamptz)")
        params["date_to"] = date_to
    return filters, params


def _feedback_select_sql(where_sql: str) -> str:
    return f"""
        SELECT sf.*,
               au.display_name AS handler_display_name
        FROM student_feedback sf
        LEFT JOIN app_users au ON au.id = sf.handler_user_id
        WHERE {where_sql}
    """


def _load_visible_feedback(session: Any, feedback_id: str, user: AuthUser) -> dict[str, Any]:
    visibility_sql, params = feedback_visibility_sql(user, "sf")
    params["feedback_id"] = feedback_id
    row = (
        session.execute(
            text(_feedback_select_sql(f"sf.id = CAST(:feedback_id AS uuid) AND {visibility_sql}")),
            params,
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    return feedback_row_to_item(dict(row))


@router.get("/feedback/summary", response_model=FeedbackSummaryResponse)
async def admin_feedback_summary(
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> FeedbackSummaryResponse:
    visibility_sql, params = feedback_visibility_sql(user, "sf")
    with db_session() as session:
        row = (
            session.execute(
                text(
                    f"""
                    SELECT
                      COUNT(*) AS total_count,
                      COUNT(*) FILTER (WHERE status = 'open') AS open_count,
                      COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress_count,
                      COUNT(*) FILTER (WHERE status = 'resolved') AS resolved_count,
                      COUNT(*) FILTER (WHERE status = 'archived') AS archived_count,
                      COUNT(*) FILTER (WHERE created_at >= now() - interval '7 days') AS recent_count
                    FROM student_feedback sf
                    WHERE {visibility_sql}
                    """
                ),
                params,
            )
            .mappings()
            .one()
        )
    summary_fields = getattr(FeedbackSummaryResponse, "model_fields", None) or getattr(FeedbackSummaryResponse, "__fields__", {})
    return FeedbackSummaryResponse(**{key: int(row.get(key) or 0) for key in summary_fields})


@router.get("/feedback", response_model=FeedbackListResponse)
async def admin_list_feedback(
    status_filter: str | None = Query(default=None, alias="status"),
    feedback_type: str | None = None,
    class_id: str | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> FeedbackListResponse:
    filters, params = _feedback_filters(
        user,
        status_filter=status_filter,
        feedback_type=feedback_type,
        class_id=class_id,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )
    where_sql = " AND ".join(f"({item})" for item in filters)
    with db_session() as session:
        total = int(
            session.execute(
                text(f"SELECT COUNT(*) FROM student_feedback sf WHERE {where_sql}"),
                params,
            ).scalar_one()
            or 0
        )
        rows = [
            feedback_row_to_item(dict(row))
            for row in session.execute(
                text(
                    _feedback_select_sql(where_sql)
                    + """
                    ORDER BY sf.created_at DESC, sf.id DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {**params, "limit": limit, "offset": offset},
            )
            .mappings()
            .all()
        ]
    return FeedbackListResponse(items=rows, total=total)


@router.get("/feedback/{feedback_id}")
async def admin_get_feedback(
    feedback_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        return _load_visible_feedback(session, feedback_id, user)


@router.patch("/feedback/{feedback_id}")
async def admin_update_feedback(
    payload: FeedbackUpdateRequest,
    feedback_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    data = _dump_model(payload)
    with db_session() as session:
        _load_visible_feedback(session, feedback_id, user)
        set_clauses = ["handler_user_id = CAST(:handler_user_id AS uuid)", "updated_at = now()"]
        params: dict[str, Any] = {"feedback_id": feedback_id, "handler_user_id": user.id}
        if "status" in data and data["status"] is not None:
            if data["status"] not in FEEDBACK_STATUSES:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid feedback status")
            set_clauses.append("status = :next_status")
            set_clauses.append(
                "resolved_at = CASE WHEN :next_status = 'resolved' THEN COALESCE(resolved_at, now()) ELSE NULL END"
            )
            params["next_status"] = data["status"]
        if "internal_note" in data:
            set_clauses.append("internal_note = :internal_note")
            params["internal_note"] = data.get("internal_note")
        if len(set_clauses) > 2:
            session.execute(
                text(
                    f"""
                    UPDATE student_feedback
                    SET {", ".join(set_clauses)}
                    WHERE id = CAST(:feedback_id AS uuid)
                    """
                ),
                params,
            )
        return _load_visible_feedback(session, feedback_id, user)


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


def _teacher_can_access_class(user: AuthUser, class_id: str) -> bool:
    if user.role == "admin":
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


def require_class_access(class_id: str, user: AuthUser) -> None:
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


@router.get("/classes", response_model=list[ClassResponse])
async def list_classes(user: AuthUser = Depends(require_roles("admin", "teacher"))) -> list[ClassResponse]:
    if user.role == "admin":
        sql = """
            SELECT c.id, c.class_name, c.description, c.status,
                   COUNT(re.id) FILTER (WHERE re.status <> 'disabled') AS student_count
            FROM classes c
            LEFT JOIN roster_entries re ON re.class_id = c.id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """
        params: dict[str, Any] = {}
    else:
        sql = """
            SELECT c.id, c.class_name, c.description, c.status,
                   COUNT(re.id) FILTER (WHERE re.status <> 'disabled') AS student_count
            FROM teacher_classes tc
            JOIN classes c ON c.id = tc.class_id
            LEFT JOIN roster_entries re ON re.class_id = c.id
            WHERE tc.teacher_user_id = CAST(:teacher_id AS uuid)
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """
        params = {"teacher_id": user.id}
    with db_session() as session:
        rows = [dict(row) for row in session.execute(text(sql), params).mappings().all()]
    return [_class_row_to_response(row) for row in rows]


@router.get("/registration-settings", response_model=RegistrationSettingsResponse)
async def get_registration_settings(
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> RegistrationSettingsResponse:
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


@router.put("/registration-settings", response_model=RegistrationSettingsResponse)
async def update_registration_settings(
    payload: RegistrationSettingsUpdateRequest,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> RegistrationSettingsResponse:
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


@router.get("/classes/{class_id}/registration-settings", response_model=RegistrationSettingsResponse)
async def get_class_registration_settings(
    class_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> RegistrationSettingsResponse:
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


@router.put("/classes/{class_id}/registration-settings", response_model=RegistrationSettingsResponse)
async def update_class_registration_settings(
    payload: RegistrationSettingsUpdateRequest,
    class_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
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


@router.get("/curriculum/versions")
async def admin_list_curriculum_versions(
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> list[dict[str, Any]]:
    return list_curriculum_versions()


@router.post("/curriculum/versions")
async def admin_create_curriculum_version(
    payload: CurriculumCreateRequest,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    curriculum = load_curriculum_artifact(FilePath(payload.artifact_path))
    return create_curriculum_draft(curriculum, actor_user_id=user.id)


@router.get("/curriculum/versions/{version_id}")
async def admin_get_curriculum_version(
    version_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    version = get_curriculum_version(version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum version not found")
    return version


@router.post("/curriculum/versions/{version_id}/publish")
async def admin_publish_curriculum_version(
    version_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    try:
        return publish_curriculum_version(version_id, actor_user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/curriculum/versions/{version_id}/archive")
async def admin_archive_curriculum_version(
    version_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    try:
        return archive_curriculum_version(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/review/items")
async def admin_list_review_items(
    item_type: str | None = None,
    status_filter: str | None = None,
    chapter_id: str | None = None,
    search: str | None = None,
    limit: int = 300,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return list_review_items(
        item_type=item_type,
        status=status_filter,
        chapter_id=chapter_id,
        search=search,
        limit=limit,
    )


@router.get("/review/items/{item_id}")
async def admin_get_review_item(
    item_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    item = get_review_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review item not found")
    return item


@router.post("/review/items/{item_id}/actions")
async def admin_apply_review_action(
    payload: ReviewActionRequest,
    item_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    try:
        return apply_review_action(
            item_id=item_id,
            action=payload.action,
            actor_user_id=user.id,
            note=payload.note,
            payload=payload.payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/media/assets")
async def admin_list_media_assets(
    upload_status: str | None = None,
    limit: int = 200,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return list_media_assets(upload_status=upload_status, limit=limit)


@router.get("/media/assets/{asset_id}/file", include_in_schema=False)
async def admin_get_media_asset_file(
    asset_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> FileResponse:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT id, relative_path, mime_type, original_file_name, upload_status
                    FROM media_assets
                    WHERE id = CAST(:asset_id AS uuid)
                    """
                ),
                {"asset_id": asset_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    if row["upload_status"] != "ready":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Media asset is not ready for preview")
    root = get_settings().media_root.resolve()
    file_path = (root / row["relative_path"]).resolve()
    if root != file_path and root not in file_path.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found")
    return FileResponse(
        file_path,
        media_type=row.get("mime_type") or "application/octet-stream",
        filename=row.get("original_file_name") or file_path.name,
    )


@router.post("/media/assets")
async def admin_upload_media_asset(
    title: str = Form(...),
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    content = await file.read()
    return create_media_asset(
        title=title,
        filename=file.filename or "upload.mp4",
        content=content,
        content_type=file.content_type,
        uploaded_by=user.id,
    )


@router.post("/media/assets/{asset_id}/replace")
async def admin_replace_media_asset(
    asset_id: str = PathParam(min_length=1),
    title: str = Form(...),
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    content = await file.read()
    return create_media_asset(
        title=title,
        filename=file.filename or "upload.mp4",
        content=content,
        content_type=file.content_type,
        uploaded_by=user.id,
        replace_asset_id=asset_id,
    )


@router.post("/media/bindings")
async def admin_create_media_binding(
    payload: MediaBindingRequest,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    return create_media_binding(
        media_asset_id=payload.media_asset_id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        title=payload.title,
        status=payload.status,
        metadata=payload.metadata,
    )


@router.post("/media/bindings/{binding_id}/publish")
async def admin_publish_media_binding(
    binding_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    try:
        return publish_media_binding(binding_id, actor_user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/classes", response_model=ClassResponse)
async def create_class(
    payload: ClassCreateRequest,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> ClassResponse:
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


@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> ClassResponse:
    require_class_access(class_id, user)
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT c.id, c.class_name, c.description, c.status,
                           COUNT(re.id) FILTER (WHERE re.status <> 'disabled') AS student_count
                    FROM classes c
                    LEFT JOIN roster_entries re ON re.class_id = c.id
                    WHERE c.id = :class_id
                    GROUP BY c.id
                    """
                ),
                {"class_id": class_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return _class_row_to_response(dict(row))


@router.patch("/classes/{class_id}", response_model=ClassResponse)
async def update_class(
    payload: ClassUpdateRequest,
    class_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> ClassResponse:
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
                                WHERE class_id = classes.id AND status <> 'disabled'
                              ) AS student_count
                    """
                ),
                {
                    "class_id": class_id,
                    "class_name": payload.class_name,
                    "description": payload.description,
                    "status": payload.status,
                },
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return _class_row_to_response(dict(row))


@router.post("/classes/{class_id}/teachers")
async def assign_teacher_to_class(
    payload: TeacherClassAssignRequest,
    class_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin")),
) -> dict[str, bool]:
    with db_session() as session:
        teacher = (
            session.execute(
                text("SELECT id FROM app_users WHERE id = CAST(:id AS uuid) AND role = 'teacher'"),
                {"id": payload.teacher_user_id},
            )
            .mappings()
            .first()
        )
        klass = session.execute(text("SELECT id FROM classes WHERE id = :class_id"), {"class_id": class_id}).first()
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


@router.post("/classes/{class_id}/roster/preview")
async def preview_roster_import(
    class_id: str = PathParam(min_length=1),
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    require_class_access(class_id, user)
    class_name = _load_class_name(class_id)
    content = await file.read()
    rows = parse_roster(file.filename or "roster.csv", content, default_class_name=class_name)
    return roster_preview(rows)


@router.post("/classes/{class_id}/roster/import")
async def import_roster(
    class_id: str = PathParam(min_length=1),
    file: UploadFile = File(...),
    mode: str = Form(default="upsert"),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    require_class_access(class_id, user)
    if mode not in {"upsert", "overwrite"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Import mode must be upsert or overwrite")
    class_name = _load_class_name(class_id)
    content = await file.read()
    rows = parse_roster(file.filename or "roster.csv", content, default_class_name=class_name)
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
                    "file_name": file.filename,
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


@router.get("/classes/{class_id}/students", response_model=list[RosterStudentResponse])
async def list_roster_students(
    class_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> list[RosterStudentResponse]:
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
                    ORDER BY
                      CASE re.status
                        WHEN 'active' THEN 1
                        WHEN 'pending' THEN 2
                        ELSE 3
                      END,
                      re.student_id
                    """
                ),
                {"class_id": class_id},
            )
            .mappings()
            .all()
        )
    return [_roster_student_response(dict(row)) for row in rows]


@router.post("/classes/{class_id}/students", response_model=RosterStudentResponse)
async def create_roster_student(
    payload: RosterStudentCreateRequest,
    class_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
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


@router.patch("/classes/{class_id}/students/{student_id}", response_model=RosterStudentResponse)
async def update_roster_student(
    payload: RosterStudentUpdateRequest,
    class_id: str = PathParam(min_length=1),
    student_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
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


@router.delete("/classes/{class_id}/students/{student_id}", response_model=RosterStudentResponse)
async def disable_roster_student(
    class_id: str = PathParam(min_length=1),
    student_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> RosterStudentResponse:
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


@router.post("/classes/{class_id}/students/{student_id}/reset-password")
async def reset_student_password(
    payload: StudentPasswordResetRequest,
    class_id: str = PathParam(min_length=1),
    student_id: str = PathParam(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activated student not found")
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

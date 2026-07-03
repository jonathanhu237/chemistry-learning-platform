from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from server.app.auth import AuthUser, is_teacher_role, require_teacher_user
from server.app.domains.platform.roles import TEACHER_ROLE
from server.app.domains.assessments.reports import (
    get_global_report_prompt_settings,
    reset_global_report_prompt_settings,
    save_global_report_prompt_settings,
)
from server.app.domains.platform.settings import (
    AIConfigurationResponse,
    AIConfigurationUpdate,
    LearningBehaviorSettings,
    PlatformSettingsResponse,
    get_ai_configuration_response,
    get_learning_behavior_settings,
    save_ai_configuration,
    save_learning_behavior_settings,
)
from server.app.student_assessment_report_schemas import (
    AssessmentReportPromptSettingsResponse,
    AssessmentReportPromptSettingsUpdate,
)
from server.app.infrastructure.database import db_session
from server.app.security import hash_password


router = APIRouter(prefix="/api/teacher", tags=["teacher-platform"])


class TeacherAccountCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    display_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=128)
    must_change_password: bool = True


class TeacherAccountUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    status: Literal["active", "disabled"] | None = None
    must_change_password: bool | None = None


class TeacherAccountResponse(BaseModel):
    id: str
    username: str
    role: str
    display_name: str
    status: str
    must_change_password: bool


def _teacher_account_response(row: dict[str, object]) -> TeacherAccountResponse:
    return TeacherAccountResponse(
        id=str(row["id"]),
        username=str(row["username"]),
        role=str(row["role"]),
        display_name=str(row["display_name"]),
        status=str(row["status"]),
        must_change_password=bool(row["must_change_password"]),
    )


@router.get("/accounts/teachers", response_model=list[TeacherAccountResponse])
async def teacher_list_teacher_accounts(
    user: AuthUser = Depends(require_teacher_user),
) -> list[TeacherAccountResponse]:
    if not is_teacher_role(user.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher role is required")

    with db_session() as session:
        rows = (
            session.execute(
                text(
                    """
                    SELECT id, username, role, display_name, status, must_change_password
                    FROM app_users
                    WHERE role = :role
                    ORDER BY
                      CASE WHEN id = CAST(:current_user_id AS uuid) THEN 0 ELSE 1 END,
                      created_at,
                      username
                    """
                ),
                {"role": TEACHER_ROLE, "current_user_id": user.id},
            )
            .mappings()
            .all()
        )
    return [_teacher_account_response(dict(row)) for row in rows]


@router.post("/accounts/teachers", response_model=TeacherAccountResponse, status_code=status.HTTP_201_CREATED)
async def teacher_create_teacher_account(
    payload: TeacherAccountCreateRequest,
    user: AuthUser = Depends(require_teacher_user),
) -> TeacherAccountResponse:
    if not is_teacher_role(user.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher role is required")

    username = payload.username.strip()
    display_name = payload.display_name.strip()
    if not username:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Teacher username is required")
    if not display_name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Teacher display name is required")

    with db_session() as session:
        existing = session.execute(
            text("SELECT id FROM app_users WHERE username = :username"),
            {"username": username},
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Teacher username already exists")

        row = (
            session.execute(
                text(
                    """
                    INSERT INTO app_users (
                      username, role, display_name, password_hash, status,
                      must_change_password, password_version, updated_at
                    )
                    VALUES (
                      :username, :role, :display_name, :password_hash, 'active',
                      :must_change_password, 1, now()
                    )
                    RETURNING id, username, role, display_name, status, must_change_password
                    """
                ),
                {
                    "username": username,
                    "role": TEACHER_ROLE,
                    "display_name": display_name,
                    "password_hash": hash_password(payload.password),
                    "must_change_password": payload.must_change_password,
                },
            )
            .mappings()
            .one()
        )

    return _teacher_account_response(dict(row))


@router.patch("/accounts/teachers/{teacher_id}", response_model=TeacherAccountResponse)
async def teacher_update_teacher_account(
    teacher_id: str,
    payload: TeacherAccountUpdateRequest,
    user: AuthUser = Depends(require_teacher_user),
) -> TeacherAccountResponse:
    if not is_teacher_role(user.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher role is required")
    if payload.display_name is None and payload.status is None and payload.must_change_password is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No teacher account updates provided")

    display_name = payload.display_name.strip() if payload.display_name is not None else None
    if payload.display_name is not None and not display_name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Teacher display name is required")
    if payload.status == "disabled" and teacher_id == user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Current teacher account cannot be disabled")

    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE app_users
                    SET display_name = COALESCE(:display_name, display_name),
                        status = COALESCE(:account_status, status),
                        must_change_password = COALESCE(:must_change_password, must_change_password),
                        updated_at = now()
                    WHERE id = CAST(:teacher_id AS uuid)
                      AND role = :role
                    RETURNING id, username, role, display_name, status, must_change_password
                    """
                ),
                {
                    "teacher_id": teacher_id,
                    "role": TEACHER_ROLE,
                    "display_name": display_name,
                    "account_status": payload.status,
                    "must_change_password": payload.must_change_password,
                },
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher account not found")
    return _teacher_account_response(dict(row))


@router.get("/platform-settings", response_model=PlatformSettingsResponse)
async def teacher_get_platform_settings(
    user: AuthUser = Depends(require_teacher_user),
) -> PlatformSettingsResponse:
    return PlatformSettingsResponse(settings=get_learning_behavior_settings(), can_edit=is_teacher_role(user.role))


@router.put("/platform-settings", response_model=PlatformSettingsResponse)
async def teacher_update_platform_settings(
    payload: LearningBehaviorSettings,
    user: AuthUser = Depends(require_teacher_user),
) -> PlatformSettingsResponse:
    saved = save_learning_behavior_settings(payload, user.id)
    return PlatformSettingsResponse(settings=saved, can_edit=True)


@router.get("/ai-configuration", response_model=AIConfigurationResponse)
async def teacher_get_ai_configuration(
    user: AuthUser = Depends(require_teacher_user),
) -> AIConfigurationResponse:
    return get_ai_configuration_response(can_edit=is_teacher_role(user.role))


@router.put("/ai-configuration", response_model=AIConfigurationResponse)
async def teacher_update_ai_configuration(
    payload: AIConfigurationUpdate,
    user: AuthUser = Depends(require_teacher_user),
) -> AIConfigurationResponse:
    return save_ai_configuration(payload, user.id)


@router.get("/assessment-report-prompts", response_model=AssessmentReportPromptSettingsResponse)
async def teacher_get_assessment_report_prompts(
    user: AuthUser = Depends(require_teacher_user),
) -> AssessmentReportPromptSettingsResponse:
    return get_global_report_prompt_settings(user)


@router.put("/assessment-report-prompts", response_model=AssessmentReportPromptSettingsResponse)
async def teacher_update_assessment_report_prompts(
    payload: AssessmentReportPromptSettingsUpdate,
    user: AuthUser = Depends(require_teacher_user),
) -> AssessmentReportPromptSettingsResponse:
    return save_global_report_prompt_settings(payload, user)


@router.delete("/assessment-report-prompts", response_model=AssessmentReportPromptSettingsResponse)
async def teacher_reset_assessment_report_prompts(
    user: AuthUser = Depends(require_teacher_user),
) -> AssessmentReportPromptSettingsResponse:
    return reset_global_report_prompt_settings(user)

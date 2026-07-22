from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path

from server.app.auth import AuthUser, require_supervisor_teacher
from server.app.domains.platform.teacher_accounts import (
    TeacherAccountCreateRequest,
    TeacherAccountPasswordResetRequest,
    TeacherAccountResponse,
    create_teacher_account,
    disable_teacher_account,
    enable_teacher_account,
    list_teacher_accounts,
    reset_teacher_account_password,
)


router = APIRouter(prefix="/api/admin/teacher-accounts", tags=["admin-teacher-accounts"])
SupervisorTeacher = Annotated[AuthUser, Depends(require_supervisor_teacher)]
TeacherAccountId = Annotated[UUID, Path(description="Teacher account user ID")]


@router.get("", response_model=list[TeacherAccountResponse])
def admin_list_teacher_accounts(_user: SupervisorTeacher) -> list[TeacherAccountResponse]:
    return list_teacher_accounts()


@router.post("", response_model=TeacherAccountResponse)
def admin_create_teacher_account(
    payload: TeacherAccountCreateRequest,
    _user: SupervisorTeacher,
) -> TeacherAccountResponse:
    return create_teacher_account(payload)


@router.post("/{account_id}/reset-password", response_model=TeacherAccountResponse)
def admin_reset_teacher_account_password(
    payload: TeacherAccountPasswordResetRequest,
    account_id: TeacherAccountId,
    user: SupervisorTeacher,
) -> TeacherAccountResponse:
    return reset_teacher_account_password(str(account_id), payload, actor_user_id=user.id)


@router.post("/{account_id}/disable", response_model=TeacherAccountResponse)
def admin_disable_teacher_account(
    account_id: TeacherAccountId,
    user: SupervisorTeacher,
) -> TeacherAccountResponse:
    return disable_teacher_account(str(account_id), actor_user_id=user.id)


@router.post("/{account_id}/enable", response_model=TeacherAccountResponse)
def admin_enable_teacher_account(
    account_id: TeacherAccountId,
    user: SupervisorTeacher,
) -> TeacherAccountResponse:
    return enable_teacher_account(str(account_id), actor_user_id=user.id)

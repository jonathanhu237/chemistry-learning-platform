from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from server.app.api.web_admin.auth import WebAdminSessionResponse, require_web_admin_token
from server.app.domains.platform.teacher_accounts import (
    TeacherAccountCreateRequest,
    TeacherAccountPasswordResetRequest,
    TeacherAccountPatchRequest,
    TeacherAccountResponse,
    create_teacher_account,
    delete_teacher_account,
    disable_teacher_account,
    enable_teacher_account,
    list_teacher_accounts,
    patch_teacher_account,
    reset_teacher_account_password,
)


router = APIRouter(prefix="/api/web-admin", tags=["web-admin-teacher-accounts"])


@router.get("/session", response_model=WebAdminSessionResponse)
async def web_admin_session(_auth: None = Depends(require_web_admin_token)) -> WebAdminSessionResponse:
    return WebAdminSessionResponse(ok=True)


@router.get("/teacher-accounts", response_model=list[TeacherAccountResponse])
async def web_admin_list_teacher_accounts(
    _auth: None = Depends(require_web_admin_token),
) -> list[TeacherAccountResponse]:
    return list_teacher_accounts()


@router.post("/teacher-accounts", response_model=TeacherAccountResponse)
async def web_admin_create_teacher_account(
    payload: TeacherAccountCreateRequest,
    _auth: None = Depends(require_web_admin_token),
) -> TeacherAccountResponse:
    return create_teacher_account(payload)


@router.patch("/teacher-accounts/{account_id}", response_model=TeacherAccountResponse)
async def web_admin_patch_teacher_account(
    payload: TeacherAccountPatchRequest,
    account_id: str = Path(min_length=1),
    _auth: None = Depends(require_web_admin_token),
) -> TeacherAccountResponse:
    return patch_teacher_account(account_id, payload)


@router.post("/teacher-accounts/{account_id}/reset-password", response_model=TeacherAccountResponse)
async def web_admin_reset_teacher_account_password(
    payload: TeacherAccountPasswordResetRequest,
    account_id: str = Path(min_length=1),
    _auth: None = Depends(require_web_admin_token),
) -> TeacherAccountResponse:
    return reset_teacher_account_password(account_id, payload)


@router.post("/teacher-accounts/{account_id}/disable", response_model=TeacherAccountResponse)
async def web_admin_disable_teacher_account(
    account_id: str = Path(min_length=1),
    _auth: None = Depends(require_web_admin_token),
) -> TeacherAccountResponse:
    return disable_teacher_account(account_id)


@router.post("/teacher-accounts/{account_id}/enable", response_model=TeacherAccountResponse)
async def web_admin_enable_teacher_account(
    account_id: str = Path(min_length=1),
    _auth: None = Depends(require_web_admin_token),
) -> TeacherAccountResponse:
    return enable_teacher_account(account_id)


@router.delete("/teacher-accounts/{account_id}", response_model=TeacherAccountResponse)
async def web_admin_delete_teacher_account(
    account_id: str = Path(min_length=1),
    _auth: None = Depends(require_web_admin_token),
) -> TeacherAccountResponse:
    return delete_teacher_account(account_id)

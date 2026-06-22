from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, Path, UploadFile

from server.app.auth import AuthUser, require_teacher_console_user
from server.app.domains.roster.classes import (
    ClassCreateRequest,
    ClassResponse,
    ClassUpdateRequest,
    RegistrationSettingsResponse,
    RegistrationSettingsUpdateRequest,
    RosterStudentCreateRequest,
    RosterStudentResponse,
    RosterStudentUpdateRequest,
    StudentPasswordResetRequest,
    TeacherClassAssignRequest,
    assign_teacher_to_class,
    create_class,
    create_roster_student,
    disable_roster_student,
    get_class,
    get_class_registration_settings,
    get_registration_settings,
    import_roster,
    list_classes,
    list_roster_students,
    preview_roster_import,
    reset_student_password,
    update_class,
    update_class_registration_settings,
    update_registration_settings,
    update_roster_student,
)


router = APIRouter(prefix="/api/admin", tags=["admin-classes"])


@router.get("/classes", response_model=list[ClassResponse])
async def admin_list_classes(user: AuthUser = Depends(require_teacher_console_user)) -> list[ClassResponse]:
    return list_classes(user)


@router.get("/registration-settings", response_model=RegistrationSettingsResponse)
async def admin_get_registration_settings(
    user: AuthUser = Depends(require_teacher_console_user),
) -> RegistrationSettingsResponse:
    return get_registration_settings()


@router.put("/registration-settings", response_model=RegistrationSettingsResponse)
async def admin_update_registration_settings(
    payload: RegistrationSettingsUpdateRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> RegistrationSettingsResponse:
    return update_registration_settings(payload, user)


@router.get("/classes/{class_id}/registration-settings", response_model=RegistrationSettingsResponse)
async def admin_get_class_registration_settings(
    class_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> RegistrationSettingsResponse:
    return get_class_registration_settings(class_id, user)


@router.put("/classes/{class_id}/registration-settings", response_model=RegistrationSettingsResponse)
async def admin_update_class_registration_settings(
    payload: RegistrationSettingsUpdateRequest,
    class_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> RegistrationSettingsResponse:
    return update_class_registration_settings(payload, class_id, user)


@router.post("/classes", response_model=ClassResponse)
async def admin_create_class(
    payload: ClassCreateRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> ClassResponse:
    return create_class(payload, user)


@router.get("/classes/{class_id}", response_model=ClassResponse)
async def admin_get_class(
    class_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> ClassResponse:
    return get_class(class_id, user)


@router.patch("/classes/{class_id}", response_model=ClassResponse)
async def admin_update_class(
    payload: ClassUpdateRequest,
    class_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> ClassResponse:
    return update_class(payload, class_id, user)


@router.post("/classes/{class_id}/teachers")
async def admin_assign_teacher_to_class(
    payload: TeacherClassAssignRequest,
    class_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, bool]:
    return assign_teacher_to_class(payload, class_id)


@router.post("/classes/{class_id}/roster/preview")
async def admin_preview_roster_import(
    class_id: str = Path(min_length=1),
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    content = await file.read()
    return preview_roster_import(class_id, file.filename, content, user)


@router.post("/classes/{class_id}/roster/import")
async def admin_import_roster(
    class_id: str = Path(min_length=1),
    file: UploadFile = File(...),
    mode: str = Form(default="upsert"),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    content = await file.read()
    return import_roster(class_id, file.filename, content, mode, user)


@router.get("/classes/{class_id}/students", response_model=list[RosterStudentResponse])
async def admin_list_roster_students(
    class_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> list[RosterStudentResponse]:
    return list_roster_students(class_id, user)


@router.post("/classes/{class_id}/students", response_model=RosterStudentResponse)
async def admin_create_roster_student(
    payload: RosterStudentCreateRequest,
    class_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> RosterStudentResponse:
    return create_roster_student(payload, class_id, user)


@router.patch("/classes/{class_id}/students/{student_id}", response_model=RosterStudentResponse)
async def admin_update_roster_student(
    payload: RosterStudentUpdateRequest,
    class_id: str = Path(min_length=1),
    student_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> RosterStudentResponse:
    return update_roster_student(payload, class_id, student_id, user)


@router.delete("/classes/{class_id}/students/{student_id}", response_model=RosterStudentResponse)
async def admin_disable_roster_student(
    class_id: str = Path(min_length=1),
    student_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> RosterStudentResponse:
    return disable_roster_student(class_id, student_id, user)


@router.post("/classes/{class_id}/students/{student_id}/reset-password")
async def admin_reset_student_password(
    payload: StudentPasswordResetRequest,
    class_id: str = Path(min_length=1),
    student_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, bool]:
    return reset_student_password(payload, class_id, student_id, user)

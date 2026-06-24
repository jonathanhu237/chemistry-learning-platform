from __future__ import annotations

from fastapi import APIRouter, Depends

from server.app.auth import AuthUser, is_teacher_console_role, require_teacher_console_user
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


router = APIRouter(prefix="/api/admin", tags=["admin-platform"])


@router.get("/platform-settings", response_model=PlatformSettingsResponse)
async def admin_get_platform_settings(
    user: AuthUser = Depends(require_teacher_console_user),
) -> PlatformSettingsResponse:
    return PlatformSettingsResponse(settings=get_learning_behavior_settings(), can_edit=is_teacher_console_role(user.role))


@router.put("/platform-settings", response_model=PlatformSettingsResponse)
async def admin_update_platform_settings(
    payload: LearningBehaviorSettings,
    user: AuthUser = Depends(require_teacher_console_user),
) -> PlatformSettingsResponse:
    saved = save_learning_behavior_settings(payload, user.id)
    return PlatformSettingsResponse(settings=saved, can_edit=True)


@router.get("/ai-configuration", response_model=AIConfigurationResponse)
async def admin_get_ai_configuration(
    user: AuthUser = Depends(require_teacher_console_user),
) -> AIConfigurationResponse:
    return get_ai_configuration_response(can_edit=is_teacher_console_role(user.role))


@router.put("/ai-configuration", response_model=AIConfigurationResponse)
async def admin_update_ai_configuration(
    payload: AIConfigurationUpdate,
    user: AuthUser = Depends(require_teacher_console_user),
) -> AIConfigurationResponse:
    return save_ai_configuration(payload, user.id)


@router.get("/assessment-report-prompts", response_model=AssessmentReportPromptSettingsResponse)
async def admin_get_assessment_report_prompts(
    user: AuthUser = Depends(require_teacher_console_user),
) -> AssessmentReportPromptSettingsResponse:
    return get_global_report_prompt_settings(user)


@router.put("/assessment-report-prompts", response_model=AssessmentReportPromptSettingsResponse)
async def admin_update_assessment_report_prompts(
    payload: AssessmentReportPromptSettingsUpdate,
    user: AuthUser = Depends(require_teacher_console_user),
) -> AssessmentReportPromptSettingsResponse:
    return save_global_report_prompt_settings(payload, user)


@router.delete("/assessment-report-prompts", response_model=AssessmentReportPromptSettingsResponse)
async def admin_reset_assessment_report_prompts(
    user: AuthUser = Depends(require_teacher_console_user),
) -> AssessmentReportPromptSettingsResponse:
    return reset_global_report_prompt_settings(user)

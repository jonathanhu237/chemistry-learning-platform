from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from server.app.auth import AuthUser, require_teacher_user
from server.app.domains.student_legacy.video_points import (
    legacy_student_video_points,
    set_legacy_video_point_recommendation,
)
from server.app.domains.teacher_legacy.read_models import (
    teacher_legacy_class_analytics,
    teacher_legacy_class_weak_points,
    teacher_legacy_classes,
    teacher_legacy_evaluation_system,
    teacher_legacy_overview,
    teacher_legacy_question_resources,
    teacher_legacy_video_resources,
)
from server.app.student_legacy_schemas import LegacyRecommendationUpdateRequest, LegacyStudentVideoPointResponse
from server.app.teacher_legacy_schemas import (
    LegacyTeacherAnalyticsResponse,
    LegacyTeacherClassesResponse,
    LegacyTeacherEvaluationSystemResponse,
    LegacyTeacherOverviewResponse,
    LegacyTeacherQuestionResourcesResponse,
    LegacyTeacherVideoResourcesResponse,
    LegacyTeacherWeakPointsResponse,
)


router = APIRouter(prefix="/api/teacher/legacy", tags=["teacher-legacy"])


@router.get("/video-points", response_model=LegacyStudentVideoPointResponse)
def teacher_legacy_video_points(
    q: str = Query(default="", max_length=120),
    limit: int = Query(default=500, ge=1, le=500),
    user: AuthUser = Depends(require_teacher_user),
) -> LegacyStudentVideoPointResponse:
    return legacy_student_video_points(query=q, limit=limit)


@router.put("/video-points/{node_id}/recommendation", response_model=LegacyStudentVideoPointResponse)
def teacher_set_legacy_video_point_recommendation(
    node_id: str,
    payload: LegacyRecommendationUpdateRequest,
    user: AuthUser = Depends(require_teacher_user),
) -> LegacyStudentVideoPointResponse:
    updated = set_legacy_video_point_recommendation(
        node_id=node_id,
        recommended=payload.recommended,
        sort_order=payload.sort_order,
        user_id=user.id,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legacy video point not found")
    return legacy_student_video_points(query="", limit=500)


@router.get("/teacher-demo/overview", response_model=LegacyTeacherOverviewResponse)
def teacher_legacy_teacher_demo_overview(
    user: AuthUser = Depends(require_teacher_user),
) -> LegacyTeacherOverviewResponse:
    return teacher_legacy_overview(user)


@router.get("/teacher-demo/video-resources", response_model=LegacyTeacherVideoResourcesResponse)
def teacher_legacy_teacher_demo_video_resources(
    q: str = Query(default="", max_length=120),
    user: AuthUser = Depends(require_teacher_user),
) -> LegacyTeacherVideoResourcesResponse:
    return teacher_legacy_video_resources(q=q)


@router.get("/teacher-demo/question-resources", response_model=LegacyTeacherQuestionResourcesResponse)
def teacher_legacy_teacher_demo_question_resources(
    user: AuthUser = Depends(require_teacher_user),
) -> LegacyTeacherQuestionResourcesResponse:
    return teacher_legacy_question_resources()


@router.get("/teacher-demo/classes", response_model=LegacyTeacherClassesResponse)
def teacher_legacy_teacher_demo_classes(
    user: AuthUser = Depends(require_teacher_user),
) -> LegacyTeacherClassesResponse:
    return teacher_legacy_classes(user)


@router.get("/teacher-demo/classes/{class_id}/analytics", response_model=LegacyTeacherAnalyticsResponse)
def teacher_legacy_teacher_demo_class_analytics(
    class_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> LegacyTeacherAnalyticsResponse:
    return teacher_legacy_class_analytics(class_id=class_id, user=user)


@router.get("/teacher-demo/classes/{class_id}/weak-points", response_model=LegacyTeacherWeakPointsResponse)
def teacher_legacy_teacher_demo_class_weak_points(
    class_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_user),
) -> LegacyTeacherWeakPointsResponse:
    return teacher_legacy_class_weak_points(class_id=class_id, user=user)


@router.get("/teacher-demo/evaluation-system", response_model=LegacyTeacherEvaluationSystemResponse)
def teacher_legacy_teacher_demo_evaluation_system(
    user: AuthUser = Depends(require_teacher_user),
) -> LegacyTeacherEvaluationSystemResponse:
    return teacher_legacy_evaluation_system()

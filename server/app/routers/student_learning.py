from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import FileResponse

from server.app.auth import AuthUser, get_user_from_access_token, require_roles
from server.app.services.student_learning_service import (
    get_student_experiment_detail,
    get_student_experiment_group,
    get_student_learning_home,
    get_student_media_thumbnail,
    stream_student_media_asset,
)
from server.app.student_learning_schemas import (
    StudentExperimentDetailResponse,
    StudentExperimentGroupResponse,
    StudentLearningHomeResponse,
)


router = APIRouter(prefix="/api/student", tags=["student-learning"])
StudentUser = Annotated[AuthUser, Depends(require_roles("student"))]


@router.get("/learning-home", response_model=StudentLearningHomeResponse)
def learning_home(user: StudentUser) -> StudentLearningHomeResponse:
    return get_student_learning_home(user)


@router.get("/experiment-groups/{parent_code}", response_model=StudentExperimentGroupResponse)
def experiment_group(parent_code: Annotated[str, Path(min_length=1)], user: StudentUser) -> StudentExperimentGroupResponse:
    return get_student_experiment_group(user, parent_code)


@router.get("/experiments/{experiment_id}", response_model=StudentExperimentDetailResponse)
def experiment_detail(experiment_id: Annotated[str, Path(min_length=1)], user: StudentUser) -> StudentExperimentDetailResponse:
    return get_student_experiment_detail(user, experiment_id)


def _student_from_query_token(access_token: str) -> AuthUser:
    user = get_user_from_access_token(access_token)
    if user.role != "student" or user.must_change_password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user


@router.get("/media/assets/{asset_id}/stream", include_in_schema=False)
def student_media_stream(
    asset_id: Annotated[str, Path(min_length=1)],
    access_token: Annotated[str, Query(min_length=1)],
) -> FileResponse:
    _student_from_query_token(access_token)
    return stream_student_media_asset(asset_id)


@router.get("/media/assets/{asset_id}/thumbnail", include_in_schema=False)
def student_media_thumbnail(
    asset_id: Annotated[str, Path(min_length=1)],
    access_token: Annotated[str, Query(min_length=1)],
) -> FileResponse:
    _student_from_query_token(access_token)
    return get_student_media_thumbnail(asset_id)

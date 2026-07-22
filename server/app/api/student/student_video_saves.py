from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from server.app.auth import AuthUser, require_roles
from server.app.domains.student_home_feed import student_saved_video_feed
from server.app.domains.student_video_saves import set_student_video_favorite
from server.app.student_home_feed_schemas import StudentHomeVideoFeedResponse
from server.app.student_video_save_schemas import StudentVideoSaveRequest, StudentVideoSaveResponse


router = APIRouter(prefix="/api/student", tags=["student-video-saves"])
StudentUser = Annotated[AuthUser, Depends(require_roles("student"))]


@router.put("/video-saves/favorite", response_model=StudentVideoSaveResponse)
def save_student_video_favorite(
    payload: StudentVideoSaveRequest,
    user: StudentUser,
) -> StudentVideoSaveResponse:
    return set_student_video_favorite(user, payload=payload, active=True)


@router.delete("/video-saves/favorite", response_model=StudentVideoSaveResponse)
def remove_student_video_favorite(
    payload: StudentVideoSaveRequest,
    user: StudentUser,
) -> StudentVideoSaveResponse:
    return set_student_video_favorite(user, payload=payload, active=False)


@router.get("/video-saves/favorite/feed", response_model=StudentHomeVideoFeedResponse)
def favorite_video_feed(
    user: StudentUser,
    limit: Annotated[int, Query(ge=1, le=30)] = 12,
    cursor: Annotated[str | None, Query()] = None,
) -> StudentHomeVideoFeedResponse:
    return student_saved_video_feed(user, limit=limit, cursor=cursor)

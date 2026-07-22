from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from server.app.auth import AuthUser, require_roles
from server.app.domains.student_home_feed import student_home_video_feed
from server.app.student_home_feed_schemas import StudentHomeVideoFeedResponse


router = APIRouter(prefix="/api/student", tags=["student-home-feed"])
StudentUser = Annotated[AuthUser, Depends(require_roles("student"))]


@router.get("/home-video-feed", response_model=StudentHomeVideoFeedResponse)
def student_home_video_feed_route(
    user: StudentUser,
    q: Annotated[str | None, Query(max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=30)] = 12,
    cursor: Annotated[str | None, Query()] = None,
) -> StudentHomeVideoFeedResponse:
    return student_home_video_feed(user, query=q, limit=limit, cursor=cursor)

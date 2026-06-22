from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path

from server.app.auth import AuthUser, require_teacher_console_user
from server.app.domains.video_library.index_client import video_library_index_diagnostics
from server.app.domains.video_library.search import diagnose_video_library_search
from server.app.domains.catalog.experiments import (
    get_experiment,
    list_experiment_videos,
    list_experiments_overview,
)


router = APIRouter(prefix="/api/admin", tags=["experiment-admin"])


@router.get("/experiments")
async def admin_list_experiments(
    chapter_id: str | None = None,
    status_filter: str | None = None,
    include_archived: bool = False,
    video_status: str | None = None,
    question_status: str | None = None,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return list_experiments_overview(
        chapter_id=chapter_id,
        status_filter=status_filter,
        include_archived=include_archived,
        video_status=video_status,
        question_status=question_status,
    )


@router.get("/experiments/{experiment_id}")
async def admin_get_experiment(
    experiment_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return get_experiment(experiment_id=experiment_id)


@router.get("/experiment-videos")
async def admin_list_experiment_videos(
    experiment_id: str | None = None,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return list_experiment_videos(experiment_id=experiment_id)


@router.get("/video-library/index/diagnostics")
async def admin_video_library_index_diagnostics(
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return video_library_index_diagnostics()


@router.get("/video-library/search/diagnostics")
async def admin_video_library_search_diagnostics(
    q: str = "",
    limit: int = 10,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    bounded_limit = max(1, min(limit, 50))
    return diagnose_video_library_search(query=q, limit=bounded_limit)

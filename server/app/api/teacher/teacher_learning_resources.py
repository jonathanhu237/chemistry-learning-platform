from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from server.app.auth import AuthUser, require_teacher_user
from server.app.domains.catalog.learning_resources import (
    get_experiment_knowledge_framework_overview,
    get_learning_resource_overview,
)


router = APIRouter(prefix="/api/teacher", tags=["experiment-teacher"])


@router.get("/learning-resources/overview")
async def teacher_learning_resources_overview(
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    return get_learning_resource_overview()


@router.get("/experiment-knowledge-framework/overview")
async def teacher_experiment_knowledge_framework_overview(
    user: AuthUser = Depends(require_teacher_user),
) -> dict[str, Any]:
    return get_experiment_knowledge_framework_overview()

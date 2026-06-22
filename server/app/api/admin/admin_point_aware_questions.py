from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from server.app.auth import AuthUser, require_teacher_console_user
from server.app.experiment_admin_schemas import PointAwareSuggestionRequest
from server.app.domains.platform.settings import ai_feature_enabled
from server.app.domains.questions.point_aware import create_point_aware_suggestions
from server.app.domains.questions.generation import OBJECTIVE_TYPES
from server.app.domains.questions.workbench import _ensure_question_workbench_rag_ready, _load_workbench_evidence_package


router = APIRouter(prefix="/api/admin", tags=["experiment-admin"])


@router.post("/question-banks/point-aware-suggestions")
async def admin_create_point_aware_suggestions(
    payload: PointAwareSuggestionRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    if not ai_feature_enabled("question_bank_assistant"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Question bank assistant is disabled")
    invalid_types = [item for item in payload.question_types if item not in OBJECTIVE_TYPES]
    if invalid_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported question types: {invalid_types}")
    if payload.intent == "repair_question" and not payload.question_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="question_id is required for repair suggestions")
    rag_gate = _ensure_question_workbench_rag_ready()
    return create_point_aware_suggestions(
        payload=payload,
        user=user,
        rag_gate=rag_gate,
        evidence_loader=_load_workbench_evidence_package,
    )

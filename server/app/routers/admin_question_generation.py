from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from server.app.auth import AuthUser, require_roles
from server.app.experiment_admin import _ensure_question_workbench_rag_ready, _load_workbench_evidence_package
from server.app.experiment_admin_schemas import GenerationRequest
from server.app.platform_settings import ai_feature_enabled
from server.app.services.question_generation_service import OBJECTIVE_TYPES, generate_question_drafts


router = APIRouter(prefix="/api/admin", tags=["experiment-admin"])


@router.post("/question-banks/generate")
async def admin_generate_questions(
    payload: GenerationRequest,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    if not ai_feature_enabled("question_bank_assistant"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="题库助手当前未启用。")
    invalid_types = [item for item in payload.question_types if item not in OBJECTIVE_TYPES]
    if invalid_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported question types: {invalid_types}")
    rag_gate = _ensure_question_workbench_rag_ready()
    return generate_question_drafts(
        payload=payload,
        user=user,
        rag_gate=rag_gate,
        evidence_loader=_load_workbench_evidence_package,
    )

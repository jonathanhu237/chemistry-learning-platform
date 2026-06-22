from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path as FilePath
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from server.app.domains.assistant.agent import run_agent, run_agent_stream
from server.app.auth import AuthUser, is_teacher_console_role, require_teacher_console_user
from server.app.infrastructure.settings import get_settings
from server.app.domains.platform.settings import (
    effective_ai_settings,
    get_ai_configuration_response,
    get_learning_behavior_settings,
)
from server.app.schemas import AgentAskRequest, AgentAskResponse, AgentChatMessage


router = APIRouter(prefix="/api/admin", tags=["admin-learning-assistant"])

RAG_ASSET_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class LearningAssistantAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1024)
    student_id: str | None = Field(default=None, max_length=128)
    chapter_id: str | None = Field(default=None, max_length=128)
    experiment_id: str | None = Field(default=None, max_length=128)
    point_key: str | None = Field(default=None, max_length=256)
    knowledge_point_ids: list[str] = Field(default_factory=list, max_length=10)
    allow_progress_lookup: bool = True
    allow_rag_lookup: bool = True
    conversation_history: list[AgentChatMessage] = Field(default_factory=list, max_length=20)
    max_answer_chars: int | None = Field(default=0, ge=0, le=20000)


def _within_root(path: FilePath, root: FilePath) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _rag_asset_candidates(raw_path: str, rag_root: FilePath) -> list[FilePath]:
    raw_text = str(raw_path or "").strip()
    normalized = raw_text.replace("\\", "/")
    candidates: list[FilePath] = []
    known_roots = ["E:/chemistry-rag/", "/chemistry-rag/"]
    for prefix in known_roots:
        if normalized.lower().startswith(prefix.lower()):
            candidates.append(rag_root / normalized[len(prefix):])
    raw_file_path = FilePath(raw_text)
    if raw_file_path.is_absolute():
        candidates.append(raw_file_path)
    else:
        candidates.append(rag_root / normalized)
    return candidates


def _resolve_rag_asset(raw_path: str) -> FilePath:
    rag_root = get_settings().chemistry_rag_root.resolve()
    for candidate in _rag_asset_candidates(raw_path, rag_root):
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if not _within_root(resolved, rag_root):
            continue
        if resolved.suffix.lower() not in RAG_ASSET_IMAGE_EXTENSIONS:
            continue
        if resolved.is_file():
            return resolved
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RAG 蝗ｾ蜒剰ｵ・ｺｧ荳榊ｭ伜惠謌紋ｸ榊庄隶ｿ髣ｮ")


def _sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


def _dump_full_model(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


@router.get("/learning-assistant/runtime")
async def admin_get_learning_assistant_runtime(
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    settings = get_settings()
    ai_config = get_ai_configuration_response(can_edit=is_teacher_console_role(user.role), auto_check=False)
    rag_runtime = ai_config.rag_runtime
    payload: dict[str, Any] = {
        "checked_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "rag_runtime": _dump_full_model(rag_runtime),
        "bge_status": "not_required",
        "bge_metrics": None,
        "bge_error": None,
    }
    if rag_runtime.bge_service_required and not settings.rag_bge_service_url:
        payload["bge_status"] = "not_configured"
        payload["bge_error"] = "BGE service URL is not configured"
    elif settings.rag_bge_service_url and rag_runtime.bge_service_required:
        payload["bge_status"] = "checking"
        metrics_started_at = time.perf_counter()
        try:
            with urllib.request.urlopen(
                f"{settings.rag_bge_service_url.rstrip('/')}/metrics",
                timeout=2.0,
            ) as response:
                metrics = json.loads(response.read().decode("utf-8"))
            if isinstance(metrics, dict):
                metrics["request_ms"] = round((time.perf_counter() - metrics_started_at) * 1000, 2)
                payload["bge_metrics"] = metrics
                payload["bge_status"] = "healthy" if metrics.get("ok") else "degraded"
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            payload["bge_status"] = "unreachable"
            payload["bge_error"] = f"{exc.__class__.__name__}: {str(exc)[:160]}"
    return payload


@router.get("/rag-assets")
async def admin_rag_asset(
    path: str = Query(..., min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> FileResponse:
    return FileResponse(_resolve_rag_asset(path))


@router.post("/learning-assistant/ask", response_model=AgentAskResponse)
async def admin_test_learning_assistant(
    payload: LearningAssistantAskRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> AgentAskResponse:
    learning_settings = get_learning_behavior_settings()
    ai_config = get_ai_configuration_response(can_edit=is_teacher_console_role(user.role), auto_check=False)
    if not learning_settings.learning_features.ai_assistant_enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="蟄ｦ逕溽ｫｯ AI 蟄ｦ荵蜉ｩ謇句・蜿｣蟾ｲ蜈ｳ髣ｭ")
    if not ai_config.enabled_features.student_ai_assistant:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="蟄ｦ逕・AI 蟄ｦ荵蜉ｩ謇句粥閭ｽ蟾ｲ蜈ｳ髣ｭ")

    request = AgentAskRequest(
        student_id=payload.student_id or None,
        user_id=user.id,
        user_role="admin_debug",
        question=payload.question,
        chapter_id=payload.chapter_id or None,
        experiment_id=payload.experiment_id or None,
        point_key=payload.point_key or None,
        knowledge_point_ids=payload.knowledge_point_ids,
        allow_progress_lookup=payload.allow_progress_lookup,
        allow_rag_lookup=payload.allow_rag_lookup and ai_config.enabled_features.rag_access_enabled,
        conversation_history=payload.conversation_history,
        max_answer_chars=payload.max_answer_chars,
    )
    return await run_agent(request, settings=effective_ai_settings(get_settings()))


@router.post("/learning-assistant/ask/stream")
async def admin_stream_learning_assistant(
    payload: LearningAssistantAskRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> StreamingResponse:
    learning_settings = get_learning_behavior_settings()
    ai_config = get_ai_configuration_response(can_edit=is_teacher_console_role(user.role), auto_check=False)
    if not learning_settings.learning_features.ai_assistant_enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="陝・ｽｦ騾墓ｺｽ・ｫ・ｯ AI 陝・ｽｦ闕ｵ・ｰ陷会ｽｩ隰・唱繝ｻ陷ｿ・｣陝ｾ・ｲ陷茨ｽｳ鬮｣・ｭ")
    if not ai_config.enabled_features.student_ai_assistant:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="陝・ｽｦ騾輔・AI 陝・ｽｦ闕ｵ・ｰ陷会ｽｩ隰・唱邊･髢ｭ・ｽ陝ｾ・ｲ陷茨ｽｳ鬮｣・ｭ")

    request = AgentAskRequest(
        student_id=payload.student_id or None,
        user_id=user.id,
        user_role="admin_debug",
        question=payload.question,
        chapter_id=payload.chapter_id or None,
        experiment_id=payload.experiment_id or None,
        point_key=payload.point_key or None,
        knowledge_point_ids=payload.knowledge_point_ids,
        allow_progress_lookup=payload.allow_progress_lookup,
        allow_rag_lookup=payload.allow_rag_lookup and ai_config.enabled_features.rag_access_enabled,
        conversation_history=payload.conversation_history,
        max_answer_chars=payload.max_answer_chars,
    )

    async def event_stream():
        async for item in run_agent_stream(request, settings=effective_ai_settings(get_settings())):
            event = str(item.get("event") or "message")
            data = {key: value for key, value in item.items() if key != "event"}
            yield _sse_event(event, data)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

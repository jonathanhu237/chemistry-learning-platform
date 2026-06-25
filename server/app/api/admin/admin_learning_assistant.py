from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path as FilePath
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from server.app.auth import AuthUser, is_teacher_console_role, require_teacher_console_user
from server.app.domains.assistant.adapters.admin_debug import run_admin_debug_agent, stream_admin_debug_agent
from server.app.infrastructure.settings import get_settings
from server.app.domains.platform.settings import (
    effective_ai_settings,
    get_ai_configuration_response,
    get_learning_behavior_settings,
)
from server.app.schemas import AgentAskResponse, AgentChatMessage


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
    ai_config = get_ai_configuration_response(can_edit=is_teacher_console_role(user.role), auto_check=False)
    rag_runtime = ai_config.rag_runtime
    payload: dict[str, Any] = {
        "checked_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "rag_runtime": _dump_full_model(rag_runtime),
        "textbook_rag_status": rag_runtime.textbook_rag_status,
        "textbook_rag_error": None if rag_runtime.textbook_rag_status in {"disabled", "healthy"} else rag_runtime.textbook_rag_message,
        "textbook_rag_diagnostics": rag_runtime.textbook_rag_diagnostics,
    }
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

    return await run_admin_debug_agent(
        payload,
        user,
        settings=effective_ai_settings(get_settings()),
        rag_access_enabled=bool(ai_config.enabled_features.rag_access_enabled),
    )


@router.post("/learning-assistant/ask/stream")
async def admin_stream_learning_assistant(
    payload: LearningAssistantAskRequest,
    http_request: Request,
    user: AuthUser = Depends(require_teacher_console_user),
) -> StreamingResponse:
    learning_settings = get_learning_behavior_settings()
    ai_config = get_ai_configuration_response(can_edit=is_teacher_console_role(user.role), auto_check=False)
    if not learning_settings.learning_features.ai_assistant_enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="陝・ｽｦ騾墓ｺｽ・ｫ・ｯ AI 陝・ｽｦ闕ｵ・ｰ陷会ｽｩ隰・唱繝ｻ陷ｿ・｣陝ｾ・ｲ陷茨ｽｳ鬮｣・ｭ")
    if not ai_config.enabled_features.student_ai_assistant:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="陝・ｽｦ騾輔・AI 陝・ｽｦ闕ｵ・ｰ陷会ｽｩ隰・唱邊･髢ｭ・ｽ陝ｾ・ｲ陷茨ｽｳ鬮｣・ｭ")

    async def should_cancel() -> bool:
        return await http_request.is_disconnected()

    async def event_stream():
        async for item in stream_admin_debug_agent(
            payload,
            user,
            settings=effective_ai_settings(get_settings()),
            rag_access_enabled=bool(ai_config.enabled_features.rag_access_enabled),
            should_cancel=should_cancel,
        ):
            if await should_cancel():
                return
            event = str(item.get("event") or "message")
            data = {key: value for key, value in item.items() if key != "event"}
            if await should_cancel():
                return
            yield _sse_event(event, data)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import StreamingResponse

from server.app.auth import AuthUser, require_teacher_console_user
from server.app.domains.errors import DomainHTTPException
from server.app.experiment_admin_schemas import WorkbenchMessageRequest, WorkbenchSessionRequest
from server.app.domains.platform.settings import ai_feature_enabled
from server.app.domains.questions.workbench import (
    OBJECTIVE_TYPES,
    create_question_workbench_session,
    get_question_workbench_session,
    publish_question_workbench_candidate,
    reject_question_workbench_candidate,
    send_question_workbench_message,
)


router = APIRouter(prefix="/api/admin", tags=["experiment-admin"])


def _sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


@router.post("/question-banks/workbench-sessions")
async def admin_create_question_workbench_session(
    payload: WorkbenchSessionRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return create_question_workbench_session(payload=payload, user=user)


@router.get("/question-banks/workbench-sessions/{session_id}")
async def admin_get_question_workbench_session(
    session_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return get_question_workbench_session(session_id=session_id)


@router.post("/question-banks/workbench-sessions/{session_id}/messages/stream")
async def admin_stream_question_workbench_message(
    payload: WorkbenchMessageRequest,
    session_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> StreamingResponse:
    if not ai_feature_enabled("question_bank_assistant"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Question bank assistant is disabled")
    invalid_types = [item for item in payload.question_types if item not in OBJECTIVE_TYPES]
    if invalid_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported question types: {invalid_types}")

    async def event_stream():
        yield _sse_event("status", {"message": "已收到提示，正在准备题目上下文"})
        yield _sse_event("status", {"message": "正在调用 AI 生成候选题"})
        try:
            result = send_question_workbench_message(payload=payload, session_id=session_id, user=user)
            yield _sse_event("final", {"session": result})
        except (HTTPException, DomainHTTPException) as exc:
            yield _sse_event("error", {"message": exc.detail, "status": exc.status_code})
        except Exception as exc:
            yield _sse_event("error", {"message": str(exc) or exc.__class__.__name__})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/question-banks/workbench-sessions/{session_id}/messages")
async def admin_send_question_workbench_message(
    payload: WorkbenchMessageRequest,
    session_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return send_question_workbench_message(payload=payload, session_id=session_id, user=user)


@router.post("/question-banks/workbench-candidates/{candidate_id}/reject")
async def admin_reject_question_workbench_candidate(
    candidate_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return reject_question_workbench_candidate(candidate_id=candidate_id)


@router.post("/question-banks/workbench-candidates/{candidate_id}/publish")
async def admin_publish_question_workbench_candidate(
    candidate_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return publish_question_workbench_candidate(candidate_id=candidate_id, user=user)

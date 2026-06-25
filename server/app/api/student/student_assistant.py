from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from server.app.auth import AuthUser, require_roles
from server.app.domains.assistant.student_assistant import (
    generate_posttest_ai_summary,
    generate_posttest_mistake_explanation,
    stream_student_assistant_answer,
)
from server.app.student_assistant_schemas import (
    StudentAssistantAskRequest,
    StudentAssistantGeneratedResponse,
    StudentAssistantPosttestRequest,
)


router = APIRouter(prefix="/api/student", tags=["student-assistant"])
StudentUser = Annotated[AuthUser, Depends(require_roles("student"))]


def _sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


@router.post("/assistant/ask/stream")
async def stream_assistant_answer(payload: StudentAssistantAskRequest, user: StudentUser, request: Request) -> StreamingResponse:
    async def should_cancel() -> bool:
        return await request.is_disconnected()

    async def event_stream():
        async for item in stream_student_assistant_answer(user, payload, should_cancel=should_cancel):
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


@router.post("/assistant/posttest-summary", response_model=StudentAssistantGeneratedResponse)
async def posttest_summary(payload: StudentAssistantPosttestRequest, user: StudentUser) -> StudentAssistantGeneratedResponse:
    return await generate_posttest_ai_summary(user, payload.session_id)


@router.post("/assistant/posttest-mistakes", response_model=StudentAssistantGeneratedResponse)
async def posttest_mistakes(payload: StudentAssistantPosttestRequest, user: StudentUser) -> StudentAssistantGeneratedResponse:
    return await generate_posttest_mistake_explanation(user, payload.session_id)

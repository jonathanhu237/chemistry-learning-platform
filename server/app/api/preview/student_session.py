from __future__ import annotations

from fastapi import APIRouter

from server.app.domains.preview.student_device_preview import (
    StudentPreviewExchangeRequest,
    StudentPreviewExchangeResponse,
    exchange_preview_ticket,
)


router = APIRouter(prefix="/api/preview/student-session", tags=["student-preview-session"])


@router.post("/exchange", response_model=StudentPreviewExchangeResponse)
def exchange_student_preview_session(payload: StudentPreviewExchangeRequest) -> StudentPreviewExchangeResponse:
    return exchange_preview_ticket(payload.ticket)

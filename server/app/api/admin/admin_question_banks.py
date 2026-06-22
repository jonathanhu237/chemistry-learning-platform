from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, Path, Query, UploadFile

from server.app.auth import AuthUser, require_teacher_console_user
from server.app.experiment_admin_schemas import (
    QuestionBankAssistantRequest,
    QuestionRequest,
    QuestionUpdateRequest,
)
from server.app.domains.questions.bank import (
    create_question,
    disable_question,
    export_question_bank,
    import_question_bank,
    list_chapter_questions,
    list_question_bank_chapters_overview,
    list_question_banks,
    list_questions,
    preview_question_bank_assistant,
    publish_question,
    update_question,
)


router = APIRouter(prefix="/api/admin", tags=["experiment-admin"])


@router.get("/question-banks/chapters")
async def admin_list_question_bank_chapters(
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return list_question_bank_chapters_overview()


@router.get("/question-banks/chapter-questions")
async def admin_list_chapter_questions(
    chapter_id: str = Query(min_length=1),
    question_type: str | None = None,
    status_filter: str | None = None,
    experiment_id: str | None = None,
    search: str | None = None,
    limit: int = Query(default=300, ge=1, le=1000),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return list_chapter_questions(
        chapter_id=chapter_id,
        question_type=question_type,
        status_filter=status_filter,
        experiment_id=experiment_id,
        search=search,
        limit=limit,
    )


@router.post("/question-banks/assistant/preview")
async def admin_question_bank_assistant_preview(
    payload: QuestionBankAssistantRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return preview_question_bank_assistant(payload=payload, user=user)


@router.get("/question-banks")
async def admin_list_question_banks(
    experiment_id: str | None = None,
    chapter_id: str | None = None,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return list_question_banks(experiment_id=experiment_id, chapter_id=chapter_id)


@router.get("/question-banks/questions")
async def admin_list_questions(
    experiment_id: str | None = None,
    question_type: str | None = None,
    difficulty: str | None = None,
    status_filter: str | None = None,
    search: str | None = None,
    limit: int = Query(default=300, ge=1, le=1000),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return list_questions(
        experiment_id=experiment_id,
        question_type=question_type,
        difficulty=difficulty,
        status_filter=status_filter,
        search=search,
        limit=limit,
    )


@router.post("/question-banks/questions")
async def admin_create_question(
    payload: QuestionRequest,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return create_question(payload=payload, user=user)


@router.patch("/question-banks/questions/{question_id}")
async def admin_update_question(
    payload: QuestionUpdateRequest,
    question_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return update_question(payload=payload, question_id=question_id, user=user)


@router.post("/question-banks/questions/{question_id}/publish")
async def admin_publish_question(
    question_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return publish_question(question_id=question_id, user=user)


@router.post("/question-banks/questions/{question_id}/disable")
async def admin_disable_question(
    question_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return disable_question(question_id=question_id, user=user)


@router.post("/question-banks/import")
async def admin_import_question_bank(
    file: UploadFile = File(...),
    publish: bool = Form(False),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    content = await file.read()
    return import_question_bank(filename=file.filename, content=content, publish=publish, user=user)


@router.get("/question-banks/export")
async def admin_export_question_bank(
    experiment_id: str | None = None,
    status_filter: str | None = "published",
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return export_question_bank(experiment_id=experiment_id, status_filter=status_filter)

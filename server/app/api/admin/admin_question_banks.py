from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Path, Query, UploadFile
from pydantic import BaseModel, Field

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
    list_catalog_question_bank,
    list_question_bank_chapters_overview,
    list_question_banks,
    list_questions,
    preview_question_bank_assistant,
    process_question_bank_evidence_refresh_jobs,
    publish_question,
    refresh_catalog_question_bank_evidence,
    revoke_question_to_draft,
    update_question,
)


router = APIRouter(prefix="/api/admin", tags=["experiment-admin"])


class CatalogQuestionBankEvidenceRefreshRequest(BaseModel):
    chapter_id: str | None = None
    point_node_id: str | None = None
    force: bool = False
    process_now: bool = True
    process_limit: int = Field(default=200, ge=0, le=1000)


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


@router.get("/question-banks/catalog")
async def admin_list_catalog_question_bank(
    chapter_id: str | None = None,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return list_catalog_question_bank(chapter_id=chapter_id)


@router.post("/question-banks/catalog/evidence-refresh")
async def admin_refresh_catalog_question_bank_evidence(
    payload: CatalogQuestionBankEvidenceRefreshRequest,
    background_tasks: BackgroundTasks,
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    result = refresh_catalog_question_bank_evidence(
        chapter_id=payload.chapter_id,
        point_node_id=payload.point_node_id,
        force=payload.force,
    )
    job_ids = [str(job_id) for job_id in result.get("job_ids") or [] if str(job_id or "").strip()]
    if payload.process_now and job_ids:
        background_tasks.add_task(
            process_question_bank_evidence_refresh_jobs,
            job_ids,
            limit=payload.process_limit,
        )
    return {**result, "processing_started": bool(payload.process_now and job_ids), "process_limit": payload.process_limit}


@router.get("/question-banks/questions")
async def admin_list_questions(
    experiment_id: str | None = None,
    point_node_id: str | None = None,
    canonical_point_id: str | None = None,
    question_type: str | None = None,
    difficulty: str | None = None,
    status_filter: str | None = None,
    search: str | None = None,
    limit: int = Query(default=300, ge=1, le=1000),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return list_questions(
        experiment_id=experiment_id,
        point_node_id=point_node_id,
        canonical_point_id=canonical_point_id,
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


@router.post("/question-banks/questions/{question_id}/revoke-to-draft")
async def admin_revoke_question_to_draft(
    question_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_teacher_console_user),
) -> dict[str, Any]:
    return revoke_question_to_draft(question_id=question_id, user=user)


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

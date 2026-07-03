from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.app.api.error_translation import domain_http_exception_handler
from server.app.api.auth.routes import router as auth_router
from server.app.domains.errors import DomainHTTPException
from server.app.infrastructure.settings import get_settings
from server.app.infrastructure.database import check_database_connection
from server.app.repositories import get_repositories
from server.app.api.teacher.teacher_analytics import router as teacher_analytics_router
from server.app.api.teacher.teacher_catalog_tree import router as teacher_catalog_tree_router
from server.app.api.teacher.teacher_classes import router as teacher_classes_router
from server.app.api.teacher.teacher_curriculum_review import router as teacher_curriculum_review_router
from server.app.api.teacher.teacher_experiments import router as teacher_experiments_router
from server.app.api.teacher.teacher_feedback import router as teacher_feedback_router
from server.app.api.teacher.teacher_learning_assistant import router as teacher_learning_assistant_router
from server.app.api.teacher.teacher_learning_resources import router as teacher_learning_resources_router
from server.app.api.teacher.teacher_legacy import router as teacher_legacy_router
from server.app.api.teacher.teacher_media import router as teacher_media_router
from server.app.api.teacher.teacher_platform import router as teacher_platform_router
from server.app.api.teacher.teacher_question_banks import router as teacher_question_banks_router
from server.app.api.teacher.teacher_question_drafts import router as teacher_question_drafts_router
from server.app.api.teacher.teacher_question_generation import router as teacher_question_generation_router
from server.app.api.teacher.teacher_question_workbench import router as teacher_question_workbench_router
from server.app.api.teacher.teacher_point_aware_questions import router as teacher_point_aware_questions_router
from server.app.api.teacher.teacher_student_preview import router as teacher_student_preview_router
from server.app.api.student.student_catalog import router as student_catalog_router
from server.app.api.preview.catalog_preview import router as catalog_preview_router
from server.app.api.preview.student_session import router as student_preview_session_router
from server.app.api.student.student_experiment_questions import router as student_experiment_questions_router
from server.app.api.student.student_assistant import router as student_assistant_router
from server.app.api.student.student_assessment_reports import router as student_assessment_reports_router
from server.app.api.student.student_custom_assessment import router as student_custom_assessment_router
from server.app.api.student.student_learning import router as student_learning_router
from server.app.api.student.student_legacy import router as student_legacy_router
from server.app.api.student.student_home_feed import router as student_home_feed_router
from server.app.api.student.student_video_saves import router as student_video_saves_router
from server.app.api.student.student_posttest import router as student_posttest_router
from server.app.api.student.student_pretest import router as student_pretest_router
from server.app.api.student.student_platform import router as student_platform_router
from server.app.api.student.student_smart_assessment import router as student_smart_assessment_router
from server.app.api.student.student_video_library import router as student_video_library_router


settings = get_settings()
settings.validate_startup()
repositories = get_repositories()


def _cors_origins() -> list[str]:
    if "*" in settings.frontend_allowed_origins:
        return ["*"]
    return sorted({*settings.frontend_allowed_origins, *settings.student_preview_allowed_origins})


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    if settings.run_db_check_on_startup:
        check_database_connection()
    settings.media_root.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="SYSU Chemistry Teacher Service", version="0.1.0", lifespan=lifespan)
app.add_exception_handler(DomainHTTPException, domain_http_exception_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials="*" not in _cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(teacher_analytics_router)
app.include_router(teacher_catalog_tree_router)
app.include_router(teacher_classes_router)
app.include_router(teacher_curriculum_review_router)
app.include_router(teacher_experiments_router)
app.include_router(teacher_feedback_router)
app.include_router(teacher_learning_assistant_router)
app.include_router(teacher_learning_resources_router)
app.include_router(teacher_legacy_router)
app.include_router(teacher_media_router)
app.include_router(teacher_platform_router)
app.include_router(teacher_question_banks_router)
app.include_router(teacher_question_drafts_router)
app.include_router(teacher_question_generation_router)
app.include_router(teacher_question_workbench_router)
app.include_router(teacher_point_aware_questions_router)
app.include_router(teacher_student_preview_router)
app.include_router(student_catalog_router)
app.include_router(catalog_preview_router)
app.include_router(student_preview_session_router)
app.include_router(student_experiment_questions_router)
app.include_router(student_assistant_router)
app.include_router(student_assessment_reports_router)
app.include_router(student_custom_assessment_router)
app.include_router(student_home_feed_router)
app.include_router(student_learning_router)
app.include_router(student_legacy_router)
app.include_router(student_posttest_router)
app.include_router(student_pretest_router)
app.include_router(student_platform_router)
app.include_router(student_smart_assessment_router)
app.include_router(student_video_saves_router)
app.include_router(student_video_library_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _experiment_matches_chapter(experiment: dict[str, Any], chapter_id: str) -> bool:
    chapter_ids = experiment.get("chapter_ids") or []
    return experiment.get("chapter_id") == chapter_id or chapter_id in chapter_ids


def _chapter_summary(chapter: dict[str, Any]) -> dict[str, Any]:
    chapter_id = chapter["chapter_id"]
    kps = [item for item in repositories.content.knowledge_points() if item.get("chapter_id") == chapter_id]
    visible_experiments = [
        item
        for item in repositories.content.experiments()
        if _experiment_matches_chapter(item, chapter_id) and item.get("student_visible")
    ]
    questions = [
        item
        for item in repositories.content.questions()
        if item.get("chapter_id") == chapter_id and item.get("student_visible")
    ]
    return {
        **chapter,
        "knowledge_point_count": len(kps),
        "visible_experiment_count": len(visible_experiments),
        "question_count": len(questions),
    }


@app.get("/api/chapters")
async def api_chapters() -> list[dict[str, Any]]:
    return [_chapter_summary(chapter) for chapter in repositories.content.chapters()]

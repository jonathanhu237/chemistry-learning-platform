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
from server.app.api.admin.admin_analytics import router as admin_analytics_router
from server.app.api.admin.admin_catalog_tree import router as admin_catalog_tree_router
from server.app.api.admin.admin_classes import router as admin_classes_router
from server.app.api.admin.admin_curriculum_review import router as admin_curriculum_review_router
from server.app.api.admin.admin_experiments import router as admin_experiments_router
from server.app.api.admin.admin_feedback import router as admin_feedback_router
from server.app.api.admin.admin_learning_assistant import router as admin_learning_assistant_router
from server.app.api.admin.admin_learning_resources import router as admin_learning_resources_router
from server.app.api.admin.admin_media import router as admin_media_router
from server.app.api.admin.admin_platform import router as admin_platform_router
from server.app.api.admin.admin_question_banks import router as admin_question_banks_router
from server.app.api.admin.admin_question_drafts import router as admin_question_drafts_router
from server.app.api.admin.admin_question_generation import router as admin_question_generation_router
from server.app.api.admin.admin_question_workbench import router as admin_question_workbench_router
from server.app.api.admin.admin_point_aware_questions import router as admin_point_aware_questions_router
from server.app.api.admin.admin_student_preview import router as admin_student_preview_router
from server.app.api.web_admin.student_preview import router as web_admin_student_preview_router
from server.app.api.web_admin.teacher_accounts import router as web_admin_teacher_accounts_router
from server.app.api.student.student_catalog import router as student_catalog_router
from server.app.api.preview.catalog_preview import router as catalog_preview_router
from server.app.api.preview.student_session import router as student_preview_session_router
from server.app.api.student.student_experiment_questions import router as student_experiment_questions_router
from server.app.api.student.student_assistant import router as student_assistant_router
from server.app.api.student.student_assessment_reports import router as student_assessment_reports_router
from server.app.api.student.student_custom_assessment import router as student_custom_assessment_router
from server.app.api.student.student_learning import router as student_learning_router
from server.app.api.student.student_home_feed import router as student_home_feed_router
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


app = FastAPI(title="SYSU Chemistry Admin Service", version="0.1.0", lifespan=lifespan)
app.add_exception_handler(DomainHTTPException, domain_http_exception_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials="*" not in _cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_analytics_router)
app.include_router(admin_catalog_tree_router)
app.include_router(admin_classes_router)
app.include_router(admin_curriculum_review_router)
app.include_router(admin_experiments_router)
app.include_router(admin_feedback_router)
app.include_router(admin_learning_assistant_router)
app.include_router(admin_learning_resources_router)
app.include_router(admin_media_router)
app.include_router(admin_platform_router)
app.include_router(admin_question_banks_router)
app.include_router(admin_question_drafts_router)
app.include_router(admin_question_generation_router)
app.include_router(admin_question_workbench_router)
app.include_router(admin_point_aware_questions_router)
app.include_router(admin_student_preview_router)
app.include_router(web_admin_teacher_accounts_router)
app.include_router(web_admin_student_preview_router)
app.include_router(student_catalog_router)
app.include_router(catalog_preview_router)
app.include_router(student_preview_session_router)
app.include_router(student_experiment_questions_router)
app.include_router(student_assistant_router)
app.include_router(student_assessment_reports_router)
app.include_router(student_custom_assessment_router)
app.include_router(student_home_feed_router)
app.include_router(student_learning_router)
app.include_router(student_posttest_router)
app.include_router(student_pretest_router)
app.include_router(student_platform_router)
app.include_router(student_smart_assessment_router)
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

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.app.admin import router as admin_router
from server.app.auth import AuthUser, LoginResponse
from server.app.auth import change_password, change_student_password, login, logout, me, student_login
from server.app.config import get_settings
from server.app.database import check_database_connection
from server.app.repositories import get_repositories
from server.app.routers.admin_analytics import router as admin_analytics_router
from server.app.routers.admin_experiments import router as admin_experiments_router
from server.app.routers.admin_learning_resources import router as admin_learning_resources_router
from server.app.routers.admin_question_banks import router as admin_question_banks_router
from server.app.routers.admin_question_drafts import router as admin_question_drafts_router
from server.app.routers.admin_question_generation import router as admin_question_generation_router
from server.app.routers.admin_question_workbench import router as admin_question_workbench_router
from server.app.routers.admin_point_aware_questions import router as admin_point_aware_questions_router
from server.app.routers.student_experiment_questions import router as student_experiment_questions_router
from server.app.routers.student_assistant import router as student_assistant_router
from server.app.routers.student_learning import router as student_learning_router
from server.app.routers.student_posttest import router as student_posttest_router
from server.app.routers.student_pretest import router as student_pretest_router


settings = get_settings()
settings.validate_startup()
repositories = get_repositories()

app = FastAPI(title="SYSU Chemistry Admin Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.frontend_allowed_origins),
    allow_credentials=settings.frontend_allowed_origins != ("*",),
    allow_methods=["*"],
    allow_headers=["*"],
)

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
auth_router.post("/login", response_model=LoginResponse)(login)
auth_router.post("/student/login", response_model=LoginResponse)(student_login)
auth_router.get("/me", response_model=AuthUser)(me)
auth_router.post("/logout")(logout)
auth_router.post("/password")(change_password)
auth_router.post("/student/password", response_model=LoginResponse)(change_student_password)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_analytics_router)
app.include_router(admin_experiments_router)
app.include_router(admin_learning_resources_router)
app.include_router(admin_question_banks_router)
app.include_router(admin_question_drafts_router)
app.include_router(admin_question_generation_router)
app.include_router(admin_question_workbench_router)
app.include_router(admin_point_aware_questions_router)
app.include_router(student_experiment_questions_router)
app.include_router(student_assistant_router)
app.include_router(student_learning_router)
app.include_router(student_posttest_router)
app.include_router(student_pretest_router)

if (settings.admin_web_dist / "assets").exists():
    app.mount(
        "/admin/assets",
        StaticFiles(directory=settings.admin_web_dist / "assets"),
        name="admin-assets",
    )

if (settings.student_web_dist / "assets").exists():
    app.mount(
        "/assets",
        StaticFiles(directory=settings.student_web_dist / "assets"),
        name="student-assets",
    )


@app.on_event("startup")
async def startup_checks() -> None:
    if settings.run_db_check_on_startup:
        check_database_connection()
    settings.media_root.mkdir(parents=True, exist_ok=True)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/admin/sysu-logo.svg", include_in_schema=False)
async def admin_logo() -> FileResponse:
    logo_path = settings.admin_web_dist / "sysu-logo.svg"
    if not logo_path.exists():
        raise HTTPException(status_code=404, detail="Admin logo has not been built")
    return FileResponse(logo_path, media_type="image/svg+xml")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    logo_path = settings.student_web_dist / "sysu-logo.svg"
    if not logo_path.exists():
        logo_path = settings.admin_web_dist / "sysu-logo.svg"
    if not logo_path.exists():
        raise HTTPException(status_code=404, detail="Frontend logo has not been built")
    return FileResponse(logo_path, media_type="image/svg+xml")


@app.get("/admin", include_in_schema=False)
@app.get("/admin/{full_path:path}", include_in_schema=False)
async def admin_web(full_path: str = "") -> FileResponse:
    index_path = settings.admin_web_dist / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Admin web has not been built")
    return FileResponse(index_path)


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


@app.get("/", include_in_schema=False)
@app.get("/{full_path:path}", include_in_schema=False)
async def student_web(full_path: str = "") -> FileResponse:
    if full_path.startswith(("api/", "admin/", "assets/")) or full_path in {"api", "admin", "assets"}:
        raise HTTPException(status_code=404, detail="Not found")
    index_path = settings.student_web_dist / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Student web has not been built")
    return FileResponse(index_path)

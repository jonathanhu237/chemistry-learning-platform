from __future__ import annotations

from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.app.admin import router as admin_router
from server.app.auth import AuthUser, LoginResponse
from server.app.auth import change_password, login, logout, me
from server.app.config import get_settings
from server.app.database import check_database_connection
from server.app.experiment_admin import admin_router as experiment_admin_router
from server.app.repositories import get_repositories


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
auth_router.get("/me", response_model=AuthUser)(me)
auth_router.post("/logout")(logout)
auth_router.post("/password")(change_password)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(experiment_admin_router)

if (settings.admin_web_dist / "assets").exists():
    app.mount(
        "/admin/assets",
        StaticFiles(directory=settings.admin_web_dist / "assets"),
        name="admin-assets",
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
    logo_path = settings.admin_web_dist / "sysu-logo.svg"
    if not logo_path.exists():
        raise HTTPException(status_code=404, detail="Admin logo has not been built")
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

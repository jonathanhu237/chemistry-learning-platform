from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

from server.app import admin_main


def _prepare_student_dist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    dist_dir = tmp_path / "student-web"
    dist_dir.mkdir()
    index_path = dist_dir / "index.html"
    index_path.write_text("<!doctype html><div id=\"root\"></div>", encoding="utf-8")
    monkeypatch.setattr(admin_main, "settings", replace(admin_main.settings, student_web_dist=dist_dir))
    return index_path


def _student_fallback(path: str) -> FileResponse:
    return asyncio.run(admin_main.student_web(path))


@pytest.mark.parametrize(
    "path",
    [
        "",
        "home",
        "learn",
        "ai",
        "assessment",
        "profile",
        "chapter/halogens-17",
        "point/EXP_19_1_01",
        "ai/chat",
        "assessment/session/posttest-session",
        "assessment/report/posttest-session",
        "feedback/new",
    ],
)
def test_student_spa_fallback_serves_root_and_detail_routes(
    path: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index_path = _prepare_student_dist(tmp_path, monkeypatch)

    response = _student_fallback(path)

    assert isinstance(response, FileResponse)
    assert Path(response.path) == index_path


@pytest.mark.parametrize(
    "path",
    [
        "api",
        "api/student/app-config",
        "admin",
        "admin/dashboard",
        "assets",
        "assets/index.js",
    ],
)
def test_student_spa_fallback_excludes_api_admin_and_assets(
    path: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_student_dist(tmp_path, monkeypatch)

    with pytest.raises(HTTPException) as exc_info:
        _student_fallback(path)

    assert exc_info.value.status_code == 404

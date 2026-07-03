from __future__ import annotations

from pathlib import Path

import pytest

from server.app.app_runtime.main import app


ADMIN_ROUTE_CONTRACTS = [
    ("GET", "/api/teacher/platform-settings"),
    ("PUT", "/api/teacher/platform-settings"),
    ("GET", "/api/teacher/assessment-report-prompts"),
    ("PUT", "/api/teacher/assessment-report-prompts"),
    ("DELETE", "/api/teacher/assessment-report-prompts"),
    ("GET", "/api/teacher/ai-configuration"),
    ("PUT", "/api/teacher/ai-configuration"),
    ("GET", "/api/teacher/learning-assistant/runtime"),
    ("GET", "/api/teacher/rag-assets"),
    ("POST", "/api/teacher/learning-assistant/ask"),
    ("POST", "/api/teacher/learning-assistant/ask/stream"),
    ("GET", "/api/teacher/feedback/summary"),
    ("GET", "/api/teacher/feedback"),
    ("GET", "/api/teacher/feedback/{feedback_id}"),
    ("PATCH", "/api/teacher/feedback/{feedback_id}"),
    ("GET", "/api/teacher/classes"),
    ("POST", "/api/teacher/classes"),
    ("GET", "/api/teacher/classes/{class_id}"),
    ("PATCH", "/api/teacher/classes/{class_id}"),
    ("POST", "/api/teacher/classes/{class_id}/teachers"),
    ("GET", "/api/teacher/registration-settings"),
    ("PUT", "/api/teacher/registration-settings"),
    ("GET", "/api/teacher/classes/{class_id}/registration-settings"),
    ("PUT", "/api/teacher/classes/{class_id}/registration-settings"),
    ("GET", "/api/teacher/classes/{class_id}/assessment-report-prompts"),
    ("PUT", "/api/teacher/classes/{class_id}/assessment-report-prompts"),
    ("DELETE", "/api/teacher/classes/{class_id}/assessment-report-prompts"),
    ("POST", "/api/teacher/classes/{class_id}/roster/preview"),
    ("POST", "/api/teacher/classes/{class_id}/roster/import"),
    ("GET", "/api/teacher/classes/{class_id}/students"),
    ("POST", "/api/teacher/classes/{class_id}/students"),
    ("PATCH", "/api/teacher/classes/{class_id}/students/{student_id}"),
    ("DELETE", "/api/teacher/classes/{class_id}/students/{student_id}"),
    ("POST", "/api/teacher/classes/{class_id}/students/{student_id}/reset-password"),
    ("GET", "/api/teacher/classes/{class_id}/students/{student_id}/assessment-reports"),
    ("GET", "/api/teacher/classes/{class_id}/students/{student_id}/assessment-reports/{report_id}"),
    ("GET", "/api/teacher/curriculum/versions"),
    ("POST", "/api/teacher/curriculum/versions"),
    ("GET", "/api/teacher/curriculum/versions/{version_id}"),
    ("POST", "/api/teacher/curriculum/versions/{version_id}/publish"),
    ("POST", "/api/teacher/curriculum/versions/{version_id}/archive"),
    ("GET", "/api/teacher/review/items"),
    ("GET", "/api/teacher/review/items/{item_id}"),
    ("POST", "/api/teacher/review/items/{item_id}/actions"),
    ("GET", "/api/teacher/media/assets"),
    ("GET", "/api/teacher/media/upload-policy"),
    ("POST", "/api/teacher/media/assets/precheck"),
    ("GET", "/api/teacher/media/assets/processing"),
    ("POST", "/api/teacher/media/assets/complete-upload"),
    ("GET", "/api/teacher/media/assets/{asset_id}/file"),
    ("GET", "/api/teacher/media/assets/{asset_id}/stream"),
    ("GET", "/api/teacher/media/assets/{asset_id}/thumbnail"),
    ("GET", "/api/teacher/media/assets/{asset_id}/subtitle-tracks"),
    ("POST", "/api/teacher/media/assets/{asset_id}/subtitle-tracks"),
    ("PATCH", "/api/teacher/media/assets/{asset_id}/subtitle-tracks/{track_id}"),
    ("DELETE", "/api/teacher/media/assets/{asset_id}/subtitle-tracks/{track_id}"),
    ("POST", "/api/teacher/media/assets/{asset_id}/subtitle-tracks/{track_id}/retry"),
    ("GET", "/api/teacher/media/assets/{asset_id}/subtitle-tracks/{track_id}/stream"),
    ("POST", "/api/teacher/media/assets/{asset_id}/retry-processing"),
    ("GET", "/api/teacher/media/assets/{asset_id}/delete-plan"),
    ("POST", "/api/teacher/media/assets/{asset_id}/delete"),
    ("PATCH", "/api/teacher/media/duplicate-candidates/{candidate_id}"),
    ("POST", "/api/teacher/media/assets"),
    ("POST", "/api/teacher/media/assets/{asset_id}/replace"),
    ("POST", "/api/teacher/media/bindings"),
    ("POST", "/api/teacher/media/bindings/{binding_id}/publish"),
    ("POST", "/api/teacher/media/bindings/{binding_id}/unpublish"),
    ("DELETE", "/api/teacher/media/bindings/{binding_id}"),
    ("POST", "/api/teacher/student-preview/session"),
]


def _routes_for(path: str, method: str) -> list[object]:
    routes: list[object] = []
    stack = list(app.routes)
    while stack:
        route = stack.pop(0)
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            stack[0:0] = list(getattr(original_router, "routes", []) or [])
            continue
        routes.append(route)
    return [
        route
        for route in routes
        if getattr(route, "path", "") == path and method in getattr(route, "methods", set())
    ]


@pytest.mark.parametrize(("method", "path"), ADMIN_ROUTE_CONTRACTS)
def test_teacher_routes_are_registered_once(method: str, path: str) -> None:
    assert len(_routes_for(path, method)) == 1


def test_media_binding_canonical_routes_are_registered_and_aliases_removed() -> None:
    _routes_for_binding = {
        (method, path): len(_routes_for(path, method))
        for method, path in ADMIN_ROUTE_CONTRACTS
        if "/api/teacher/media/bindings/{binding_id}" in path
    }

    assert _routes_for_binding == {
        ("POST", "/api/teacher/media/bindings/{binding_id}/publish"): 1,
        ("POST", "/api/teacher/media/bindings/{binding_id}/unpublish"): 1,
        ("DELETE", "/api/teacher/media/bindings/{binding_id}"): 1,
    }

    assert _routes_for("/api/teacher/media/bindings/{binding_id}/delete", "POST") == []
    assert _routes_for("/api/teacher/media/bindings/{binding_id}/archive", "POST") == []


def test_legacy_teacher_router_files_are_removed() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    assert not (repo_root / "server" / "app" / "admin.py").exists()
    assert not (repo_root / "server" / "app" / "experiment_admin.py").exists()

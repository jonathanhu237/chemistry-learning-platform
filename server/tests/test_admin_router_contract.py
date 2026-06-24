from __future__ import annotations

from pathlib import Path

import pytest

from server.app.app_runtime.main import app


ADMIN_ROUTE_CONTRACTS = [
    ("GET", "/api/admin/platform-settings"),
    ("PUT", "/api/admin/platform-settings"),
    ("GET", "/api/admin/assessment-report-prompts"),
    ("PUT", "/api/admin/assessment-report-prompts"),
    ("DELETE", "/api/admin/assessment-report-prompts"),
    ("GET", "/api/admin/ai-configuration"),
    ("PUT", "/api/admin/ai-configuration"),
    ("GET", "/api/admin/learning-assistant/runtime"),
    ("GET", "/api/admin/rag-assets"),
    ("POST", "/api/admin/learning-assistant/ask"),
    ("POST", "/api/admin/learning-assistant/ask/stream"),
    ("GET", "/api/admin/feedback/summary"),
    ("GET", "/api/admin/feedback"),
    ("GET", "/api/admin/feedback/{feedback_id}"),
    ("PATCH", "/api/admin/feedback/{feedback_id}"),
    ("GET", "/api/admin/classes"),
    ("POST", "/api/admin/classes"),
    ("GET", "/api/admin/classes/{class_id}"),
    ("PATCH", "/api/admin/classes/{class_id}"),
    ("POST", "/api/admin/classes/{class_id}/teachers"),
    ("GET", "/api/admin/registration-settings"),
    ("PUT", "/api/admin/registration-settings"),
    ("GET", "/api/admin/classes/{class_id}/registration-settings"),
    ("PUT", "/api/admin/classes/{class_id}/registration-settings"),
    ("GET", "/api/admin/classes/{class_id}/assessment-report-prompts"),
    ("PUT", "/api/admin/classes/{class_id}/assessment-report-prompts"),
    ("DELETE", "/api/admin/classes/{class_id}/assessment-report-prompts"),
    ("POST", "/api/admin/classes/{class_id}/roster/preview"),
    ("POST", "/api/admin/classes/{class_id}/roster/import"),
    ("GET", "/api/admin/classes/{class_id}/students"),
    ("POST", "/api/admin/classes/{class_id}/students"),
    ("PATCH", "/api/admin/classes/{class_id}/students/{student_id}"),
    ("DELETE", "/api/admin/classes/{class_id}/students/{student_id}"),
    ("POST", "/api/admin/classes/{class_id}/students/{student_id}/reset-password"),
    ("GET", "/api/admin/classes/{class_id}/students/{student_id}/assessment-reports"),
    ("GET", "/api/admin/classes/{class_id}/students/{student_id}/assessment-reports/{report_id}"),
    ("GET", "/api/admin/curriculum/versions"),
    ("POST", "/api/admin/curriculum/versions"),
    ("GET", "/api/admin/curriculum/versions/{version_id}"),
    ("POST", "/api/admin/curriculum/versions/{version_id}/publish"),
    ("POST", "/api/admin/curriculum/versions/{version_id}/archive"),
    ("GET", "/api/admin/review/items"),
    ("GET", "/api/admin/review/items/{item_id}"),
    ("POST", "/api/admin/review/items/{item_id}/actions"),
    ("GET", "/api/admin/media/assets"),
    ("POST", "/api/admin/media/assets/precheck"),
    ("GET", "/api/admin/media/assets/processing"),
    ("POST", "/api/admin/media/assets/complete-upload"),
    ("GET", "/api/admin/media/assets/{asset_id}/file"),
    ("GET", "/api/admin/media/assets/{asset_id}/stream"),
    ("GET", "/api/admin/media/assets/{asset_id}/thumbnail"),
    ("POST", "/api/admin/media/assets/{asset_id}/retry-processing"),
    ("PATCH", "/api/admin/media/duplicate-candidates/{candidate_id}"),
    ("POST", "/api/admin/media/assets"),
    ("POST", "/api/admin/media/assets/{asset_id}/replace"),
    ("POST", "/api/admin/media/bindings"),
    ("POST", "/api/admin/media/bindings/{binding_id}/publish"),
    ("POST", "/api/admin/media/bindings/{binding_id}/unpublish"),
    ("DELETE", "/api/admin/media/bindings/{binding_id}"),
    ("POST", "/api/admin/student-preview/session"),
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
def test_admin_routes_are_registered_once(method: str, path: str) -> None:
    assert len(_routes_for(path, method)) == 1


def test_media_binding_canonical_routes_are_registered_and_aliases_removed() -> None:
    _routes_for_binding = {
        (method, path): len(_routes_for(path, method))
        for method, path in ADMIN_ROUTE_CONTRACTS
        if "/api/admin/media/bindings/{binding_id}" in path
    }

    assert _routes_for_binding == {
        ("POST", "/api/admin/media/bindings/{binding_id}/publish"): 1,
        ("POST", "/api/admin/media/bindings/{binding_id}/unpublish"): 1,
        ("DELETE", "/api/admin/media/bindings/{binding_id}"): 1,
    }

    assert _routes_for("/api/admin/media/bindings/{binding_id}/delete", "POST") == []
    assert _routes_for("/api/admin/media/bindings/{binding_id}/archive", "POST") == []


def test_legacy_admin_router_files_are_removed() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    assert not (repo_root / "server" / "app" / "admin.py").exists()
    assert not (repo_root / "server" / "app" / "experiment_admin.py").exists()

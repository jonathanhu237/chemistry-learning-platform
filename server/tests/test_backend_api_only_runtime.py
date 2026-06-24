from __future__ import annotations

from server.app.app_runtime.main import app


def _route_pairs() -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    stack = list(app.routes)
    while stack:
        route = stack.pop(0)
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            stack[0:0] = list(getattr(original_router, "routes", []) or [])
            continue
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", None)
        if not methods:
            pairs.add(("MOUNT", path))
            continue
        for method in methods:
            if method not in {"HEAD", "OPTIONS"}:
                pairs.add((method, path))
    return pairs


def test_backend_runtime_does_not_serve_frontend_spa_fallbacks() -> None:
    routes = _route_pairs()

    assert ("GET", "/") not in routes
    assert ("GET", "/{full_path:path}") not in routes
    assert ("GET", "/admin") not in routes
    assert ("GET", "/admin/{full_path:path}") not in routes


def test_backend_runtime_does_not_mount_frontend_assets() -> None:
    routes = _route_pairs()

    assert ("MOUNT", "/assets") not in routes
    assert ("MOUNT", "/admin/assets") not in routes
    assert ("GET", "/admin/sysu-logo.svg") not in routes
    assert ("GET", "/favicon.ico") not in routes


def test_backend_runtime_keeps_health_and_api_routes() -> None:
    routes = _route_pairs()

    assert ("GET", "/health") in routes
    assert ("POST", "/api/auth/login") in routes
    assert ("GET", "/api/admin/classes") in routes
    assert ("GET", "/api/student/app-config") in routes
    assert ("GET", "/api/student/assessment-reports") in routes
    assert ("GET", "/api/student/assessment-reports/{report_id}") in routes

from __future__ import annotations

from server.app.admin_main import app


def _routes_for(path: str) -> list[object]:
    return [route for route in app.routes if getattr(route, "path", "") == path]


def test_learning_resource_overview_route_is_registered_once() -> None:
    routes = _routes_for("/api/admin/learning-resources/overview")

    assert len(routes) == 1
    assert "GET" in getattr(routes[0], "methods", set())


def test_experiment_knowledge_framework_overview_route_is_registered_once() -> None:
    routes = _routes_for("/api/admin/experiment-knowledge-framework/overview")

    assert len(routes) == 1
    assert "GET" in getattr(routes[0], "methods", set())

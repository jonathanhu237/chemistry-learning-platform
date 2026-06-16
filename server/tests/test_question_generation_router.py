from __future__ import annotations

from server.app.admin_main import app


def test_question_generation_route_is_registered_once() -> None:
    routes = [
        route
        for route in app.routes
        if getattr(route, "path", "") == "/api/admin/question-banks/generate"
        and "POST" in getattr(route, "methods", set())
    ]

    assert len(routes) == 1

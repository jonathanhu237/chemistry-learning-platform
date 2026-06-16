from __future__ import annotations

from server.app.admin_main import app
from server.app.services.student_experiment_service import _normalize_answer


def test_student_experiment_submit_route_is_registered_once() -> None:
    routes = [
        route
        for route in app.routes
        if getattr(route, "path", "") == "/api/experiment-questions/submit"
    ]

    assert len(routes) == 1
    assert "POST" in getattr(routes[0], "methods", set())


def test_student_true_false_answer_normalization_preserves_cn_aliases() -> None:
    assert _normalize_answer("true_false", "对") == {"value": True}
    assert _normalize_answer("true_false", "正确") == {"value": True}
    assert _normalize_answer("true_false", "错") == {"value": False}
    assert _normalize_answer("true_false", "错误") == {"value": False}

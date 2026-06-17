from __future__ import annotations

from server.tests.route_helpers import assert_route


def test_learning_resource_overview_route_is_registered_once() -> None:
    assert_route("/api/admin/learning-resources/overview", "GET")


def test_experiment_knowledge_framework_overview_route_is_registered_once() -> None:
    assert_route("/api/admin/experiment-knowledge-framework/overview", "GET")

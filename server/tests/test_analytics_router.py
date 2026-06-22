from __future__ import annotations

from server.app.domains.analytics.read_models import _attempt_primary_points
from server.tests.route_helpers import assert_route


def test_class_dashboard_route_is_registered_once() -> None:
    assert_route("/api/admin/analytics/classes/{class_id}/dashboard", "GET")


def test_student_report_route_is_registered_once() -> None:
    assert_route("/api/admin/analytics/classes/{class_id}/students/{student_id}", "GET")


def test_class_weak_points_route_is_registered_once() -> None:
    assert_route("/api/admin/analytics/classes/{class_id}/weak-points", "GET")


def test_class_export_route_is_registered_once() -> None:
    assert_route("/api/admin/analytics/classes/{class_id}/export", "GET")


def test_attempt_primary_points_prefers_stable_node_identity() -> None:
    points = _attempt_primary_points(
        {
            "point_node_id": "cat-point-fallback",
            "metadata": {
                "primary_points": [{"point_key": "legacy-point", "point_title": "Legacy title"}],
                "primary_point_node_ids": ["cat-point-1"],
            },
            "question_metadata": {"primary_point_keys": ["legacy-point"]},
        }
    )

    assert points == [
        {
            "point_key": "legacy-point",
            "point_title": "Legacy title",
            "point_node_id": "cat-point-1",
        }
    ]


def test_attempt_primary_points_falls_back_to_attempt_point_node_id() -> None:
    points = _attempt_primary_points({"point_node_id": "cat-point-fallback", "metadata": {}, "question_metadata": {}})

    assert points == [
        {
            "point_node_id": "cat-point-fallback",
            "point_title": "cat-point-fallback",
            "point_key": "",
        }
    ]

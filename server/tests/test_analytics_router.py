from __future__ import annotations

from server.tests.route_helpers import assert_route


def test_class_dashboard_route_is_registered_once() -> None:
    assert_route("/api/admin/analytics/classes/{class_id}/dashboard", "GET")


def test_student_report_route_is_registered_once() -> None:
    assert_route("/api/admin/analytics/classes/{class_id}/students/{student_id}", "GET")


def test_class_weak_points_route_is_registered_once() -> None:
    assert_route("/api/admin/analytics/classes/{class_id}/weak-points", "GET")


def test_class_export_route_is_registered_once() -> None:
    assert_route("/api/admin/analytics/classes/{class_id}/export", "GET")

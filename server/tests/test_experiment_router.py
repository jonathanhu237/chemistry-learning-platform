from __future__ import annotations

from server.tests.route_helpers import assert_route


def test_experiment_catalog_routes_are_registered_once() -> None:
    assert_route("/api/admin/experiments", "GET")
    assert_route("/api/admin/experiments", "POST")
    assert_route("/api/admin/experiments/{experiment_id}", "GET")
    assert_route("/api/admin/experiments/{experiment_id}", "PATCH")
    assert_route("/api/admin/experiments/{experiment_id}/chapter-bindings", "PUT")


def test_experiment_video_routes_are_registered_once() -> None:
    assert_route("/api/admin/experiments/{experiment_id}/videos/upload", "POST")
    assert_route("/api/admin/experiments/{experiment_id}/videos/bind", "POST")
    assert_route("/api/admin/experiments/{experiment_id}/video-points", "GET")
    assert_route("/api/admin/experiments/{experiment_id}/video-points/{point_key}/resources", "POST")
    assert_route("/api/admin/experiment-videos", "GET")

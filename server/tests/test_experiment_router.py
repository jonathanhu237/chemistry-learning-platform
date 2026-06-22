from __future__ import annotations

from server.app.app_runtime.main import app
from server.tests.route_helpers import assert_route


def test_experiment_catalog_routes_are_registered_once() -> None:
    assert_route("/api/admin/experiments", "GET")
    assert_route("/api/admin/experiments/{experiment_id}", "GET")


def test_catalog_tree_routes_are_registered_once() -> None:
    assert_route("/api/admin/catalog/chapters/{chapter_id}/roots", "GET")
    assert_route("/api/admin/catalog/nodes", "POST")
    assert_route("/api/admin/catalog/nodes/{node_id}", "GET")
    assert_route("/api/admin/catalog/nodes/{node_id}", "PATCH")
    assert_route("/api/admin/catalog/nodes/{node_id}/children", "GET")
    assert_route("/api/admin/catalog/nodes/{node_id}/copy", "POST")
    assert_route("/api/admin/catalog/nodes/{node_id}/move", "POST")
    assert_route("/api/admin/catalog/nodes/reorder", "POST")
    assert_route("/api/admin/catalog/nodes/{node_id}/status", "POST")
    assert_route("/api/admin/catalog/nodes/{node_id}/point-content", "PUT")
    assert_route("/api/admin/catalog/nodes/{node_id}/point-content/publication", "POST")
    assert_route("/api/admin/catalog/nodes/{node_id}/media-bindings", "POST")
    assert "/api/admin/catalog/nodes/{node_id}/media/upload" not in app.openapi()["paths"]
    assert_route("/api/admin/catalog/media-bindings/{binding_id}/{action}", "POST")
    assert_route("/api/admin/catalog/nodes/{node_id}/related-links", "PUT")
    assert_route("/api/admin/catalog/nodes/{node_id}/validation", "GET")
    assert_route("/api/admin/catalog/nodes/{node_id}/job-state", "GET")
    assert_route("/api/admin/catalog/nodes/{node_id}/jobs/{action}", "POST")
    assert_route("/api/admin/catalog/search", "GET")


def test_experiment_video_read_routes_are_registered_once() -> None:
    assert_route("/api/admin/experiment-videos", "GET")
    assert_route("/api/admin/video-library/index/diagnostics", "GET")

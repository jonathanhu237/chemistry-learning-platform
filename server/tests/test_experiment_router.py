from __future__ import annotations

from pathlib import Path

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
    assert_route("/api/admin/catalog/nodes/{node_id}/home-recommendation", "PUT")
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
    assert_route("/api/admin/catalog/search/index/diagnostics", "GET")
    assert_route("/api/admin/catalog/search/query/diagnostics", "GET")


def test_experiment_video_read_routes_are_registered_once() -> None:
    assert_route("/api/admin/experiment-videos", "GET")


def test_catalog_admin_uses_teacher_search_job_and_diagnostic_contracts() -> None:
    api_source = Path("server/app/api/admin/admin_catalog_tree.py").read_text(encoding="utf-8")
    nodes_source = Path("server/app/domains/catalog_tree/nodes.py").read_text(encoding="utf-8")

    assert "teacher-search-refresh" in api_source
    assert "teacher-search-delete" in api_source
    assert "es-refresh" not in api_source
    assert "es-delete" not in api_source
    assert "teacher_catalog_search_index_diagnostics" in api_source
    assert "search_teacher_catalog_nodes" in api_source
    assert "teacher_search_document" in nodes_source
    assert "teacher_search_state" in nodes_source
    assert "queue_subtree_point_indexes" not in nodes_source
    assert "queue_index_state" not in nodes_source

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from server.app.catalog_tree_schemas import CatalogNodeCreateRequest, CatalogNodeUpdateRequest
from server.app.domains.catalog_tree.tree import _content_publication_errors, _queue_index_state, validate_node_payload


class _Result:
    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self.row = row

    def mappings(self) -> "_Result":
        return self

    def first(self) -> dict[str, Any] | None:
        return self.row

    def scalars(self) -> "_Result":
        return self


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def execute(self, statement: Any, params: dict[str, Any] | None = None) -> _Result:
        sql = str(statement)
        self.calls.append(params or {})
        if "SELECT canonical_point_id FROM experiment_catalog_nodes" in sql:
            return _Result({"canonical_point_id": "cat-canon-1"})
        if "SELECT id AS placement_node_id, canonical_point_id" in sql:
            return _Result({"placement_node_id": (params or {}).get("node_id"), "canonical_point_id": "cat-canon-1"})
        return _Result()


def test_catalog_point_validation_requires_title_but_not_saved_content() -> None:
    invalid = validate_node_payload(
        {
            "node_id": "cat-point-1",
            "node_kind": "point",
            "canonical_point_id": "cat-canon-1",
            "title": "",
            "has_children": False,
        }
    )

    assert invalid["ok"] is False
    assert "Title is required" in invalid["errors"]
    assert invalid["warnings"] == []


def test_catalog_directory_validation_rejects_point_resources() -> None:
    invalid = validate_node_payload(
        {
            "node_id": "cat-dir-1",
            "node_kind": "directory",
            "title": "Directory",
            "has_children": True,
            "has_point_content": True,
            "media_count": 1,
        }
    )

    assert invalid["ok"] is False
    assert "Directory nodes cannot own point content or videos" in invalid["errors"]


def test_catalog_point_validation_rejects_children() -> None:
    invalid = validate_node_payload(
        {
            "node_id": "cat-point-1",
            "node_kind": "point",
            "canonical_point_id": "cat-canon-1",
            "title": "Point",
            "has_children": True,
        }
    )

    assert invalid["ok"] is False
    assert "Point nodes cannot have children" in invalid["errors"]


def test_catalog_point_validation_requires_canonical_target() -> None:
    invalid = validate_node_payload(
        {
            "node_id": "cat-point-1",
            "node_kind": "point",
            "title": "Point",
            "has_children": False,
        }
    )

    assert invalid["ok"] is False
    assert "Point placement must target a canonical experiment point" in invalid["errors"]


def test_catalog_node_schema_rejects_retired_hybrid_and_shortcut_kinds() -> None:
    with pytest.raises(ValidationError):
        CatalogNodeCreateRequest(chapter_id="CH1", title="Hybrid", node_kind="hybrid")

    with pytest.raises(ValidationError):
        CatalogNodeUpdateRequest(node_kind="shortcut")


def test_catalog_point_publication_requires_exact_primary_principle_and_safety() -> None:
    errors = _content_publication_errors(
        {"node_id": "cat-point-1", "canonical_point_id": "cat-canon-1", "node_kind": "point", "title": "Orange layer"},
        {
            "principle_mode": "equation",
            "principle_equation": "",
            "principle_text": "secondary text should not be primary",
            "phenomenon_explanation": "",
            "safety_note": "",
            "content_status": "draft",
        },
    )

    assert "Equation-mode principle requires at least one valid reaction equation" in errors
    assert "Phenomenon explanation is required" in errors
    assert "Safety note is required" in errors


def test_catalog_point_publication_accepts_complete_text_mode() -> None:
    errors = _content_publication_errors(
        {"node_id": "cat-point-1", "canonical_point_id": "cat-canon-1", "node_kind": "point", "title": "Halogen displacement"},
        {
            "principle_mode": "text",
            "principle_text": "Chlorine oxidizes bromide ions under acidic conditions.",
            "phenomenon_explanation": "Bromine forms and dissolves in the organic layer.",
            "safety_note": "Handle chlorine water in a ventilated space.",
            "content_status": "published",
        },
    )

    assert errors == []


def test_catalog_point_index_queue_uses_stable_node_id() -> None:
    session = _FakeSession()

    _queue_index_state(session, node_id="cat-point-1", action="upsert")

    index_call = next(call for call in session.calls if call.get("desired_action") == "upsert")
    assert index_call == {
        "node_id": "cat-point-1",
        "canonical_point_id": "cat-canon-1",
        "desired_action": "upsert",
        "last_error": None,
    }
    job_call = next(call for call in session.calls if call.get("job_type") == "es_upsert")
    assert job_call["node_id"] == "cat-point-1"
    assert job_call["placement_node_id"] == "cat-point-1"
    assert job_call["canonical_point_id"] == "cat-canon-1"
    assert job_call["trigger_source"] == "automatic"

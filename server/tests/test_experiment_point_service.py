from __future__ import annotations

from typing import Any

from server.app.domains.catalog_tree.tree import _content_publication_errors, _queue_index_state, validate_node_payload


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def execute(self, _statement: Any, params: dict[str, Any] | None = None) -> None:
        self.calls.append(params or {})


def test_catalog_point_validation_requires_title_and_saved_content() -> None:
    invalid = validate_node_payload(
        {
            "node_id": "cat-point-1",
            "node_kind": "point",
            "title": "",
            "has_children": False,
        }
    )

    assert invalid["ok"] is False
    assert "Title is required" in invalid["errors"]
    assert "Point content has not been saved" in invalid["warnings"]


def test_catalog_point_publication_requires_exact_primary_principle_and_safety() -> None:
    errors = _content_publication_errors(
        {"node_id": "cat-point-1", "node_kind": "point", "title": "Orange layer"},
        {
            "principle_mode": "equation",
            "principle_equation": "",
            "principle_text": "secondary text should not be primary",
            "phenomenon_explanation": "",
            "safety_note": "",
            "content_status": "draft",
        },
    )

    assert "Equation-mode principle requires a chemical equation" in errors
    assert "Phenomenon explanation is required" in errors
    assert "Safety note is required" in errors


def test_catalog_point_publication_accepts_complete_text_mode() -> None:
    errors = _content_publication_errors(
        {"node_id": "cat-point-1", "node_kind": "point", "title": "Halogen displacement"},
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

    assert session.calls == [
        {
            "node_id": "cat-point-1",
            "desired_action": "upsert",
            "last_error": None,
        }
    ]

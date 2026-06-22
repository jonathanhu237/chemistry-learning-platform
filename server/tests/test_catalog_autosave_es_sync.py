from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from server.app.catalog_tree_schemas import CatalogPointContentRequest
from server.app.domains.catalog_tree import points


class _Result:
    def __init__(self, row: dict[str, Any] | None = None, rowcount: int = 1) -> None:
        self.row = row
        self.rowcount = rowcount

    def mappings(self) -> "_Result":
        return self

    def first(self) -> dict[str, Any] | None:
        return self.row


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def execute(self, statement: Any, params: dict[str, Any] | None = None) -> _Result:
        self.calls.append({"sql": str(statement), "params": params or {}})
        return _Result(rowcount=1)


@contextmanager
def _fake_db_session(session: _FakeSession):
    yield session


def _payload(**overrides: Any) -> CatalogPointContentRequest:
    data = {
        "point_title": "氯水 + KI",
        "teacher_note": "",
        "principle_mode": "text",
        "principle_text": "氯气氧化碘离子生成碘。",
        "phenomenon_explanation": "淀粉试纸变蓝。",
        "safety_note": "通风橱内操作。",
    }
    data.update(overrides)
    return CatalogPointContentRequest(**data)


def _published_content(**overrides: Any) -> dict[str, Any]:
    data = {
        "point_title": "氯水 + KI",
        "teacher_note": "",
        "principle_mode": "text",
        "principle_equation": "",
        "principle_text": "氯气氧化碘离子生成碘。",
        "reaction_equations": [],
        "phenomenon_explanation": "淀粉试纸变蓝。",
        "safety_note": "通风橱内操作。",
        "content_status": "published",
    }
    data.update(overrides)
    return data


def _patch_save_dependencies(monkeypatch: Any, session: _FakeSession, existing_content: dict[str, Any] | None) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    monkeypatch.setattr(points, "db_session", lambda: _fake_db_session(session))
    monkeypatch.setattr(
        points,
        "get_node",
        lambda _session, _node_id: {
            "node_id": "cat-point-1",
            "node_kind": "point",
            "canonical_point_id": "cat-canon-1",
            "title": "氯水 + KI",
            "has_children": False,
            "status": "published",
        },
    )
    monkeypatch.setattr(points, "point_capable", lambda _node: True)
    monkeypatch.setattr(points, "canonical_point_id_for_node", lambda _session, _node_id: "cat-canon-1")
    monkeypatch.setattr(points, "get_content", lambda _session, _node_id: existing_content)
    monkeypatch.setattr(points, "active_placement_ids_for_canonical_point", lambda _session, _canonical_id: ["cat-point-1", "cat-point-2"])
    monkeypatch.setattr(points, "replace_reaction_equations", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(points, "queue_index_state", lambda _session, **kwargs: events.append({"kind": "index", **kwargs}))
    monkeypatch.setattr(points, "mark_point_evidence_stale", lambda _session, **kwargs: events.append({"kind": "rag", **kwargs}))

    import server.app.domains.catalog_tree.nodes as nodes

    monkeypatch.setattr(nodes, "get_node_detail", lambda node_id: {"node": {"node_id": node_id}})
    return events


def test_published_point_autosave_preserves_published_status_and_schedules_soft_upsert(monkeypatch: Any) -> None:
    session = _FakeSession()
    events = _patch_save_dependencies(monkeypatch, session, _published_content())

    points.save_point_content(
        node_id="cat-point-1",
        payload=_payload(phenomenon_explanation="湿润淀粉试纸变蓝。"),
        user=type("User", (), {"id": "00000000-0000-0000-0000-000000000001"})(),
    )

    content_update = next(call for call in session.calls if "UPDATE experiment_catalog_point_content" in call["sql"])
    assert "WHEN experiment_catalog_point_content.content_status = 'published' THEN 'published'" in content_update["sql"]
    assert {"kind": "index", "node_id": "cat-point-1", "action": "upsert", "soft": True} in events
    assert {"kind": "index", "node_id": "cat-point-2", "action": "upsert", "soft": True} in events
    assert {"kind": "rag", "node_id": "cat-point-1", "reason": "point_content_edited"} in events


def test_draft_point_autosave_does_not_create_student_search_upsert(monkeypatch: Any) -> None:
    session = _FakeSession()
    events = _patch_save_dependencies(monkeypatch, session, _published_content(content_status="draft"))

    points.save_point_content(
        node_id="cat-point-1",
        payload=_payload(phenomenon_explanation="湿润淀粉试纸变蓝。"),
        user=type("User", (), {"id": "00000000-0000-0000-0000-000000000001"})(),
    )

    assert not [event for event in events if event["kind"] == "index"]
    assert {"kind": "rag", "node_id": "cat-point-1", "reason": "point_content_edited"} in events


def test_teacher_note_only_autosave_does_not_trigger_es_or_rag(monkeypatch: Any) -> None:
    session = _FakeSession()
    events = _patch_save_dependencies(monkeypatch, session, _published_content())

    points.save_point_content(
        node_id="cat-point-1",
        payload=_payload(teacher_note="课堂演示时提醒学生观察颜色。"),
        user=type("User", (), {"id": "00000000-0000-0000-0000-000000000001"})(),
    )

    assert events == []

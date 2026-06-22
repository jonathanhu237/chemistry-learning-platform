from __future__ import annotations

from typing import Any

from server.app.domains.catalog_tree import media_asset_events


class _Result:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows = rows or []

    def mappings(self) -> "_Result":
        return self

    def all(self) -> list[dict[str, Any]]:
        return self.rows


class _FakeSession:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.calls: list[dict[str, Any]] = []

    def execute(self, statement: Any, params: dict[str, Any] | None = None) -> _Result:
        self.calls.append({"sql": str(statement), "params": params or {}})
        if "UPDATE experiment_catalog_point_media_bindings" in str(statement):
            return _Result(self.rows)
        return _Result()


def test_handle_media_asset_archived_archives_bindings_and_queues_point_refresh(monkeypatch) -> None:
    session = _FakeSession(
        [
            {
                "binding_id": "binding-1",
                "node_id": "source-point",
                "canonical_point_id": "canonical-point",
                "source_placement_node_id": "source-point",
            }
        ]
    )
    queued: list[dict[str, Any]] = []
    monkeypatch.setattr(
        media_asset_events,
        "active_placement_ids_for_canonical_point",
        lambda _session, _canonical_point_id: ["placement-a", "placement-b"],
    )
    monkeypatch.setattr(
        media_asset_events,
        "queue_index_state",
        lambda _session, **kwargs: queued.append({"kind": "index", **kwargs}),
    )
    monkeypatch.setattr(
        media_asset_events,
        "mark_point_evidence_stale",
        lambda _session, **kwargs: queued.append({"kind": "rag", **kwargs}),
    )

    result = media_asset_events.handle_media_asset_archived(
        session,
        media_asset_id="asset-1",
        lifecycle_event_id="event-1",
        actor_user_id="teacher-1",
        reason="teacher_archive",
    )

    update_call = session.calls[0]
    assert "binding_status = 'archived'" in update_call["sql"]
    assert "'archived_reason', 'media_asset_archived'" in update_call["sql"]
    assert "'archived_media_asset_id', CAST(:media_asset_id AS text)" in update_call["sql"]
    assert "'media_asset_lifecycle_event_id', CAST(:lifecycle_event_id AS text)" in update_call["sql"]
    assert "'previous_binding_status', binding_status" in update_call["sql"]
    assert update_call["params"]["media_asset_id"] == "asset-1"
    assert update_call["params"]["lifecycle_event_id"] == "event-1"
    assert result["archived_binding_count"] == 1
    assert result["affected_placement_node_ids"] == ["placement-a", "placement-b"]
    assert queued == [
        {"kind": "index", "node_id": "placement-a", "action": "upsert", "trigger_source": "system"},
        {"kind": "rag", "node_id": "placement-a", "reason": "media_asset_archived", "trigger_source": "system"},
        {"kind": "index", "node_id": "placement-b", "action": "upsert", "trigger_source": "system"},
        {"kind": "rag", "node_id": "placement-b", "reason": "media_asset_archived", "trigger_source": "system"},
    ]


def test_handle_media_asset_archived_is_idempotent_when_bindings_already_archived(monkeypatch) -> None:
    session = _FakeSession([])
    queued: list[dict[str, Any]] = []
    monkeypatch.setattr(media_asset_events, "queue_index_state", lambda _session, **kwargs: queued.append(kwargs))
    monkeypatch.setattr(media_asset_events, "mark_point_evidence_stale", lambda _session, **kwargs: queued.append(kwargs))

    result = media_asset_events.handle_media_asset_archived(
        session,
        media_asset_id="asset-1",
        lifecycle_event_id="event-1",
        actor_user_id="teacher-1",
        reason="teacher_archive",
    )

    assert result["archived_binding_count"] == 0
    assert result["affected_placement_count"] == 0
    assert queued == []

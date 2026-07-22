from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any

import pytest

from server.app.catalog_tree_schemas import CatalogNodeStatusRequest
from server.app.domains.catalog_tree import nodes


class _Mappings:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class _Result:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []

    def mappings(self) -> _Mappings:
        return _Mappings(self._rows)


class _Session:
    def __init__(self) -> None:
        self.updates: list[dict[str, Any]] = []

    def execute(self, statement: Any, params: dict[str, Any]) -> _Result:
        sql = str(statement)
        if "WITH selected_points AS" in sql:
            return _Result(
                [
                    {
                        "canonical_point_id": "canonical-1",
                        "sample_placement_node_id": "point-1",
                        "selected_count": 1,
                        "active_count": 1,
                    }
                ]
            )
        if "UPDATE experiment_catalog_nodes" in sql:
            self.updates.append(params)
        return _Result()


def _install_status_dependencies(monkeypatch: pytest.MonkeyPatch, session: _Session) -> None:
    @contextmanager
    def fake_db_session():
        yield session

    monkeypatch.setattr(nodes, "db_session", fake_db_session)
    monkeypatch.setattr(
        nodes,
        "get_node",
        lambda _session, _node_id: {
            "node_id": "point-1",
            "node_kind": "point",
            "status": "published",
        },
    )
    monkeypatch.setattr(nodes, "queue_subtree_teacher_indexes", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(nodes, "mark_subtree_evidence_stale", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(nodes, "get_node_detail", lambda *, node_id: {"node": {"node_id": node_id, "status": "archived"}})


def test_archiving_final_placement_without_explicit_decision_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _Session()
    _install_status_dependencies(monkeypatch, session)

    with pytest.raises(Exception) as caught:
        nodes.set_node_status(
            node_id="point-1",
            payload=CatalogNodeStatusRequest(action="archive"),
            user=SimpleNamespace(id="00000000-0000-0000-0000-000000000001"),
        )

    assert caught.value.status_code == 409
    assert caught.value.detail["message"] == "Archiving the final placement requires an explicit canonical archive decision"
    assert session.updates == []


def test_archiving_final_placement_succeeds_after_explicit_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _Session()
    _install_status_dependencies(monkeypatch, session)

    result = nodes.set_node_status(
        node_id="point-1",
        payload=CatalogNodeStatusRequest(action="archive", archive_final_placement=True),
        user=SimpleNamespace(id="00000000-0000-0000-0000-000000000001"),
    )

    assert result["node"]["status"] == "archived"
    assert session.updates == [
        {
            "status": "archived",
            "node_ids": ["point-1"],
            "user_id": "00000000-0000-0000-0000-000000000001",
        }
    ]

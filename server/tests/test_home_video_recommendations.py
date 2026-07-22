from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from server.app.catalog_tree_schemas import CatalogHomeRecommendationRequest
from server.app.domains.catalog_tree import home_recommendations


MIGRATION = Path("server/migrations/047_home_video_recommendations_and_favorite_saves.sql")


class _Mappings:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def first(self) -> dict[str, Any] | None:
        return self.rows[0] if self.rows else None


class _Result:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows = rows or []

    def mappings(self) -> _Mappings:
        return _Mappings(self.rows)


class _FakeSession:
    def __init__(self, *, placement_exists: bool = True) -> None:
        self.placement_exists = placement_exists
        self.recommended = False
        self.executed: list[dict[str, Any]] = []

    def execute(self, statement: Any, params: dict[str, Any]) -> _Result:
        sql = str(statement)
        self.executed.append({"statement": sql, "params": params})
        if "SELECT placement.id" in sql:
            return _Result([{"id": params["node_id"]}] if self.placement_exists else [])
        if "INSERT INTO student_home_video_recommendations" in sql:
            self.recommended = True
            return _Result()
        if "DELETE FROM student_home_video_recommendations" in sql:
            self.recommended = False
            return _Result()
        if "FROM student_home_video_recommendations" in sql:
            if not self.recommended:
                return _Result()
            return _Result(
                [
                    {
                        "placement_node_id": params["node_id"],
                        "sort_order": 3,
                        "recommended_by": "00000000-0000-0000-0000-000000000456",
                        "updated_at": "2026-07-22T10:00:00+08:00",
                    }
                ]
            )
        return _Result()


def test_migration_copies_valid_legacy_rows_and_narrows_saves_to_favorites() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS student_home_video_recommendations" in sql
    assert "placement_node_id text PRIMARY KEY" in sql
    assert "CHECK (sort_order >= 0)" in sql
    assert "to_regclass('public.legacy_recommended_video_points')" in sql
    assert "placement.node_kind = 'point'" in sql
    assert "actor.id::text = NULLIF(btrim(legacy.recommended_by), '')" in sql
    assert "DROP TABLE IF EXISTS legacy_recommended_video_points" in sql
    assert "DELETE FROM student_video_saves" in sql
    assert "WHERE save_type = 'watch_later'" in sql
    assert "CHECK (save_type = 'favorite')" in sql


def test_recommendation_request_rejects_negative_order() -> None:
    with pytest.raises(ValidationError):
        CatalogHomeRecommendationRequest(recommended=True, sort_order=-1)


def test_set_home_video_recommendation_validates_point_and_uses_canonical_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession()

    @contextmanager
    def fake_db_session():
        yield session

    monkeypatch.setattr(home_recommendations, "db_session", fake_db_session)

    result = home_recommendations.set_home_video_recommendation(
        node_id="cat-point-1",
        recommended=True,
        sort_order=3,
        user_id="00000000-0000-0000-0000-000000000456",
    )

    assert result == {
        "node_id": "cat-point-1",
        "home_recommendation": {
            "recommended": True,
            "sort_order": 3,
            "recommended_by": "00000000-0000-0000-0000-000000000456",
            "updated_at": "2026-07-22T10:00:00+08:00",
        },
    }
    insert = next(call for call in session.executed if "INSERT INTO student_home_video_recommendations" in call["statement"])
    assert "SELECT id FROM app_users WHERE id::text = :user_id" in insert["statement"]
    assert insert["params"]["sort_order"] == 3


def test_set_home_video_recommendation_rejects_non_point_placement(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession(placement_exists=False)

    @contextmanager
    def fake_db_session():
        yield session

    monkeypatch.setattr(home_recommendations, "db_session", fake_db_session)

    with pytest.raises(Exception) as error:
        home_recommendations.set_home_video_recommendation(
            node_id="cat-directory-1",
            recommended=True,
            sort_order=0,
            user_id=None,
        )

    assert error.value.status_code == 404


def test_home_recommendation_runtime_has_no_schema_ddl() -> None:
    source = Path("server/app/domains/catalog_tree/home_recommendations.py").read_text(encoding="utf-8")

    assert "student_home_video_recommendations" in source
    assert "CREATE TABLE" not in source
    assert "legacy_recommended_video_points" not in source

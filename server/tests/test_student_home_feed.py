from __future__ import annotations

from typing import Any
from pathlib import Path

import pytest

from server.app.domains import student_home_feed as home_feed_service
from server.app.student_video_save_schemas import StudentVideoPersonalState
from server.tests.route_helpers import assert_route


class _SessionContext:
    def __enter__(self) -> object:
        return object()

    def __exit__(self, *_args: object) -> None:
        return None


def test_student_home_video_feed_route_is_registered() -> None:
    assert_route("/api/student/home-video-feed", "GET")


def test_home_feed_sql_only_uses_existing_reaction_equation_columns() -> None:
    source = Path("server/app/domains/student_home_feed.py").read_text(encoding="utf-8")
    assert "eq.condition_tags" not in source


def test_home_feed_sql_excludes_placeholder_videos() -> None:
    source = Path("server/app/domains/student_home_feed.py").read_text(encoding="utf-8")
    assert "placeholder_video" in source
    assert "no-video-placeholder.mp4" in source


def test_student_home_video_feed_maps_rows_to_video_cards(monkeypatch: pytest.MonkeyPatch) -> None:
    rows: list[dict[str, Any]] = [
        {
            "node_id": "cat-point-halogen",
            "placement_node_id": "cat-point-halogen",
            "canonical_point_id": "cat-canon-halogen",
            "chapter_id": "CH17",
            "chapter_title": "第 13 章 卤族元素",
            "point_title": "卤素置换观察",
            "point_summary": "氯水与溴离子的置换反应。",
            "snippet": "氯水能够氧化溴离子。",
            "catalog_path": ["卤素置换目录", "卤素置换观察"],
            "media_id": "media-halogen",
            "media_title": "卤素置换视频",
            "mime_type": "video/mp4",
            "duration_seconds": 35,
            "has_thumbnail": True,
        }
    ]
    monkeypatch.setattr(home_feed_service, "db_session", lambda: _SessionContext())
    monkeypatch.setattr(home_feed_service, "_feed_rows", lambda _session: rows)

    response = home_feed_service.student_home_video_feed(object(), topic="all", limit=99)

    assert response.status == "ok"
    assert response.topic == "all"
    assert response.batch_size == 30
    assert response.has_more is False
    assert response.next_cursor is None
    assert len(response.items) == 1
    item = response.items[0]
    assert item.id == "home-video:cat-point-halogen:media-halogen"
    assert item.instance_id.startswith("home-feed:all:")
    assert item.title == "卤素置换观察"
    assert item.catalog_path == ["卤素置换目录", "卤素置换观察"]
    assert item.badges == ["第 13 章 卤族元素", "卤素置换目录", "卤素置换观察"]
    assert item.video.stream_path == "/api/student/media/assets/media-halogen/stream"
    assert item.video.thumbnail_path == "/api/student/media/assets/media-halogen/thumbnail"
    assert item.target.kind == "point_detail"
    assert item.target.node_id == "cat-point-halogen"
    assert item.personal_state.watch_later is False
    assert item.personal_state.favorite is False


def _row(suffix: str, *, snippet: str = "颜色变化") -> dict[str, Any]:
    return {
        "node_id": f"cat-point-{suffix}",
        "placement_node_id": f"cat-point-{suffix}",
        "canonical_point_id": f"cat-canon-{suffix}",
        "chapter_id": "CH17",
        "chapter_title": "第 13 章 卤族元素",
        "point_title": f"实验 {suffix}",
        "point_summary": f"实验 {suffix} 摘要",
        "snippet": snippet,
        "catalog_path": ["实验目录", f"实验 {suffix}"],
        "media_id": f"00000000-0000-0000-0000-0000000000{suffix}",
        "media_title": f"实验 {suffix} 视频",
        "mime_type": "video/mp4",
        "duration_seconds": 35,
        "has_thumbnail": True,
        "reaction_features": [],
        "condition_tags": [],
        "phenomenon_tags": [],
        "property_tags": [],
    }


def test_discover_feed_repeats_small_pool_with_unique_instances(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [_row("01"), _row("02")]
    monkeypatch.setattr(home_feed_service, "db_session", lambda: _SessionContext())
    monkeypatch.setattr(home_feed_service, "_feed_rows", lambda _session: rows)

    first = home_feed_service.student_home_video_feed(object(), topic="discover", limit=5)
    second = home_feed_service.student_home_video_feed(object(), topic="discover", limit=5, cursor=first.next_cursor)

    assert first.repeat_mode == "cycled"
    assert first.has_more is True
    assert first.next_cursor
    assert len(first.items) == 5
    assert len({item.id for item in first.items}) == 2
    assert len({item.instance_id for item in first.items}) == 5
    assert len(second.items) == 5
    assert set(item.id for item in second.items) == set(item.id for item in first.items)
    assert set(item.instance_id for item in second.items).isdisjoint({item.instance_id for item in first.items})


def test_finite_topics_do_not_repeat_and_recover_from_invalid_cursor(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [_row("01", snippet="产生沉淀"), _row("02", snippet="产生沉淀")]
    monkeypatch.setattr(home_feed_service, "db_session", lambda: _SessionContext())
    monkeypatch.setattr(home_feed_service, "_feed_rows", lambda _session: rows)

    first = home_feed_service.student_home_video_feed(object(), topic="precipitation", limit=1, cursor="not-a-cursor")
    second = home_feed_service.student_home_video_feed(object(), topic="precipitation", limit=5, cursor=first.next_cursor)

    assert first.topic == "precipitation"
    assert first.has_more is True
    assert len(first.items) == 1
    assert len(second.items) == 1
    assert second.has_more is False
    assert second.next_cursor is None
    assert first.items[0].id != second.items[0].id


def test_saved_topics_are_student_scoped_finite_streams(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [_row("01"), _row("02")]

    def states(_session: object, _user: object, _items: list[tuple[str, str]]) -> dict[str, StudentVideoPersonalState]:
        return {
            "cat-point-01:00000000-0000-0000-0000-000000000001": StudentVideoPersonalState(
                watch_later=True,
                watch_later_saved_at="2026-06-25T10:00:00",
            ),
            "cat-point-02:00000000-0000-0000-0000-000000000002": StudentVideoPersonalState(
                favorite=True,
                favorite_saved_at="2026-06-25T11:00:00",
            ),
        }

    monkeypatch.setattr(home_feed_service, "db_session", lambda: _SessionContext())
    monkeypatch.setattr(home_feed_service, "_feed_rows", lambda _session: rows)
    monkeypatch.setattr(home_feed_service, "personal_states_for_items", states)

    watch_later = home_feed_service.student_home_video_feed(object(), topic="watch_later", limit=10)
    favorites = home_feed_service.student_saved_video_feed(object(), save_type="favorite", limit=10)

    assert [item.placement_node_id for item in watch_later.items] == ["cat-point-01"]
    assert watch_later.has_more is False
    assert watch_later.items[0].personal_state.watch_later is True
    assert watch_later.items[0].personal_state.favorite is False
    assert [item.placement_node_id for item in favorites.items] == ["cat-point-02"]
    assert favorites.topic == "favorites"
    assert favorites.items[0].personal_state.favorite is True
    assert favorites.items[0].personal_state.watch_later is False

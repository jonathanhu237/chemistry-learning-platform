from __future__ import annotations

from typing import Any

import pytest

from server.app.domains import student_home_feed as home_feed_service
from server.tests.route_helpers import assert_route


class _SessionContext:
    def __enter__(self) -> object:
        return object()

    def __exit__(self, *_args: object) -> None:
        return None


def test_student_home_video_feed_route_is_registered() -> None:
    assert_route("/api/student/home-video-feed", "GET")


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
    monkeypatch.setattr(home_feed_service, "_feed_rows", lambda _session, *, limit: rows)

    response = home_feed_service.student_home_video_feed(object(), limit=99)

    assert response.status == "ok"
    assert len(response.items) == 1
    item = response.items[0]
    assert item.id == "home-video:cat-point-halogen:media-halogen"
    assert item.title == "卤素置换观察"
    assert item.catalog_path == ["卤素置换目录", "卤素置换观察"]
    assert item.badges == ["第 13 章 卤族元素", "卤素置换目录", "卤素置换观察"]
    assert item.video.stream_path == "/api/student/media/assets/media-halogen/stream"
    assert item.video.thumbnail_path == "/api/student/media/assets/media-halogen/thumbnail"
    assert item.target.kind == "point_detail"
    assert item.target.node_id == "cat-point-halogen"

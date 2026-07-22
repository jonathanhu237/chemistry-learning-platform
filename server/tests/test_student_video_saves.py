from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from server.app.domains import student_video_saves as saves_service
from server.app.student_video_save_schemas import StudentVideoPersonalState, StudentVideoSaveRequest
from server.tests.route_helpers import assert_route


@dataclass
class _Student:
    id: str = "00000000-0000-0000-0000-000000000123"


class _SessionContext:
    def __init__(self, session: "_FakeSession") -> None:
        self.session = session

    def __enter__(self) -> "_FakeSession":
        return self.session

    def __exit__(self, *_args: object) -> None:
        return None


class _FakeSession:
    def __init__(self) -> None:
        self.executed: list[dict[str, Any]] = []

    def execute(self, statement: Any, params: dict[str, Any]) -> None:
        self.executed.append({"statement": str(statement), "params": params})


def test_student_video_save_routes_are_favorite_only() -> None:
    assert_route("/api/student/video-saves/favorite", "PUT")
    assert_route("/api/student/video-saves/favorite", "DELETE")
    assert_route("/api/student/video-saves/favorite/feed", "GET")


def test_visible_favorite_target_uses_same_published_playable_policy_as_home() -> None:
    source = Path("server/app/domains/student_video_saves.py").read_text(encoding="utf-8")
    visibility_source = Path("server/app/domains/media/student_catalog_visibility.py").read_text(encoding="utf-8")

    assert "STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES" in source
    assert "FROM student_visible_playable_media visible_media" in source
    assert "content.content_status = 'published'" in visibility_source
    assert "binding.binding_status = 'published'" in visibility_source
    assert "asset.upload_status = 'ready'" in visibility_source
    assert "asset.playback_relative_path" in visibility_source
    assert "placeholder_video" in visibility_source
    assert "no-video-placeholder.mp4" in visibility_source


def test_set_student_video_favorite_uses_upsert_and_archive_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = _FakeSession()
    visible = {
        "placement_node_id": "cat-point-halogen",
        "canonical_point_id": "cat-canon-halogen",
        "media_asset_id": "00000000-0000-0000-0000-000000000001",
    }

    def personal_state(_session: Any, _user: Any, *, placement_node_id: str, media_id: str) -> StudentVideoPersonalState:
        statement = fake_session.executed[-1]["statement"]
        return StudentVideoPersonalState(favorite="INSERT INTO student_video_saves" in statement)

    monkeypatch.setattr(saves_service, "db_session", lambda: _SessionContext(fake_session))
    monkeypatch.setattr(saves_service, "_visible_point_media", lambda *_args, **_kwargs: visible)
    monkeypatch.setattr(saves_service, "personal_state_for_item", personal_state)

    payload = StudentVideoSaveRequest(
        placement_node_id="cat-point-halogen",
        canonical_point_id="spoofed-canonical-point",
        media_id="00000000-0000-0000-0000-000000000001",
        source="unit_test",
    )

    saved = saves_service.set_student_video_favorite(_Student(), payload=payload, active=True)
    removed = saves_service.set_student_video_favorite(_Student(), payload=payload, active=False)

    assert saved.save_type == "favorite"
    assert saved.active is True
    assert saved.canonical_point_id == "cat-canon-halogen"
    assert saved.personal_state.favorite is True
    assert removed.save_type == "favorite"
    assert removed.active is False
    assert removed.personal_state.favorite is False
    assert "INSERT INTO student_video_saves" in fake_session.executed[0]["statement"]
    assert "save_type" in fake_session.executed[0]["statement"]
    assert "'favorite'" in fake_session.executed[0]["statement"]
    assert "UPDATE student_video_saves" in fake_session.executed[1]["statement"]
    assert "watch_later" not in Path("server/app/domains/student_video_saves.py").read_text(encoding="utf-8")

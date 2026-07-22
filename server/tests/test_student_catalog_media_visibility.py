from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from server.app.domains import student_home_feed as home_feed_service
from server.app.domains.catalog_tree import files as catalog_files
from server.app.domains.media.student_catalog_visibility import STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES
from server.app.student_video_save_schemas import StudentVideoPersonalState


ASSET_ID = "00000000-0000-0000-0000-000000000001"


class _Result:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row

    def mappings(self) -> "_Result":
        return self

    def first(self) -> dict[str, Any] | None:
        return self.row


class _Session:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row
        self.statements: list[str] = []

    def execute(self, statement: Any, _params: dict[str, Any]) -> _Result:
        self.statements.append(str(statement))
        return _Result(self.row)


class _SessionScope:
    def __init__(self, session: _Session) -> None:
        self.session = session

    def __enter__(self) -> _Session:
        return self.session

    def __exit__(self, *_args: object) -> None:
        return None


def _home_row() -> dict[str, Any]:
    return {
        "node_id": "cat-point-published-placement",
        "placement_node_id": "cat-point-published-placement",
        "canonical_point_id": "cat-canon-shared",
        "chapter_id": "CH13",
        "chapter_title": "第 13 章",
        "node_title": "氯气性质",
        "point_title": "氯气性质",
        "catalog_path": ["卤族元素", "氯气性质"],
        "media_id": ASSET_ID,
        "media_title": "氯气性质视频",
        "mime_type": "video/mp4",
        "has_thumbnail": True,
    }


def test_visibility_cte_is_strict_and_allows_any_published_canonical_placement() -> None:
    assert "placement.status = 'published'" in STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES
    assert "canonical_point.status = 'published'" in STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES
    assert "path.status IS DISTINCT FROM 'published'" in STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES
    assert "content.content_status = 'published'" in STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES
    assert "binding.binding_status = 'published'" in STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES
    assert "binding.binding_status <> 'archived'" not in STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES
    assert "binding.canonical_point_id = visible_placement.canonical_point_id" in STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES
    assert "OR binding.node_id = visible_placement.placement_node_id" in STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES


def test_home_stream_url_uses_asset_authorized_by_shared_visibility_contract(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    media_path = tmp_path / "published.mp4"
    media_path.write_bytes(b"published-video")
    item = home_feed_service._feed_item(_home_row(), personal_state=StudentVideoPersonalState())
    assert item is not None
    assert item.video.stream_path == f"/api/student/media/assets/{ASSET_ID}/stream"

    session = _Session(
        {
            "id": ASSET_ID,
            "relative_path": media_path.name,
            "mime_type": "video/mp4",
            "original_file_name": "published.mp4",
        }
    )
    monkeypatch.setattr(catalog_files, "db_session", lambda: _SessionScope(session))
    monkeypatch.setattr(catalog_files, "get_settings", lambda: type("Settings", (), {"media_root": tmp_path})())

    path, mime_type, filename = catalog_files.student_media_asset_file(item.video.media_id)

    assert path == media_path
    assert mime_type == "video/mp4"
    assert filename == "published.mp4"
    assert "WITH RECURSIVE" in session.statements[0]
    assert "student_visible_playable_media" in session.statements[0]


def test_draft_or_archived_binding_cannot_authorize_student_media(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _Session(None)
    monkeypatch.setattr(catalog_files, "db_session", lambda: _SessionScope(session))

    with pytest.raises(Exception) as exc_info:
        catalog_files.student_media_asset_file(ASSET_ID)

    assert exc_info.value.status_code == 404
    assert "binding.binding_status = 'published'" in session.statements[0]
    assert "binding.binding_status <> 'archived'" not in session.statements[0]

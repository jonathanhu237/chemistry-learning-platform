from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from server.app import search_index
from server.app.infrastructure.settings import get_settings


class _Response:
    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        self.payload = payload or {}

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_document_hash_is_deterministic_and_serializes_datetime() -> None:
    timestamp = datetime(2026, 7, 22, 9, 30, tzinfo=timezone.utc)

    assert search_index.document_hash({"b": timestamp, "a": 1}) == search_index.document_hash(
        {"a": 1, "b": timestamp}
    )


def test_search_index_client_serializes_payload_and_builds_index_url(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> _Response:
        captured.update({"url": request.full_url, "method": request.method, "body": request.data, "timeout": timeout})
        return _Response()

    monkeypatch.setattr(search_index.urllib.request, "urlopen", fake_urlopen)
    client = search_index.SearchIndexClient(base_url="http://search:9200/", index="teacher-index", timeout=4.5)

    client.upsert_document({"id": "node-1", "updated_at": datetime(2026, 7, 22, tzinfo=timezone.utc)})

    assert captured["url"] == "http://search:9200/teacher-index/_doc/node-1"
    assert captured["method"] == "PUT"
    assert captured["timeout"] == 4.5
    assert json.loads(captured["body"])["updated_at"] == "2026-07-22T00:00:00+00:00"


def test_chemistry_analyzer_asset_inventory_is_complete() -> None:
    assets = search_index.chemistry_analyzer_assets()

    assert assets["ok"] is True
    assert assets["missing"] == []
    assert assets["total_dictionary_lines"] > 0
    assert all(item["exists"] for item in assets["files"])


def test_legacy_video_search_environment_does_not_configure_teacher_search(monkeypatch) -> None:
    monkeypatch.setenv("VIDEO_LIBRARY_SEARCH_URL", "http://retired-search:9200")
    monkeypatch.delenv("TEACHER_CATALOG_SEARCH_URL", raising=False)
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert not hasattr(settings, "video_library_search_url")
        assert settings.teacher_catalog_search_url == ""
    finally:
        get_settings.cache_clear()

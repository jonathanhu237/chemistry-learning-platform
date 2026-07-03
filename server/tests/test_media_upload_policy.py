from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from server.app.api.teacher import teacher_media
from server.app.domains.media import assets as media_assets
from server.app.domains.media import files as media_files


def _settings(tmp_path, *, max_media_upload_mb: int = 1):
    return SimpleNamespace(
        media_root=tmp_path,
        max_media_upload_mb=max_media_upload_mb,
        tus_upload_dir="tus",
    )


def test_teacher_media_upload_policy_reports_effective_limit(monkeypatch, tmp_path):
    monkeypatch.setattr(media_files, "get_settings", lambda: _settings(tmp_path, max_media_upload_mb=8192))

    result = asyncio.run(teacher_media.teacher_media_upload_policy(user=SimpleNamespace(id="teacher-1")))

    assert result["max_media_upload_mb"] == 8192
    assert result["max_media_upload_bytes"] == 8192 * 1024 * 1024
    assert ".mp4" in result["allowed_extensions"]
    assert ".mkv" in result["allowed_extensions"]


def test_direct_oversized_upload_raises_policy_error_without_processing(monkeypatch, tmp_path):
    monkeypatch.setattr(media_files, "get_settings", lambda: _settings(tmp_path, max_media_upload_mb=1))
    monkeypatch.setattr(
        media_assets,
        "enqueue_processing_job",
        lambda *_args, **_kwargs: pytest.fail("oversized direct uploads must not enqueue processing"),
    )

    with pytest.raises(media_assets.MediaUploadPolicyError) as exc_info:
        media_assets.create_media_asset(
            title="Large video",
            filename="large.mp4",
            content=b"x" * (1024 * 1024 + 1),
            content_type="video/mp4",
            uploaded_by=None,
        )

    detail = exc_info.value.detail()
    assert detail["reason"] == "file_too_large"
    assert detail["file_size_bytes"] == 1024 * 1024 + 1
    assert detail["max_media_upload_mb"] == 1


def test_resumable_oversized_upload_rejects_and_removes_tus_temp_files(monkeypatch, tmp_path):
    settings = _settings(tmp_path, max_media_upload_mb=1)
    monkeypatch.setattr(media_files, "get_settings", lambda: settings)
    monkeypatch.setattr(media_assets, "get_settings", lambda: settings)
    monkeypatch.setattr(
        media_assets,
        "enqueue_processing_job",
        lambda *_args, **_kwargs: pytest.fail("oversized tus finalization must not enqueue processing"),
    )
    tus_dir = tmp_path / "tus"
    tus_dir.mkdir()
    upload_path = tus_dir / "upload-1"
    info_path = tus_dir / "upload-1.info"
    upload_path.write_bytes(b"x" * (1024 * 1024 + 1))
    info_path.write_text("{}", encoding="utf-8")

    with pytest.raises(media_assets.MediaUploadPolicyError) as exc_info:
        media_assets.complete_resumable_upload(
            title="Large video",
            upload_id="upload-1",
            filename="large.mp4",
            content_type="video/mp4",
            uploaded_by=None,
        )

    assert exc_info.value.detail()["reason"] == "file_too_large"
    assert not upload_path.exists()
    assert not info_path.exists()


def test_file_too_large_summary_is_policy_rejected_not_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(media_assets, "get_settings", lambda: _settings(tmp_path, max_media_upload_mb=1))
    monkeypatch.setattr(media_files, "get_settings", lambda: _settings(tmp_path, max_media_upload_mb=1))

    summary = media_assets.media_asset_file_summary(
        {
            "relative_path": "failed/oversized.mp4",
            "source_relative_path": "failed/oversized.mp4",
            "playback_relative_path": None,
            "thumbnail_relative_path": None,
            "upload_status": "failed",
            "error_reason": "file_too_large",
            "renditions": [],
        }
    )

    assert summary["file_state"] == "policy_rejected"
    assert summary["primary_file_available"] is False

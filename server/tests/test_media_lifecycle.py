from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from server.app.domains.media import assets as media_assets
from server.app.domains.media import files as media_files
from server.app.domains.media import lifecycle as media_lifecycle


MEDIA_LIFECYCLE_MIGRATION = Path("server/migrations/029_media_asset_lifecycle_and_es_purity.sql")
MEDIA_FRESH_BASELINE = Path("server/migrations/003_workflows_media_agent.sql")


def test_media_asset_file_summary_reports_available_primary_file(monkeypatch, tmp_path):
    source = tmp_path / "originals" / "asset-1" / "source.mp4"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"video")
    monkeypatch.setattr(media_assets, "get_settings", lambda: SimpleNamespace(media_root=tmp_path))
    monkeypatch.setattr(media_files, "get_settings", lambda: SimpleNamespace(media_root=tmp_path))

    summary = media_assets.media_asset_file_summary(
        {
            "relative_path": "originals/asset-1/source.mp4",
            "source_relative_path": "originals/asset-1/source.mp4",
            "playback_relative_path": None,
            "thumbnail_relative_path": None,
            "upload_status": "ready",
            "renditions": [],
        }
    )

    assert summary["file_state"] == "available"
    assert summary["primary_file_available"] is True
    assert summary["existing_file_count"] == 1
    assert summary["missing_file_count"] == 0


def test_media_asset_file_summary_reports_missing_ready_asset(monkeypatch, tmp_path):
    monkeypatch.setattr(media_assets, "get_settings", lambda: SimpleNamespace(media_root=tmp_path))
    monkeypatch.setattr(media_files, "get_settings", lambda: SimpleNamespace(media_root=tmp_path))

    summary = media_assets.media_asset_file_summary(
        {
            "relative_path": "originals/asset-2/source.mp4",
            "source_relative_path": "originals/asset-2/source.mp4",
            "playback_relative_path": "renditions/asset-2/learning.mp4",
            "thumbnail_relative_path": "thumbnails/asset-2.jpg",
            "upload_status": "ready",
            "renditions": [{"kind": "learning", "relative_path": "renditions/asset-2/learning.mp4"}],
        }
    )

    assert summary["file_state"] == "missing"
    assert summary["primary_file_available"] is False
    assert summary["existing_file_count"] == 0
    assert summary["missing_file_count"] == 3


def test_orphan_media_files_excludes_referenced_paths(monkeypatch, tmp_path):
    kept = tmp_path / "uploads" / "kept.mp4"
    orphan = tmp_path / "uploads" / "orphan.mp4"
    kept.parent.mkdir(parents=True)
    kept.write_bytes(b"kept")
    orphan.write_bytes(b"orphan")
    monkeypatch.setattr(media_lifecycle, "get_settings", lambda: SimpleNamespace(media_root=tmp_path))

    files, total_count, total_bytes = media_lifecycle.orphan_media_files({"uploads/kept.mp4"}, limit=10)

    assert total_count == 1
    assert total_bytes == len(b"orphan")
    assert files == [{"relative_path": "uploads/orphan.mp4", "file_size_bytes": len(b"orphan")}]


def test_media_archive_plan_reports_catalog_binding_impact(monkeypatch):
    session = object()
    monkeypatch.setattr(
        media_lifecycle,
        "_asset_row",
        lambda _session, _asset_id: {
            "id": "asset-1",
            "lifecycle_status": "active",
            "file_state": "available",
            "primary_file_available": True,
            "existing_file_count": 2,
            "missing_file_count": 0,
            "media_files": [{"relative_path": "video.mp4"}],
        },
    )
    monkeypatch.setattr(
        media_lifecycle,
        "_catalog_binding_rows",
        lambda _session, _asset_id: [
            {
                "binding_id": "binding-1",
                "placement_node_id": "point-a",
                "catalog_path": ["Chapter", "Point A"],
                "student_visible": True,
            }
        ],
    )
    monkeypatch.setattr(media_lifecycle, "_legacy_binding_rows", lambda _session, _asset_id: [{"binding_id": "legacy-1"}])
    monkeypatch.setattr(
        media_lifecycle,
        "_processing_rows",
        lambda _session, _asset_id: [
            {"id": "job-1", "status": "queued"},
            {"id": "job-2", "status": "succeeded"},
        ],
    )
    monkeypatch.setattr(media_lifecycle, "_rendition_rows", lambda _session, _asset_id: [{"id": "rendition-1"}])
    monkeypatch.setattr(media_lifecycle, "_fingerprint_rows", lambda _session, _asset_id: [{"id": "fingerprint-1"}])
    monkeypatch.setattr(media_lifecycle, "_duplicate_candidate_rows", lambda _session, _asset_id: [{"id": "candidate-1"}])

    plan = media_lifecycle._archive_plan_for_session(session, "asset-1")

    assert plan["can_archive"] is True
    assert plan["catalog_binding_count"] == 1
    assert plan["student_visible_catalog_binding_count"] == 1
    assert plan["legacy_generic_binding_count"] == 1
    assert plan["active_processing_job_count"] == 1
    assert plan["rendition_count"] == 1
    assert plan["fingerprint_count"] == 1
    assert plan["duplicate_candidate_count"] == 1
    assert "Point content remains" in plan["message"]


def test_media_archive_plan_for_unbound_asset_is_low_impact(monkeypatch):
    session = object()
    monkeypatch.setattr(
        media_lifecycle,
        "_asset_row",
        lambda _session, _asset_id: {
            "id": "asset-2",
            "lifecycle_status": "active",
            "file_state": "missing",
            "primary_file_available": False,
            "existing_file_count": 0,
            "missing_file_count": 1,
            "media_files": [],
        },
    )
    monkeypatch.setattr(media_lifecycle, "_catalog_binding_rows", lambda _session, _asset_id: [])
    monkeypatch.setattr(media_lifecycle, "_legacy_binding_rows", lambda _session, _asset_id: [])
    monkeypatch.setattr(media_lifecycle, "_processing_rows", lambda _session, _asset_id: [])
    monkeypatch.setattr(media_lifecycle, "_rendition_rows", lambda _session, _asset_id: [])
    monkeypatch.setattr(media_lifecycle, "_fingerprint_rows", lambda _session, _asset_id: [])
    monkeypatch.setattr(media_lifecycle, "_duplicate_candidate_rows", lambda _session, _asset_id: [])

    plan = media_lifecycle._archive_plan_for_session(session, "asset-2")

    assert plan["can_archive"] is True
    assert plan["catalog_binding_count"] == 0
    assert plan["active_processing_job_count"] == 0
    assert "without changing point video bindings" in plan["message"]


def test_media_cleanup_action_only_allows_db_file_cleanup_after_archive():
    dependencies = {"active_binding_count": 0, "active_catalog_binding_count": 0}

    assert media_lifecycle.media_cleanup_action(
        {"lifecycle_status": "active", "upload_status": "ready", "file_state": "available"},
        dependencies,
    ) == "keep_ready_asset_without_binding"
    assert media_lifecycle.media_cleanup_action(
        {"lifecycle_status": "archived", "upload_status": "ready", "file_state": "available"},
        dependencies,
    ) == "eligible_archived_asset_file_cleanup"
    assert media_lifecycle.media_cleanup_action(
        {"lifecycle_status": "tombstoned", "upload_status": "ready", "file_state": "available"},
        dependencies,
    ) == "eligible_archived_asset_file_cleanup"


def test_media_lifecycle_migration_keeps_lifecycle_separate_from_upload_status() -> None:
    migration_sql = MEDIA_LIFECYCLE_MIGRATION.read_text(encoding="utf-8")
    baseline_sql = MEDIA_FRESH_BASELINE.read_text(encoding="utf-8")

    for sql in [migration_sql, baseline_sql]:
        assert "lifecycle_status text NOT NULL DEFAULT 'active'" in sql
        assert "lifecycle_status IN ('active', 'archived', 'tombstoned')" in sql
        assert "media_asset_lifecycle_events" in sql
        assert "event_type IN ('media_asset_archived')" in sql
        assert "previous_lifecycle_status" in sql
        assert "new_lifecycle_status" in sql
        assert "affected_binding_summary jsonb NOT NULL DEFAULT '{}'::jsonb" in sql
        assert "upload_status IN ('pending', 'processing', 'ready', 'failed', 'replaced')" in baseline_sql
        assert "upload_status IN ('active', 'archived', 'tombstoned')" not in sql

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_admin_subtitle_routes_require_teacher_console_auth() -> None:
    source = _source("app/api/admin/admin_media.py")
    protected_routes = [
        'router.get("/media/assets/{asset_id}/subtitle-tracks")',
        'router.post("/media/assets/{asset_id}/subtitle-tracks")',
        'router.patch("/media/assets/{asset_id}/subtitle-tracks/{track_id}")',
        'router.delete("/media/assets/{asset_id}/subtitle-tracks/{track_id}")',
        'router.post("/media/assets/{asset_id}/subtitle-tracks/{track_id}/retry")',
    ]

    for marker in protected_routes:
        block = source[source.index(marker) : source.index(marker) + 900]
        assert "Depends(require_teacher_console_user)" in block

    stream_block = source[
        source.index('router.get("/media/assets/{asset_id}/subtitle-tracks/{track_id}/stream"') :
        source.index('router.get("/media/assets/{asset_id}/subtitle-tracks/{track_id}/stream"') + 900
    ]
    assert "get_user_from_access_token(access_token)" in stream_block
    assert "is_teacher_console_role(user.role)" in stream_block
    assert "subtitle_track_file(asset_id, track_id)" in stream_block
    assert "FileResponse(path, media_type=media_type, filename=filename)" in stream_block


def test_student_and_preview_subtitle_streams_use_existing_visibility_scopes() -> None:
    student_api = _source("app/api/student/student_learning.py")
    preview_api = _source("app/api/preview/catalog_preview.py")
    file_source = _source("app/domains/catalog_tree/files.py")
    visibility_source = _source("app/domains/media/student_catalog_visibility.py")

    student_block = student_api[
        student_api.index('"/media/assets/{asset_id}/subtitle-tracks/{track_id}/stream"') :
        student_api.index('"/media/assets/{asset_id}/subtitle-tracks/{track_id}/stream"') + 700
    ]
    assert "_student_from_query_token(access_token)" in student_block
    assert "student_media_subtitle_file(asset_id, track_id)" in student_block

    preview_block = preview_api[
        preview_api.index('"/media/assets/{asset_id}/subtitle-tracks/{track_id}/stream"') :
        preview_api.index('"/media/assets/{asset_id}/subtitle-tracks/{track_id}/stream"') + 700
    ]
    assert "assert_preview_media_scope(asset_id=asset_id, preview_token=preview_token)" in preview_block
    assert "preview_media_subtitle_file(asset_id, track_id, node_id=node_id)" in preview_block

    assert "FROM media_subtitle_tracks st" in file_source
    assert "JOIN student_visible_playable_media visible_media" in file_source
    assert "JOIN experiment_catalog_point_media_bindings mb" in file_source
    assert "placement.status = 'published'" in visibility_source
    assert "binding.binding_status = 'published'" in visibility_source
    assert "ma.upload_status = 'ready'" in file_source
    assert "COALESCE(ma.lifecycle_status, 'active') = 'active'" in file_source
    assert '"text/vtt; charset=utf-8"' in file_source

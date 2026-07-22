from __future__ import annotations

from pathlib import Path

from server.app.app_runtime.main import app


ROOT = Path(__file__).resolve().parents[2]


def test_student_video_library_route_is_removed() -> None:
    routes = {(route.path, method) for route in app.routes for method in getattr(route, "methods", set())}

    assert ("/api/student/video-library/search", "GET") not in routes


def test_student_video_library_projection_modules_and_scripts_are_removed() -> None:
    removed_paths = [
        "server/app/api/student/student_video_library.py",
        "server/app/student_video_library_schemas.py",
        "server/app/domains/video_library/__init__.py",
        "server/app/domains/video_library/index_client.py",
        "server/app/domains/video_library/search.py",
        "server/app/domains/catalog_tree/search_documents.py",
        "server/app/domains/experiment_points/index_events.py",
        "scripts/rebuild_video_library_index.py",
        "scripts/validate_video_library_search.py",
    ]

    assert all(not (ROOT / path).exists() for path in removed_paths)

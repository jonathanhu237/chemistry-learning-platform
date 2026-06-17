from __future__ import annotations

from server.app.admin_main import app


def assert_route(path: str, method: str) -> None:
    operations = app.openapi()["paths"].get(path, {})

    assert method.lower() in operations, f"{method.upper()} {path} is not registered"

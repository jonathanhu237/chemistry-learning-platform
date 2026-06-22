from __future__ import annotations

from scripts.validate_backend_architecture import (
    validate_fastapi_tool_entrypoint,
    validate_import_boundaries,
    validate_legacy_paths_removed,
    validate_route_inventory,
)


def test_backend_import_boundaries_are_respected() -> None:
    assert validate_import_boundaries() == []


def test_legacy_backend_compatibility_paths_are_removed() -> None:
    assert validate_legacy_paths_removed() == []


def test_fastapi_tool_entrypoint_uses_canonical_runtime() -> None:
    assert validate_fastapi_tool_entrypoint() == []


def test_backend_route_inventory_is_exact() -> None:
    assert validate_route_inventory() == []

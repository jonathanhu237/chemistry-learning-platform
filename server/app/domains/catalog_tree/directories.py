from __future__ import annotations

from typing import Any

from server.app.domains.catalog_tree.common import clean


def create_node_params(data: dict[str, Any], *, kind: str) -> dict[str, Any]:
    _ = kind
    return {
        "summary": clean(data.get("summary")),
        "teacher_note": clean(data.get("teacher_note")),
    }


def update_node_params(data: dict[str, Any], current: dict[str, Any], *, kind: str) -> dict[str, Any]:
    _ = kind

    def value(name: str, default: Any = "") -> Any:
        return data[name] if name in data else current.get(name, default)

    summary = clean(value("summary", current.get("summary", "")))
    return {
        "summary": summary,
        "teacher_note": clean(value("teacher_note", current.get("teacher_note", ""))),
    }

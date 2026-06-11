from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "data" / "app"
PROCESSED_DIR = ROOT / "data" / "processed"
SEED_DIR = ROOT / "data" / "seed"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@lru_cache(maxsize=64)
def load_app_json(name: str, default_json: str = "[]") -> Any:
    default = json.loads(default_json)
    app_path = APP_DIR / name
    if app_path.exists():
        return _read_json(app_path, default)
    processed_name = name.removeprefix("app_")
    return _read_json(PROCESSED_DIR / processed_name, default)


@lru_cache(maxsize=16)
def load_processed_json(name: str, default_json: str = "[]") -> Any:
    return _read_json(PROCESSED_DIR / name, json.loads(default_json))


def clear_cache() -> None:
    load_app_json.cache_clear()
    load_processed_json.cache_clear()


def chapters() -> list[dict[str, Any]]:
    return load_app_json("app_chapters.json")


def areas() -> list[dict[str, Any]]:
    return load_app_json("app_areas.json")


def units() -> list[dict[str, Any]]:
    return load_app_json("app_knowledge_units.json")


def knowledge_points() -> list[dict[str, Any]]:
    return load_app_json("app_knowledge_points.json")


def experiments() -> list[dict[str, Any]]:
    formal_seed = _read_json(SEED_DIR / "formal_experiments.json", {})
    formal_experiments = list(formal_seed.get("experiments") or []) if isinstance(formal_seed, dict) else []
    if formal_experiments:
        rows: list[dict[str, Any]] = []
        for item in formal_experiments:
            bindings = list(item.get("chapter_bindings") or [])
            primary_binding = next((binding for binding in bindings if binding.get("coverage_type") == "primary"), None)
            first_binding = primary_binding or (bindings[0] if bindings else {})
            metadata = item.get("metadata") or {}
            status = item.get("status") or "published"
            rows.append(
                {
                    "id": item.get("id"),
                    "experiment_id": item.get("id"),
                    "code": item.get("code"),
                    "name": item.get("title"),
                    "normalized_name": item.get("title"),
                    "title_en": item.get("title_en"),
                    "objective": item.get("summary"),
                    "summary": item.get("summary"),
                    "content_status": status,
                    "display_order": item.get("display_order") or 0,
                    "source_refs": item.get("source_refs") or [],
                    "metadata": metadata,
                    "chapter_ids": [binding.get("chapter_id") for binding in bindings if binding.get("chapter_id")],
                    "chapter_id": first_binding.get("chapter_id"),
                    "related_knowledge_point_ids": [],
                    "source_chunk_ids": [],
                    "video_url": None,
                    "resource_mode": "experiment_unit",
                    "review_required": False,
                    "student_visible": status == "published",
                    "formal_catalog": True,
                    "video_candidates": list(metadata.get("video_candidates") or []),
                    "parent_title": metadata.get("parent_title"),
                    "module_title": metadata.get("module_display_title"),
                }
            )
        return rows
    return load_app_json("app_experiments.json")


def learning_cards() -> list[dict[str, Any]]:
    return load_app_json("app_learning_cards.json")


def questions() -> list[dict[str, Any]]:
    formal_ids = {item.get("id") for item in experiments() if item.get("id")}
    rows = load_app_json("app_questions.json")
    if formal_ids:
        filtered_rows = []
        for row in rows:
            item = dict(row)
            item["related_experiment_ids"] = [
                experiment_id
                for experiment_id in item.get("related_experiment_ids") or []
                if experiment_id in formal_ids
            ]
            filtered_rows.append(item)
        return filtered_rows
    return rows


def links() -> list[dict[str, Any]]:
    formal_ids = {item.get("id") for item in experiments() if item.get("id")}
    rows = load_app_json("app_links.json")
    if formal_ids:
        return [
            item
            for item in rows
            if not (
                (item.get("from_type") == "experiment" and item.get("from_id") not in formal_ids)
                or (item.get("to_type") == "experiment" and item.get("to_id") not in formal_ids)
            )
        ]
    return rows


def resources() -> list[dict[str, Any]]:
    return load_app_json("app_resources.json")


def review_queue() -> list[dict[str, Any]]:
    return load_app_json("app_review_queue.json")


def source_chunks() -> list[dict[str, Any]]:
    formal_ids = {item.get("id") for item in experiments() if item.get("id")}
    rows = load_processed_json("source_chunks.json")
    if not formal_ids:
        return rows
    filtered_rows: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["related_experiment_ids"] = [
            experiment_id
            for experiment_id in item.get("related_experiment_ids") or []
            if experiment_id in formal_ids
        ]
        filtered_rows.append(item)
    return filtered_rows


def source_documents() -> list[dict[str, Any]]:
    return load_processed_json("source_documents.json")


def by_id(items: list[dict[str, Any]], *keys: str) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for item in items:
        for key in keys:
            value = item.get(key)
            if value:
                lookup[str(value)] = item
    return lookup


def get_chapter(chapter_id: str) -> dict[str, Any] | None:
    return by_id(chapters(), "chapter_id").get(chapter_id)


def get_unit(unit_id: str) -> dict[str, Any] | None:
    return by_id(units(), "unit_id").get(unit_id)


def get_knowledge_point(kp_id: str) -> dict[str, Any] | None:
    return by_id(knowledge_points(), "knowledge_point_id", "id").get(kp_id)


def get_experiment(experiment_id: str) -> dict[str, Any] | None:
    return by_id(experiments(), "experiment_id", "id").get(experiment_id)


def get_learning_card(experiment_id: str) -> dict[str, Any] | None:
    for card in learning_cards():
        if card.get("experiment_id") == experiment_id:
            return card
    return None


def get_question(question_id: str) -> dict[str, Any] | None:
    return by_id(questions(), "question_id", "id").get(question_id)


def chunks_by_ids(chunk_ids: list[str]) -> list[dict[str, Any]]:
    lookup = by_id(source_chunks(), "chunk_id", "id")
    return [lookup[chunk_id] for chunk_id in chunk_ids if chunk_id in lookup]


def related_chunks_for_kp(kp_id: str, limit: int = 8) -> list[dict[str, Any]]:
    linked_ids = [
        link.get("from_id")
        for link in links()
        if link.get("from_type") == "source_chunk" and link.get("to_type") == "knowledge_point" and link.get("to_id") == kp_id
    ]
    chunks = chunks_by_ids([str(item) for item in linked_ids if item])
    if chunks:
        return chunks[:limit]
    return [chunk for chunk in source_chunks() if kp_id in (chunk.get("candidate_knowledge_point_ids") or [])][:limit]


def load_events() -> list[dict[str, Any]]:
    return _read_json(APP_DIR / "demo_events.json", [])


def save_events(events: list[dict[str, Any]]) -> None:
    _write_json(APP_DIR / "demo_events.json", events)


def append_event(event: dict[str, Any]) -> dict[str, Any]:
    events = load_events()
    events.append(event)
    save_events(events)
    return event


def load_mastery() -> dict[str, Any]:
    return _read_json(APP_DIR / "demo_mastery.json", {})


def save_mastery(data: dict[str, Any]) -> None:
    _write_json(APP_DIR / "demo_mastery.json", data)


def load_students() -> list[dict[str, Any]]:
    return _read_json(APP_DIR / "demo_students.json", [])


def save_students(students: list[dict[str, Any]]) -> None:
    _write_json(APP_DIR / "demo_students.json", students)

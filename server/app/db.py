from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"


def load_json(name: str, default: Any) -> Any:
    path = PROCESSED_DIR / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_chunks() -> list[dict[str, Any]]:
    return load_json("source_chunks.json", [])


@lru_cache(maxsize=1)
def load_experiments() -> list[dict[str, Any]]:
    return load_json("experiments.json", [])


@lru_cache(maxsize=1)
def load_knowledge_points() -> list[dict[str, Any]]:
    return load_json("knowledge_points.json", [])


def clear_cache() -> None:
    load_chunks.cache_clear()
    load_experiments.cache_clear()
    load_knowledge_points.cache_clear()


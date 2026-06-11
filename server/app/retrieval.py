from __future__ import annotations

import math
import re
from difflib import SequenceMatcher
from typing import Any

from server.app.db import load_chunks

CHEMISTRY_TERMS = [
    "卤素",
    "氟",
    "氯",
    "溴",
    "碘",
    "氧",
    "硫",
    "氮",
    "磷",
    "碳",
    "硅",
    "硼",
    "铝",
    "钠",
    "钾",
    "镁",
    "钙",
    "铜",
    "锌",
    "铁",
    "锰",
    "铬",
    "沉淀",
    "配位",
    "氧化",
    "还原",
    "水解",
    "酸性",
    "碱性",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def tokenize(text: str) -> set[str]:
    text = normalize(text)
    tokens = set(re.findall(r"[A-Za-z][A-Za-z0-9+\-]*|[0-9]+|[\u4e00-\u9fff]{2,}", text))
    for term in CHEMISTRY_TERMS:
        if term in text:
            tokens.add(term)
    return tokens


def metadata_match(
    chunk: dict[str, Any],
    chapter_id: str | None = None,
    experiment_id: str | None = None,
    knowledge_point_ids: list[str] | None = None,
) -> bool:
    knowledge_point_ids = knowledge_point_ids or []
    if chapter_id and chunk.get("chapter_id") != chapter_id:
        return False
    if experiment_id and experiment_id not in chunk.get("related_experiment_ids", []):
        return False
    if knowledge_point_ids and not set(knowledge_point_ids).intersection(chunk.get("candidate_knowledge_point_ids", [])):
        return False
    return True


def keyword_score(
    query: str,
    chunk: dict[str, Any],
    chapter_id: str | None = None,
    experiment_id: str | None = None,
    knowledge_point_ids: list[str] | None = None,
) -> float:
    q_tokens = tokenize(query)
    c_tokens = tokenize(chunk.get("text", ""))
    if not q_tokens:
        return 0.0
    overlap = len(q_tokens & c_tokens) / max(1, len(q_tokens))
    ratio = SequenceMatcher(None, normalize(query), normalize(chunk.get("text", ""))[:900]).ratio()
    score = overlap * 0.70 + ratio * 0.20
    if chapter_id and chunk.get("chapter_id") == chapter_id:
        score += 0.08
    if experiment_id and experiment_id in chunk.get("related_experiment_ids", []):
        score += 0.18
    if knowledge_point_ids and set(knowledge_point_ids).intersection(chunk.get("candidate_knowledge_point_ids", [])):
        score += 0.18
    return round(min(score, 1.0), 4)


def retrieve(
    question: str,
    chapter_id: str | None = None,
    experiment_id: str | None = None,
    knowledge_point_ids: list[str] | None = None,
    top_k: int = 5,
) -> tuple[list[dict[str, Any]], str]:
    chunks = load_chunks()
    knowledge_point_ids = knowledge_point_ids or []
    scopes: list[list[dict[str, Any]]] = []

    if chapter_id or experiment_id or knowledge_point_ids:
        scoped = [
            chunk
            for chunk in chunks
            if metadata_match(chunk, chapter_id=chapter_id, experiment_id=experiment_id, knowledge_point_ids=knowledge_point_ids)
        ]
        scopes.append(scoped)
    if chapter_id:
        scopes.append([chunk for chunk in chunks if chunk.get("chapter_id") == chapter_id])
    scopes.append(chunks)

    seen_scope_ids: set[int] = set()
    for scope in scopes:
        if id(scope) in seen_scope_ids:
            continue
        seen_scope_ids.add(id(scope))
        scored = [
            (
                keyword_score(
                    question,
                    chunk,
                    chapter_id=chapter_id,
                    experiment_id=experiment_id,
                    knowledge_point_ids=knowledge_point_ids,
                ),
                chunk,
            )
            for chunk in scope
        ]
        scored = [(score, chunk) for score, chunk in scored if score > 0]
        scored.sort(key=lambda item: item[0], reverse=True)
        if scored:
            return [{**chunk, "_score": score} for score, chunk in scored[:top_k]], "keyword"
    return [], "keyword"


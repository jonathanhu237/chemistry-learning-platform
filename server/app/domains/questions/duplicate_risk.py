from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from server.app.domains.platform.settings import effective_textbook_rag_settings
from server.app.domains.textbook_rag.clients import QwenEmbeddingClient, TextbookRAGClientError
from server.app.infrastructure.settings import Settings, get_settings


DUPLICATE_RISK_KEY = "duplicate_risk"
MAX_DUPLICATE_MATCHES = 3
RULE_SIMILARITY_THRESHOLD = 0.68
EMBEDDING_SIMILARITY_THRESHOLD = 0.84


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _payload_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(payload.get("metadata"))


def duplicate_point_node_ids(payload: dict[str, Any]) -> list[str]:
    metadata = _payload_metadata(payload)
    source_audit = _as_dict(metadata.get("source_audit"))
    lineage = _as_dict(metadata.get("evidence_lineage"))
    candidates = [
        payload.get("source_placement_node_ids"),
        metadata.get("source_placement_node_ids"),
        payload.get("primary_point_node_ids"),
        metadata.get("primary_point_node_ids"),
        metadata.get("target_point_node_ids"),
        source_audit.get("target_point_node_ids"),
        lineage.get("source_placement_node_ids"),
        lineage.get("target_point_node_ids"),
    ]
    output: list[str] = []
    seen: set[str] = set()
    for group in candidates:
        for item in _as_list(group):
            value = _clean(item)
            if value and value not in seen:
                seen.add(value)
                output.append(value)
    return output


def question_semantic_text(payload: dict[str, Any]) -> str:
    options = payload.get("options")
    option_text = ""
    if isinstance(options, list):
        option_text = " ".join(
            _clean(option if isinstance(option, str) else f"{_as_dict(option).get('label', '')} {_as_dict(option).get('text', '')}")
            for option in options
        )
    answer = payload.get("answer")
    return " ".join(
        item
        for item in [
            _clean(payload.get("question_type")),
            _clean(payload.get("stem")),
            option_text,
            _json_dumps(answer) if answer is not None else "",
            _clean(payload.get("explanation")),
        ]
        if item
    ).strip()


def _normalized_text(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"\s+", "", lowered)
    lowered = re.sub(r"[，。！？、；：,.!?;:()（）\\[\\]【】{}《》“”\"'`~^=+\\-_/|\\\\]", "", lowered)
    return lowered


def _char_bigrams(value: str) -> set[str]:
    normalized = _normalized_text(value)
    if len(normalized) <= 1:
        return {normalized} if normalized else set()
    return {normalized[index : index + 2] for index in range(len(normalized) - 1)}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _answer_key(payload: dict[str, Any]) -> str:
    return _normalized_text(_json_dumps(payload.get("answer") or {}))


def _rule_similarity(left: dict[str, Any], right: dict[str, Any]) -> tuple[float, str]:
    left_stem = _clean(left.get("stem"))
    right_stem = _clean(right.get("stem"))
    left_norm = _normalized_text(left_stem)
    right_norm = _normalized_text(right_stem)
    if left_norm and left_norm == right_norm:
        return 1.0, "题干高度一致"
    stem_score = _jaccard(_char_bigrams(left_stem), _char_bigrams(right_stem))
    full_score = _jaccard(_char_bigrams(question_semantic_text(left)), _char_bigrams(question_semantic_text(right)))
    answer_same = bool(_answer_key(left) and _answer_key(left) == _answer_key(right))
    type_same = _clean(left.get("question_type")) == _clean(right.get("question_type"))
    score = max(stem_score, full_score)
    if type_same and answer_same and score >= 0.46:
        return max(score, 0.72), "同题型、答案一致且题意相近"
    if score >= RULE_SIMILARITY_THRESHOLD:
        return score, "题干、答案或解析文本相近"
    return score, ""


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def _fingerprint_hash(text_value: str) -> str:
    return hashlib.sha256(text_value.encode("utf-8")).hexdigest()


def _embedding_client(settings: Settings | None = None) -> QwenEmbeddingClient | None:
    settings = settings or get_settings()
    effective_rag = effective_textbook_rag_settings()
    embedding_config = _as_dict(effective_rag.get("embedding"))
    client = QwenEmbeddingClient(
        base_url=_clean(embedding_config.get("base_url")) or settings.textbook_rag_embedding_base_url,
        api_key=_clean(embedding_config.get("api_key")) or settings.textbook_rag_embedding_api_key,
        model=_clean(embedding_config.get("model")) or settings.textbook_rag_embedding_model,
        dimensions=int(effective_rag.get("embedding_dimension") or settings.textbook_rag_embedding_dimension or 0) or None,
        timeout_seconds=float(effective_rag.get("timeout_seconds") or settings.textbook_rag_timeout_seconds),
    )
    return client if client.ready else None


def _cached_embedding(
    session: Any,
    *,
    owner_kind: str,
    owner_id: str,
    point_node_id: str,
    model: str,
    text_hash: str,
) -> list[float] | None:
    row = (
        session.execute(
            text(
                """
                SELECT embedding
                FROM question_semantic_fingerprints
                WHERE owner_kind = :owner_kind
                  AND owner_id = CAST(:owner_id AS uuid)
                  AND point_node_id = :point_node_id
                  AND embedding_model = :model
                  AND text_hash = :text_hash
                LIMIT 1
                """
            ),
            {
                "owner_kind": owner_kind,
                "owner_id": owner_id,
                "point_node_id": point_node_id,
                "model": model,
                "text_hash": text_hash,
            },
        )
        .mappings()
        .first()
    )
    if not row or not isinstance(row.get("embedding"), list):
        return None
    return [float(value) for value in row["embedding"]]


def _store_embedding(
    session: Any,
    *,
    owner_kind: str,
    owner_id: str,
    point_node_id: str,
    model: str,
    text_hash: str,
    embedding: list[float],
) -> None:
    session.execute(
        text(
            """
            INSERT INTO question_semantic_fingerprints (
              owner_kind, owner_id, point_node_id, text_hash, embedding_model, embedding
            )
            VALUES (
              :owner_kind, CAST(:owner_id AS uuid), :point_node_id, :text_hash, :model, CAST(:embedding AS jsonb)
            )
            ON CONFLICT (owner_kind, owner_id, point_node_id, embedding_model, text_hash)
            DO UPDATE SET embedding = EXCLUDED.embedding, updated_at = now()
            """
        ),
        {
            "owner_kind": owner_kind,
            "owner_id": owner_id,
            "point_node_id": point_node_id,
            "text_hash": text_hash,
            "model": model,
            "embedding": _json_dumps(embedding),
        },
    )


def _embedding_for_payload(
    session: Any,
    *,
    payload: dict[str, Any],
    owner_kind: str | None,
    owner_id: str | None,
    point_node_id: str,
    client: QwenEmbeddingClient | None,
) -> list[float] | None:
    if not client:
        return None
    text_value = question_semantic_text(payload)
    if not text_value:
        return None
    text_hash = _fingerprint_hash(text_value)
    if owner_kind and owner_id:
        cached = _cached_embedding(
            session,
            owner_kind=owner_kind,
            owner_id=owner_id,
            point_node_id=point_node_id,
            model=client.model,
            text_hash=text_hash,
        )
        if cached is not None:
            return cached
    try:
        embedding = client.embed([text_value])[0]
    except (TextbookRAGClientError, OSError, RuntimeError):
        return None
    if owner_kind and owner_id:
        _store_embedding(
            session,
            owner_kind=owner_kind,
            owner_id=owner_id,
            point_node_id=point_node_id,
            model=client.model,
            text_hash=text_hash,
            embedding=embedding,
        )
    return embedding


def _question_payload_from_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "question_type": row.get("question_type"),
        "stem": row.get("stem"),
        "options": row.get("options") or [],
        "answer": row.get("answer") or {},
        "explanation": row.get("explanation") or "",
        "primary_point_node_ids": row.get("primary_point_node_ids") or [],
        "source_placement_node_ids": row.get("source_placement_node_ids") or [],
        "metadata": row.get("metadata") or {},
    }
    return payload


def _load_same_point_rows(
    session: Any,
    *,
    point_node_id: str,
    exclude_owner_kind: str | None,
    exclude_owner_id: str | None,
    limit: int = 80,
) -> list[dict[str, Any]]:
    published_rows = [
        {
            "kind": "published",
            "owner_kind": "question",
            "owner_id": str(row["id"]),
            "payload": _question_payload_from_row(dict(row)),
        }
        for row in session.execute(
            text(
                """
                SELECT id, question_type, stem, options, answer, explanation,
                       primary_point_node_ids, source_placement_node_ids, metadata
                FROM experiment_questions
                WHERE status = 'published'
                  AND (:point_node_id = ANY(primary_point_node_ids)
                       OR :point_node_id = ANY(source_placement_node_ids))
                ORDER BY updated_at DESC
                LIMIT :limit
                """
            ),
            {"point_node_id": point_node_id, "limit": limit},
        )
        .mappings()
        .all()
    ]
    draft_rows = [
        {
            "kind": "draft",
            "owner_kind": "draft",
            "owner_id": str(row["id"]),
            "payload": dict(row["payload"] or {}),
        }
        for row in session.execute(
            text(
                """
                SELECT id, payload
                FROM experiment_question_drafts d
                WHERE d.status = 'draft'
                  AND (:exclude_owner_kind IS DISTINCT FROM 'draft'
                       OR d.id <> CAST(NULLIF(:exclude_owner_id, '') AS uuid))
                  AND EXISTS (
                    SELECT 1
                    FROM jsonb_array_elements_text(
                      COALESCE(
                        d.payload->'source_placement_node_ids',
                        d.payload->'primary_point_node_ids',
                        d.payload->'metadata'->'source_placement_node_ids',
                        d.payload->'metadata'->'primary_point_node_ids',
                        '[]'::jsonb
                      )
                    ) AS point_ids(value)
                    WHERE point_ids.value = :point_node_id
                  )
                ORDER BY d.updated_at DESC
                LIMIT :limit
                """
            ),
            {
                "point_node_id": point_node_id,
                "exclude_owner_kind": exclude_owner_kind or "",
                "exclude_owner_id": exclude_owner_id or "",
                "limit": limit,
            },
        )
        .mappings()
        .all()
    ]
    rows = [*published_rows, *draft_rows]
    if exclude_owner_kind and exclude_owner_id:
        rows = [row for row in rows if not (row["owner_kind"] == exclude_owner_kind and row["owner_id"] == exclude_owner_id)]
    return rows[:limit]


def _match_summary(row: dict[str, Any], *, score: float, reason: str) -> dict[str, Any]:
    payload = _as_dict(row.get("payload"))
    return {
        "kind": row.get("kind") or row.get("owner_kind") or "question",
        "owner_kind": row.get("owner_kind") or row.get("kind") or "question",
        "owner_id": row.get("owner_id"),
        "question_type": _clean(payload.get("question_type")),
        "stem": _clean(payload.get("stem"))[:140],
        "score": round(float(score), 4),
        "reason": reason or "同点位题目语义相近",
    }


def build_duplicate_risk(
    payload: dict[str, Any],
    *,
    comparison_rows: list[dict[str, Any]],
    session: Any | None = None,
    owner_kind: str | None = None,
    owner_id: str | None = None,
    point_node_id: str | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    point_node_id = point_node_id or next(iter(duplicate_point_node_ids(payload)), "")
    client = _embedding_client(settings) if session is not None else None
    current_embedding = (
        _embedding_for_payload(
            session,
            payload=payload,
            owner_kind=owner_kind,
            owner_id=owner_id,
            point_node_id=point_node_id,
            client=client,
        )
        if point_node_id
        else None
    )
    matches: list[dict[str, Any]] = []
    for row in comparison_rows:
        other_payload = _as_dict(row.get("payload"))
        score, reason = _rule_similarity(payload, other_payload)
        has_match = score >= RULE_SIMILARITY_THRESHOLD
        if current_embedding is not None and session is not None and point_node_id:
            other_embedding = _embedding_for_payload(
                session,
                payload=other_payload,
                owner_kind=_clean(row.get("owner_kind")) or None,
                owner_id=_clean(row.get("owner_id")) or None,
                point_node_id=point_node_id,
                client=client,
            )
            if other_embedding is not None:
                embedding_score = _cosine(current_embedding, other_embedding)
                if embedding_score > score:
                    score = embedding_score
                    reason = "同点位题目语义相近"
                has_match = has_match or embedding_score >= EMBEDDING_SIMILARITY_THRESHOLD
        if has_match:
            matches.append(_match_summary(row, score=score, reason=reason))
    matches.sort(key=lambda item: float(item.get("score") or 0), reverse=True)
    matches = matches[:MAX_DUPLICATE_MATCHES]
    return {
        "has_risk": bool(matches),
        "level": "possible" if matches else "none",
        "blocking": False,
        "message": f"这道题可能与 {len(matches)} 道同点位题目考察意图相近，请发布前确认。" if matches else "未发现同点位重复风险。",
        "matches": matches,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "method": "rules+embedding" if current_embedding is not None else "rules",
        "scope": "same_point",
    }


def apply_duplicate_risk_metadata(payload: dict[str, Any], risk: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(_payload_metadata(payload))
    metadata[DUPLICATE_RISK_KEY] = risk
    return {**payload, "metadata": metadata}


def evaluate_duplicate_risk_for_payload(
    session: Any,
    *,
    payload: dict[str, Any],
    owner_kind: str | None = None,
    owner_id: str | None = None,
    point_node_id: str | None = None,
) -> dict[str, Any]:
    point_ids = [point_node_id] if point_node_id else duplicate_point_node_ids(payload)
    point_ids = [point_id for point_id in point_ids if point_id]
    if not point_ids:
        return build_duplicate_risk(payload, comparison_rows=[])
    comparison_rows = _load_same_point_rows(
        session,
        point_node_id=point_ids[0],
        exclude_owner_kind=owner_kind,
        exclude_owner_id=owner_id,
    )
    return build_duplicate_risk(
        payload,
        comparison_rows=comparison_rows,
        session=session,
        owner_kind=owner_kind,
        owner_id=owner_id,
        point_node_id=point_ids[0],
    )


def attach_duplicate_risk_for_payload(
    session: Any,
    *,
    payload: dict[str, Any],
    owner_kind: str | None = None,
    owner_id: str | None = None,
    point_node_id: str | None = None,
) -> dict[str, Any]:
    risk = evaluate_duplicate_risk_for_payload(
        session,
        payload=payload,
        owner_kind=owner_kind,
        owner_id=owner_id,
        point_node_id=point_node_id,
    )
    return apply_duplicate_risk_metadata(payload, risk)

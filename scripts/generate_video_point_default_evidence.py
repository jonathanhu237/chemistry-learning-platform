from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import bindparam, create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.domains.experiment_points.canonical_points import candidate_point_key as _candidate_point_key


DEFAULT_DATABASE_URL = "postgresql+psycopg://chemistry:chemistry@127.0.0.1:15432/chemistry_exam"
DEFAULT_BGE_URL = "http://127.0.0.1:8011"
EXPERIMENT_COLLECTION = "textbook_experiment_clean_v1"
THEORY_COLLECTION = "textbook_inorganic_lower_v1"
SPOT_EXPERIMENT_IDS = {
    "EXP_19_1_08",
    "EXP_19_2_05",
    "EXP_19_3_02",
    "EXP_19_3_03",
    "EXP_20_1_08",
}
SUBSCRIPT_SUPERSCRIPT_TRANSLATION = str.maketrans(
    {
        "₀": "0",
        "₁": "1",
        "₂": "2",
        "₃": "3",
        "₄": "4",
        "₅": "5",
        "₆": "6",
        "₇": "7",
        "₈": "8",
        "₉": "9",
        "⁰": "0",
        "¹": "1",
        "²": "2",
        "³": "3",
        "⁴": "4",
        "⁵": "5",
        "⁶": "6",
        "⁷": "7",
        "⁸": "8",
        "⁹": "9",
        "⁺": "+",
        "⁻": "-",
        "＋": "+",
        "－": "-",
    }
)
FORMULA_STOP_TERMS = {"A", "AI", "CH", "FIG", "L", "ML", "MOL", "PAGE", "PH"}
FORMULA_ALIASES = {
    "AGCL": ["氯化银"],
    "AGBR": ["溴化银"],
    "AGI": ["碘化银"],
    "H2O2": ["过氧化氢"],
    "H2S": ["硫化氢"],
    "KMNO4": ["高锰酸钾"],
    "SO2": ["二氧化硫"],
    "SO32": ["亚硫酸盐"],
    "SO42": ["硫酸根", "硫酸盐"],
    "NA2S2O3": ["硫代硫酸钠"],
    "KSCN": ["硫氰酸钾"],
    "NH3": ["氨", "氨水"],
    "HG(I)": ["汞(I)", "汞（I）", "汞(Ⅰ)", "汞（Ⅰ）", "HG2"],
}
EXPERIMENT_FORMULA_ALIASES = {
    "AGCL": ["NACL"],
    "AGBR": ["KBR"],
    "AGI": ["KI"],
}
DIRECT_TEXT_TERMS = [
    "冰水",
    "冷却",
    "酸化",
    "试纸",
    "酸碱性",
    "品红",
    "漂白",
    "褪色",
    "恢复",
    "加热",
    "水浴",
    "沉淀",
    "溶解",
    "颜色",
    "变色",
    "气体",
    "产物",
    "检验",
    "检出",
    "验证",
    "分离",
    "清液",
    "通风橱",
    "对照",
    "催化",
    "氧化性",
    "还原性",
    "歧化",
    "配合物",
    "络合物",
    "乙醚",
    "丙酮",
    "戊醇",
    "乙二胺",
    "氨水",
    "氯水",
    "溴水",
    "碘水",
    "铅丹",
    "硫化氢",
    "硫化钠",
    "饱和",
    "浓",
    "稀",
]
SPECIFIC_TEXT_TERMS = {
    "冰水",
    "冷却",
    "酸化",
    "试纸",
    "酸碱性",
    "品红",
    "漂白",
    "褪色",
    "恢复",
    "检验",
    "检出",
    "验证",
    "分离",
    "清液",
    "通风橱",
    "对照",
    "催化",
    "乙醚",
    "丙酮",
    "戊醇",
    "乙二胺",
    "氨水",
    "氯水",
    "溴水",
    "碘水",
    "铅丹",
    "硫化氢",
    "硫化钠",
}
THEORY_REQUIRED_SPECIFIC_TERMS = {
    "品红",
    "漂白",
    "褪色",
    "恢复",
    "丙酮",
    "戊醇",
    "乙二胺",
    "配合物",
    "络合物",
}
GENERIC_EXPERIMENT_TYPES = {"experiment_protocol", "safety_note", "teaching_question_seed"}
WEAK_THEORY_TYPES = {"table_context", "table_record"}
GENERIC_EXPERIMENT_SECTION_MARKERS = ("实验目的", "实验预习", "安全知识", "思考题")


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "as_posix"):
        return str(value)
    return str(value)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def _utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _metadata_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _chunk_document(chunk: dict[str, Any]) -> str:
    return _clean_text(chunk.get("text") or chunk.get("markdown") or "")


def _matchable_text(value: Any) -> str:
    text_value = unicodedata.normalize("NFKC", str(value or "")).translate(SUBSCRIPT_SUPERSCRIPT_TRANSLATION)
    text_value = re.sub(r"\\(?:mathrm|ce|text|left|right|cdot|Delta|ominus|circ)\b", "", text_value)
    text_value = re.sub(r"\\[A-Za-z]+", "", text_value)
    text_value = text_value.replace("{", "").replace("}", "").replace("_", "").replace("^", "")
    return text_value.upper()


def _formula_terms(value: str) -> list[str]:
    canonical = _matchable_text(value)
    terms: list[str] = []
    for match in re.finditer(r"[A-Z][A-Z0-9()+\-.·]{1,}", canonical):
        term = match.group(0).strip(".-+·")
        if len(term) < 2 or term in FORMULA_STOP_TERMS:
            continue
        if not any(char.isdigit() for char in term) and len(term) > 6:
            continue
        if term not in terms:
            terms.append(term)
    return terms


def evidence_terms(point_title: str) -> list[dict[str, str]]:
    title = _clean_text(point_title)
    terms: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, term: str) -> None:
        cleaned = _clean_text(term)
        if not cleaned:
            return
        key = (kind, cleaned)
        if key in seen:
            return
        seen.add(key)
        terms.append({"kind": kind, "term": cleaned})

    for term in _formula_terms(title):
        add("formula", term)
    for term in DIRECT_TEXT_TERMS:
        if term in title:
            add("text", term)
    return terms


def _document_match_terms(document: str, terms: list[dict[str, str]], pool: str) -> tuple[list[str], int, int]:
    raw_document = _clean_text(document)
    canonical_document = _matchable_text(raw_document)
    matched: list[str] = []
    formula_hits = 0
    text_hits = 0
    for item in terms:
        term = item["term"]
        if item["kind"] == "formula":
            canonical_term = _matchable_text(term)
            aliases = list(FORMULA_ALIASES.get(canonical_term, []))
            if pool == "experiment":
                aliases.extend(EXPERIMENT_FORMULA_ALIASES.get(canonical_term, []))
            alias_matched = any(_matchable_text(alias) in canonical_document or alias in raw_document for alias in aliases)
            if canonical_term in canonical_document or alias_matched:
                matched.append(term)
                formula_hits += 1
        elif term in raw_document:
            matched.append(term)
            text_hits += 1
    return matched, formula_hits, text_hits


def _post_json(base_url: str, path: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=_json_dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_json(base_url: str, path: str, timeout: float) -> dict[str, Any]:
    with urllib.request.urlopen(f"{base_url.rstrip('/')}{path}", timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def embed_query(base_url: str, query: str, timeout: float) -> list[float]:
    payload = _post_json(base_url, "/embed", {"texts": [query]}, timeout)
    embeddings = payload.get("embeddings")
    if not isinstance(embeddings, list) or not embeddings:
        raise RuntimeError("BGE embed response missing embeddings")
    first = embeddings[0]
    if not isinstance(first, list) or not first:
        raise RuntimeError("BGE embed response has empty embedding")
    return [float(item) for item in first]


def rerank_documents(
    base_url: str,
    query: str,
    documents: list[str],
    *,
    batch_size: int,
    timeout: float,
) -> list[float]:
    scores: list[float] = []
    for offset in range(0, len(documents), batch_size):
        batch = documents[offset : offset + batch_size]
        payload = _post_json(base_url, "/rerank", {"query": query, "documents": batch}, timeout)
        batch_scores = payload.get("scores")
        if not isinstance(batch_scores, list) or len(batch_scores) != len(batch):
            raise RuntimeError("BGE rerank response has unexpected score count")
        scores.extend(float(score) for score in batch_scores)
    return scores


def load_points(engine: Any, experiment_ids: set[str], limit: int | None) -> list[dict[str, Any]]:
    conditions = ["fe.status <> 'archived'"]
    params: dict[str, Any] = {}
    stmt = text(
        """
        SELECT fe.id AS experiment_id,
               fe.code,
               fe.title,
               fe.summary,
               fe.display_order,
               fe.metadata,
               COALESCE(
                 array_agg(DISTINCT ecb.chapter_id) FILTER (WHERE ecb.chapter_id IS NOT NULL),
                 '{}'::text[]
               ) AS chapter_ids
        FROM formal_experiments fe
        LEFT JOIN experiment_chapter_bindings ecb ON ecb.experiment_id = fe.id
        WHERE __CONDITIONS__
        GROUP BY fe.id, fe.code, fe.title, fe.summary, fe.display_order, fe.metadata
        ORDER BY fe.display_order, fe.code, fe.id
        """.replace("__CONDITIONS__", " AND ".join(conditions))
    )
    if experiment_ids:
        conditions.append("fe.id IN :experiment_ids")
        stmt = text(
            """
            SELECT fe.id AS experiment_id,
                   fe.code,
                   fe.title,
                   fe.summary,
                   fe.display_order,
                   fe.metadata,
                   COALESCE(
                     array_agg(DISTINCT ecb.chapter_id) FILTER (WHERE ecb.chapter_id IS NOT NULL),
                     '{}'::text[]
                   ) AS chapter_ids
            FROM formal_experiments fe
            LEFT JOIN experiment_chapter_bindings ecb ON ecb.experiment_id = fe.id
            WHERE fe.status <> 'archived'
              AND fe.id IN :experiment_ids
            GROUP BY fe.id, fe.code, fe.title, fe.summary, fe.display_order, fe.metadata
            ORDER BY fe.display_order, fe.code, fe.id
            """
        ).bindparams(bindparam("experiment_ids", expanding=True))
        params["experiment_ids"] = sorted(experiment_ids)

    with engine.connect() as connection:
        rows = [dict(row) for row in connection.execute(stmt, params).mappings().all()]
    points: list[dict[str, Any]] = []
    for row in rows:
        metadata = _metadata_dict(row.get("metadata"))
        raw_candidates = metadata.get("video_candidates")
        if not isinstance(raw_candidates, list):
            continue
        seen_titles: set[str] = set()
        for index, raw_title in enumerate(raw_candidates):
            point_title = _clean_text(raw_title)
            if not point_title or point_title in seen_titles:
                continue
            seen_titles.add(point_title)
            points.append(
                {
                    "experiment_id": row["experiment_id"],
                    "experiment_code": row.get("code"),
                    "experiment_title": _clean_text(row.get("title")),
                    "experiment_summary": _clean_text(row.get("summary")),
                    "display_order": row.get("display_order"),
                    "chapter_ids": list(row.get("chapter_ids") or []),
                    "point_index": index,
                    "point_key": _candidate_point_key(index, point_title),
                    "point_title": point_title,
                }
            )
            if limit is not None and len(points) >= limit:
                return points
    return points


def build_query(point: dict[str, Any]) -> str:
    parts = [
        "Task: retrieve only direct evidence chunks for a chemistry lab video point.",
        f"Experiment code: {point.get('experiment_code') or ''}",
        f"Experiment title: {point.get('experiment_title') or ''}",
        f"Video point: {point.get('point_title') or ''}",
        (
            "High-quality evidence must explicitly mention the same reagents, ions, operation, "
            "phenomenon, reaction equation, diagnostic criterion, or principle needed to explain this exact point."
        ),
        (
            "Low-quality evidence: chapter title only, experiment overview only, safety note only, "
            "same-element background without the point reaction, or unrelated same-chapter material."
        ),
    ]
    if point.get("chapter_ids"):
        parts.append("Chapter scope: " + ", ".join(point["chapter_ids"]))
    return "\n".join(part for part in parts if _clean_text(part))


def build_pool_query(point: dict[str, Any], pool: str) -> str:
    if pool == "experiment":
        target = (
            "Rank highest the experimental textbook chunk that directly contains this operation, reagent chain, "
            "observed phenomenon, diagnostic step, or exact experimental procedure for the video point. "
            "Rank generic experiment titles, objectives, safety notes, and unrelated steps very low."
        )
    else:
        target = (
            "Rank highest the theory textbook chunk that directly explains the reaction principle, equation, "
            "redox/acid-base/precipitation/complexation rule, color, or phenomenon for the video point. "
            "Rank same-chapter background, unrelated compounds, uses, broad definitions, and indirect figures very low."
        )
    return "\n".join(
        [
            f"Video point: {point.get('point_title') or ''}",
            f"Experiment: {point.get('experiment_code') or ''} {point.get('experiment_title') or ''}",
            target,
        ]
    )


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.8f}" for value in values) + "]"


def canonical_experiment_candidates(engine: Any, experiment_id: str) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT sc.id AS chunk_id,
                       sc.document_id,
                       sd.file_name AS source_file,
                       sc.chapter_id,
                       sc.page_number,
                       sc.section_title,
                       sc.chunk_index,
                       sc.text,
                       sc.markdown,
                       sc.tags,
                       sc.metadata,
                       efl.confidence AS link_confidence,
                       efl.sort_order AS link_sort_order
                FROM experiment_framework_formal_links efl
                JOIN source_chunks sc ON sc.id = efl.evidence_chunk_id
                LEFT JOIN source_documents sd ON sd.id = sc.document_id
                WHERE efl.experiment_id = :experiment_id
                  AND efl.relation_type = 'canonical_evidence'
                  AND COALESCE(sc.content_status, 'pending_review') = 'published'
                ORDER BY efl.sort_order, sc.id
                """
            ),
            {"experiment_id": experiment_id},
        ).mappings().all()
    candidates = []
    for row in rows:
        item = dict(row)
        item["candidate_source"] = "canonical_experiment_link"
        item["vector_score"] = None
        candidates.append(item)
    return candidates


def vector_recall(
    engine: Any,
    *,
    embedding: list[float],
    collection: str,
    limit: int,
    source: str,
    chapter_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    conditions = [
        "ce.embedding IS NOT NULL",
        "sc.metadata->>'source_collection' = :collection",
        "COALESCE(sc.content_status, 'pending_review') = 'published'",
    ]
    params: dict[str, Any] = {
        "embedding": vector_literal(embedding),
        "collection": collection,
        "limit": max(1, int(limit)),
    }
    stmt = text(
        """
        SELECT sc.id AS chunk_id,
               sc.document_id,
               sd.file_name AS source_file,
               sc.chapter_id,
               sc.page_number,
               sc.section_title,
               sc.chunk_index,
               sc.text,
               sc.markdown,
               sc.tags,
               sc.metadata,
               1 - (ce.embedding <=> CAST(:embedding AS vector)) AS vector_score
        FROM chunk_embeddings ce
        JOIN source_chunks sc ON sc.id = ce.chunk_id
        LEFT JOIN source_documents sd ON sd.id = sc.document_id
        WHERE __CONDITIONS__
        ORDER BY ce.embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
        """.replace("__CONDITIONS__", " AND ".join(conditions))
    )
    if chapter_ids:
        conditions.append("sc.chapter_id IN :chapter_ids")
        stmt = text(
            """
            SELECT sc.id AS chunk_id,
                   sc.document_id,
                   sd.file_name AS source_file,
                   sc.chapter_id,
                   sc.page_number,
                   sc.section_title,
                   sc.chunk_index,
                   sc.text,
                   sc.markdown,
                   sc.tags,
                   sc.metadata,
                   1 - (ce.embedding <=> CAST(:embedding AS vector)) AS vector_score
            FROM chunk_embeddings ce
            JOIN source_chunks sc ON sc.id = ce.chunk_id
            LEFT JOIN source_documents sd ON sd.id = sc.document_id
            WHERE ce.embedding IS NOT NULL
              AND sc.metadata->>'source_collection' = :collection
              AND COALESCE(sc.content_status, 'pending_review') = 'published'
              AND sc.chapter_id IN :chapter_ids
            ORDER BY ce.embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
            """
        ).bindparams(bindparam("chapter_ids", expanding=True))
        params["chapter_ids"] = chapter_ids
    with engine.connect() as connection:
        rows = connection.execute(stmt, params).mappings().all()
    candidates = []
    for row in rows:
        item = dict(row)
        item["candidate_source"] = source
        candidates.append(item)
    return candidates


def experiment_scope_vector_recall(
    engine: Any,
    *,
    experiment_id: str,
    embedding: list[float],
    limit: int,
) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                WITH RECURSIVE scope_nodes AS (
                  SELECT n.id
                  FROM experiment_framework_formal_links efl
                  JOIN experiment_framework_nodes n ON n.id = efl.node_id
                  WHERE efl.experiment_id = :experiment_id
                    AND efl.relation_type = 'formal_parent_title'
                  UNION ALL
                  SELECT child.id
                  FROM experiment_framework_nodes child
                  JOIN scope_nodes parent ON child.parent_id = parent.id
                ),
                scope_chunks AS (
                  SELECT DISTINCT link.chunk_id
                  FROM experiment_framework_chunk_links link
                  WHERE link.node_id IN (SELECT id FROM scope_nodes)
                )
                SELECT sc.id AS chunk_id,
                       sc.document_id,
                       sd.file_name AS source_file,
                       sc.chapter_id,
                       sc.page_number,
                       sc.section_title,
                       sc.chunk_index,
                       sc.text,
                       sc.markdown,
                       sc.tags,
                       sc.metadata,
                       1 - (ce.embedding <=> CAST(:embedding AS vector)) AS vector_score
                FROM scope_chunks scoped
                JOIN chunk_embeddings ce ON ce.chunk_id = scoped.chunk_id
                JOIN source_chunks sc ON sc.id = ce.chunk_id
                LEFT JOIN source_documents sd ON sd.id = sc.document_id
                WHERE ce.embedding IS NOT NULL
                  AND COALESCE(sc.content_status, 'pending_review') = 'published'
                ORDER BY ce.embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
                """
            ),
            {
                "experiment_id": experiment_id,
                "embedding": vector_literal(embedding),
                "limit": max(1, int(limit)),
            },
        ).mappings().all()
    candidates = []
    for row in rows:
        item = dict(row)
        item["candidate_source"] = "experiment_vector_scope"
        candidates.append(item)
    return candidates


def merge_candidates(candidate_groups: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for group in candidate_groups:
        for item in group:
            chunk_id = str(item.get("chunk_id") or "")
            if not chunk_id:
                continue
            existing = by_id.get(chunk_id)
            source = item.get("candidate_source")
            if existing is None:
                merged = dict(item)
                merged["candidate_sources"] = [source] if source else []
                by_id[chunk_id] = merged
                continue
            if source and source not in existing["candidate_sources"]:
                existing["candidate_sources"].append(source)
            current_score = item.get("vector_score")
            existing_score = existing.get("vector_score")
            if current_score is not None and (
                existing_score is None or float(current_score) > float(existing_score)
            ):
                existing["vector_score"] = float(current_score)
    return sorted(
        by_id.values(),
        key=lambda item: (
            float(item.get("vector_score") or -1.0),
            str(item.get("chunk_id") or ""),
        ),
        reverse=True,
    )


def rerank_candidates(
    *,
    bge_url: str,
    query: str,
    candidates: list[dict[str, Any]],
    batch_size: int,
    timeout: float,
) -> list[dict[str, Any]]:
    documents = [_chunk_document(item) for item in candidates]
    valid_indices = [index for index, document in enumerate(documents) if document]
    valid_documents = [documents[index] for index in valid_indices]
    scores = rerank_documents(bge_url, query, valid_documents, batch_size=batch_size, timeout=timeout)
    for index, score in zip(valid_indices, scores, strict=False):
        candidates[index]["rerank_score"] = float(score)
    for item in candidates:
        item.setdefault("rerank_score", None)
    return sorted(
        candidates,
        key=lambda item: (
            float(item.get("rerank_score") if item.get("rerank_score") is not None else -1.0),
            float(item.get("vector_score") if item.get("vector_score") is not None else -1.0),
        ),
        reverse=True,
    )


def add_direct_evidence_scores(point: dict[str, Any], pool: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    terms = evidence_terms(point.get("point_title") or "")
    formula_terms = [term["term"] for term in terms if term["kind"] == "formula"]
    formula_count = len(formula_terms)
    specific_terms = {term["term"] for term in terms if term["kind"] == "text" and term["term"] in SPECIFIC_TEXT_TERMS}
    theory_required_terms = specific_terms & THEORY_REQUIRED_SPECIFIC_TERMS
    for item in candidates:
        metadata = _metadata_dict(item.get("metadata"))
        content_type = str(metadata.get("content_type") or "")
        section_title = str(item.get("section_title") or "")
        weak_experiment_section = any(marker in section_title for marker in GENERIC_EXPERIMENT_SECTION_MARKERS)
        document = _chunk_document(item)
        matched_terms, formula_hits, text_hits = _document_match_terms(document, terms, pool)
        matched_set = set(matched_terms)
        specific_text_hits = len(matched_set & specific_terms)
        required_specific_hit = bool(matched_set & theory_required_terms)
        generic_text_hits = max(0, text_hits - specific_text_hits)
        primary_formula_hit = bool(formula_terms and formula_terms[0] in matched_set)
        formula_sufficient = False
        if formula_count == 1:
            formula_sufficient = formula_hits >= 1
        elif formula_count > 1:
            formula_sufficient = formula_hits >= 2 or primary_formula_hit
        directness_score = min(
            1.0,
            min(0.55, formula_hits * 0.28)
            + min(0.35, specific_text_hits * 0.25)
            + min(0.12, generic_text_hits * 0.04),
        )
        rerank_score = float(item.get("rerank_score") if item.get("rerank_score") is not None else 0.0)
        generic_penalty = 0.0
        if pool == "experiment" and (
            content_type in GENERIC_EXPERIMENT_TYPES or weak_experiment_section
        ) and (formula_hits + specific_text_hits) < 2:
            generic_penalty = 0.55
        if pool == "theory" and content_type in WEAK_THEORY_TYPES and (formula_hits + specific_text_hits) < 2:
            generic_penalty = 0.35
        if pool == "theory" and content_type == "figure" and (formula_hits + specific_text_hits) < 2:
            generic_penalty = 0.2
        evidence_score = max(0.0, rerank_score * 0.6 + directness_score * 0.4 - generic_penalty)
        if pool == "experiment":
            if formula_count:
                direct_evidence = formula_sufficient or (
                    formula_hits >= 1 and rerank_score >= 0.65 and content_type not in GENERIC_EXPERIMENT_TYPES
                )
            else:
                direct_evidence = specific_text_hits >= 1 or (generic_text_hits >= 2 and rerank_score >= 0.7)
            direct_evidence = direct_evidence and not (
                (content_type in GENERIC_EXPERIMENT_TYPES or weak_experiment_section)
                and (formula_hits + specific_text_hits) < 2
            )
            if formula_count and rerank_score < 0.3:
                direct_evidence = False
            threshold = 0.2 if specific_text_hits and not formula_count else 0.28
        else:
            if formula_count:
                direct_evidence = formula_sufficient or (formula_hits >= 1 and specific_text_hits >= 1)
            else:
                direct_evidence = specific_text_hits >= 1 or (generic_text_hits >= 2 and rerank_score >= 0.75)
            if theory_required_terms and not required_specific_hit:
                direct_evidence = False
            if content_type in WEAK_THEORY_TYPES and (formula_hits + specific_text_hits) < 2:
                direct_evidence = False
            threshold = 0.25
        item["evidence_terms"] = [term["term"] for term in terms]
        item["direct_match_terms"] = matched_terms
        item["directness_score"] = round(directness_score, 6)
        item["evidence_score"] = round(evidence_score, 6)
        item["direct_evidence"] = bool(direct_evidence and evidence_score >= threshold)
    return sorted(
        candidates,
        key=lambda item: (
            bool(item.get("direct_evidence")),
            float(item.get("evidence_score") or 0.0),
            float(item.get("rerank_score") if item.get("rerank_score") is not None else -1.0),
            float(item.get("vector_score") if item.get("vector_score") is not None else -1.0),
        ),
        reverse=True,
    )


def select_default_chunk_ids(candidates: list[dict[str, Any]], limit: int) -> list[str]:
    selected: list[str] = []
    for item in candidates:
        if not item.get("direct_evidence"):
            continue
        chunk_id = item.get("chunk_id")
        if chunk_id:
            selected.append(str(chunk_id))
        if len(selected) >= limit:
            break
    return selected


def raw_candidate_record(
    point: dict[str, Any],
    pool: str,
    rank: int,
    item: dict[str, Any],
    selected: bool,
) -> dict[str, Any]:
    metadata = _metadata_dict(item.get("metadata"))
    return {
        "experiment_id": point["experiment_id"],
        "experiment_code": point.get("experiment_code"),
        "point_key": point["point_key"],
        "point_title": point["point_title"],
        "pool": pool,
        "rank": rank,
        "selected_default": selected,
        "chunk_id": item.get("chunk_id"),
        "candidate_sources": item.get("candidate_sources") or [item.get("candidate_source")],
        "vector_score": item.get("vector_score"),
        "rerank_score": item.get("rerank_score"),
        "direct_evidence": item.get("direct_evidence"),
        "directness_score": item.get("directness_score"),
        "evidence_score": item.get("evidence_score"),
        "evidence_terms": item.get("evidence_terms"),
        "direct_match_terms": item.get("direct_match_terms"),
        "source_file": item.get("source_file"),
        "chapter_id": item.get("chapter_id"),
        "page_number": item.get("page_number"),
        "section_title": item.get("section_title"),
        "content_type": metadata.get("content_type"),
        "source_collection": metadata.get("source_collection"),
        "text": item.get("text"),
        "markdown": item.get("markdown"),
        "metadata": metadata,
    }


def compact_candidate(item: dict[str, Any]) -> dict[str, Any]:
    metadata = _metadata_dict(item.get("metadata"))
    return {
        "chunk_id": item.get("chunk_id"),
        "vector_score": item.get("vector_score"),
        "rerank_score": item.get("rerank_score"),
        "candidate_sources": item.get("candidate_sources") or [item.get("candidate_source")],
        "source_file": item.get("source_file"),
        "chapter_id": item.get("chapter_id"),
        "page_number": item.get("page_number"),
        "section_title": item.get("section_title"),
        "content_type": metadata.get("content_type"),
        "direct_evidence": item.get("direct_evidence"),
        "directness_score": item.get("directness_score"),
        "evidence_score": item.get("evidence_score"),
        "direct_match_terms": item.get("direct_match_terms"),
        "text_preview": _chunk_document(item)[:260],
    }


def write_summary(
    output_dir: Path,
    *,
    manifest: dict[str, Any],
    point_records: list[dict[str, Any]],
    spot_experiment_ids: set[str],
) -> None:
    lines = [
        "# Video Point Default Evidence Spike",
        "",
        f"- Run ID: `{manifest['run_id']}`",
        f"- Points processed: {manifest['point_count']}",
        f"- BGE URL: `{manifest['bge_url']}`",
        f"- Experiment final top k: {manifest['config']['experiment_final_top_k']}",
        f"- Theory final top k: {manifest['config']['theory_final_top_k']}",
        f"- Raw candidate rows: {manifest['raw_candidate_count']}",
        "",
        "## Spot Checks",
        "",
    ]
    for record in point_records:
        if record["experiment_id"] not in spot_experiment_ids:
            continue
        lines.extend(
            [
                f"### {record['experiment_code']} / {record['point_key']}",
                "",
                f"- Point: {record['point_title']}",
                f"- Experiment chunks: {', '.join(record['default_experiment_chunk_ids'][:8]) or '-'}",
                f"- Theory chunks: {', '.join(record['default_theory_chunk_ids'][:8]) or '-'}",
                "- Top experiment candidates:",
            ]
        )
        for item in record["experiment_reranked_top"][:5]:
            lines.append(
                f"  - `{item['chunk_id']}` rerank={item.get('rerank_score')} evidence={item.get('evidence_score')} "
                f"direct={item.get('direct_evidence')} matches={item.get('direct_match_terms')} "
                f"type={item.get('content_type')} page={item.get('page_number')} - {item.get('text_preview')}"
            )
        lines.append("- Top theory candidates:")
        for item in record["theory_reranked_top"][:5]:
            lines.append(
                f"  - `{item['chunk_id']}` rerank={item.get('rerank_score')} evidence={item.get('evidence_score')} "
                f"direct={item.get('direct_evidence')} matches={item.get('direct_match_terms')} "
                f"type={item.get('content_type')} page={item.get('page_number')} - {item.get('text_preview')}"
            )
        lines.append("")
    output_dir.joinpath("summary.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate retired temporary default evidence chunks for legacy video points.")
    parser.add_argument(
        "--allow-retired-legacy-workflow",
        action="store_true",
        help="Explicitly run the retired experiment_id + point_key workflow for historical recovery only.",
    )
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    parser.add_argument("--bge-url", default=DEFAULT_BGE_URL)
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/video-point-default-evidence"))
    parser.add_argument("--run-id", default=_utc_run_id())
    parser.add_argument("--experiment-id", action="append", default=[])
    parser.add_argument("--spot-only", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--experiment-vector-top-k", type=int, default=80)
    parser.add_argument("--theory-chapter-top-k", type=int, default=100)
    parser.add_argument("--theory-global-top-k", type=int, default=40)
    parser.add_argument("--experiment-final-top-k", type=int, default=12)
    parser.add_argument("--theory-final-top-k", type=int, default=20)
    parser.add_argument("--rerank-batch-size", type=int, default=8)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.allow_retired_legacy_workflow:
        raise SystemExit(
            "This legacy video-point evidence workflow is retired. "
            "Use scripts/generate_catalog_node_default_evidence.py for catalog-node evidence planning, "
            "then run the future GPU/BGE rerank job against catalog_node_id or catalog_seed_key."
        )
    if args.rerank_batch_size < 1 or args.rerank_batch_size > 64:
        raise ValueError("--rerank-batch-size must be between 1 and 64")
    experiment_ids = set(args.experiment_id)
    if args.spot_only:
        experiment_ids.update(SPOT_EXPERIMENT_IDS)

    output_dir = args.output_root / args.run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(args.database_url)
    bge_health = _get_json(args.bge_url, "/health", args.timeout_seconds)
    points = load_points(engine, experiment_ids, args.limit)

    started_at = time.perf_counter()
    point_records: list[dict[str, Any]] = []
    raw_candidate_count = 0
    point_path = output_dir / "point_default_evidence.jsonl"
    raw_path = output_dir / "raw_candidates.jsonl"

    with point_path.open("w", encoding="utf-8") as point_handle, raw_path.open("w", encoding="utf-8") as raw_handle:
        for index, point in enumerate(points, start=1):
            query = build_query(point)
            embedding = embed_query(args.bge_url, query, args.timeout_seconds)
            experiment_candidates = merge_candidates(
                [
                    canonical_experiment_candidates(engine, point["experiment_id"]),
                    experiment_scope_vector_recall(
                        engine,
                        experiment_id=point["experiment_id"],
                        embedding=embedding,
                        limit=args.experiment_vector_top_k,
                    ),
                ]
            )
            theory_groups = [
                vector_recall(
                    engine,
                    embedding=embedding,
                    collection=THEORY_COLLECTION,
                    limit=args.theory_global_top_k,
                    source="theory_vector_global",
                )
            ]
            if point.get("chapter_ids"):
                theory_groups.append(
                    vector_recall(
                        engine,
                        embedding=embedding,
                        collection=THEORY_COLLECTION,
                        limit=args.theory_chapter_top_k,
                        source="theory_vector_chapter",
                        chapter_ids=point["chapter_ids"],
                    )
                )
            theory_candidates = merge_candidates(theory_groups)
            experiment_reranked = rerank_candidates(
                bge_url=args.bge_url,
                query=build_pool_query(point, "experiment"),
                candidates=experiment_candidates,
                batch_size=args.rerank_batch_size,
                timeout=args.timeout_seconds,
            )
            theory_reranked = rerank_candidates(
                bge_url=args.bge_url,
                query=build_pool_query(point, "theory"),
                candidates=theory_candidates,
                batch_size=args.rerank_batch_size,
                timeout=args.timeout_seconds,
            )
            experiment_reranked = add_direct_evidence_scores(point, "experiment", experiment_reranked)
            theory_reranked = add_direct_evidence_scores(point, "theory", theory_reranked)
            default_experiment = select_default_chunk_ids(experiment_reranked, args.experiment_final_top_k)
            default_theory = select_default_chunk_ids(theory_reranked, args.theory_final_top_k)
            point_record = {
                **point,
                "evidence_mode": "direct-v2",
                "evidence_terms": [term["term"] for term in evidence_terms(point.get("point_title") or "")],
                "query_text": query,
                "default_experiment_chunk_ids": default_experiment,
                "default_theory_chunk_ids": default_theory,
                "experiment_candidate_count": len(experiment_reranked),
                "theory_candidate_count": len(theory_reranked),
                "experiment_reranked_top": [compact_candidate(item) for item in experiment_reranked[:20]],
                "theory_reranked_top": [compact_candidate(item) for item in theory_reranked[:30]],
            }
            point_handle.write(_json_dumps(point_record) + "\n")
            point_records.append(point_record)
            experiment_selected = set(default_experiment)
            theory_selected = set(default_theory)
            for rank, item in enumerate(experiment_reranked, start=1):
                raw_handle.write(
                    _json_dumps(
                        raw_candidate_record(point, "experiment", rank, item, str(item.get("chunk_id")) in experiment_selected)
                    )
                    + "\n"
                )
                raw_candidate_count += 1
            for rank, item in enumerate(theory_reranked, start=1):
                raw_handle.write(
                    _json_dumps(raw_candidate_record(point, "theory", rank, item, str(item.get("chunk_id")) in theory_selected))
                    + "\n"
                )
                raw_candidate_count += 1
            if index % 10 == 0 or index == len(points):
                print(f"processed {index}/{len(points)} points", flush=True)

    manifest = {
        "run_id": args.run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.perf_counter() - started_at, 2),
        "database_url": args.database_url,
        "bge_url": args.bge_url,
        "bge_health": bge_health,
        "point_count": len(point_records),
        "raw_candidate_count": raw_candidate_count,
        "evidence_mode": "direct-v2",
        "output_files": {
            "point_default_evidence": str(point_path),
            "raw_candidates": str(raw_path),
            "summary": str(output_dir / "summary.md"),
        },
        "config": {
            "evidence_mode": "direct-v2",
            "experiment_vector_top_k": args.experiment_vector_top_k,
            "theory_chapter_top_k": args.theory_chapter_top_k,
            "theory_global_top_k": args.theory_global_top_k,
            "experiment_final_top_k": args.experiment_final_top_k,
            "theory_final_top_k": args.theory_final_top_k,
            "rerank_batch_size": args.rerank_batch_size,
            "timeout_seconds": args.timeout_seconds,
            "experiment_ids": sorted(experiment_ids),
        },
    }
    (output_dir / "manifest.json").write_text(_json_dumps(manifest) + "\n", encoding="utf-8")
    write_summary(output_dir, manifest=manifest, point_records=point_records, spot_experiment_ids=SPOT_EXPERIMENT_IDS)
    print(_json_dumps(manifest))


if __name__ == "__main__":
    main()

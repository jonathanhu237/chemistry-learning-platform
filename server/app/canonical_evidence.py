from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from sqlalchemy import text

from server.app.retrieval import keyword_score


CANONICAL_SOURCE_ROLE = "canonical_textbook"
EXPERIMENT_SOURCE_COLLECTION = "textbook_experiment_clean_v1"


def _json_value(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value


def _preview(text_value: str | None, markdown: str | None, limit: int = 360) -> str:
    text_source = text_value or markdown or ""
    return " ".join(text_source.split())[:limit]


def _source_ref_from_row(row: dict[str, Any]) -> dict[str, Any]:
    metadata = _json_value(row.get("metadata"), {})
    section_path = metadata.get("section_path") or []
    if not isinstance(section_path, list):
        section_path = [str(section_path)]
    page_start = metadata.get("page_start") or row.get("page_number")
    page_end = metadata.get("page_end") or page_start
    book_title = metadata.get("book_title") or row.get("source_file") or row.get("document_id")
    section_title = row.get("section_title") or " / ".join(str(item) for item in section_path if str(item).strip())
    return {
        "chunk_id": row.get("chunk_id") or row.get("id"),
        "source_file": book_title,
        "book_title": book_title,
        "document_id": row.get("document_id"),
        "source_collection": metadata.get("source_collection"),
        "source_role": metadata.get("source_role"),
        "authority_level": metadata.get("authority_level"),
        "content_type": metadata.get("content_type"),
        "chapter_id": row.get("chapter_id"),
        "page_number": page_start,
        "page_start": page_start,
        "page_end": page_end,
        "section_title": section_title,
        "section_path": section_path,
        "text_preview": _preview(row.get("text"), row.get("markdown")),
    }


def canonical_chunk_rows_by_ids(session: Any, chunk_ids: Iterable[str]) -> list[dict[str, Any]]:
    ordered_ids = [str(item) for item in chunk_ids if str(item).strip()]
    if not ordered_ids:
        return []
    rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT sc.id AS chunk_id,
                       sc.document_id,
                       sd.file_name AS source_file,
                       sc.chapter_id,
                       sc.page_number,
                       sc.section_title,
                       sc.text,
                       sc.markdown,
                       sc.related_knowledge_point_ids,
                       sc.related_experiment_ids,
                       sc.tags,
                       sc.metadata,
                       sc.content_status
                FROM source_chunks sc
                JOIN source_documents sd ON sd.id = sc.document_id
                WHERE sc.id = ANY(:chunk_ids)
                  AND COALESCE(sc.metadata->>'source_role', '') = :source_role
                  AND COALESCE(sc.content_status, 'pending_review') = 'published'
                  AND sd.publication_status = 'published'
                """
            ),
            {"chunk_ids": ordered_ids, "source_role": CANONICAL_SOURCE_ROLE},
        )
        .mappings()
        .all()
    ]
    by_id = {str(row["chunk_id"]): row for row in rows}
    return [by_id[chunk_id] for chunk_id in ordered_ids if chunk_id in by_id]


def missing_canonical_chunk_ids(session: Any, chunk_ids: Iterable[str]) -> list[str]:
    requested = [str(item) for item in chunk_ids if str(item).strip()]
    if not requested:
        return []
    found = {
        str(row["id"])
        for row in session.execute(
            text(
                """
                SELECT sc.id
                FROM source_chunks sc
                JOIN source_documents sd ON sd.id = sc.document_id
                WHERE sc.id = ANY(:chunk_ids)
                  AND COALESCE(sc.metadata->>'source_role', '') = :source_role
                  AND COALESCE(sc.content_status, 'pending_review') = 'published'
                  AND sd.publication_status = 'published'
                """
            ),
            {"chunk_ids": requested, "source_role": CANONICAL_SOURCE_ROLE},
        )
        .mappings()
        .all()
    }
    return [chunk_id for chunk_id in requested if chunk_id not in found]


def resolve_source_refs(session: Any, chunk_ids: Iterable[str]) -> list[dict[str, Any]]:
    return [_source_ref_from_row(row) for row in canonical_chunk_rows_by_ids(session, chunk_ids)]


def _load_candidate_rows(
    session: Any,
    *,
    chapter_ids: list[str],
    experiment_id: str | None,
    limit: int,
    allow_unscoped: bool,
) -> list[dict[str, Any]]:
    filters = [
        "COALESCE(sc.content_status, 'pending_review') = 'published'",
        "sd.publication_status = 'published'",
        "COALESCE(sc.metadata->>'source_role', '') = :source_role",
    ]
    params: dict[str, Any] = {"source_role": CANONICAL_SOURCE_ROLE, "limit": limit}
    scoped_filters: list[str] = []
    if chapter_ids:
        scoped_filters.append("sc.chapter_id = ANY(:chapter_ids)")
        params["chapter_ids"] = chapter_ids
    if experiment_id:
        scoped_filters.append(":experiment_id = ANY(sc.related_experiment_ids)")
        params["experiment_id"] = experiment_id
    if scoped_filters:
        filters.append("(" + " OR ".join(scoped_filters) + ")")
    elif not allow_unscoped:
        return []

    rows = [
        dict(row)
        for row in session.execute(
            text(
                f"""
                SELECT sc.id AS chunk_id,
                       sc.document_id,
                       sd.file_name AS source_file,
                       sc.chapter_id,
                       sc.page_number,
                       sc.section_title,
                       sc.text,
                       sc.markdown,
                       sc.related_knowledge_point_ids,
                       sc.related_experiment_ids,
                       sc.tags,
                       sc.metadata,
                       sc.content_status
                FROM source_chunks sc
                JOIN source_documents sd ON sd.id = sc.document_id
                WHERE {" AND ".join(filters)}
                ORDER BY sc.document_id, sc.chunk_index, sc.id
                LIMIT :limit
                """
            ),
            params,
        )
        .mappings()
        .all()
    ]
    return rows


def load_evidence_source_refs(
    session: Any,
    *,
    prompt: str,
    experiment: dict[str, Any] | None = None,
    chapter_ids: list[str] | None = None,
    knowledge_point_ids: list[str] | None = None,
    limit: int = 6,
) -> list[dict[str, Any]]:
    chapter_ids = [str(item) for item in (chapter_ids or []) if str(item).strip()]
    knowledge_point_ids = [str(item) for item in (knowledge_point_ids or []) if str(item).strip()]
    experiment_id = str((experiment or {}).get("id") or (experiment or {}).get("experiment_id") or "").strip() or None
    query = " ".join(
        item
        for item in [
            prompt,
            str((experiment or {}).get("title") or ""),
            str((experiment or {}).get("summary") or ""),
        ]
        if item
    )
    rows = _load_candidate_rows(
        session,
        chapter_ids=chapter_ids,
        experiment_id=experiment_id,
        limit=800,
        allow_unscoped=False,
    )
    if not rows:
        rows = _load_candidate_rows(
            session,
            chapter_ids=chapter_ids,
            experiment_id=None,
            limit=800,
            allow_unscoped=bool(chapter_ids),
        )
    if not rows and experiment_id:
        rows = _load_candidate_rows(
            session,
            chapter_ids=[],
            experiment_id=experiment_id,
            limit=800,
            allow_unscoped=False,
        )
    if not rows:
        return []

    def score(row: dict[str, Any]) -> float:
        metadata = _json_value(row.get("metadata"), {})
        base = keyword_score(query, {"text": row.get("text") or row.get("markdown") or ""}, chapter_id=row.get("chapter_id"))
        if experiment_id and experiment_id in (row.get("related_experiment_ids") or []):
            base += 0.25
        if metadata.get("source_collection") == EXPERIMENT_SOURCE_COLLECTION:
            base += 0.04
        if knowledge_point_ids and set(knowledge_point_ids).intersection(row.get("related_knowledge_point_ids") or []):
            base += 0.12
        return base

    rows.sort(key=score, reverse=True)
    return [_source_ref_from_row(row) for row in rows[:limit]]

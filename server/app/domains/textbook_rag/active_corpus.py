from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any, Iterable

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings


@dataclass(frozen=True)
class ActiveTextbookDocument:
    document_id: str
    logical_textbook_key: str
    document_version: int
    document_kind: str
    source_collection: str
    index_document_id: str = ""
    projection_run_id: str = ""


@dataclass(frozen=True)
class ActiveTextbookCorpus:
    documents: tuple[ActiveTextbookDocument, ...] = ()
    revision: int = 0
    load_error: str = ""


def _mapping_rows(result: Any) -> list[Any]:
    try:
        return list(result.mappings().all())
    except (AttributeError, TypeError):
        try:
            row = result.mappings().first()
        except (AttributeError, TypeError):
            return []
        return [row] if row else []


def load_active_textbook_corpus(session: Any | None = None) -> ActiveTextbookCorpus:
    """Load the published textbook projection allow-list from PostgreSQL.

    A database/configuration failure deliberately returns an empty corpus. Retrieval
    then emits ``match_none`` instead of falling back to every document in the index.
    """

    if session is None and get_settings().data_backend != "postgres":
        return ActiveTextbookCorpus(load_error="postgres_data_backend_required")

    context = nullcontext(session) if session is not None else db_session()
    try:
        with context as active_session:
            rows = _mapping_rows(
                active_session.execute(
                    text(
                        """
                        SELECT sd.id, sd.logical_textbook_key, sd.version_number,
                               sd.document_kind, sd.metadata,
                               sd.active_projection_run_id, state.revision
                        FROM textbook_corpus_state state
                        LEFT JOIN source_documents sd
                          ON sd.publication_status = 'published'
                         AND sd.document_kind IN ('textbook', 'canonical_textbook')
                        WHERE state.singleton_key = 1
                        ORDER BY sd.logical_textbook_key, sd.version_number, sd.id
                        """
                    )
                )
            )
            documents: list[ActiveTextbookDocument] = []
            revision = max(
                (max(0, int(row.get("revision") or 0)) for row in rows),
                default=0,
            )
            for row in rows:
                document_id = str(row.get("id") or "").strip()
                logical_key = str(row.get("logical_textbook_key") or "").strip()
                document_kind = str(row.get("document_kind") or "").strip()
                if not document_id or not logical_key or document_kind not in {"textbook", "canonical_textbook"}:
                    continue
                metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
                source_collection = str(metadata.get("source_collection") or logical_key).strip()
                index_document_id = (
                    str(metadata.get("index_document_id") or "").strip()
                    if document_kind == "canonical_textbook"
                    else document_id
                )
                documents.append(
                    ActiveTextbookDocument(
                        document_id=document_id,
                        logical_textbook_key=logical_key,
                        document_version=max(1, int(row.get("version_number") or 1)),
                        document_kind=document_kind,
                        source_collection=source_collection,
                        index_document_id=index_document_id,
                        projection_run_id=(
                            str(row.get("active_projection_run_id") or "").strip()
                            if document_kind == "textbook"
                            else ""
                        ),
                    )
                )
            return ActiveTextbookCorpus(
                documents=tuple(documents),
                revision=revision,
            )
    except (SQLAlchemyError, AttributeError, TypeError, ValueError) as exc:
        return ActiveTextbookCorpus(load_error=exc.__class__.__name__)


def active_textbook_filter(documents: Iterable[ActiveTextbookDocument]) -> dict[str, Any]:
    clauses: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for document in documents:
        # ``source_collection`` is deliberately not an activation discriminator:
        # staged online versions share it with the canonical seed. ``doc_id`` is
        # the immutable ES generation identity (the upload document id for online
        # versions, and an explicitly registered seed id for legacy documents).
        index_document_id = document.index_document_id
        key = (index_document_id, document.document_version)
        if not index_document_id or key in seen:
            continue
        seen.add(key)
        filters: list[dict[str, Any]] = [{"term": {"doc_id": index_document_id}}]
        if document.document_kind == "textbook":
            if not document.projection_run_id:
                # A published online row without its durable generation is not
                # safe to retrieve; recovery can rebuild and register it.
                continue
            filters.extend(
                [
                    {"term": {"document_version": document.document_version}},
                    {"term": {"projection_run_id": document.projection_run_id}},
                ]
            )
        clauses.append(
            {
                "bool": {
                    "filter": filters
                }
            }
        )
    if not clauses:
        return {"match_none": {}}
    return {"bool": {"should": clauses, "minimum_should_match": 1}}


def corpus_from_settings(settings: dict[str, Any]) -> ActiveTextbookCorpus:
    configured = settings.get("_active_textbook_corpus")
    if isinstance(configured, ActiveTextbookCorpus):
        return configured
    return load_active_textbook_corpus()


def settings_with_active_textbook_corpus(
    settings: dict[str, Any],
    *,
    session: Any | None = None,
) -> dict[str, Any]:
    corpus = load_active_textbook_corpus(session)
    return {
        **settings,
        "corpus_revision": corpus.revision,
        "_active_textbook_corpus": corpus,
    }

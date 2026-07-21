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

    @property
    def is_legacy_seed(self) -> bool:
        return self.document_kind == "canonical_textbook"


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


def _current_revision(session: Any) -> int:
    registry_row = (
        session.execute(
            text("SELECT to_regclass('public.textbook_corpus_state')::text AS table_name")
        )
        .mappings()
        .first()
    )
    if not registry_row or not registry_row.get("table_name"):
        return 0
    revision_row = (
        session.execute(
            text(
                """
                SELECT revision
                FROM textbook_corpus_state
                ORDER BY revision DESC
                LIMIT 1
                """
            )
        )
        .mappings()
        .first()
    )
    return max(0, int((revision_row or {}).get("revision") or 0))


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
                        SELECT id, logical_textbook_key, version_number,
                               document_kind, metadata
                        FROM source_documents
                        WHERE publication_status = 'published'
                          AND document_kind IN ('textbook', 'canonical_textbook')
                        ORDER BY logical_textbook_key, version_number, id
                        """
                    )
                )
            )
            documents: list[ActiveTextbookDocument] = []
            for row in rows:
                document_id = str(row.get("id") or "").strip()
                logical_key = str(row.get("logical_textbook_key") or "").strip()
                document_kind = str(row.get("document_kind") or "").strip()
                if not document_id or not logical_key or document_kind not in {"textbook", "canonical_textbook"}:
                    continue
                metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
                source_collection = str(metadata.get("source_collection") or logical_key).strip()
                documents.append(
                    ActiveTextbookDocument(
                        document_id=document_id,
                        logical_textbook_key=logical_key,
                        document_version=max(1, int(row.get("version_number") or 1)),
                        document_kind=document_kind,
                        source_collection=source_collection,
                    )
                )
            return ActiveTextbookCorpus(
                documents=tuple(documents),
                revision=_current_revision(active_session),
            )
    except (SQLAlchemyError, AttributeError, TypeError, ValueError) as exc:
        return ActiveTextbookCorpus(load_error=exc.__class__.__name__)


def active_textbook_filter(documents: Iterable[ActiveTextbookDocument]) -> dict[str, Any]:
    clauses: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for document in documents:
        if document.is_legacy_seed:
            field, value = "source_collection", document.source_collection
        else:
            # Online generations share source_collection with the legacy seed.
            # document_id is therefore the only safe discriminator for an upload.
            field, value = "document_id", document.document_id
        key = (field, value)
        if not value or key in seen:
            continue
        seen.add(key)
        clauses.append({"term": {field: value}})
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

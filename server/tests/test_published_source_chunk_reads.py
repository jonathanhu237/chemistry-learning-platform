from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from server.app import canonical_evidence, experiment_framework, repositories
from server.app.domains.catalog_tree import ai_context


def _normalized(statement: Any) -> str:
    return " ".join(str(statement).split())


def _assert_published_chunk_and_parent(statement: Any, *, optional_parent: bool = False) -> None:
    sql = _normalized(statement)
    assert "source_documents sd ON sd.id = sc.document_id" in sql
    if not optional_parent:
        assert "LEFT JOIN source_documents sd" not in sql
    assert "COALESCE(sc.content_status, 'pending_review') = 'published'" in sql
    assert "sd.publication_status = 'published'" in sql


class _EmptyResult:
    def mappings(self) -> "_EmptyResult":
        return self

    def all(self) -> list[dict[str, Any]]:
        return []

    def scalar(self) -> int:
        return 0

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(())


class _RecordingSession:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def execute(self, statement: Any, params: dict[str, Any] | None = None) -> _EmptyResult:
        self.statements.append(str(statement))
        return _EmptyResult()


def test_postgres_repository_filters_source_chunk_reads_by_published_parent(monkeypatch: Any) -> None:
    statements: list[str] = []

    def record_rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        statements.append(sql)
        return []

    monkeypatch.setattr(repositories, "_rows", record_rows)
    repository = repositories.PostgresContentRepository()

    assert repository.source_chunks() == []
    assert repository.related_chunks_for_kp("KP-1") == []

    assert len(statements) == 3
    for statement in statements:
        _assert_published_chunk_and_parent(statement)
        sql = _normalized(statement)
        assert "sd.document_kind =" not in sql
        assert "sd.document_kind IN" not in sql


def test_canonical_evidence_filters_direct_lookup_missing_check_and_candidates() -> None:
    session = _RecordingSession()

    assert canonical_evidence.canonical_chunk_rows_by_ids(session, ["chunk-1"]) == []
    assert canonical_evidence.missing_canonical_chunk_ids(session, ["chunk-1"]) == ["chunk-1"]
    assert (
        canonical_evidence._load_candidate_rows(
            session,
            chapter_ids=["chapter-1"],
            experiment_id=None,
            limit=5,
            allow_unscoped=False,
        )
        == []
    )

    assert len(session.statements) == 3
    for statement in session.statements:
        _assert_published_chunk_and_parent(statement)


def test_static_evidence_hydration_requires_published_chunk_parent() -> None:
    session = _RecordingSession()

    assert ai_context._evidence_binding_rows(session, node_id="cat-point-1") == []

    assert len(session.statements) == 1
    statement = _normalized(session.statements[0])
    _assert_published_chunk_and_parent(statement)
    assert "WHERE ( b.node_id = :node_id OR" in statement
    assert ") AND COALESCE(sc.content_status" in statement


def test_experiment_framework_excludes_inactive_chunk_evidence_but_keeps_unscoped_formal_links() -> None:
    session = _RecordingSession()

    assert experiment_framework._load_chunk_links(session) == {}
    assert experiment_framework._load_formal_links(session) == []
    assert experiment_framework._count_source_chunks(session) == 0

    assert len(session.statements) == 3
    chunk_links, formal_links, chunk_count = map(_normalized, session.statements)
    _assert_published_chunk_and_parent(chunk_links)
    _assert_published_chunk_and_parent(formal_links, optional_parent=True)
    _assert_published_chunk_and_parent(chunk_count)
    assert "l.evidence_chunk_id IS NULL OR" in formal_links
    assert "LEFT JOIN source_documents sd ON sd.id = sc.document_id" in formal_links

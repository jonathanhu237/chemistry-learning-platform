from __future__ import annotations

from pathlib import Path


MIGRATION = Path("server/migrations/041_online_textbook_ingestion.sql")


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def test_online_textbook_migration_preserves_seed_documents_as_published_versions() -> None:
    sql = _sql()

    assert "logical_textbook_key = COALESCE" in sql
    assert "metadata->>'source_collection'" in sql
    assert "publication_status = COALESCE(publication_status, 'published')" in sql
    assert "idx_source_documents_one_published_version" in sql
    assert "WHERE publication_status = 'published'" in sql


def test_online_textbook_migration_adds_fenced_job_queue_and_page_facts() -> None:
    sql = _sql()

    assert "CREATE TABLE IF NOT EXISTS textbook_ingestion_jobs" in sql
    assert "lease_token uuid" in sql
    assert "lease_expires_at timestamptz" in sql
    assert "run_after timestamptz NOT NULL DEFAULT now()" in sql
    assert "idempotency_key text NOT NULL" in sql
    assert "idx_textbook_ingestion_jobs_one_open" in sql
    assert "CREATE TABLE IF NOT EXISTS textbook_document_pages" in sql
    assert "PRIMARY KEY (document_id, page_number)" in sql
    assert "CREATE TABLE IF NOT EXISTS textbook_ingestion_job_events" in sql


def test_online_textbook_migration_does_not_remove_postgres_embeddings_yet() -> None:
    sql = _sql().lower()

    assert "drop table chunk_embeddings" not in sql
    assert "insert into chunk_embeddings" not in sql

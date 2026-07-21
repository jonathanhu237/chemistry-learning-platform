from __future__ import annotations

from pathlib import Path


MIGRATION = Path("server/migrations/042_textbook_publication_consistency.sql")


def test_textbook_publication_migration_adds_corpus_revision_and_audit_fields() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS textbook_corpus_state" in sql
    assert "revision bigint NOT NULL" in sql
    assert "CHECK (singleton_key = 1)" in sql
    assert "corpus_revision bigint" in sql
    assert "previous_publication_status text" in sql
    assert "new_publication_status text" in sql
    assert "WHERE publication_status = 'published'" in sql


def test_textbook_publication_migration_hardens_job_idempotency_fields() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "textbook_ingestion_jobs_idempotency_key_nonempty" in sql
    assert "SET idempotency_key = 'legacy:' || id::text" in sql
    assert "length(btrim(idempotency_key)) > 0" in sql
    assert "textbook_ingestion_jobs_processing_fingerprint_nonempty" in sql
    assert "digest(COALESCE(config_snapshot" in sql
    assert "length(btrim(processing_fingerprint)) > 0" in sql

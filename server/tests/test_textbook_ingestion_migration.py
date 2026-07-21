from __future__ import annotations

from pathlib import Path


MIGRATION = Path("server/migrations/041_online_textbook_ingestion.sql")
SEED_IDENTITY_MIGRATION = Path("server/migrations/043_textbook_seed_index_identity.sql")
PAGE_CHECKPOINT_MIGRATION = Path("server/migrations/044_textbook_page_processing_fingerprint.sql")
ACTIVE_PROJECTION_MIGRATION = Path("server/migrations/045_textbook_active_projection_run.sql")


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


def test_seed_identity_migration_registers_exact_es_generation_without_reindexing() -> None:
    sql = SEED_IDENTITY_MIGRATION.read_text(encoding="utf-8")

    assert "count(DISTINCT sc.metadata->>'doc_id') = 1" in sql
    assert "jsonb_build_object('index_document_id'" in sql
    assert "source_collection" in sql  # explanatory guard against the unsafe discriminator
    assert "UPDATE source_documents" in sql


def test_page_checkpoint_migration_keys_reusable_ocr_by_processing_fingerprint() -> None:
    sql = PAGE_CHECKPOINT_MIGRATION.read_text(encoding="utf-8")

    assert "ADD COLUMN IF NOT EXISTS processing_fingerprint text" in sql
    assert "idx_textbook_document_pages_reusable_ocr" in sql
    assert "extraction_method IN ('mineru', 'mixed')" in sql


def test_active_projection_migration_persists_the_retrievable_lease_generation() -> None:
    sql = ACTIVE_PROJECTION_MIGRATION.read_text(encoding="utf-8")

    assert "ADD COLUMN IF NOT EXISTS active_projection_run_id text" in sql
    assert "idx_source_documents_active_projection_run" in sql

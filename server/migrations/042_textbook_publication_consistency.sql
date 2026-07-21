CREATE TABLE IF NOT EXISTS textbook_corpus_state (
  singleton_key smallint PRIMARY KEY DEFAULT 1 CHECK (singleton_key = 1),
  revision bigint NOT NULL DEFAULT 1 CHECK (revision > 0),
  last_action text,
  last_document_id text REFERENCES source_documents(id) ON DELETE SET NULL,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO textbook_corpus_state (singleton_key, revision)
VALUES (1, 1)
ON CONFLICT (singleton_key) DO NOTHING;

ALTER TABLE source_documents
  ADD COLUMN IF NOT EXISTS corpus_revision bigint,
  ADD COLUMN IF NOT EXISTS published_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS deactivated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS deleted_at timestamptz,
  ADD COLUMN IF NOT EXISTS deleted_by uuid REFERENCES app_users(id) ON DELETE SET NULL;

ALTER TABLE textbook_lifecycle_events
  ADD COLUMN IF NOT EXISTS previous_publication_status text,
  ADD COLUMN IF NOT EXISTS new_publication_status text,
  ADD COLUMN IF NOT EXISTS corpus_revision bigint;

CREATE INDEX IF NOT EXISTS idx_source_documents_active_corpus
  ON source_documents(logical_textbook_key, document_kind, version_number, id)
  WHERE publication_status = 'published';

CREATE INDEX IF NOT EXISTS idx_source_chunks_document_content_status
  ON source_chunks(document_id, content_status, chunk_index);

UPDATE textbook_ingestion_jobs
SET idempotency_key = 'legacy:' || id::text
WHERE length(btrim(idempotency_key)) = 0;

UPDATE textbook_ingestion_jobs
SET processing_fingerprint = encode(
      digest(COALESCE(config_snapshot, '{}'::jsonb)::text, 'sha256'),
      'hex'
    )
WHERE length(btrim(processing_fingerprint)) = 0;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'textbook_ingestion_jobs_idempotency_key_nonempty'
  ) THEN
    ALTER TABLE textbook_ingestion_jobs
      ADD CONSTRAINT textbook_ingestion_jobs_idempotency_key_nonempty
      CHECK (length(btrim(idempotency_key)) > 0);
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'textbook_ingestion_jobs_processing_fingerprint_nonempty'
  ) THEN
    ALTER TABLE textbook_ingestion_jobs
      ADD CONSTRAINT textbook_ingestion_jobs_processing_fingerprint_nonempty
      CHECK (length(btrim(processing_fingerprint)) > 0);
  END IF;
END $$;

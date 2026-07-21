CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE source_documents
  ADD COLUMN IF NOT EXISTS title text,
  ADD COLUMN IF NOT EXISTS logical_textbook_key text,
  ADD COLUMN IF NOT EXISTS version_number int,
  ADD COLUMN IF NOT EXISTS version_label text,
  ADD COLUMN IF NOT EXISTS publication_status text,
  ADD COLUMN IF NOT EXISTS checksum_sha256 text,
  ADD COLUMN IF NOT EXISTS mime_type text,
  ADD COLUMN IF NOT EXISTS uploaded_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS published_at timestamptz,
  ADD COLUMN IF NOT EXISTS deactivated_at timestamptz,
  ADD COLUMN IF NOT EXISTS supersedes_document_id text REFERENCES source_documents(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS processing_fingerprint text,
  ADD COLUMN IF NOT EXISTS quality_summary jsonb NOT NULL DEFAULT '{}'::jsonb;

UPDATE source_documents
SET logical_textbook_key = COALESCE(
      NULLIF(btrim(metadata->>'source_collection'), ''),
      NULLIF(btrim(id), '')
    ),
    version_number = COALESCE(version_number, 1),
    title = COALESCE(
      NULLIF(btrim(title), ''),
      NULLIF(btrim(metadata->>'book_title'), ''),
      NULLIF(btrim(file_name), ''),
      id
    ),
    publication_status = COALESCE(publication_status, 'published'),
    published_at = COALESCE(published_at, created_at, now())
WHERE logical_textbook_key IS NULL
   OR title IS NULL
   OR version_number IS NULL
   OR publication_status IS NULL;

ALTER TABLE source_documents
  ALTER COLUMN title SET NOT NULL,
  ALTER COLUMN logical_textbook_key SET NOT NULL,
  ALTER COLUMN version_number SET NOT NULL,
  ALTER COLUMN version_number SET DEFAULT 1,
  ALTER COLUMN publication_status SET NOT NULL,
  ALTER COLUMN publication_status SET DEFAULT 'draft';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'source_documents_version_positive'
  ) THEN
    ALTER TABLE source_documents
      ADD CONSTRAINT source_documents_version_positive CHECK (version_number > 0);
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'source_documents_publication_status_valid'
  ) THEN
    ALTER TABLE source_documents
      ADD CONSTRAINT source_documents_publication_status_valid CHECK (
        publication_status IN ('draft', 'processing', 'review_ready', 'published', 'inactive', 'failed', 'deleted')
      );
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'source_documents_checksum_sha256_valid'
  ) THEN
    ALTER TABLE source_documents
      ADD CONSTRAINT source_documents_checksum_sha256_valid CHECK (
        checksum_sha256 IS NULL OR checksum_sha256 ~ '^[0-9a-f]{64}$'
      );
  END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_source_documents_logical_version
  ON source_documents(logical_textbook_key, version_number);

CREATE UNIQUE INDEX IF NOT EXISTS idx_source_documents_one_published_version
  ON source_documents(logical_textbook_key)
  WHERE publication_status = 'published';

CREATE INDEX IF NOT EXISTS idx_source_documents_publication_recent
  ON source_documents(publication_status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_source_documents_checksum
  ON source_documents(checksum_sha256, size_bytes)
  WHERE checksum_sha256 IS NOT NULL;

ALTER TABLE source_chunks
  ADD COLUMN IF NOT EXISTS page_end int,
  ADD COLUMN IF NOT EXISTS document_version int NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS section_path text[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS content_type text,
  ADD COLUMN IF NOT EXISTS content_hash text,
  ADD COLUMN IF NOT EXISTS parent_chunk_id text,
  ADD COLUMN IF NOT EXISTS previous_chunk_id text,
  ADD COLUMN IF NOT EXISTS next_chunk_id text,
  ADD COLUMN IF NOT EXISTS extraction_method text,
  ADD COLUMN IF NOT EXISTS processing_fingerprint text,
  ADD COLUMN IF NOT EXISTS quality_flags text[] NOT NULL DEFAULT '{}';

UPDATE source_chunks sc
SET page_end = COALESCE(sc.page_end, sc.page_number),
    document_version = COALESCE(sd.version_number, sc.document_version, 1),
    section_path = CASE
      WHEN cardinality(sc.section_path) > 0 THEN sc.section_path
      WHEN NULLIF(btrim(sc.section_title), '') IS NOT NULL THEN ARRAY[sc.section_title]
      ELSE '{}'::text[]
    END,
    content_type = COALESCE(NULLIF(sc.content_type, ''), NULLIF(sc.metadata->>'content_type', ''), 'text'),
    content_hash = COALESCE(NULLIF(sc.content_hash, ''), NULLIF(sc.metadata->>'content_hash', ''), md5(sc.text)),
    extraction_method = COALESCE(NULLIF(sc.extraction_method, ''), 'seed')
FROM source_documents sd
WHERE sd.id = sc.document_id
  AND (
    sc.page_end IS NULL
    OR sc.content_type IS NULL
    OR sc.content_hash IS NULL
    OR sc.extraction_method IS NULL
    OR cardinality(sc.section_path) = 0
  );

CREATE INDEX IF NOT EXISTS idx_source_chunks_document_version_page
  ON source_chunks(document_id, document_version, page_number, chunk_index);

CREATE INDEX IF NOT EXISTS idx_source_chunks_content_hash
  ON source_chunks(document_id, content_hash);

CREATE TABLE IF NOT EXISTS textbook_ingestion_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id text NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'uploaded' CHECK (
    status IN (
      'uploaded', 'extracting', 'awaiting_ocr', 'ocr', 'structuring',
      'chunking', 'embedding', 'indexing', 'review_ready', 'ready',
      'failed', 'cancelled'
    )
  ),
  progress int NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
  attempts int NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  max_attempts int NOT NULL DEFAULT 3 CHECK (max_attempts > 0),
  resume_from_status text,
  worker_id text,
  lease_token uuid,
  lease_expires_at timestamptz,
  heartbeat_at timestamptz,
  run_after timestamptz NOT NULL DEFAULT now(),
  total_pages int NOT NULL DEFAULT 0 CHECK (total_pages >= 0),
  processed_pages int NOT NULL DEFAULT 0 CHECK (processed_pages >= 0),
  ocr_pages int NOT NULL DEFAULT 0 CHECK (ocr_pages >= 0),
  total_chunks int NOT NULL DEFAULT 0 CHECK (total_chunks >= 0),
  embedded_chunks int NOT NULL DEFAULT 0 CHECK (embedded_chunks >= 0),
  indexed_chunks int NOT NULL DEFAULT 0 CHECK (indexed_chunks >= 0),
  idempotency_key text NOT NULL,
  processing_fingerprint text NOT NULL,
  config_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
  stage_metrics jsonb NOT NULL DEFAULT '{}'::jsonb,
  quality_report jsonb NOT NULL DEFAULT '{}'::jsonb,
  outputs jsonb NOT NULL DEFAULT '{}'::jsonb,
  error_code text,
  error_message text,
  cancellation_requested_at timestamptz,
  created_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_textbook_ingestion_jobs_one_open
  ON textbook_ingestion_jobs(document_id)
  WHERE status NOT IN ('ready', 'failed', 'cancelled');

CREATE UNIQUE INDEX IF NOT EXISTS idx_textbook_ingestion_jobs_idempotency
  ON textbook_ingestion_jobs(idempotency_key);

CREATE INDEX IF NOT EXISTS idx_textbook_ingestion_jobs_claim
  ON textbook_ingestion_jobs(status, run_after, lease_expires_at, created_at)
  WHERE status = 'uploaded' OR status IN ('extracting', 'ocr', 'structuring', 'chunking', 'embedding', 'indexing');

CREATE INDEX IF NOT EXISTS idx_textbook_ingestion_jobs_document_recent
  ON textbook_ingestion_jobs(document_id, created_at DESC);

CREATE TABLE IF NOT EXISTS textbook_document_pages (
  document_id text NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
  page_number int NOT NULL CHECK (page_number > 0),
  last_job_id uuid REFERENCES textbook_ingestion_jobs(id) ON DELETE SET NULL,
  width_points double precision,
  height_points double precision,
  extraction_method text NOT NULL CHECK (extraction_method IN ('native', 'mineru', 'mixed')),
  text text NOT NULL DEFAULT '',
  markdown text NOT NULL DEFAULT '',
  blocks jsonb NOT NULL DEFAULT '[]'::jsonb,
  content_hash text NOT NULL,
  quality_score double precision NOT NULL DEFAULT 0 CHECK (quality_score BETWEEN 0 AND 1),
  quality_flags text[] NOT NULL DEFAULT '{}',
  needs_ocr boolean NOT NULL DEFAULT false,
  ocr_provider text,
  ocr_model text,
  diagnostics jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (document_id, page_number)
);

CREATE INDEX IF NOT EXISTS idx_textbook_document_pages_quality
  ON textbook_document_pages(document_id, needs_ocr, quality_score, page_number);

CREATE TABLE IF NOT EXISTS textbook_ingestion_job_events (
  id bigserial PRIMARY KEY,
  job_id uuid NOT NULL REFERENCES textbook_ingestion_jobs(id) ON DELETE CASCADE,
  status text NOT NULL,
  progress int NOT NULL CHECK (progress BETWEEN 0 AND 100),
  event_type text NOT NULL,
  message text,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_textbook_ingestion_job_events_job
  ON textbook_ingestion_job_events(job_id, id);

CREATE TABLE IF NOT EXISTS textbook_lifecycle_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id text NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
  job_id uuid REFERENCES textbook_ingestion_jobs(id) ON DELETE SET NULL,
  action text NOT NULL CHECK (
    action IN ('uploaded', 'processing_started', 'retry', 'cancel', 'publish', 'deactivate', 'rollback', 'delete')
  ),
  actor_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_textbook_lifecycle_events_document
  ON textbook_lifecycle_events(document_id, created_at DESC);

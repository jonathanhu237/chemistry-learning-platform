ALTER TABLE source_documents
  ADD COLUMN IF NOT EXISTS active_projection_run_id text;

CREATE INDEX IF NOT EXISTS idx_source_documents_active_projection_run
  ON source_documents(active_projection_run_id)
  WHERE active_projection_run_id IS NOT NULL;

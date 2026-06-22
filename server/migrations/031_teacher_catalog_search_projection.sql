CREATE TABLE IF NOT EXISTS experiment_catalog_teacher_search_index_state (
  node_id text PRIMARY KEY REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  placement_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE SET NULL,
  document_id text NOT NULL,
  desired_action text NOT NULL DEFAULT 'upsert' CHECK (desired_action IN ('upsert', 'delete')),
  sync_status text NOT NULL DEFAULT 'pending' CHECK (
    sync_status IN ('pending', 'running', 'synced', 'failed', 'disabled', 'unavailable')
  ),
  attempts int NOT NULL DEFAULT 0,
  document_hash text,
  last_error text,
  indexed_at timestamptz,
  last_attempted_at timestamptz,
  analyzer_version text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (attempts >= 0)
);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_teacher_search_state_status
  ON experiment_catalog_teacher_search_index_state(sync_status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_teacher_search_state_canonical
  ON experiment_catalog_teacher_search_index_state(canonical_point_id, sync_status);

ALTER TABLE experiment_catalog_point_jobs
  DROP CONSTRAINT IF EXISTS experiment_catalog_point_jobs_job_type_check;

ALTER TABLE experiment_catalog_point_jobs
  ADD CONSTRAINT experiment_catalog_point_jobs_job_type_check CHECK (
    job_type IN (
      'es_upsert',
      'es_delete',
      'teacher_search_upsert',
      'teacher_search_delete',
      'rag_evidence_refresh',
      'rag_evidence_delete'
    )
  );

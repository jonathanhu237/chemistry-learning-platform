CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS experiment_catalog_point_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id text NOT NULL REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  job_type text NOT NULL CHECK (
    job_type IN ('es_upsert', 'es_delete', 'rag_evidence_refresh', 'rag_evidence_delete')
  ),
  trigger_source text NOT NULL DEFAULT 'automatic' CHECK (
    trigger_source IN ('automatic', 'manual', 'retry', 'system')
  ),
  status text NOT NULL DEFAULT 'pending' CHECK (
    status IN ('pending', 'running', 'succeeded', 'failed', 'disabled', 'unavailable')
  ),
  attempts int NOT NULL DEFAULT 0,
  max_attempts int NOT NULL DEFAULT 3,
  idempotency_key text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  result jsonb NOT NULL DEFAULT '{}'::jsonb,
  latest_error text,
  worker_id text,
  run_after timestamptz NOT NULL DEFAULT now(),
  locked_at timestamptz,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (attempts >= 0),
  CHECK (max_attempts > 0),
  CHECK (idempotency_key = btrim(idempotency_key)),
  CHECK (length(btrim(idempotency_key)) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_experiment_catalog_point_jobs_open_idempotency
  ON experiment_catalog_point_jobs(idempotency_key)
  WHERE status IN ('pending', 'running');

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_point_jobs_claim
  ON experiment_catalog_point_jobs(status, run_after, created_at)
  WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_point_jobs_node_recent
  ON experiment_catalog_point_jobs(node_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS experiment_catalog_point_evidence_state (
  node_id text PRIMARY KEY REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  evidence_status text NOT NULL DEFAULT 'missing' CHECK (
    evidence_status IN ('missing', 'pending', 'running', 'succeeded', 'failed', 'stale', 'disabled', 'unavailable')
  ),
  source_mode text NOT NULL DEFAULT 'none',
  trigger_policy text NOT NULL DEFAULT 'stale_until_manual_refresh',
  selected_chunk_ids text[] NOT NULL DEFAULT '{}',
  source_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  diagnostics jsonb NOT NULL DEFAULT '{}'::jsonb,
  stale_reason text,
  latest_error text,
  refreshed_at timestamptz,
  stale_at timestamptz,
  last_attempted_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_point_evidence_state_status
  ON experiment_catalog_point_evidence_state(evidence_status, updated_at DESC);

CREATE TABLE IF NOT EXISTS experiment_catalog_point_evidence_bindings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id text NOT NULL REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  chunk_id text NOT NULL REFERENCES source_chunks(id) ON DELETE RESTRICT,
  evidence_role text NOT NULL DEFAULT 'dynamic_rag' CHECK (
    evidence_role IN ('experiment', 'theory', 'supplemental', 'fallback', 'dynamic_rag')
  ),
  selection_status text NOT NULL DEFAULT 'selected' CHECK (
    selection_status IN ('selected', 'candidate', 'rejected', 'stale')
  ),
  freshness_status text NOT NULL DEFAULT 'fresh' CHECK (
    freshness_status IN ('fresh', 'stale', 'missing')
  ),
  rank int NOT NULL DEFAULT 0,
  score double precision,
  rerank_score double precision,
  source_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  diagnostics jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (node_id, chunk_id, evidence_role)
);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_point_evidence_bindings_node
  ON experiment_catalog_point_evidence_bindings(node_id, freshness_status, rank, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_point_evidence_bindings_chunk
  ON experiment_catalog_point_evidence_bindings(chunk_id);

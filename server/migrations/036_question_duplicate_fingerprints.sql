CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS question_semantic_fingerprints (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_kind text NOT NULL CHECK (owner_kind IN ('question', 'draft')),
  owner_id uuid NOT NULL,
  point_node_id text NOT NULL REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  text_hash text NOT NULL,
  embedding_model text NOT NULL,
  embedding jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (text_hash = btrim(text_hash)),
  CHECK (embedding_model = btrim(embedding_model)),
  CHECK (jsonb_typeof(embedding) = 'array')
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_question_semantic_fingerprints_owner
  ON question_semantic_fingerprints(owner_kind, owner_id, point_node_id, embedding_model, text_hash);

CREATE INDEX IF NOT EXISTS idx_question_semantic_fingerprints_point
  ON question_semantic_fingerprints(point_node_id, embedding_model, updated_at DESC);

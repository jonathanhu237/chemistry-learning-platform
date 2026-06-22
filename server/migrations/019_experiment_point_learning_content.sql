CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS experiment_video_points (
  experiment_id text NOT NULL REFERENCES formal_experiments(id) ON DELETE CASCADE,
  point_key text NOT NULL,
  point_title text NOT NULL,
  display_order int NOT NULL DEFAULT 0,
  source text NOT NULL DEFAULT 'manual' CHECK (source IN ('seed_candidate', 'media_binding', 'manual', 'legacy')),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (experiment_id, point_key),
  CHECK (point_key = btrim(point_key)),
  CHECK (length(btrim(point_key)) > 0),
  CHECK (length(btrim(point_title)) > 0)
);

CREATE TABLE IF NOT EXISTS experiment_point_learning_content (
  experiment_id text NOT NULL,
  point_key text NOT NULL,
  principle_mode text NOT NULL DEFAULT 'text' CHECK (principle_mode IN ('equation', 'text')),
  principle_equation text,
  principle_text text,
  phenomenon_explanation text NOT NULL DEFAULT '',
  safety_note text NOT NULL DEFAULT '',
  content_status text NOT NULL DEFAULT 'draft' CHECK (content_status IN ('draft', 'published', 'archived')),
  published_at timestamptz,
  published_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (experiment_id, point_key),
  FOREIGN KEY (experiment_id, point_key)
    REFERENCES experiment_video_points(experiment_id, point_key)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS experiment_point_related_links (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_experiment_id text NOT NULL,
  source_point_key text NOT NULL,
  target_experiment_id text NOT NULL,
  target_point_key text NOT NULL,
  relation_type text NOT NULL DEFAULT 'manual' CHECK (relation_type IN ('manual', 'default_override')),
  hidden boolean NOT NULL DEFAULT false,
  sort_order int NOT NULL DEFAULT 0,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (source_experiment_id, source_point_key)
    REFERENCES experiment_video_points(experiment_id, point_key)
    ON DELETE CASCADE,
  FOREIGN KEY (target_experiment_id, target_point_key)
    REFERENCES experiment_video_points(experiment_id, point_key)
    ON DELETE CASCADE,
  UNIQUE (source_experiment_id, source_point_key, target_experiment_id, target_point_key)
);

CREATE TABLE IF NOT EXISTS experiment_video_point_search_index_state (
  experiment_id text NOT NULL,
  point_key text NOT NULL,
  document_id text NOT NULL,
  desired_action text NOT NULL DEFAULT 'upsert' CHECK (desired_action IN ('upsert', 'delete')),
  sync_status text NOT NULL DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'failed', 'disabled')),
  attempts int NOT NULL DEFAULT 0,
  document_hash text,
  last_error text,
  indexed_at timestamptz,
  last_attempted_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (experiment_id, point_key),
  FOREIGN KEY (experiment_id, point_key)
    REFERENCES experiment_video_points(experiment_id, point_key)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_experiment_video_points_experiment_order
  ON experiment_video_points(experiment_id, status, display_order, point_key);

CREATE INDEX IF NOT EXISTS idx_experiment_point_learning_content_status
  ON experiment_point_learning_content(content_status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_experiment_point_related_links_source
  ON experiment_point_related_links(source_experiment_id, source_point_key, hidden, sort_order);

CREATE INDEX IF NOT EXISTS idx_experiment_point_related_links_target
  ON experiment_point_related_links(target_experiment_id, target_point_key);

CREATE INDEX IF NOT EXISTS idx_experiment_video_point_search_status
  ON experiment_video_point_search_index_state(sync_status, updated_at DESC);

WITH candidate_points AS (
  SELECT
    fe.id AS experiment_id,
    ('candidate-' || candidate.ordinality || '-' || substring(encode(digest(convert_to(btrim(candidate.value::text), 'UTF8'), 'sha1'), 'hex') for 8)) AS point_key,
    btrim(candidate.value::text) AS point_title,
    candidate.ordinality::int AS display_order
  FROM formal_experiments fe
  CROSS JOIN LATERAL jsonb_array_elements_text(
    CASE
      WHEN jsonb_typeof(fe.metadata->'video_candidates') = 'array' THEN fe.metadata->'video_candidates'
      ELSE '[]'::jsonb
    END
  ) WITH ORDINALITY AS candidate(value, ordinality)
  WHERE btrim(candidate.value::text) <> ''
)
INSERT INTO experiment_video_points (
  experiment_id, point_key, point_title, display_order, source, status, metadata
)
SELECT
  experiment_id,
  point_key,
  point_title,
  display_order,
  'seed_candidate',
  'active',
  jsonb_build_object('backfill_source', 'formal_experiments.metadata.video_candidates')
FROM candidate_points
ON CONFLICT (experiment_id, point_key) DO UPDATE SET
  point_title = EXCLUDED.point_title,
  display_order = LEAST(experiment_video_points.display_order, EXCLUDED.display_order),
  source = CASE
    WHEN experiment_video_points.source = 'manual' THEN experiment_video_points.source
    ELSE EXCLUDED.source
  END,
  metadata = experiment_video_points.metadata || EXCLUDED.metadata,
  updated_at = now();

WITH media_points AS (
  SELECT
    mb.target_id AS experiment_id,
    COALESCE(
      NULLIF(btrim(mb.metadata->>'point_key'), ''),
      'media-' || left(mb.id::text, 8)
    ) AS point_key,
    COALESCE(
      NULLIF(btrim(mb.metadata->>'point_title'), ''),
      NULLIF(btrim(mb.title), ''),
      NULLIF(btrim(ma.title), ''),
      NULLIF(btrim(ma.original_file_name), ''),
      '未命名实验点位'
    ) AS point_title,
    row_number() OVER (PARTITION BY mb.target_id ORDER BY mb.sort_order, mb.created_at)::int + 10000 AS display_order,
    mb.id AS binding_id
  FROM media_bindings mb
  JOIN media_assets ma ON ma.id = mb.media_asset_id
  WHERE mb.target_type = 'experiment'
    AND mb.status <> 'archived'
    AND (
      NULLIF(btrim(mb.metadata->>'point_key'), '') IS NOT NULL
      OR NULLIF(btrim(mb.metadata->>'point_title'), '') IS NOT NULL
    )
)
INSERT INTO experiment_video_points (
  experiment_id, point_key, point_title, display_order, source, status, metadata
)
SELECT
  experiment_id,
  point_key,
  point_title,
  display_order,
  'media_binding',
  'active',
  jsonb_build_object('backfill_source', 'media_bindings.metadata', 'binding_id', binding_id)
FROM media_points
ON CONFLICT (experiment_id, point_key) DO UPDATE SET
  point_title = COALESCE(NULLIF(experiment_video_points.point_title, ''), EXCLUDED.point_title),
  display_order = LEAST(experiment_video_points.display_order, EXCLUDED.display_order),
  metadata = experiment_video_points.metadata || EXCLUDED.metadata,
  updated_at = now();

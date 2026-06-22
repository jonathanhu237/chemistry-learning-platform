CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS experiment_catalog_points (
  id text PRIMARY KEY,
  title text NOT NULL,
  summary text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  published_at timestamptz,
  archived_at timestamptz,
  created_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (id = btrim(id)),
  CHECK (length(btrim(id)) > 0),
  CHECK (title = btrim(title)),
  CHECK (length(btrim(title)) > 0)
);

ALTER TABLE experiment_catalog_nodes
  ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE RESTRICT;

WITH point_rows AS (
  SELECT
    n.*,
    COUNT(*) OVER (PARTITION BY n.title) AS title_count
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'point'
),
canonicalized AS (
  SELECT
    id AS placement_node_id,
    CASE
      WHEN title_count > 1 THEN 'cat-canon-title-' || left(encode(digest(convert_to(title, 'UTF8'), 'sha1'), 'hex'), 24)
      ELSE 'cat-canon-node-' || left(encode(digest(convert_to(id, 'UTF8'), 'sha1'), 'hex'), 24)
    END AS canonical_point_id,
    CASE
      WHEN title_count > 1 THEN 'reviewed_exact_duplicate_title'
      ELSE 'singleton_point_node'
    END AS grouping_decision,
    title,
    summary,
    status,
    metadata,
    published_at,
    created_by,
    updated_by,
    created_at,
    updated_at
  FROM point_rows
),
ranked AS (
  SELECT
    *,
    row_number() OVER (
      PARTITION BY canonical_point_id
      ORDER BY CASE status WHEN 'published' THEN 0 WHEN 'draft' THEN 1 ELSE 2 END,
               updated_at DESC,
               placement_node_id
    ) AS rank
  FROM canonicalized
)
INSERT INTO experiment_catalog_points (
  id, title, summary, status, metadata, published_at, created_by, updated_by, created_at, updated_at
)
SELECT
  canonical_point_id,
  btrim(title),
  COALESCE(summary, ''),
  status,
  COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'point_identity_migration',
    jsonb_build_object(
      'source', '025_catalog_point_placements',
      'grouping_decision', grouping_decision
    )
  ),
  published_at,
  created_by,
  updated_by,
  created_at,
  now()
FROM ranked
WHERE rank = 1
ON CONFLICT (id) DO UPDATE SET
  title = EXCLUDED.title,
  summary = EXCLUDED.summary,
  status = EXCLUDED.status,
  metadata = experiment_catalog_points.metadata || EXCLUDED.metadata,
  published_at = COALESCE(experiment_catalog_points.published_at, EXCLUDED.published_at),
  updated_at = now();

WITH point_rows AS (
  SELECT
    n.id,
    CASE
      WHEN COUNT(*) OVER (PARTITION BY n.title) > 1 THEN 'cat-canon-title-' || left(encode(digest(convert_to(n.title, 'UTF8'), 'sha1'), 'hex'), 24)
      ELSE 'cat-canon-node-' || left(encode(digest(convert_to(n.id, 'UTF8'), 'sha1'), 'hex'), 24)
    END AS canonical_point_id
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'point'
)
UPDATE experiment_catalog_nodes n
SET canonical_point_id = point_rows.canonical_point_id,
    metadata = COALESCE(n.metadata, '{}'::jsonb) || jsonb_build_object(
      'point_identity_migration',
      jsonb_build_object(
        'source', '025_catalog_point_placements',
        'placement_node_id', n.id,
        'canonical_point_id', point_rows.canonical_point_id
      )
    ),
    updated_at = now()
FROM point_rows
WHERE n.id = point_rows.id
  AND n.canonical_point_id IS NULL;

UPDATE experiment_catalog_nodes
SET canonical_point_id = NULL
WHERE node_kind = 'directory'
  AND canonical_point_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS experiment_catalog_point_identity_map (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  old_node_id text NOT NULL,
  placement_node_id text NOT NULL REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  canonical_point_id text NOT NULL REFERENCES experiment_catalog_points(id) ON DELETE RESTRICT,
  grouping_decision text NOT NULL,
  conflict_status text NOT NULL DEFAULT 'ok' CHECK (conflict_status IN ('ok', 'conflict_detected', 'needs_review')),
  resource_counts jsonb NOT NULL DEFAULT '{}'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (old_node_id),
  UNIQUE (placement_node_id)
);

WITH placement_rows AS (
  SELECT
    n.id AS placement_node_id,
    n.canonical_point_id,
    n.title,
    COUNT(*) OVER (PARTITION BY n.canonical_point_id) AS placement_count
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'point'
    AND n.canonical_point_id IS NOT NULL
),
resource_counts AS (
  SELECT
    p.placement_node_id,
    p.canonical_point_id,
    jsonb_build_object(
      'content_rows', (SELECT COUNT(*) FROM experiment_catalog_point_content pc WHERE pc.node_id = p.placement_node_id),
      'media_rows', (SELECT COUNT(*) FROM experiment_catalog_point_media_bindings mb WHERE mb.node_id = p.placement_node_id),
      'related_source_rows', (SELECT COUNT(*) FROM experiment_catalog_point_related_links rl WHERE rl.source_node_id = p.placement_node_id),
      'related_target_rows', (SELECT COUNT(*) FROM experiment_catalog_point_related_links rl WHERE rl.target_node_id = p.placement_node_id),
      'evidence_state_rows', (SELECT COUNT(*) FROM experiment_catalog_point_evidence_state es WHERE es.node_id = p.placement_node_id),
      'evidence_binding_rows', (SELECT COUNT(*) FROM experiment_catalog_point_evidence_bindings eb WHERE eb.node_id = p.placement_node_id),
      'question_reference_rows', (SELECT COUNT(*) FROM experiment_questions q WHERE p.placement_node_id = ANY(q.primary_point_node_ids)),
      'attempt_rows', (SELECT COUNT(*) FROM experiment_question_attempts a WHERE a.point_node_id = p.placement_node_id),
      'event_rows', (SELECT COUNT(*) FROM student_events e WHERE e.point_node_id = p.placement_node_id),
      'feedback_rows', (SELECT COUNT(*) FROM student_feedback f WHERE f.point_node_id = p.placement_node_id),
      'mastery_rows', (SELECT COUNT(*) FROM student_experiment_mastery m WHERE m.point_node_id = p.placement_node_id)
    ) AS resource_counts,
    CASE WHEN p.placement_count > 1 THEN 'reviewed_exact_duplicate_title' ELSE 'singleton_point_node' END AS grouping_decision,
    p.placement_count
  FROM placement_rows p
)
INSERT INTO experiment_catalog_point_identity_map (
  old_node_id, placement_node_id, canonical_point_id, grouping_decision, conflict_status, resource_counts, metadata, updated_at
)
SELECT
  placement_node_id,
  placement_node_id,
  canonical_point_id,
  grouping_decision,
  CASE
    WHEN placement_count > 1 AND (
      SELECT SUM((value #>> '{}')::int)
      FROM jsonb_each(resource_counts)
    ) > 0 THEN 'needs_review'
    ELSE 'ok'
  END,
  resource_counts,
  jsonb_build_object('migration_source', '025_catalog_point_placements'),
  now()
FROM resource_counts
ON CONFLICT (old_node_id) DO UPDATE SET
  placement_node_id = EXCLUDED.placement_node_id,
  canonical_point_id = EXCLUDED.canonical_point_id,
  grouping_decision = EXCLUDED.grouping_decision,
  conflict_status = EXCLUDED.conflict_status,
  resource_counts = EXCLUDED.resource_counts,
  metadata = experiment_catalog_point_identity_map.metadata || EXCLUDED.metadata,
  updated_at = now();

ALTER TABLE experiment_catalog_point_content
  ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE CASCADE;

UPDATE experiment_catalog_point_content pc
SET canonical_point_id = n.canonical_point_id,
    metadata = COALESCE(pc.metadata, '{}'::jsonb) || jsonb_build_object(
      'point_identity_migration',
      jsonb_build_object('source', '025_catalog_point_placements', 'old_node_id', pc.node_id, 'canonical_point_id', n.canonical_point_id)
    ),
    updated_at = now()
FROM experiment_catalog_nodes n
WHERE pc.node_id = n.id
  AND n.canonical_point_id IS NOT NULL
  AND pc.canonical_point_id IS NULL;

ALTER TABLE experiment_catalog_point_reaction_equations
  ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE CASCADE;

UPDATE experiment_catalog_point_reaction_equations eq
SET canonical_point_id = n.canonical_point_id,
    metadata = COALESCE(eq.metadata, '{}'::jsonb) || jsonb_build_object(
      'point_identity_migration',
      jsonb_build_object('source', '025_catalog_point_placements', 'old_node_id', eq.node_id, 'canonical_point_id', n.canonical_point_id)
    ),
    updated_at = now()
FROM experiment_catalog_nodes n
WHERE eq.node_id = n.id
  AND n.canonical_point_id IS NOT NULL
  AND eq.canonical_point_id IS NULL;

ALTER TABLE experiment_catalog_point_media_bindings
  ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS source_placement_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

UPDATE experiment_catalog_point_media_bindings mb
SET canonical_point_id = n.canonical_point_id,
    source_placement_node_id = COALESCE(mb.source_placement_node_id, mb.node_id),
    metadata = COALESCE(mb.metadata, '{}'::jsonb) || jsonb_build_object(
      'point_identity_migration',
      jsonb_build_object('source', '025_catalog_point_placements', 'old_node_id', mb.node_id, 'canonical_point_id', n.canonical_point_id)
    ),
    updated_at = now()
FROM experiment_catalog_nodes n
WHERE mb.node_id = n.id
  AND n.canonical_point_id IS NOT NULL
  AND mb.canonical_point_id IS NULL;

ALTER TABLE experiment_catalog_point_related_links
  ADD COLUMN IF NOT EXISTS source_canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS target_canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS source_placement_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS target_placement_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

UPDATE experiment_catalog_point_related_links rl
SET source_canonical_point_id = source_node.canonical_point_id,
    target_canonical_point_id = target_node.canonical_point_id,
    source_placement_node_id = COALESCE(rl.source_placement_node_id, rl.source_node_id),
    target_placement_node_id = COALESCE(rl.target_placement_node_id, rl.target_node_id),
    metadata = COALESCE(rl.metadata, '{}'::jsonb) || jsonb_build_object(
      'point_identity_migration',
      jsonb_build_object(
        'source', '025_catalog_point_placements',
        'source_node_id', rl.source_node_id,
        'target_node_id', rl.target_node_id,
        'source_canonical_point_id', source_node.canonical_point_id,
        'target_canonical_point_id', target_node.canonical_point_id
      )
    ),
    updated_at = now()
FROM experiment_catalog_nodes source_node,
     experiment_catalog_nodes target_node
WHERE rl.source_node_id = source_node.id
  AND rl.target_node_id = target_node.id
  AND source_node.canonical_point_id IS NOT NULL
  AND target_node.canonical_point_id IS NOT NULL
  AND (rl.source_canonical_point_id IS NULL OR rl.target_canonical_point_id IS NULL);

ALTER TABLE experiment_catalog_point_search_index_state
  ADD COLUMN IF NOT EXISTS placement_node_id text,
  ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE SET NULL;

UPDATE experiment_catalog_point_search_index_state s
SET placement_node_id = COALESCE(s.placement_node_id, s.node_id),
    canonical_point_id = n.canonical_point_id,
    updated_at = now()
FROM experiment_catalog_nodes n
WHERE s.node_id = n.id
  AND n.canonical_point_id IS NOT NULL
  AND s.canonical_point_id IS NULL;

ALTER TABLE experiment_catalog_point_jobs
  ADD COLUMN IF NOT EXISTS placement_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE SET NULL;

UPDATE experiment_catalog_point_jobs j
SET placement_node_id = COALESCE(j.placement_node_id, j.node_id),
    canonical_point_id = n.canonical_point_id,
    payload = COALESCE(j.payload, '{}'::jsonb) || jsonb_build_object(
      'placement_node_id', COALESCE(j.placement_node_id, j.node_id),
      'canonical_point_id', n.canonical_point_id
    ),
    updated_at = now()
FROM experiment_catalog_nodes n
WHERE j.node_id = n.id
  AND n.canonical_point_id IS NOT NULL
  AND j.canonical_point_id IS NULL;

ALTER TABLE experiment_catalog_point_evidence_state
  ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS source_placement_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

UPDATE experiment_catalog_point_evidence_state es
SET canonical_point_id = n.canonical_point_id,
    source_placement_node_id = COALESCE(es.source_placement_node_id, es.node_id),
    diagnostics = COALESCE(es.diagnostics, '{}'::jsonb) || jsonb_build_object(
      'point_identity_migration',
      jsonb_build_object('source', '025_catalog_point_placements', 'old_node_id', es.node_id, 'canonical_point_id', n.canonical_point_id)
    ),
    updated_at = now()
FROM experiment_catalog_nodes n
WHERE es.node_id = n.id
  AND n.canonical_point_id IS NOT NULL
  AND es.canonical_point_id IS NULL;

ALTER TABLE experiment_catalog_point_evidence_bindings
  ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS source_placement_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

UPDATE experiment_catalog_point_evidence_bindings eb
SET canonical_point_id = n.canonical_point_id,
    source_placement_node_id = COALESCE(eb.source_placement_node_id, eb.node_id),
    source_metadata = COALESCE(eb.source_metadata, '{}'::jsonb) || jsonb_build_object(
      'point_identity_migration',
      jsonb_build_object('source', '025_catalog_point_placements', 'old_node_id', eb.node_id, 'canonical_point_id', n.canonical_point_id)
    ),
    updated_at = now()
FROM experiment_catalog_nodes n
WHERE eb.node_id = n.id
  AND n.canonical_point_id IS NOT NULL
  AND eb.canonical_point_id IS NULL;

ALTER TABLE experiment_questions
  ADD COLUMN IF NOT EXISTS primary_canonical_point_ids text[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS source_placement_node_ids text[] NOT NULL DEFAULT '{}';

UPDATE experiment_questions q
SET primary_canonical_point_ids = COALESCE((
      SELECT array_agg(DISTINCT n.canonical_point_id ORDER BY n.canonical_point_id)
      FROM unnest(q.primary_point_node_ids) AS item(node_id)
      JOIN experiment_catalog_nodes n ON n.id = item.node_id
      WHERE n.canonical_point_id IS NOT NULL
    ), '{}'),
    source_placement_node_ids = COALESCE((
      SELECT array_agg(DISTINCT item.node_id ORDER BY item.node_id)
      FROM unnest(q.primary_point_node_ids) AS item(node_id)
    ), '{}'),
    metadata = COALESCE(q.metadata, '{}'::jsonb) || jsonb_build_object(
      'primary_canonical_point_ids',
      COALESCE((
        SELECT to_jsonb(array_agg(DISTINCT n.canonical_point_id ORDER BY n.canonical_point_id))
        FROM unnest(q.primary_point_node_ids) AS item(node_id)
        JOIN experiment_catalog_nodes n ON n.id = item.node_id
        WHERE n.canonical_point_id IS NOT NULL
      ), '[]'::jsonb),
      'source_placement_node_ids',
      COALESCE(to_jsonb(q.primary_point_node_ids), '[]'::jsonb)
    ),
    updated_at = now()
WHERE array_length(q.primary_point_node_ids, 1) > 0;

ALTER TABLE experiment_video_point_evidence
  ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS source_placement_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

UPDATE experiment_video_point_evidence evidence
SET canonical_point_id = n.canonical_point_id,
    source_placement_node_id = COALESCE(evidence.source_placement_node_id, evidence.point_node_id),
    metadata = COALESCE(evidence.metadata, '{}'::jsonb) || jsonb_build_object(
      'canonical_point_id', n.canonical_point_id,
      'source_placement_node_id', COALESCE(evidence.source_placement_node_id, evidence.point_node_id)
    ),
    updated_at = now()
FROM experiment_catalog_nodes n
WHERE evidence.point_node_id = n.id
  AND n.canonical_point_id IS NOT NULL
  AND evidence.canonical_point_id IS NULL;

ALTER TABLE experiment_question_attempts
  ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS source_placement_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

UPDATE experiment_question_attempts attempts
SET canonical_point_id = n.canonical_point_id,
    source_placement_node_id = COALESCE(attempts.source_placement_node_id, attempts.point_node_id),
    metadata = COALESCE(attempts.metadata, '{}'::jsonb) || jsonb_build_object(
      'canonical_point_id', n.canonical_point_id,
      'source_placement_node_id', COALESCE(attempts.source_placement_node_id, attempts.point_node_id)
    )
FROM experiment_catalog_nodes n
WHERE attempts.point_node_id = n.id
  AND n.canonical_point_id IS NOT NULL
  AND attempts.canonical_point_id IS NULL;

ALTER TABLE student_events
  ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS source_placement_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

UPDATE student_events events
SET canonical_point_id = n.canonical_point_id,
    source_placement_node_id = COALESCE(events.source_placement_node_id, events.point_node_id),
    metadata = COALESCE(events.metadata, '{}'::jsonb) || jsonb_build_object(
      'canonical_point_id', n.canonical_point_id,
      'source_placement_node_id', COALESCE(events.source_placement_node_id, events.point_node_id)
    )
FROM experiment_catalog_nodes n
WHERE events.point_node_id = n.id
  AND n.canonical_point_id IS NOT NULL
  AND events.canonical_point_id IS NULL;

ALTER TABLE student_feedback
  ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS source_placement_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

UPDATE student_feedback feedback
SET canonical_point_id = n.canonical_point_id,
    source_placement_node_id = COALESCE(feedback.source_placement_node_id, feedback.point_node_id),
    metadata = COALESCE(feedback.metadata, '{}'::jsonb) || jsonb_build_object(
      'canonical_point_id', n.canonical_point_id,
      'source_placement_node_id', COALESCE(feedback.source_placement_node_id, feedback.point_node_id)
    ),
    updated_at = now()
FROM experiment_catalog_nodes n
WHERE feedback.point_node_id = n.id
  AND n.canonical_point_id IS NOT NULL
  AND feedback.canonical_point_id IS NULL;

ALTER TABLE student_experiment_mastery
  ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS source_placement_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

UPDATE student_experiment_mastery mastery
SET canonical_point_id = n.canonical_point_id,
    source_placement_node_id = COALESCE(mastery.source_placement_node_id, mastery.point_node_id),
    metadata = COALESCE(mastery.metadata, '{}'::jsonb) || jsonb_build_object(
      'canonical_point_id', n.canonical_point_id,
      'source_placement_node_id', COALESCE(mastery.source_placement_node_id, mastery.point_node_id)
    ),
    updated_at = now()
FROM experiment_catalog_nodes n
WHERE mastery.point_node_id = n.id
  AND n.canonical_point_id IS NOT NULL
  AND mastery.canonical_point_id IS NULL;

ALTER TABLE student_posttest_sessions
  ADD COLUMN IF NOT EXISTS canonical_point_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS source_placement_node_ids jsonb NOT NULL DEFAULT '[]'::jsonb;

UPDATE student_posttest_sessions sessions
SET canonical_point_ids = COALESCE((
      SELECT jsonb_agg(DISTINCT n.canonical_point_id)
      FROM jsonb_array_elements_text(sessions.point_node_ids) AS item(node_id)
      JOIN experiment_catalog_nodes n ON n.id = item.node_id
      WHERE n.canonical_point_id IS NOT NULL
    ), '[]'::jsonb),
    source_placement_node_ids = COALESCE(sessions.point_node_ids, '[]'::jsonb),
    metadata = COALESCE(sessions.metadata, '{}'::jsonb) || jsonb_build_object(
      'canonical_point_ids',
      COALESCE((
        SELECT jsonb_agg(DISTINCT n.canonical_point_id)
        FROM jsonb_array_elements_text(sessions.point_node_ids) AS item(node_id)
        JOIN experiment_catalog_nodes n ON n.id = item.node_id
        WHERE n.canonical_point_id IS NOT NULL
      ), '[]'::jsonb),
      'source_placement_node_ids',
      COALESCE(sessions.point_node_ids, '[]'::jsonb)
    ),
    updated_at = now()
WHERE jsonb_array_length(sessions.point_node_ids) > 0;

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_points_status
  ON experiment_catalog_points(status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_nodes_canonical_point
  ON experiment_catalog_nodes(canonical_point_id, status, chapter_id, parent_id)
  WHERE canonical_point_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_experiment_catalog_point_placement_parent_canonical
  ON experiment_catalog_nodes(chapter_id, COALESCE(parent_id, ''), canonical_point_id)
  WHERE node_kind = 'point' AND status <> 'archived' AND canonical_point_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_point_content_canonical
  ON experiment_catalog_point_content(canonical_point_id, content_status, updated_at DESC)
  WHERE canonical_point_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_catalog_point_reaction_equations_canonical
  ON experiment_catalog_point_reaction_equations(canonical_point_id, row_order)
  WHERE canonical_point_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_catalog_point_media_canonical
  ON experiment_catalog_point_media_bindings(canonical_point_id, binding_status, display_order)
  WHERE canonical_point_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_catalog_point_related_source_canonical
  ON experiment_catalog_point_related_links(source_canonical_point_id, hidden, sort_order)
  WHERE source_canonical_point_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_catalog_point_related_target_canonical
  ON experiment_catalog_point_related_links(target_canonical_point_id)
  WHERE target_canonical_point_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_catalog_point_search_state_canonical
  ON experiment_catalog_point_search_index_state(canonical_point_id, sync_status, updated_at DESC)
  WHERE canonical_point_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_catalog_point_jobs_canonical
  ON experiment_catalog_point_jobs(canonical_point_id, status, updated_at DESC)
  WHERE canonical_point_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_catalog_point_evidence_state_canonical
  ON experiment_catalog_point_evidence_state(canonical_point_id, evidence_status, updated_at DESC)
  WHERE canonical_point_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_catalog_point_evidence_bindings_canonical
  ON experiment_catalog_point_evidence_bindings(canonical_point_id, freshness_status, rank, updated_at DESC)
  WHERE canonical_point_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_experiment_questions_primary_canonical_points
  ON experiment_questions USING gin(primary_canonical_point_ids);

CREATE INDEX IF NOT EXISTS idx_experiment_question_attempts_canonical_point
  ON experiment_question_attempts(canonical_point_id, created_at DESC)
  WHERE canonical_point_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_student_events_canonical_point
  ON student_events(student_id, canonical_point_id, created_at DESC)
  WHERE canonical_point_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_student_feedback_canonical_point
  ON student_feedback(canonical_point_id, created_at DESC)
  WHERE canonical_point_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_student_experiment_mastery_canonical_point
  ON student_experiment_mastery(canonical_point_id, mastery_score)
  WHERE canonical_point_id IS NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'experiment_catalog_nodes_point_target_check'
  ) THEN
    ALTER TABLE experiment_catalog_nodes
      ADD CONSTRAINT experiment_catalog_nodes_point_target_check
      CHECK (
        (node_kind = 'point' AND canonical_point_id IS NOT NULL)
        OR
        (node_kind = 'directory' AND canonical_point_id IS NULL)
      );
  END IF;
END $$;

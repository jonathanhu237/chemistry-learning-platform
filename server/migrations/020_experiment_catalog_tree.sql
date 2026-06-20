CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS experiment_catalog_nodes (
  id text PRIMARY KEY,
  chapter_id text NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  parent_id text REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  node_kind text NOT NULL DEFAULT 'directory' CHECK (node_kind IN ('directory', 'point', 'hybrid', 'shortcut')),
  title text NOT NULL,
  summary text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
  display_order int NOT NULL DEFAULT 0,
  shortcut_target_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE RESTRICT,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  published_at timestamptz,
  created_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (id = btrim(id)),
  CHECK (length(btrim(id)) > 0),
  CHECK (title = btrim(title)),
  CHECK (length(btrim(title)) > 0),
  CHECK (parent_id IS NULL OR parent_id <> id),
  CHECK (shortcut_target_node_id IS NULL OR shortcut_target_node_id <> id),
  CHECK ((node_kind = 'shortcut' AND shortcut_target_node_id IS NOT NULL) OR (node_kind <> 'shortcut' AND shortcut_target_node_id IS NULL))
);

CREATE TABLE IF NOT EXISTS experiment_catalog_point_content (
  node_id text PRIMARY KEY REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  point_title text NOT NULL,
  teacher_note text NOT NULL DEFAULT '',
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
  CHECK (point_title = btrim(point_title)),
  CHECK (length(btrim(point_title)) > 0)
);

CREATE TABLE IF NOT EXISTS experiment_catalog_point_media_bindings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id text NOT NULL REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  media_asset_id uuid NOT NULL REFERENCES media_assets(id) ON DELETE CASCADE,
  title text,
  binding_status text NOT NULL DEFAULT 'draft' CHECK (binding_status IN ('draft', 'published', 'archived')),
  display_order int NOT NULL DEFAULT 0,
  published_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  published_at timestamptz,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (node_id, media_asset_id)
);

CREATE TABLE IF NOT EXISTS experiment_catalog_point_related_links (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_node_id text NOT NULL REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  target_node_id text NOT NULL REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  relation_type text NOT NULL DEFAULT 'manual' CHECK (relation_type IN ('manual', 'default_override', 'generated_default')),
  hidden boolean NOT NULL DEFAULT false,
  sort_order int NOT NULL DEFAULT 0,
  label text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (source_node_id <> target_node_id),
  UNIQUE (source_node_id, target_node_id)
);

CREATE TABLE IF NOT EXISTS experiment_catalog_point_search_index_state (
  node_id text PRIMARY KEY REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  document_id text NOT NULL,
  desired_action text NOT NULL DEFAULT 'upsert' CHECK (desired_action IN ('upsert', 'delete')),
  sync_status text NOT NULL DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'failed', 'disabled')),
  attempts int NOT NULL DEFAULT 0,
  document_hash text,
  last_error text,
  indexed_at timestamptz,
  last_attempted_at timestamptz,
  analyzer_version text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS experiment_catalog_legacy_identity_map (
  legacy_identity text PRIMARY KEY,
  legacy_kind text NOT NULL CHECK (legacy_kind IN ('formal_experiment', 'experiment_point')),
  legacy_experiment_id text NOT NULL,
  legacy_point_key text,
  catalog_node_id text NOT NULL REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  legacy_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (legacy_kind, legacy_experiment_id, legacy_point_key),
  UNIQUE (catalog_node_id, legacy_kind)
);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_nodes_chapter_roots
  ON experiment_catalog_nodes(chapter_id, status, display_order, id)
  WHERE parent_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_nodes_parent_children
  ON experiment_catalog_nodes(parent_id, status, display_order, id);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_nodes_status
  ON experiment_catalog_nodes(status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_nodes_display_order
  ON experiment_catalog_nodes(chapter_id, parent_id, display_order, id);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_nodes_shortcut_target
  ON experiment_catalog_nodes(shortcut_target_node_id);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_nodes_updated
  ON experiment_catalog_nodes(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_point_content_status
  ON experiment_catalog_point_content(content_status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_point_media_node
  ON experiment_catalog_point_media_bindings(node_id, binding_status, display_order);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_point_media_asset
  ON experiment_catalog_point_media_bindings(media_asset_id);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_related_source
  ON experiment_catalog_point_related_links(source_node_id, hidden, sort_order);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_related_target
  ON experiment_catalog_point_related_links(target_node_id);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_search_state_status
  ON experiment_catalog_point_search_index_state(sync_status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_legacy_point
  ON experiment_catalog_legacy_identity_map(legacy_experiment_id, legacy_point_key)
  WHERE legacy_kind = 'experiment_point';

WITH canonical_experiments AS (
  SELECT
    fe.id AS experiment_id,
    'cat-exp-' || left(encode(digest(convert_to(fe.id, 'UTF8'), 'sha1'), 'hex'), 24) AS node_id,
    COALESCE(
      (
        SELECT ecb.chapter_id
        FROM experiment_chapter_bindings ecb
        WHERE ecb.experiment_id = fe.id
        ORDER BY CASE ecb.coverage_type WHEN 'primary' THEN 0 WHEN 'partial' THEN 1 ELSE 2 END, ecb.sort_order, ecb.chapter_id
        LIMIT 1
      ),
      NULLIF(btrim(fe.metadata->>'chapter_id'), ''),
      NULLIF(btrim(fe.metadata->>'primary_chapter_id'), ''),
      (SELECT c.id FROM chapters c ORDER BY c.chapter_number NULLS LAST, c.id LIMIT 1)
    ) AS chapter_id,
    fe.title,
    COALESCE(fe.summary, '') AS summary,
    CASE WHEN fe.status = 'published' THEN 'published' ELSE 'draft' END AS status,
    fe.display_order,
    fe.metadata,
    fe.published_at
  FROM formal_experiments fe
  WHERE fe.status <> 'archived'
),
ordered_experiments AS (
  SELECT
    *,
    row_number() OVER (PARTITION BY chapter_id ORDER BY display_order, experiment_id)::int AS root_order
  FROM canonical_experiments
  WHERE chapter_id IS NOT NULL
)
INSERT INTO experiment_catalog_nodes (
  id, chapter_id, parent_id, node_kind, title, summary, status, display_order,
  metadata, published_at, updated_at
)
SELECT
  node_id,
  chapter_id,
  NULL,
  'directory',
  btrim(title),
  summary,
  status,
  root_order,
  jsonb_build_object(
    'migrated_from', 'formal_experiments',
    'legacy_experiment_id', experiment_id,
    'legacy_metadata', metadata
  ),
  published_at,
  now()
FROM ordered_experiments
ON CONFLICT (id) DO UPDATE SET
  chapter_id = EXCLUDED.chapter_id,
  node_kind = EXCLUDED.node_kind,
  title = EXCLUDED.title,
  summary = EXCLUDED.summary,
  status = EXCLUDED.status,
  display_order = EXCLUDED.display_order,
  metadata = experiment_catalog_nodes.metadata || EXCLUDED.metadata,
  published_at = COALESCE(experiment_catalog_nodes.published_at, EXCLUDED.published_at),
  updated_at = now();

WITH canonical_experiments AS (
  SELECT
    fe.id AS experiment_id,
    'cat-exp-' || left(encode(digest(convert_to(fe.id, 'UTF8'), 'sha1'), 'hex'), 24) AS node_id,
    jsonb_build_object(
      'legacy_experiment_id', fe.id,
      'legacy_code', fe.code,
      'legacy_title', fe.title,
      'legacy_status', fe.status,
      'legacy_metadata', fe.metadata
    ) AS payload
  FROM formal_experiments fe
  JOIN experiment_catalog_nodes n
    ON n.id = 'cat-exp-' || left(encode(digest(convert_to(fe.id, 'UTF8'), 'sha1'), 'hex'), 24)
)
INSERT INTO experiment_catalog_legacy_identity_map (
  legacy_identity, legacy_kind, legacy_experiment_id, legacy_point_key, catalog_node_id, legacy_payload
)
SELECT
  'formal_experiment:' || experiment_id,
  'formal_experiment',
  experiment_id,
  NULL,
  node_id,
  payload
FROM canonical_experiments
ON CONFLICT (legacy_identity) DO UPDATE SET
  catalog_node_id = EXCLUDED.catalog_node_id,
  legacy_payload = EXCLUDED.legacy_payload;

WITH point_nodes AS (
  SELECT
    evp.experiment_id,
    evp.point_key,
    'cat-point-' || left(encode(digest(convert_to(evp.experiment_id || '::' || evp.point_key, 'UTF8'), 'sha1'), 'hex'), 24) AS node_id,
    exp_map.catalog_node_id AS parent_id,
    parent.chapter_id,
    evp.point_title,
    evp.display_order,
    CASE
      WHEN COALESCE(epc.content_status, '') = 'published' AND parent.status = 'published' THEN 'published'
      ELSE 'draft'
    END AS status,
    evp.metadata,
    epc.published_at
  FROM experiment_video_points evp
  JOIN experiment_catalog_legacy_identity_map exp_map
    ON exp_map.legacy_kind = 'formal_experiment'
   AND exp_map.legacy_experiment_id = evp.experiment_id
  JOIN experiment_catalog_nodes parent ON parent.id = exp_map.catalog_node_id
  LEFT JOIN experiment_point_learning_content epc
    ON epc.experiment_id = evp.experiment_id
   AND epc.point_key = evp.point_key
  WHERE evp.status <> 'archived'
)
INSERT INTO experiment_catalog_nodes (
  id, chapter_id, parent_id, node_kind, title, summary, status, display_order,
  metadata, published_at, updated_at
)
SELECT
  node_id,
  chapter_id,
  parent_id,
  'point',
  btrim(point_title),
  '',
  status,
  display_order,
  jsonb_build_object(
    'migrated_from', 'experiment_video_points',
    'legacy_experiment_id', experiment_id,
    'legacy_point_key', point_key,
    'legacy_metadata', metadata
  ),
  published_at,
  now()
FROM point_nodes
ON CONFLICT (id) DO UPDATE SET
  chapter_id = EXCLUDED.chapter_id,
  parent_id = EXCLUDED.parent_id,
  node_kind = EXCLUDED.node_kind,
  title = EXCLUDED.title,
  status = EXCLUDED.status,
  display_order = EXCLUDED.display_order,
  metadata = experiment_catalog_nodes.metadata || EXCLUDED.metadata,
  published_at = COALESCE(experiment_catalog_nodes.published_at, EXCLUDED.published_at),
  updated_at = now();

WITH point_nodes AS (
  SELECT
    evp.experiment_id,
    evp.point_key,
    'cat-point-' || left(encode(digest(convert_to(evp.experiment_id || '::' || evp.point_key, 'UTF8'), 'sha1'), 'hex'), 24) AS node_id,
    jsonb_build_object(
      'legacy_experiment_id', evp.experiment_id,
      'legacy_point_key', evp.point_key,
      'legacy_point_title', evp.point_title,
      'legacy_source', evp.source,
      'legacy_metadata', evp.metadata
    ) AS payload
  FROM experiment_video_points evp
  JOIN experiment_catalog_nodes n
    ON n.id = 'cat-point-' || left(encode(digest(convert_to(evp.experiment_id || '::' || evp.point_key, 'UTF8'), 'sha1'), 'hex'), 24)
)
INSERT INTO experiment_catalog_legacy_identity_map (
  legacy_identity, legacy_kind, legacy_experiment_id, legacy_point_key, catalog_node_id, legacy_payload
)
SELECT
  'experiment_point:' || experiment_id || '::' || point_key,
  'experiment_point',
  experiment_id,
  point_key,
  node_id,
  payload
FROM point_nodes
ON CONFLICT (legacy_identity) DO UPDATE SET
  catalog_node_id = EXCLUDED.catalog_node_id,
  legacy_payload = EXCLUDED.legacy_payload;

INSERT INTO experiment_catalog_point_content (
  node_id, point_title, teacher_note, principle_mode, principle_equation, principle_text,
  phenomenon_explanation, safety_note, content_status, published_at, published_by,
  created_by, updated_by, metadata, created_at, updated_at
)
SELECT
  point_map.catalog_node_id,
  btrim(evp.point_title),
  '',
  COALESCE(epc.principle_mode, 'text'),
  epc.principle_equation,
  epc.principle_text,
  COALESCE(epc.phenomenon_explanation, ''),
  COALESCE(epc.safety_note, ''),
  COALESCE(epc.content_status, 'draft'),
  epc.published_at,
  epc.published_by,
  epc.created_by,
  epc.updated_by,
  COALESCE(epc.metadata, '{}'::jsonb) || jsonb_build_object(
    'migrated_from', 'experiment_point_learning_content',
    'legacy_experiment_id', evp.experiment_id,
    'legacy_point_key', evp.point_key
  ),
  COALESCE(epc.created_at, evp.created_at, now()),
  now()
FROM experiment_video_points evp
JOIN experiment_catalog_legacy_identity_map point_map
  ON point_map.legacy_kind = 'experiment_point'
 AND point_map.legacy_experiment_id = evp.experiment_id
 AND point_map.legacy_point_key = evp.point_key
LEFT JOIN experiment_point_learning_content epc
  ON epc.experiment_id = evp.experiment_id
 AND epc.point_key = evp.point_key
WHERE evp.status <> 'archived'
ON CONFLICT (node_id) DO UPDATE SET
  point_title = EXCLUDED.point_title,
  principle_mode = EXCLUDED.principle_mode,
  principle_equation = EXCLUDED.principle_equation,
  principle_text = EXCLUDED.principle_text,
  phenomenon_explanation = EXCLUDED.phenomenon_explanation,
  safety_note = EXCLUDED.safety_note,
  content_status = EXCLUDED.content_status,
  published_at = EXCLUDED.published_at,
  published_by = EXCLUDED.published_by,
  metadata = experiment_catalog_point_content.metadata || EXCLUDED.metadata,
  updated_at = now();

INSERT INTO experiment_catalog_point_related_links (
  id, source_node_id, target_node_id, relation_type, hidden, sort_order, label,
  metadata, created_by, updated_by, created_at, updated_at
)
SELECT
  l.id,
  source_map.catalog_node_id,
  target_map.catalog_node_id,
  l.relation_type,
  l.hidden,
  l.sort_order,
  l.label,
  COALESCE(l.metadata, '{}'::jsonb) || jsonb_build_object(
    'migrated_from', 'experiment_point_related_links',
    'legacy_source_experiment_id', l.source_experiment_id,
    'legacy_source_point_key', l.source_point_key,
    'legacy_target_experiment_id', l.target_experiment_id,
    'legacy_target_point_key', l.target_point_key
  ),
  l.created_by,
  l.updated_by,
  l.created_at,
  now()
FROM experiment_point_related_links l
JOIN experiment_catalog_legacy_identity_map source_map
  ON source_map.legacy_kind = 'experiment_point'
 AND source_map.legacy_experiment_id = l.source_experiment_id
 AND source_map.legacy_point_key = l.source_point_key
JOIN experiment_catalog_legacy_identity_map target_map
  ON target_map.legacy_kind = 'experiment_point'
 AND target_map.legacy_experiment_id = l.target_experiment_id
 AND target_map.legacy_point_key = l.target_point_key
WHERE source_map.catalog_node_id <> target_map.catalog_node_id
ON CONFLICT (id) DO UPDATE SET
  source_node_id = EXCLUDED.source_node_id,
  target_node_id = EXCLUDED.target_node_id,
  relation_type = EXCLUDED.relation_type,
  hidden = EXCLUDED.hidden,
  sort_order = EXCLUDED.sort_order,
  label = EXCLUDED.label,
  metadata = experiment_catalog_point_related_links.metadata || EXCLUDED.metadata,
  updated_by = EXCLUDED.updated_by,
  updated_at = now();

INSERT INTO experiment_catalog_point_media_bindings (
  id, node_id, media_asset_id, title, binding_status, display_order, published_by,
  published_at, metadata, created_at, updated_at
)
SELECT
  mb.id,
  point_map.catalog_node_id,
  mb.media_asset_id,
  mb.title,
  mb.status,
  mb.sort_order,
  mb.published_by,
  mb.published_at,
  COALESCE(mb.metadata, '{}'::jsonb) || jsonb_build_object(
    'migrated_from', 'media_bindings',
    'legacy_target_type', mb.target_type,
    'legacy_target_id', mb.target_id
  ),
  mb.created_at,
  now()
FROM media_bindings mb
JOIN experiment_catalog_legacy_identity_map point_map
  ON point_map.legacy_kind = 'experiment_point'
 AND point_map.legacy_experiment_id = mb.target_id
 AND point_map.legacy_point_key = mb.metadata->>'point_key'
WHERE mb.target_type = 'experiment'
  AND mb.status <> 'archived'
  AND NULLIF(btrim(mb.metadata->>'point_key'), '') IS NOT NULL
ON CONFLICT (node_id, media_asset_id) DO UPDATE SET
  title = EXCLUDED.title,
  binding_status = EXCLUDED.binding_status,
  display_order = EXCLUDED.display_order,
  published_by = EXCLUDED.published_by,
  published_at = EXCLUDED.published_at,
  metadata = experiment_catalog_point_media_bindings.metadata || EXCLUDED.metadata,
  updated_at = now();

INSERT INTO experiment_catalog_point_search_index_state (
  node_id, document_id, desired_action, sync_status, attempts, document_hash,
  last_error, indexed_at, last_attempted_at, created_at, updated_at
)
SELECT
  point_map.catalog_node_id,
  point_map.catalog_node_id,
  s.desired_action,
  s.sync_status,
  s.attempts,
  s.document_hash,
  s.last_error,
  s.indexed_at,
  s.last_attempted_at,
  s.created_at,
  now()
FROM experiment_video_point_search_index_state s
JOIN experiment_catalog_legacy_identity_map point_map
  ON point_map.legacy_kind = 'experiment_point'
 AND point_map.legacy_experiment_id = s.experiment_id
 AND point_map.legacy_point_key = s.point_key
ON CONFLICT (node_id) DO UPDATE SET
  document_id = EXCLUDED.document_id,
  desired_action = EXCLUDED.desired_action,
  sync_status = EXCLUDED.sync_status,
  attempts = EXCLUDED.attempts,
  document_hash = EXCLUDED.document_hash,
  last_error = EXCLUDED.last_error,
  indexed_at = EXCLUDED.indexed_at,
  last_attempted_at = EXCLUDED.last_attempted_at,
  updated_at = now();

ALTER TABLE experiment_questions
  ADD COLUMN IF NOT EXISTS primary_point_node_ids text[] NOT NULL DEFAULT '{}';

WITH question_points AS (
  SELECT
    q.id,
    array_agg(point_map.catalog_node_id ORDER BY pk.ordinality) AS point_node_ids,
    jsonb_agg(point_map.catalog_node_id ORDER BY pk.ordinality) AS point_node_ids_json
  FROM experiment_questions q
  CROSS JOIN LATERAL jsonb_array_elements_text(
    CASE
      WHEN jsonb_typeof(q.metadata->'primary_point_keys') = 'array' THEN q.metadata->'primary_point_keys'
      WHEN jsonb_typeof(q.metadata->'target_point_keys') = 'array' THEN q.metadata->'target_point_keys'
      ELSE '[]'::jsonb
    END
  ) WITH ORDINALITY AS pk(value, ordinality)
  JOIN experiment_catalog_legacy_identity_map point_map
    ON point_map.legacy_kind = 'experiment_point'
   AND point_map.legacy_experiment_id = q.experiment_id
   AND point_map.legacy_point_key = pk.value
  GROUP BY q.id
)
UPDATE experiment_questions q
SET primary_point_node_ids = question_points.point_node_ids,
    metadata = q.metadata || jsonb_build_object(
      'primary_point_node_ids', question_points.point_node_ids_json,
      'point_identity_migration', jsonb_build_object('source', 'experiment_catalog_legacy_identity_map')
    ),
    updated_at = now()
FROM question_points
WHERE q.id = question_points.id;

ALTER TABLE experiment_video_point_evidence
  ADD COLUMN IF NOT EXISTS point_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

UPDATE experiment_video_point_evidence evidence
SET point_node_id = point_map.catalog_node_id,
    metadata = COALESCE(evidence.metadata, '{}'::jsonb) || jsonb_build_object(
      'point_node_id', point_map.catalog_node_id,
      'point_identity_migration', jsonb_build_object('source', 'experiment_catalog_legacy_identity_map')
    ),
    updated_at = now()
FROM experiment_catalog_legacy_identity_map point_map
WHERE point_map.legacy_kind = 'experiment_point'
  AND point_map.legacy_experiment_id = evidence.experiment_id
  AND point_map.legacy_point_key = evidence.point_key;

CREATE INDEX IF NOT EXISTS idx_experiment_video_point_evidence_node
  ON experiment_video_point_evidence(point_node_id);

ALTER TABLE experiment_question_attempts
  ADD COLUMN IF NOT EXISTS point_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

ALTER TABLE experiment_question_attempts
  ADD COLUMN IF NOT EXISTS chapter_id text REFERENCES chapters(id) ON DELETE SET NULL;

WITH attempt_points AS (
  SELECT
    a.id,
    COALESCE(
      direct_map.catalog_node_id,
      CASE WHEN array_length(q.primary_point_node_ids, 1) > 0 THEN q.primary_point_node_ids[1] ELSE NULL END
    ) AS point_node_id
  FROM experiment_question_attempts a
  LEFT JOIN experiment_catalog_legacy_identity_map direct_map
    ON direct_map.legacy_kind = 'experiment_point'
   AND direct_map.legacy_experiment_id = a.experiment_id
   AND direct_map.legacy_point_key = a.metadata->>'point_key'
  LEFT JOIN experiment_questions q ON q.id = a.question_id
)
UPDATE experiment_question_attempts a
SET point_node_id = attempt_points.point_node_id,
    chapter_id = n.chapter_id,
    metadata = COALESCE(a.metadata, '{}'::jsonb) || jsonb_build_object(
      'point_node_id', attempt_points.point_node_id,
      'chapter_id', n.chapter_id
    )
FROM attempt_points
JOIN experiment_catalog_nodes n ON n.id = attempt_points.point_node_id
WHERE a.id = attempt_points.id
  AND attempt_points.point_node_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_experiment_question_attempts_point_node
  ON experiment_question_attempts(point_node_id, created_at DESC);

ALTER TABLE student_events
  ADD COLUMN IF NOT EXISTS point_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

ALTER TABLE student_events
  ADD COLUMN IF NOT EXISTS catalog_path jsonb NOT NULL DEFAULT '[]'::jsonb;

WITH event_points AS (
  SELECT
    se.id,
    point_map.catalog_node_id
  FROM student_events se
  JOIN experiment_catalog_legacy_identity_map point_map
    ON point_map.legacy_kind = 'experiment_point'
   AND point_map.legacy_experiment_id = se.experiment_id
   AND point_map.legacy_point_key = se.metadata->>'point_key'
)
UPDATE student_events se
SET point_node_id = event_points.catalog_node_id,
    chapter_id = n.chapter_id,
    metadata = COALESCE(se.metadata, '{}'::jsonb) || jsonb_build_object(
      'point_node_id', event_points.catalog_node_id,
      'chapter_id', n.chapter_id
    )
FROM event_points
JOIN experiment_catalog_nodes n ON n.id = event_points.catalog_node_id
WHERE se.id = event_points.id;

CREATE INDEX IF NOT EXISTS idx_student_events_point_node
  ON student_events(student_id, point_node_id, created_at DESC);

ALTER TABLE student_posttest_sessions
  ADD COLUMN IF NOT EXISTS point_node_ids jsonb NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE student_posttest_sessions
  ADD COLUMN IF NOT EXISTS chapter_ids jsonb NOT NULL DEFAULT '[]'::jsonb;

WITH session_points AS (
  SELECT
    s.id,
    jsonb_agg(DISTINCT n.id) FILTER (WHERE n.id IS NOT NULL) AS point_node_ids,
    jsonb_agg(DISTINCT n.chapter_id) FILTER (WHERE n.chapter_id IS NOT NULL) AS chapter_ids
  FROM student_posttest_sessions s
  LEFT JOIN LATERAL jsonb_array_elements_text(
    CASE WHEN jsonb_typeof(s.metadata->'point_keys') = 'array' THEN s.metadata->'point_keys' ELSE '[]'::jsonb END
  ) point_key(value) ON true
  LEFT JOIN LATERAL jsonb_array_elements_text(
    CASE WHEN jsonb_typeof(s.experiment_ids) = 'array' THEN s.experiment_ids ELSE '[]'::jsonb END
  ) experiment_id(value) ON true
  LEFT JOIN experiment_catalog_legacy_identity_map point_map
    ON point_map.legacy_kind = 'experiment_point'
   AND point_map.legacy_experiment_id = experiment_id.value
   AND point_map.legacy_point_key = point_key.value
  LEFT JOIN experiment_catalog_nodes n ON n.id = point_map.catalog_node_id
  GROUP BY s.id
)
UPDATE student_posttest_sessions s
SET point_node_ids = COALESCE(session_points.point_node_ids, '[]'::jsonb),
    chapter_ids = COALESCE(session_points.chapter_ids, '[]'::jsonb),
    metadata = COALESCE(s.metadata, '{}'::jsonb) || jsonb_build_object(
      'point_node_ids', COALESCE(session_points.point_node_ids, '[]'::jsonb),
      'chapter_ids', COALESCE(session_points.chapter_ids, '[]'::jsonb)
    )
FROM session_points
WHERE s.id = session_points.id
  AND session_points.point_node_ids IS NOT NULL;

ALTER TABLE student_feedback
  ADD COLUMN IF NOT EXISTS point_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

ALTER TABLE student_feedback
  ADD COLUMN IF NOT EXISTS catalog_path jsonb NOT NULL DEFAULT '[]'::jsonb;

WITH feedback_points AS (
  SELECT
    f.id,
    point_map.catalog_node_id
  FROM student_feedback f
  JOIN experiment_catalog_legacy_identity_map point_map
    ON point_map.legacy_kind = 'experiment_point'
   AND point_map.legacy_experiment_id = f.experiment_id
   AND point_map.legacy_point_key = f.metadata->>'point_key'
)
UPDATE student_feedback f
SET point_node_id = feedback_points.catalog_node_id,
    chapter_id = n.chapter_id,
    metadata = COALESCE(f.metadata, '{}'::jsonb) || jsonb_build_object(
      'point_node_id', feedback_points.catalog_node_id,
      'chapter_id', n.chapter_id
    )
FROM feedback_points
JOIN experiment_catalog_nodes n ON n.id = feedback_points.catalog_node_id
WHERE f.id = feedback_points.id;

CREATE INDEX IF NOT EXISTS idx_student_feedback_point_node
  ON student_feedback(point_node_id, created_at DESC);

ALTER TABLE student_experiment_mastery
  ADD COLUMN IF NOT EXISTS point_node_id text REFERENCES experiment_catalog_nodes(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_student_experiment_mastery_point_node
  ON student_experiment_mastery(point_node_id, mastery_score);

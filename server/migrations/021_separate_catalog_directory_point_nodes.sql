ALTER TABLE experiment_catalog_nodes
  ADD COLUMN IF NOT EXISTS teacher_note text NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS student_description text NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS card_image_asset_id uuid REFERENCES media_assets(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS card_icon_key text,
  ADD COLUMN IF NOT EXISTS card_accent text,
  ADD COLUMN IF NOT EXISTS card_layout text NOT NULL DEFAULT 'default',
  ADD COLUMN IF NOT EXISTS card_presentation jsonb NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS point_card_presentation jsonb NOT NULL DEFAULT '{}'::jsonb;

UPDATE experiment_catalog_nodes
SET student_description = summary
WHERE btrim(student_description) = ''
  AND btrim(summary) <> '';

WITH hybrid_sources AS (
  SELECT
    n.id,
    n.chapter_id,
    n.title,
    n.summary,
    n.student_description,
    n.status,
    n.published_at,
    n.created_by,
    n.updated_by,
    n.metadata,
    n.point_card_presentation,
    'cat-point-' || left(encode(digest(convert_to(n.id || '::hybrid-point', 'UTF8'), 'sha1'), 'hex'), 24) AS point_id,
    COALESCE((SELECT max(child.display_order) + 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id), 1) AS point_order,
    EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id) AS has_children,
    (
      EXISTS (SELECT 1 FROM experiment_catalog_point_content pc WHERE pc.node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_catalog_point_media_bindings mb WHERE mb.node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_catalog_point_related_links rl WHERE rl.source_node_id = n.id OR rl.target_node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_catalog_legacy_identity_map lm WHERE lm.catalog_node_id = n.id AND lm.legacy_kind = 'experiment_point')
      OR EXISTS (SELECT 1 FROM experiment_video_point_evidence evidence WHERE evidence.point_node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_question_attempts attempts WHERE attempts.point_node_id = n.id)
      OR EXISTS (SELECT 1 FROM student_events events WHERE events.point_node_id = n.id)
      OR EXISTS (SELECT 1 FROM student_feedback feedback WHERE feedback.point_node_id = n.id)
      OR EXISTS (SELECT 1 FROM student_experiment_mastery mastery WHERE mastery.point_node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_questions questions WHERE n.id = ANY(questions.primary_point_node_ids))
      OR EXISTS (SELECT 1 FROM student_posttest_sessions sessions WHERE sessions.point_node_ids @> to_jsonb(ARRAY[n.id]))
    ) AS has_point_resources
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
),
hybrids_to_split AS (
  SELECT *
  FROM hybrid_sources
  WHERE has_children AND has_point_resources
)
INSERT INTO experiment_catalog_nodes (
  id, chapter_id, parent_id, node_kind, title, summary, student_description,
  status, display_order, metadata, published_at, created_by, updated_by, updated_at,
  point_card_presentation
)
SELECT
  point_id,
  chapter_id,
  id,
  'point',
  title,
  summary,
  student_description,
  status,
  point_order,
  metadata || jsonb_build_object(
    'node_kind_migration',
    jsonb_build_object(
      'source', '021_separate_catalog_directory_point_nodes',
      'from_node_kind', 'hybrid',
      'from_node_id', id,
      'split_role', 'point_child'
    )
  ),
  published_at,
  created_by,
  updated_by,
  now(),
  point_card_presentation
FROM hybrids_to_split
ON CONFLICT (id) DO NOTHING;

WITH hybrids_to_split AS (
  SELECT
    n.id,
    'cat-point-' || left(encode(digest(convert_to(n.id || '::hybrid-point', 'UTF8'), 'sha1'), 'hex'), 24) AS point_id
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
    AND EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id)
    AND (
      EXISTS (SELECT 1 FROM experiment_catalog_point_content pc WHERE pc.node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_catalog_point_media_bindings mb WHERE mb.node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_catalog_point_related_links rl WHERE rl.source_node_id = n.id OR rl.target_node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_catalog_legacy_identity_map lm WHERE lm.catalog_node_id = n.id AND lm.legacy_kind = 'experiment_point')
      OR EXISTS (SELECT 1 FROM experiment_video_point_evidence evidence WHERE evidence.point_node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_question_attempts attempts WHERE attempts.point_node_id = n.id)
      OR EXISTS (SELECT 1 FROM student_events events WHERE events.point_node_id = n.id)
      OR EXISTS (SELECT 1 FROM student_feedback feedback WHERE feedback.point_node_id = n.id)
      OR EXISTS (SELECT 1 FROM student_experiment_mastery mastery WHERE mastery.point_node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_questions questions WHERE n.id = ANY(questions.primary_point_node_ids))
      OR EXISTS (SELECT 1 FROM student_posttest_sessions sessions WHERE sessions.point_node_ids @> to_jsonb(ARRAY[n.id]))
    )
)
UPDATE experiment_catalog_point_content pc
SET node_id = h.point_id
FROM hybrids_to_split h
WHERE pc.node_id = h.id;

WITH hybrids_to_split AS (
  SELECT
    n.id,
    'cat-point-' || left(encode(digest(convert_to(n.id || '::hybrid-point', 'UTF8'), 'sha1'), 'hex'), 24) AS point_id
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
    AND EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id)
    AND EXISTS (SELECT 1 FROM experiment_catalog_point_media_bindings mb WHERE mb.node_id = n.id)
)
UPDATE experiment_catalog_point_media_bindings mb
SET node_id = h.point_id
FROM hybrids_to_split h
WHERE mb.node_id = h.id;

WITH hybrids_to_split AS (
  SELECT
    n.id,
    'cat-point-' || left(encode(digest(convert_to(n.id || '::hybrid-point', 'UTF8'), 'sha1'), 'hex'), 24) AS point_id
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
    AND EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id)
    AND EXISTS (SELECT 1 FROM experiment_catalog_point_related_links rl WHERE rl.source_node_id = n.id OR rl.target_node_id = n.id)
)
UPDATE experiment_catalog_point_related_links rl
SET source_node_id = CASE WHEN rl.source_node_id = h.id THEN h.point_id ELSE rl.source_node_id END,
    target_node_id = CASE WHEN rl.target_node_id = h.id THEN h.point_id ELSE rl.target_node_id END
FROM hybrids_to_split h
WHERE rl.source_node_id = h.id OR rl.target_node_id = h.id;

WITH hybrids_to_split AS (
  SELECT
    n.id,
    'cat-point-' || left(encode(digest(convert_to(n.id || '::hybrid-point', 'UTF8'), 'sha1'), 'hex'), 24) AS point_id
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
    AND EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id)
    AND EXISTS (SELECT 1 FROM experiment_catalog_point_search_index_state si WHERE si.node_id = n.id)
    AND (
      EXISTS (SELECT 1 FROM experiment_catalog_point_content pc WHERE pc.node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_catalog_point_media_bindings mb WHERE mb.node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_catalog_point_related_links rl WHERE rl.source_node_id = n.id OR rl.target_node_id = n.id)
    )
)
UPDATE experiment_catalog_point_search_index_state si
SET node_id = h.point_id,
    document_id = h.point_id,
    updated_at = now()
FROM hybrids_to_split h
WHERE si.node_id = h.id;

WITH hybrids_to_split AS (
  SELECT
    n.id,
    'cat-point-' || left(encode(digest(convert_to(n.id || '::hybrid-point', 'UTF8'), 'sha1'), 'hex'), 24) AS point_id
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
    AND EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id)
)
UPDATE experiment_catalog_legacy_identity_map lm
SET catalog_node_id = h.point_id
FROM hybrids_to_split h
WHERE lm.catalog_node_id = h.id
  AND lm.legacy_kind = 'experiment_point';

WITH hybrids_to_split AS (
  SELECT
    n.id,
    'cat-point-' || left(encode(digest(convert_to(n.id || '::hybrid-point', 'UTF8'), 'sha1'), 'hex'), 24) AS point_id
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
    AND EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id)
)
UPDATE experiment_video_point_evidence evidence
SET point_node_id = h.point_id,
    metadata = COALESCE(evidence.metadata, '{}'::jsonb) || jsonb_build_object(
      'point_node_id', h.point_id,
      'node_kind_migration', jsonb_build_object(
        'source', '021_separate_catalog_directory_point_nodes',
        'from_node_id', h.id
      )
    ),
    updated_at = now()
FROM hybrids_to_split h
WHERE evidence.point_node_id = h.id;

WITH hybrids_to_split AS (
  SELECT
    n.id,
    'cat-point-' || left(encode(digest(convert_to(n.id || '::hybrid-point', 'UTF8'), 'sha1'), 'hex'), 24) AS point_id
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
    AND EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id)
)
UPDATE experiment_question_attempts attempts
SET point_node_id = h.point_id,
    metadata = COALESCE(attempts.metadata, '{}'::jsonb) || jsonb_build_object('point_node_id', h.point_id)
FROM hybrids_to_split h
WHERE attempts.point_node_id = h.id;

WITH hybrids_to_split AS (
  SELECT
    n.id,
    'cat-point-' || left(encode(digest(convert_to(n.id || '::hybrid-point', 'UTF8'), 'sha1'), 'hex'), 24) AS point_id
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
    AND EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id)
)
UPDATE student_events events
SET point_node_id = h.point_id,
    metadata = COALESCE(events.metadata, '{}'::jsonb) || jsonb_build_object('point_node_id', h.point_id)
FROM hybrids_to_split h
WHERE events.point_node_id = h.id;

WITH hybrids_to_split AS (
  SELECT
    n.id,
    'cat-point-' || left(encode(digest(convert_to(n.id || '::hybrid-point', 'UTF8'), 'sha1'), 'hex'), 24) AS point_id
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
    AND EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id)
)
UPDATE student_feedback feedback
SET point_node_id = h.point_id,
    metadata = COALESCE(feedback.metadata, '{}'::jsonb) || jsonb_build_object('point_node_id', h.point_id),
    updated_at = now()
FROM hybrids_to_split h
WHERE feedback.point_node_id = h.id;

WITH hybrids_to_split AS (
  SELECT
    n.id,
    'cat-point-' || left(encode(digest(convert_to(n.id || '::hybrid-point', 'UTF8'), 'sha1'), 'hex'), 24) AS point_id
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
    AND EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id)
)
UPDATE student_experiment_mastery mastery
SET point_node_id = h.point_id,
    metadata = COALESCE(mastery.metadata, '{}'::jsonb) || jsonb_build_object('point_node_id', h.point_id),
    updated_at = now()
FROM hybrids_to_split h
WHERE mastery.point_node_id = h.id;

WITH hybrids_to_split AS (
  SELECT
    n.id,
    'cat-point-' || left(encode(digest(convert_to(n.id || '::hybrid-point', 'UTF8'), 'sha1'), 'hex'), 24) AS point_id
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
    AND EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id)
)
UPDATE experiment_questions questions
SET primary_point_node_ids = ARRAY(
      SELECT COALESCE(h.point_id, item.value)
      FROM unnest(questions.primary_point_node_ids) AS item(value)
      LEFT JOIN hybrids_to_split h ON h.id = item.value
    ),
    metadata = COALESCE(questions.metadata, '{}'::jsonb) || jsonb_build_object(
      'primary_point_node_ids',
      to_jsonb(ARRAY(
        SELECT COALESCE(h.point_id, item.value)
        FROM unnest(questions.primary_point_node_ids) AS item(value)
        LEFT JOIN hybrids_to_split h ON h.id = item.value
      ))
    ),
    updated_at = now()
WHERE EXISTS (
  SELECT 1
  FROM unnest(questions.primary_point_node_ids) AS item(value)
  JOIN hybrids_to_split h ON h.id = item.value
);

WITH hybrids_to_split AS (
  SELECT
    n.id,
    'cat-point-' || left(encode(digest(convert_to(n.id || '::hybrid-point', 'UTF8'), 'sha1'), 'hex'), 24) AS point_id
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
    AND EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id)
)
UPDATE student_posttest_sessions sessions
SET point_node_ids = COALESCE((
      SELECT jsonb_agg(COALESCE(h.point_id, item.value))
      FROM jsonb_array_elements_text(sessions.point_node_ids) AS item(value)
      LEFT JOIN hybrids_to_split h ON h.id = item.value
    ), '[]'::jsonb),
    metadata = COALESCE(sessions.metadata, '{}'::jsonb) || jsonb_build_object(
      'point_node_ids',
      COALESCE((
        SELECT jsonb_agg(COALESCE(h.point_id, item.value))
        FROM jsonb_array_elements_text(sessions.point_node_ids) AS item(value)
        LEFT JOIN hybrids_to_split h ON h.id = item.value
      ), '[]'::jsonb)
    ),
    updated_at = now()
WHERE EXISTS (
  SELECT 1
  FROM jsonb_array_elements_text(sessions.point_node_ids) AS item(value)
  JOIN hybrids_to_split h ON h.id = item.value
);

WITH hybrid_sources AS (
  SELECT
    n.id,
    EXISTS (SELECT 1 FROM experiment_catalog_nodes child WHERE child.parent_id = n.id) AS has_children,
    (
      EXISTS (SELECT 1 FROM experiment_catalog_point_content pc WHERE pc.node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_catalog_point_media_bindings mb WHERE mb.node_id = n.id)
      OR EXISTS (SELECT 1 FROM experiment_catalog_point_related_links rl WHERE rl.source_node_id = n.id OR rl.target_node_id = n.id)
    ) AS has_point_resources
  FROM experiment_catalog_nodes n
  WHERE n.node_kind = 'hybrid'
)
UPDATE experiment_catalog_nodes n
SET node_kind = CASE WHEN h.has_children THEN 'directory' WHEN h.has_point_resources THEN 'point' ELSE 'directory' END,
    metadata = n.metadata || jsonb_build_object(
      'node_kind_migration',
      jsonb_build_object(
        'source', '021_separate_catalog_directory_point_nodes',
        'from_node_kind', 'hybrid',
        'normalized_to', CASE WHEN h.has_children THEN 'directory' WHEN h.has_point_resources THEN 'point' ELSE 'directory' END,
        'had_children', h.has_children,
        'had_point_resources', h.has_point_resources
      )
    ),
    updated_at = now()
FROM hybrid_sources h
WHERE n.id = h.id;

UPDATE experiment_catalog_nodes
SET node_kind = 'directory',
    status = 'archived',
    metadata = metadata || jsonb_build_object(
      'node_kind_migration',
      jsonb_build_object(
        'source', '021_separate_catalog_directory_point_nodes',
        'from_node_kind', 'shortcut',
        'normalized_to', 'directory',
        'archived', true,
        'legacy_shortcut_target_node_id', shortcut_target_node_id
      )
    ),
    shortcut_target_node_id = NULL,
    updated_at = now()
WHERE node_kind = 'shortcut';

DELETE FROM experiment_catalog_nodes n
WHERE n.node_kind = 'point'
  AND n.metadata -> 'node_kind_migration' ->> 'source' = '021_separate_catalog_directory_point_nodes'
  AND n.metadata -> 'node_kind_migration' ->> 'split_role' = 'point_child'
  AND NOT EXISTS (SELECT 1 FROM experiment_catalog_point_content pc WHERE pc.node_id = n.id)
  AND NOT EXISTS (SELECT 1 FROM experiment_catalog_point_media_bindings mb WHERE mb.node_id = n.id)
  AND NOT EXISTS (
    SELECT 1
    FROM experiment_catalog_point_related_links rl
    WHERE rl.source_node_id = n.id OR rl.target_node_id = n.id
  )
  AND NOT EXISTS (SELECT 1 FROM experiment_catalog_legacy_identity_map lm WHERE lm.catalog_node_id = n.id AND lm.legacy_kind = 'experiment_point')
  AND NOT EXISTS (SELECT 1 FROM experiment_video_point_evidence evidence WHERE evidence.point_node_id = n.id)
  AND NOT EXISTS (SELECT 1 FROM experiment_question_attempts attempts WHERE attempts.point_node_id = n.id)
  AND NOT EXISTS (SELECT 1 FROM student_events events WHERE events.point_node_id = n.id)
  AND NOT EXISTS (SELECT 1 FROM student_feedback feedback WHERE feedback.point_node_id = n.id)
  AND NOT EXISTS (SELECT 1 FROM student_experiment_mastery mastery WHERE mastery.point_node_id = n.id)
  AND NOT EXISTS (
    SELECT 1
    FROM experiment_questions questions
    WHERE n.id = ANY(questions.primary_point_node_ids)
  )
  AND NOT EXISTS (
    SELECT 1
    FROM student_posttest_sessions sessions
    WHERE sessions.point_node_ids @> to_jsonb(ARRAY[n.id])
  );

DROP INDEX IF EXISTS idx_experiment_catalog_nodes_shortcut_target;

ALTER TABLE experiment_catalog_nodes
  DROP CONSTRAINT IF EXISTS experiment_catalog_nodes_check1,
  DROP CONSTRAINT IF EXISTS experiment_catalog_nodes_check2,
  DROP CONSTRAINT IF EXISTS experiment_catalog_nodes_shortcut_target_node_id_fkey,
  DROP CONSTRAINT IF EXISTS experiment_catalog_nodes_node_kind_check;

ALTER TABLE experiment_catalog_nodes
  DROP COLUMN IF EXISTS shortcut_target_node_id;

ALTER TABLE experiment_catalog_nodes
  ADD CONSTRAINT experiment_catalog_nodes_node_kind_check CHECK (node_kind IN ('directory', 'point'));

CREATE INDEX IF NOT EXISTS idx_experiment_catalog_nodes_card_image
  ON experiment_catalog_nodes(card_image_asset_id)
  WHERE card_image_asset_id IS NOT NULL;

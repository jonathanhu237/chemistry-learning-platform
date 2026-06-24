CREATE TABLE IF NOT EXISTS student_point_mastery (
  student_id text NOT NULL,
  class_id text REFERENCES classes(id) ON DELETE SET NULL,
  point_node_id text NOT NULL REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  experiment_id text REFERENCES formal_experiments(id) ON DELETE SET NULL,
  canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE SET NULL,
  mastery_prob numeric NOT NULL DEFAULT 0.5,
  mastery_score numeric NOT NULL DEFAULT 50,
  evidence_count int NOT NULL DEFAULT 0,
  last_evidence_kind text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (student_id, point_node_id)
);

CREATE INDEX IF NOT EXISTS idx_student_point_mastery_class
  ON student_point_mastery(class_id, point_node_id, mastery_score);

CREATE INDEX IF NOT EXISTS idx_student_point_mastery_experiment
  ON student_point_mastery(student_id, experiment_id, mastery_score)
  WHERE experiment_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_student_point_mastery_canonical
  ON student_point_mastery(canonical_point_id, mastery_score)
  WHERE canonical_point_id IS NOT NULL;

INSERT INTO student_point_mastery (
  student_id, class_id, point_node_id, experiment_id, canonical_point_id,
  mastery_prob, mastery_score, evidence_count, last_evidence_kind, metadata, created_at, updated_at
)
SELECT
  m.student_id,
  m.class_id,
  m.point_node_id,
  m.experiment_id,
  m.canonical_point_id,
  m.mastery_prob,
  m.mastery_score,
  m.evidence_count,
  m.last_evidence_kind,
  COALESCE(m.metadata, '{}'::jsonb) || jsonb_build_object(
    'migration_source', '037_student_point_mastery',
    'legacy_table', 'student_experiment_mastery'
  ),
  m.created_at,
  m.updated_at
FROM student_experiment_mastery m
JOIN experiment_catalog_nodes n ON n.id = m.point_node_id
WHERE m.point_node_id IS NOT NULL
  AND n.node_kind = 'point'
ON CONFLICT (student_id, point_node_id) DO UPDATE SET
  class_id = COALESCE(EXCLUDED.class_id, student_point_mastery.class_id),
  experiment_id = COALESCE(EXCLUDED.experiment_id, student_point_mastery.experiment_id),
  canonical_point_id = COALESCE(EXCLUDED.canonical_point_id, student_point_mastery.canonical_point_id),
  mastery_prob = EXCLUDED.mastery_prob,
  mastery_score = EXCLUDED.mastery_score,
  evidence_count = GREATEST(student_point_mastery.evidence_count, EXCLUDED.evidence_count),
  last_evidence_kind = COALESCE(EXCLUDED.last_evidence_kind, student_point_mastery.last_evidence_kind),
  metadata = student_point_mastery.metadata || EXCLUDED.metadata,
  updated_at = now();

ALTER TABLE student_smart_assessment_sessions
  ADD COLUMN IF NOT EXISTS point_node_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS canonical_point_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS source_placement_node_ids jsonb NOT NULL DEFAULT '[]'::jsonb;

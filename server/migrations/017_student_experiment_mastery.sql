CREATE TABLE IF NOT EXISTS student_experiment_mastery (
  student_id text NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  class_id text REFERENCES classes(id) ON DELETE SET NULL,
  experiment_id text NOT NULL REFERENCES formal_experiments(id) ON DELETE CASCADE,
  mastery_prob numeric NOT NULL DEFAULT 0.5,
  mastery_score numeric NOT NULL DEFAULT 50,
  evidence_count int NOT NULL DEFAULT 0,
  last_evidence_kind text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (student_id, experiment_id)
);

CREATE INDEX IF NOT EXISTS idx_student_experiment_mastery_class
  ON student_experiment_mastery(class_id, experiment_id);

CREATE INDEX IF NOT EXISTS idx_student_experiment_mastery_experiment
  ON student_experiment_mastery(experiment_id, mastery_score);

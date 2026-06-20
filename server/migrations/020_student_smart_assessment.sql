CREATE TABLE IF NOT EXISTS student_smart_assessment_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id text NOT NULL,
  class_id text REFERENCES classes(id) ON DELETE SET NULL,
  status text NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),
  strategy_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
  composition_summary jsonb NOT NULL DEFAULT '{}'::jsonb,
  experiment_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  question_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  mastery_before jsonb NOT NULL DEFAULT '{}'::jsonb,
  mastery_after jsonb NOT NULL DEFAULT '{}'::jsonb,
  report jsonb NOT NULL DEFAULT '{}'::jsonb,
  score numeric,
  correct_count int,
  total_count int,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  completed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_student_smart_assessment_sessions_open
ON student_smart_assessment_sessions(student_id)
WHERE status = 'in_progress';

CREATE INDEX IF NOT EXISTS idx_student_smart_assessment_sessions_student
ON student_smart_assessment_sessions(student_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_student_smart_assessment_sessions_class
ON student_smart_assessment_sessions(class_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS class_smart_assessment_settings (
  class_id text PRIMARY KEY REFERENCES classes(id) ON DELETE CASCADE,
  value jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

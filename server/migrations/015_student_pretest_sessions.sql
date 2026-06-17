CREATE TABLE IF NOT EXISTS student_pretest_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id text NOT NULL,
  class_id text REFERENCES classes(id) ON DELETE SET NULL,
  status text NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),
  current_stage int CHECK (current_stage IN (1, 2) OR current_stage IS NULL),
  stage1_question_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  stage2_question_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
  weakest_area text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  stage1_submitted_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_student_pretest_sessions_open
ON student_pretest_sessions(student_id)
WHERE status = 'in_progress';

CREATE UNIQUE INDEX IF NOT EXISTS idx_student_pretest_sessions_completed
ON student_pretest_sessions(student_id)
WHERE status = 'completed';

CREATE INDEX IF NOT EXISTS idx_student_pretest_sessions_class
ON student_pretest_sessions(class_id, status, created_at DESC);

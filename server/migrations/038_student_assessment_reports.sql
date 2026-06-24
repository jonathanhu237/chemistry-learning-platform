CREATE TABLE IF NOT EXISTS student_assessment_reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id text NOT NULL,
  class_id text REFERENCES classes(id) ON DELETE SET NULL,
  report_type text NOT NULL CHECK (report_type IN ('pretest', 'smart', 'custom', 'point', 'posttest')),
  source_session_id uuid NOT NULL,
  source_table text NOT NULL,
  title text NOT NULL,
  score numeric NOT NULL DEFAULT 0,
  correct_count int NOT NULL DEFAULT 0,
  total_count int NOT NULL DEFAULT 0,
  correct_rate numeric NOT NULL DEFAULT 0,
  wrong_count int NOT NULL DEFAULT 0,
  summary jsonb NOT NULL DEFAULT '{}'::jsonb,
  mistake_explanation jsonb NOT NULL DEFAULT '{}'::jsonb,
  prompt_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  completed_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (report_type, source_session_id)
);

CREATE INDEX IF NOT EXISTS idx_student_assessment_reports_student
ON student_assessment_reports(student_id, completed_at DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_student_assessment_reports_class_student
ON student_assessment_reports(class_id, student_id, completed_at DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_student_assessment_reports_source
ON student_assessment_reports(source_table, source_session_id);

CREATE TABLE IF NOT EXISTS class_assessment_report_prompt_settings (
  class_id text PRIMARY KEY REFERENCES classes(id) ON DELETE CASCADE,
  value jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

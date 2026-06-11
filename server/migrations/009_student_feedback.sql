CREATE TABLE IF NOT EXISTS student_feedback (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id text NOT NULL,
  class_id text REFERENCES classes(id) ON DELETE SET NULL,
  student_name_snapshot text,
  class_name_snapshot text,
  feedback_type text NOT NULL CHECK (feedback_type IN ('course_content', 'experiment_resource', 'ai_answer', 'system_issue', 'other')),
  content text NOT NULL,
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'archived')),
  chapter_id text,
  unit_id text,
  knowledge_point_id text,
  experiment_id text,
  page_path text,
  source_event_id bigint REFERENCES student_events(id) ON DELETE SET NULL,
  handler_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
  internal_note text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  resolved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_student_feedback_status_created ON student_feedback(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_student_feedback_class_created ON student_feedback(class_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_student_feedback_student_created ON student_feedback(student_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_student_feedback_type_created ON student_feedback(feedback_type, created_at DESC);

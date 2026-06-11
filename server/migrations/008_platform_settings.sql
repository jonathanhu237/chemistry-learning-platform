CREATE TABLE IF NOT EXISTS platform_settings (
  key text PRIMARY KEY,
  value jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO platform_settings (key, value)
VALUES (
  'learning_behavior',
  '{
    "assessment": {
      "pretest_enabled": true,
      "pretest_question_count": 8,
      "posttest_enabled": true,
      "posttest_question_count": 8
    },
    "learning_features": {
      "ai_assistant_enabled": true,
      "feedback_enabled": true,
      "student_review_preview_enabled": false
    }
  }'::jsonb
)
ON CONFLICT (key) DO NOTHING;

INSERT INTO platform_settings (key, value)
VALUES (
  'ai_configuration',
  '{
    "provider": "openai",
    "base_url": "",
    "model": "",
    "connection_check_interval_minutes": 30,
    "enabled_features": {
      "rag_access_enabled": true,
      "student_ai_assistant": true,
      "student_learning_analytics": true,
      "question_bank_assistant": true,
      "teacher_learning_analytics": true
    }
  }'::jsonb
)
ON CONFLICT (key) DO NOTHING;

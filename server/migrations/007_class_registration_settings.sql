ALTER TABLE registration_settings
ADD COLUMN IF NOT EXISTS default_password_mode text NOT NULL DEFAULT 'student_id'
CHECK (default_password_mode IN ('student_id', 'shared'));

UPDATE registration_settings
SET default_password_mode = CASE
  WHEN default_password_hash IS NOT NULL THEN 'shared'
  ELSE 'student_id'
END;

CREATE TABLE IF NOT EXISTS class_registration_settings (
  class_id text PRIMARY KEY REFERENCES classes(id) ON DELETE CASCADE,
  mode text NOT NULL DEFAULT 'roster_only' CHECK (mode IN ('roster_only', 'self_registration')),
  default_password_policy text NOT NULL DEFAULT 'student_id_name_activation',
  default_password_mode text NOT NULL DEFAULT 'student_id' CHECK (default_password_mode IN ('student_id', 'shared')),
  default_password_hash text,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

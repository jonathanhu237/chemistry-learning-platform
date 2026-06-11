CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS app_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  username text NOT NULL UNIQUE,
  role text NOT NULL CHECK (role IN ('admin', 'teacher', 'student')),
  display_name text NOT NULL,
  password_hash text NOT NULL,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('pending', 'active', 'disabled')),
  must_change_password boolean NOT NULL DEFAULT false,
  password_version int NOT NULL DEFAULT 1,
  last_login_at timestamptz,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS classes (
  id text PRIMARY KEY,
  class_name text NOT NULL,
  description text,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS teacher_classes (
  teacher_user_id uuid NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  class_id text NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
  class_role text NOT NULL DEFAULT 'owner' CHECK (class_role IN ('owner', 'assistant', 'viewer')),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (teacher_user_id, class_id)
);

CREATE TABLE IF NOT EXISTS roster_imports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  uploaded_by uuid REFERENCES app_users(id),
  file_name text,
  status text NOT NULL DEFAULT 'preview' CHECK (status IN ('preview', 'imported', 'failed')),
  total_rows int NOT NULL DEFAULT 0,
  valid_rows int NOT NULL DEFAULT 0,
  invalid_rows int NOT NULL DEFAULT 0,
  errors jsonb NOT NULL DEFAULT '[]'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roster_entries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  import_id uuid REFERENCES roster_imports(id) ON DELETE SET NULL,
  class_id text NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
  student_id text NOT NULL,
  student_name text NOT NULL,
  normalized_student_id text NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'disabled')),
  activation_mode text NOT NULL DEFAULT 'default_password' CHECK (activation_mode IN ('default_password', 'self_registration')),
  activated_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
  row_number int,
  errors jsonb NOT NULL DEFAULT '[]'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (class_id, student_id)
);

CREATE TABLE IF NOT EXISTS student_profiles (
  user_id uuid PRIMARY KEY REFERENCES app_users(id) ON DELETE CASCADE,
  student_id text NOT NULL UNIQUE,
  student_name text NOT NULL,
  class_id text REFERENCES classes(id) ON DELETE SET NULL,
  roster_entry_id uuid REFERENCES roster_entries(id) ON DELETE SET NULL,
  activated_at timestamptz,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS registration_settings (
  id text PRIMARY KEY DEFAULT 'student_registration',
  mode text NOT NULL DEFAULT 'roster_only' CHECK (mode IN ('roster_only', 'self_registration')),
  default_password_policy text NOT NULL DEFAULT 'student_id_name_activation',
  default_password_hash text,
  updated_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO registration_settings (id)
VALUES ('student_registration')
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS auth_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  token_jti text NOT NULL UNIQUE,
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS admin_audit_log (
  id bigserial PRIMARY KEY,
  actor_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
  action text NOT NULL,
  target_type text,
  target_id text,
  before_state jsonb,
  after_state jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE students ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES app_users(id) ON DELETE SET NULL;
ALTER TABLE students ADD COLUMN IF NOT EXISTS student_id text;
ALTER TABLE students ADD COLUMN IF NOT EXISTS class_id text REFERENCES classes(id) ON DELETE SET NULL;
ALTER TABLE students ADD COLUMN IF NOT EXISTS status text DEFAULT 'active';
ALTER TABLE students ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

CREATE INDEX IF NOT EXISTS idx_app_users_role_status ON app_users(role, status);
CREATE INDEX IF NOT EXISTS idx_classes_status ON classes(status);
CREATE INDEX IF NOT EXISTS idx_roster_entries_class_status ON roster_entries(class_id, status);
CREATE INDEX IF NOT EXISTS idx_roster_entries_student_id ON roster_entries(student_id);
CREATE INDEX IF NOT EXISTS idx_student_profiles_class ON student_profiles(class_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_admin_audit_target ON admin_audit_log(target_type, target_id);

ALTER TABLE classes
  ADD COLUMN IF NOT EXISTS class_purpose text NOT NULL DEFAULT 'instructional',
  ADD COLUMN IF NOT EXISTS owner_teacher_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS system_managed boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS hidden_from_teacher boolean NOT NULL DEFAULT false;

ALTER TABLE roster_entries
  ADD COLUMN IF NOT EXISTS entry_purpose text NOT NULL DEFAULT 'instructional',
  ADD COLUMN IF NOT EXISTS owner_teacher_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS system_managed boolean NOT NULL DEFAULT false;

ALTER TABLE student_profiles
  ADD COLUMN IF NOT EXISTS profile_purpose text NOT NULL DEFAULT 'instructional',
  ADD COLUMN IF NOT EXISTS owner_teacher_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL;

ALTER TABLE app_users
  ADD COLUMN IF NOT EXISTS account_purpose text NOT NULL DEFAULT 'standard',
  ADD COLUMN IF NOT EXISTS owner_teacher_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_classes_teacher_preview_owner
  ON classes(owner_teacher_user_id)
  WHERE class_purpose = 'teacher_preview' AND status <> 'archived';

CREATE UNIQUE INDEX IF NOT EXISTS idx_app_users_teacher_preview_owner
  ON app_users(owner_teacher_user_id)
  WHERE account_purpose = 'teacher_preview' AND role = 'student' AND status <> 'disabled';

CREATE INDEX IF NOT EXISTS idx_classes_purpose_status
  ON classes(class_purpose, status);

CREATE INDEX IF NOT EXISTS idx_roster_entries_purpose_class
  ON roster_entries(entry_purpose, class_id, status);

CREATE INDEX IF NOT EXISTS idx_student_profiles_purpose_class
  ON student_profiles(profile_purpose, class_id);

CREATE INDEX IF NOT EXISTS idx_app_users_purpose_role
  ON app_users(account_purpose, role, status);

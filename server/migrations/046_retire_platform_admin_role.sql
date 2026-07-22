UPDATE app_users
SET role = 'admin',
    updated_at = now()
WHERE role = 'platform_admin';

ALTER TABLE app_users
  DROP CONSTRAINT IF EXISTS app_users_role_check;

ALTER TABLE app_users
  ADD CONSTRAINT app_users_role_check
  CHECK (role IN ('admin', 'teacher', 'student'));

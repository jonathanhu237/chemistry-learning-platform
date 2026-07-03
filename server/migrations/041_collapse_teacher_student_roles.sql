DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'app_users_role_check'
      AND conrelid = 'app_users'::regclass
  ) THEN
    ALTER TABLE app_users DROP CONSTRAINT app_users_role_check;
  END IF;
END $$;

UPDATE app_users
SET role = 'teacher',
    updated_at = now()
WHERE role IN ('admin', 'platform_admin');

ALTER TABLE app_users
  ADD CONSTRAINT app_users_role_check
  CHECK (role IN ('teacher', 'student'));

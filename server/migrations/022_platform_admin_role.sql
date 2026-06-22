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

ALTER TABLE app_users
  ADD CONSTRAINT app_users_role_check
  CHECK (role IN ('platform_admin', 'admin', 'teacher', 'student'));

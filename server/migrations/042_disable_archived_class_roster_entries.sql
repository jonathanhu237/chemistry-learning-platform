WITH archived_roster AS (
  SELECT re.id, COALESCE(sp.user_id, re.activated_user_id) AS user_id
  FROM roster_entries re
  JOIN classes c ON c.id = re.class_id
  LEFT JOIN student_profiles sp ON sp.roster_entry_id = re.id
  WHERE c.status = 'archived'
    AND re.status <> 'disabled'
),
disabled_roster AS (
  UPDATE roster_entries re
  SET status = 'disabled',
      updated_at = now()
  WHERE re.id IN (SELECT id FROM archived_roster)
  RETURNING re.id
),
disabled_users AS (
  UPDATE app_users au
  SET status = 'disabled',
      updated_at = now()
  WHERE au.id IN (
    SELECT user_id
    FROM archived_roster
    WHERE user_id IS NOT NULL
  )
  RETURNING au.id
),
revoked_sessions AS (
  UPDATE auth_sessions
  SET revoked_at = now()
  WHERE user_id IN (SELECT id FROM disabled_users)
    AND revoked_at IS NULL
  RETURNING id
),
disabled_students AS (
  UPDATE students
  SET status = 'disabled',
      updated_at = now()
  WHERE user_id IN (SELECT id FROM disabled_users)
  RETURNING id
)
SELECT COUNT(*) FROM disabled_roster;

WITH archived_roster AS (
  SELECT roster.id,
         roster.activated_user_id,
         profile.user_id AS profile_user_id
  FROM roster_entries roster
  JOIN classes class_record ON class_record.id = roster.class_id
  LEFT JOIN student_profiles profile ON profile.roster_entry_id = roster.id
  WHERE class_record.status = 'archived'
),
archived_user_ids AS (
  SELECT DISTINCT candidate.user_id
  FROM archived_roster roster
  CROSS JOIN LATERAL (
    VALUES (roster.activated_user_id), (roster.profile_user_id)
  ) AS candidate(user_id)
  WHERE candidate.user_id IS NOT NULL
),
disabled_roster AS (
  UPDATE roster_entries roster
  SET status = 'disabled',
      updated_at = now()
  WHERE roster.id IN (SELECT id FROM archived_roster)
    AND roster.status <> 'disabled'
  RETURNING roster.id
),
disabled_users AS (
  UPDATE app_users account
  SET status = 'disabled',
      password_version = password_version + 1,
      updated_at = now()
  WHERE account.id IN (SELECT user_id FROM archived_user_ids)
    AND account.role = 'student'
    AND account.status <> 'disabled'
  RETURNING account.id
),
revoked_sessions AS (
  UPDATE auth_sessions auth_session
  SET revoked_at = now()
  WHERE auth_session.user_id IN (SELECT user_id FROM archived_user_ids)
    AND auth_session.revoked_at IS NULL
  RETURNING auth_session.id
),
disabled_students AS (
  UPDATE students student
  SET status = 'disabled',
      updated_at = now()
  WHERE student.user_id IN (SELECT user_id FROM archived_user_ids)
    AND student.status <> 'disabled'
  RETURNING student.id
)
SELECT COUNT(*) FROM disabled_roster;

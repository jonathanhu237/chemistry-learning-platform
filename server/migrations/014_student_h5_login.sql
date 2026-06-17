CREATE UNIQUE INDEX IF NOT EXISTS idx_roster_entries_active_normalized_student_id_unique
ON roster_entries(normalized_student_id)
WHERE status <> 'disabled';

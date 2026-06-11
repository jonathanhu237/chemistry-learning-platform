ALTER TABLE student_events ADD COLUMN IF NOT EXISTS chapter_id text;
ALTER TABLE student_events ADD COLUMN IF NOT EXISTS unit_id text;

CREATE INDEX IF NOT EXISTS idx_student_events_chapter ON student_events(student_id, chapter_id);

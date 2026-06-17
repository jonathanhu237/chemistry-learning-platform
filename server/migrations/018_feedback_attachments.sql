CREATE TABLE IF NOT EXISTS feedback_attachments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  feedback_id uuid NOT NULL REFERENCES student_feedback(id) ON DELETE CASCADE,
  storage_path text NOT NULL,
  original_file_name text,
  mime_type text NOT NULL,
  file_size_bytes int NOT NULL,
  checksum_sha256 text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (storage_path)
);

CREATE INDEX IF NOT EXISTS idx_feedback_attachments_feedback_id ON feedback_attachments(feedback_id, created_at);

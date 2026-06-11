CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS curriculum_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_code text NOT NULL UNIQUE,
  title text NOT NULL,
  source_path text,
  source_label text,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'archived')),
  imported_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  validation_report jsonb NOT NULL DEFAULT '{}'::jsonb,
  counts jsonb NOT NULL DEFAULT '{}'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  published_at timestamptz,
  archived_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE chapters ADD COLUMN IF NOT EXISTS curriculum_version_id uuid REFERENCES curriculum_versions(id) ON DELETE SET NULL;
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS content_status text NOT NULL DEFAULT 'published';
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS source_label text;
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS metadata jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS published_at timestamptz DEFAULT now();
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

ALTER TABLE knowledge_units ADD COLUMN IF NOT EXISTS curriculum_version_id uuid REFERENCES curriculum_versions(id) ON DELETE SET NULL;
ALTER TABLE knowledge_units ADD COLUMN IF NOT EXISTS content_status text NOT NULL DEFAULT 'published';
ALTER TABLE knowledge_units ADD COLUMN IF NOT EXISTS source_label text;
ALTER TABLE knowledge_units ADD COLUMN IF NOT EXISTS metadata jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE knowledge_units ADD COLUMN IF NOT EXISTS published_at timestamptz DEFAULT now();
ALTER TABLE knowledge_units ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

ALTER TABLE knowledge_points ADD COLUMN IF NOT EXISTS curriculum_version_id uuid REFERENCES curriculum_versions(id) ON DELETE SET NULL;
ALTER TABLE knowledge_points ADD COLUMN IF NOT EXISTS content_status text NOT NULL DEFAULT 'published';
ALTER TABLE knowledge_points ADD COLUMN IF NOT EXISTS source_label text;
ALTER TABLE knowledge_points ADD COLUMN IF NOT EXISTS metadata jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE knowledge_points ADD COLUMN IF NOT EXISTS published_at timestamptz DEFAULT now();
ALTER TABLE knowledge_points ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

ALTER TABLE source_chunks ADD COLUMN IF NOT EXISTS content_status text NOT NULL DEFAULT 'pending_review';
ALTER TABLE source_chunks ADD COLUMN IF NOT EXISTS published_at timestamptz;
ALTER TABLE source_chunks ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

ALTER TABLE experiments ADD COLUMN IF NOT EXISTS content_status text NOT NULL DEFAULT 'pending_review';
ALTER TABLE experiments ADD COLUMN IF NOT EXISTS metadata jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE experiments ADD COLUMN IF NOT EXISTS published_at timestamptz;
ALTER TABLE experiments ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

ALTER TABLE experiment_learning_cards ADD COLUMN IF NOT EXISTS content_status text NOT NULL DEFAULT 'pending_review';
ALTER TABLE experiment_learning_cards ADD COLUMN IF NOT EXISTS metadata jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE experiment_learning_cards ADD COLUMN IF NOT EXISTS published_at timestamptz;
ALTER TABLE experiment_learning_cards ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

ALTER TABLE questions ADD COLUMN IF NOT EXISTS content_status text NOT NULL DEFAULT 'pending_review';
ALTER TABLE questions ADD COLUMN IF NOT EXISTS metadata jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS published_at timestamptz;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

ALTER TABLE resources ADD COLUMN IF NOT EXISTS content_status text NOT NULL DEFAULT 'pending_review';
ALTER TABLE resources ADD COLUMN IF NOT EXISTS published_at timestamptz;
ALTER TABLE resources ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

ALTER TABLE links ADD COLUMN IF NOT EXISTS content_status text NOT NULL DEFAULT 'pending_review';
ALTER TABLE links ADD COLUMN IF NOT EXISTS published_at timestamptz;
ALTER TABLE links ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

CREATE TABLE IF NOT EXISTS review_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  target_type text NOT NULL,
  target_id text NOT NULL,
  title text,
  chapter_id text,
  knowledge_point_id text,
  status text NOT NULL DEFAULT 'pending_review' CHECK (status IN ('draft', 'pending_review', 'approved', 'rejected', 'published', 'archived')),
  risk_flags text[] NOT NULL DEFAULT '{}',
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  source_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  assigned_to uuid REFERENCES app_users(id) ON DELETE SET NULL,
  decided_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  decided_at timestamptz,
  published_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  published_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (target_type, target_id)
);

CREATE TABLE IF NOT EXISTS review_actions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  review_item_id uuid NOT NULL REFERENCES review_items(id) ON DELETE CASCADE,
  actor_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
  action text NOT NULL CHECK (action IN ('create', 'edit', 'approve', 'reject', 'request_changes', 'publish', 'unpublish', 'archive', 'deny')),
  before_status text,
  after_status text,
  note text,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS media_assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  original_file_name text NOT NULL,
  relative_path text NOT NULL,
  checksum_sha256 text,
  mime_type text,
  file_size_bytes bigint,
  duration_seconds numeric,
  upload_status text NOT NULL DEFAULT 'pending' CHECK (upload_status IN ('pending', 'processing', 'ready', 'failed', 'replaced')),
  error_reason text,
  uploaded_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  replaced_by uuid REFERENCES media_assets(id) ON DELETE SET NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (relative_path)
);

CREATE TABLE IF NOT EXISTS media_bindings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  media_asset_id uuid NOT NULL REFERENCES media_assets(id) ON DELETE CASCADE,
  target_type text NOT NULL CHECK (target_type IN ('chapter', 'knowledge_unit', 'knowledge_point', 'experiment', 'learning_card')),
  target_id text NOT NULL,
  title text,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
  sort_order int NOT NULL DEFAULT 0,
  published_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  published_at timestamptz,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (media_asset_id, target_type, target_id)
);

CREATE TABLE IF NOT EXISTS agent_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
  student_id text,
  user_role text,
  question text NOT NULL,
  classification jsonb NOT NULL DEFAULT '{}'::jsonb,
  tool_calls jsonb NOT NULL DEFAULT '[]'::jsonb,
  source_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  guardrail_decisions jsonb NOT NULL DEFAULT '[]'::jsonb,
  response_text text,
  response_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_curriculum_versions_status ON curriculum_versions(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_curriculum_versions_one_active ON curriculum_versions(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_review_items_status_type ON review_items(status, target_type);
CREATE INDEX IF NOT EXISTS idx_review_items_chapter ON review_items(chapter_id);
CREATE INDEX IF NOT EXISTS idx_review_actions_item ON review_actions(review_item_id, created_at);
CREATE INDEX IF NOT EXISTS idx_media_assets_status ON media_assets(upload_status);
CREATE INDEX IF NOT EXISTS idx_media_bindings_target_status ON media_bindings(target_type, target_id, status);
CREATE INDEX IF NOT EXISTS idx_agent_logs_student_time ON agent_logs(student_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_logs_user_time ON agent_logs(user_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_links_unique_relation ON links(from_type, from_id, relation, to_type, to_id);

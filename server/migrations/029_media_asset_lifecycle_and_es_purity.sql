CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE media_assets
  ADD COLUMN IF NOT EXISTS lifecycle_status text NOT NULL DEFAULT 'active',
  ADD COLUMN IF NOT EXISTS archived_at timestamptz,
  ADD COLUMN IF NOT EXISTS archived_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS archive_reason text,
  ADD COLUMN IF NOT EXISTS archive_metadata jsonb NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE media_assets
  DROP CONSTRAINT IF EXISTS media_assets_lifecycle_status_check;

ALTER TABLE media_assets
  ADD CONSTRAINT media_assets_lifecycle_status_check
  CHECK (lifecycle_status IN ('active', 'archived', 'tombstoned'));

UPDATE media_assets
SET lifecycle_status = 'active'
WHERE lifecycle_status IS NULL;

CREATE TABLE IF NOT EXISTS media_asset_lifecycle_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  media_asset_id uuid NOT NULL REFERENCES media_assets(id) ON DELETE CASCADE,
  event_type text NOT NULL CHECK (event_type IN ('media_asset_archived')),
  actor_user_id uuid REFERENCES app_users(id) ON DELETE SET NULL,
  reason text,
  previous_lifecycle_status text,
  new_lifecycle_status text NOT NULL,
  affected_binding_summary jsonb NOT NULL DEFAULT '{}'::jsonb,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  handler_status text NOT NULL DEFAULT 'pending' CHECK (handler_status IN ('pending', 'succeeded', 'failed')),
  handler_error text,
  handled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_media_assets_lifecycle_status
  ON media_assets(lifecycle_status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_media_asset_lifecycle_events_asset
  ON media_asset_lifecycle_events(media_asset_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_media_asset_lifecycle_events_handler
  ON media_asset_lifecycle_events(handler_status, created_at)
  WHERE handler_status IN ('pending', 'failed');

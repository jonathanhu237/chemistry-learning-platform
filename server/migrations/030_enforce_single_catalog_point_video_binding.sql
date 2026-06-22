-- Enforce the product rule that one video point has one current video resource.
-- Historical archived rows are retained for audit, but duplicate active rows are hard-deleted.

WITH ranked_active_bindings AS (
  SELECT
    mb.id,
    row_number() OVER (
      PARTITION BY COALESCE(mb.canonical_point_id, mb.node_id)
      ORDER BY
        CASE WHEN mb.binding_status = 'published' AND ma.upload_status = 'ready' THEN 0 ELSE 1 END,
        CASE WHEN ma.upload_status = 'ready' THEN 0 ELSE 1 END,
        CASE WHEN mb.binding_status = 'published' THEN 0 ELSE 1 END,
        mb.display_order,
        mb.updated_at DESC,
        mb.created_at,
        mb.id
    ) AS keep_rank
  FROM experiment_catalog_point_media_bindings mb
  JOIN media_assets ma ON ma.id = mb.media_asset_id
  WHERE mb.binding_status <> 'archived'
)
DELETE FROM experiment_catalog_point_media_bindings mb
USING ranked_active_bindings ranked
WHERE mb.id = ranked.id
  AND ranked.keep_rank > 1;

UPDATE experiment_catalog_point_media_bindings
SET binding_status = 'published',
    metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
      'normalized_by_migration', '030_enforce_single_catalog_point_video_binding',
      'normalized_status_semantics', 'single_current_video_resource'
    ),
    published_at = COALESCE(published_at, now()),
    updated_at = now()
WHERE binding_status <> 'archived'
  AND binding_status <> 'published';

CREATE UNIQUE INDEX IF NOT EXISTS idx_catalog_point_media_one_active_canonical
  ON experiment_catalog_point_media_bindings(canonical_point_id)
  WHERE canonical_point_id IS NOT NULL
    AND binding_status <> 'archived';

CREATE UNIQUE INDEX IF NOT EXISTS idx_catalog_point_media_one_active_node_without_canonical
  ON experiment_catalog_point_media_bindings(node_id)
  WHERE canonical_point_id IS NULL
    AND binding_status <> 'archived';

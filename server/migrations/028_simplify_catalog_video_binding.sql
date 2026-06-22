-- Simplify catalog point video binding to one active video per canonical point.
-- Binding status remains for compatibility, but only "archived" means inactive.

WITH ranked_bindings AS (
  SELECT
    mb.id,
    row_number() OVER (
      PARTITION BY COALESCE(mb.canonical_point_id, mb.node_id)
      ORDER BY
        CASE WHEN mb.binding_status = 'published' AND ma.upload_status = 'ready' THEN 0 ELSE 1 END,
        CASE WHEN ma.upload_status = 'ready' THEN 0 ELSE 1 END,
        CASE WHEN mb.binding_status = 'published' THEN 0 ELSE 1 END,
        mb.display_order,
        mb.created_at,
        mb.id
    ) AS keep_rank
  FROM experiment_catalog_point_media_bindings mb
  JOIN media_assets ma ON ma.id = mb.media_asset_id
  WHERE mb.binding_status <> 'archived'
)
UPDATE experiment_catalog_point_media_bindings mb
SET binding_status = 'archived',
    metadata = COALESCE(mb.metadata, '{}'::jsonb) || jsonb_build_object(
      'archived_by_migration', '028_simplify_catalog_video_binding',
      'archived_reason', 'single_active_catalog_point_video'
    ),
    updated_at = now()
FROM ranked_bindings ranked
WHERE mb.id = ranked.id
  AND ranked.keep_rank > 1;

WITH active_bindings AS (
  SELECT mb.id
  FROM experiment_catalog_point_media_bindings mb
  WHERE mb.binding_status <> 'archived'
)
UPDATE experiment_catalog_point_media_bindings mb
SET binding_status = 'published',
    metadata = COALESCE(mb.metadata, '{}'::jsonb) || jsonb_build_object(
      'normalized_by_migration', '028_simplify_catalog_video_binding',
      'normalized_status_semantics', 'active_binding'
    ),
    published_at = COALESCE(mb.published_at, now()),
    updated_at = now()
FROM active_bindings active
WHERE mb.id = active.id
  AND mb.binding_status <> 'published';

CREATE UNIQUE INDEX IF NOT EXISTS idx_catalog_point_media_one_active_canonical
  ON experiment_catalog_point_media_bindings(canonical_point_id)
  WHERE canonical_point_id IS NOT NULL
    AND binding_status <> 'archived';

CREATE UNIQUE INDEX IF NOT EXISTS idx_catalog_point_media_one_active_node_without_canonical
  ON experiment_catalog_point_media_bindings(node_id)
  WHERE canonical_point_id IS NULL
    AND binding_status <> 'archived';

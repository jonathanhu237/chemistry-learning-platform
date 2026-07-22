from __future__ import annotations


# This CTE is the single SQL owner for student-facing catalog media visibility.
# Callers may add stricter filters (for example a concrete placement or asset),
# but must not weaken this publication/playback contract.
STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES = """
student_visible_catalog_paths (placement_node_id, node_id, parent_id, status) AS (
  SELECT placement.id, placement.id, placement.parent_id, placement.status
  FROM experiment_catalog_nodes placement
  WHERE placement.node_kind = 'point'

  UNION ALL

  SELECT path.placement_node_id, parent.id, parent.parent_id, parent.status
  FROM experiment_catalog_nodes parent
  JOIN student_visible_catalog_paths path
    ON path.parent_id = parent.id
),
student_visible_placements AS (
  SELECT
    placement.id AS placement_node_id,
    placement.canonical_point_id,
    placement.chapter_id
  FROM experiment_catalog_nodes placement
  JOIN experiment_catalog_points canonical_point
    ON canonical_point.id = placement.canonical_point_id
  JOIN chapters chapter
    ON chapter.id = placement.chapter_id
  WHERE placement.node_kind = 'point'
    AND placement.status = 'published'
    AND canonical_point.status = 'published'
    AND COALESCE(chapter.content_status, 'published') = 'published'
    AND EXISTS (
      SELECT 1
      FROM experiment_catalog_point_content content
      WHERE content.content_status = 'published'
        AND (
          content.canonical_point_id = placement.canonical_point_id
          OR content.node_id = placement.id
        )
    )
    AND NOT EXISTS (
      SELECT 1
      FROM student_visible_catalog_paths path
      WHERE path.placement_node_id = placement.id
        AND path.status IS DISTINCT FROM 'published'
    )
),
student_visible_playable_media AS (
  SELECT
    visible_placement.placement_node_id,
    visible_placement.canonical_point_id,
    visible_placement.chapter_id,
    binding.id AS binding_id,
    asset.id AS media_asset_id
  FROM student_visible_placements visible_placement
  JOIN experiment_catalog_point_media_bindings binding
    ON (
      binding.canonical_point_id = visible_placement.canonical_point_id
      OR binding.node_id = visible_placement.placement_node_id
    )
  JOIN media_assets asset
    ON asset.id = binding.media_asset_id
  WHERE binding.binding_status = 'published'
    AND asset.upload_status = 'ready'
    AND COALESCE(asset.lifecycle_status, 'active') = 'active'
    AND NULLIF(btrim(COALESCE(asset.playback_relative_path, asset.relative_path, '')), '') IS NOT NULL
    AND COALESCE(binding.metadata->>'placeholder_video', 'false') <> 'true'
    AND COALESCE(binding.metadata->>'coverage_kind', asset.metadata->>'seed_kind', '') <> 'placeholder_video'
    AND lower(COALESCE(asset.original_file_name, '')) <> 'no-video-placeholder.mp4'
)
"""

CREATE TABLE IF NOT EXISTS student_home_video_recommendations (
  placement_node_id text PRIMARY KEY REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  sort_order int NOT NULL DEFAULT 0 CHECK (sort_order >= 0),
  recommended_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_student_home_video_recommendations_order
  ON student_home_video_recommendations(sort_order, updated_at DESC, placement_node_id);

DO $$
BEGIN
  IF to_regclass('public.legacy_recommended_video_points') IS NOT NULL THEN
    EXECUTE $copy$
      INSERT INTO student_home_video_recommendations (
        placement_node_id,
        sort_order,
        recommended_by,
        created_at,
        updated_at
      )
      SELECT
        legacy.node_id,
        GREATEST(COALESCE(legacy.sort_order, 0), 0),
        actor.id,
        COALESCE(legacy.recommended_at, now()),
        COALESCE(legacy.recommended_at, now())
      FROM legacy_recommended_video_points legacy
      JOIN experiment_catalog_nodes placement
        ON placement.id = legacy.node_id
       AND placement.node_kind = 'point'
       AND placement.canonical_point_id IS NOT NULL
      JOIN experiment_catalog_points point
        ON point.id = placement.canonical_point_id
      LEFT JOIN app_users actor
        ON actor.id::text = NULLIF(btrim(legacy.recommended_by), '')
      ON CONFLICT (placement_node_id) DO UPDATE SET
        sort_order = EXCLUDED.sort_order,
        recommended_by = EXCLUDED.recommended_by,
        updated_at = EXCLUDED.updated_at
    $copy$;
  END IF;
END
$$;

DROP TABLE IF EXISTS legacy_recommended_video_points;

DELETE FROM student_video_saves
WHERE save_type = 'watch_later';

ALTER TABLE student_video_saves
  DROP CONSTRAINT IF EXISTS student_video_saves_save_type_check;

ALTER TABLE student_video_saves
  ADD CONSTRAINT student_video_saves_save_type_check
  CHECK (save_type = 'favorite');

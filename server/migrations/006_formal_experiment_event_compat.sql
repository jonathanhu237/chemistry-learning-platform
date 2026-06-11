INSERT INTO experiments (
  id, name, element_area, element_group, objective, video_url, media_status,
  resource_mode, review_required, content_status, metadata, published_at, updated_at
)
SELECT
  fe.id,
  fe.title,
  NULL,
  (
    SELECT ecb.chapter_id
    FROM experiment_chapter_bindings ecb
    WHERE ecb.experiment_id = fe.id
    ORDER BY CASE ecb.coverage_type WHEN 'primary' THEN 0 WHEN 'partial' THEN 1 ELSE 2 END,
             ecb.sort_order,
             ecb.chapter_id
    LIMIT 1
  ),
  fe.summary,
  NULL,
  'pending',
  'formal_experiment_fk',
  false,
  fe.status,
  jsonb_build_object('formal_experiment_id', fe.id, 'formal_catalog', true),
  fe.published_at,
  now()
FROM formal_experiments fe
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  element_group = EXCLUDED.element_group,
  objective = EXCLUDED.objective,
  resource_mode = EXCLUDED.resource_mode,
  review_required = EXCLUDED.review_required,
  content_status = EXCLUDED.content_status,
  metadata = experiments.metadata || EXCLUDED.metadata,
  updated_at = now();

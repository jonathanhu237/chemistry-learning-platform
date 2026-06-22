ALTER TABLE experiment_catalog_point_related_links
  DROP COLUMN IF EXISTS label;

ALTER TABLE experiment_point_related_links
  DROP COLUMN IF EXISTS label;

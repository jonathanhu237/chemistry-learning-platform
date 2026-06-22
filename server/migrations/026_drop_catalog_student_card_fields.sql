ALTER TABLE experiment_catalog_nodes
  DROP CONSTRAINT IF EXISTS experiment_catalog_nodes_card_image_asset_id_fkey;

DROP INDEX IF EXISTS idx_experiment_catalog_nodes_card_image_asset;

ALTER TABLE experiment_catalog_nodes
  DROP COLUMN IF EXISTS student_description,
  DROP COLUMN IF EXISTS card_image_asset_id,
  DROP COLUMN IF EXISTS card_icon_key,
  DROP COLUMN IF EXISTS card_accent,
  DROP COLUMN IF EXISTS card_layout,
  DROP COLUMN IF EXISTS card_presentation,
  DROP COLUMN IF EXISTS point_card_presentation;

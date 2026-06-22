CREATE TABLE IF NOT EXISTS experiment_catalog_point_reaction_equations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  node_id text NOT NULL REFERENCES experiment_catalog_point_content(node_id) ON DELETE CASCADE,
  row_order int NOT NULL DEFAULT 0,
  raw_text text NOT NULL,
  canonical_display text,
  canonical_mhchem text,
  plain_search_text text,
  formulae jsonb NOT NULL DEFAULT '[]'::jsonb,
  aliases jsonb NOT NULL DEFAULT '[]'::jsonb,
  reactants jsonb NOT NULL DEFAULT '[]'::jsonb,
  products jsonb NOT NULL DEFAULT '[]'::jsonb,
  participants jsonb NOT NULL DEFAULT '{}'::jsonb,
  reaction_features jsonb NOT NULL DEFAULT '[]'::jsonb,
  validation_status text NOT NULL DEFAULT 'warning' CHECK (validation_status IN ('valid', 'warning', 'invalid')),
  warnings jsonb NOT NULL DEFAULT '[]'::jsonb,
  errors jsonb NOT NULL DEFAULT '[]'::jsonb,
  parser_version text NOT NULL DEFAULT 'basic-v1',
  migrated_from_principle_equation boolean NOT NULL DEFAULT false,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (node_id, row_order)
);

CREATE INDEX IF NOT EXISTS idx_catalog_point_reaction_equations_node
  ON experiment_catalog_point_reaction_equations(node_id, row_order);

INSERT INTO experiment_catalog_point_reaction_equations (
  node_id, row_order, raw_text, canonical_display, canonical_mhchem, plain_search_text,
  validation_status, warnings, parser_version, migrated_from_principle_equation, metadata
)
SELECT
  node_id,
  1,
  btrim(principle_equation),
  btrim(principle_equation),
  NULL,
  btrim(principle_equation),
  'warning',
  '["Migrated from legacy principle_equation; save or preview to refresh backend normalization."]'::jsonb,
  'legacy-migration',
  true,
  jsonb_build_object('source', 'principle_equation')
FROM experiment_catalog_point_content
WHERE principle_mode = 'equation'
  AND btrim(COALESCE(principle_equation, '')) <> ''
ON CONFLICT (node_id, row_order) DO NOTHING;

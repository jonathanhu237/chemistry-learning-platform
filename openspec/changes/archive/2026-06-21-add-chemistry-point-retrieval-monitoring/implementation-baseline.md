# Implementation Baseline

This note records the baseline gathered before implementing `add-chemistry-point-retrieval-monitoring`.

## Search Backend Baseline

- Local direct Python settings:
  - `VIDEO_LIBRARY_SEARCH_BACKEND`: `local`
  - `VIDEO_LIBRARY_SEARCH_INDEX`: `student-video-library`
  - `VIDEO_LIBRARY_SEARCH_ANALYZER`: `ik_max_word`
  - `VIDEO_LIBRARY_SEARCH_LOCAL_FALLBACK`: `true`
- Compose backend settings from `chemistry-admin-backend-1`:
  - `VIDEO_LIBRARY_SEARCH_BACKEND`: `elasticsearch`
  - `VIDEO_LIBRARY_SEARCH_URL`: `http://elasticsearch:9200`
  - `VIDEO_LIBRARY_SEARCH_INDEX`: `student-video-library`
  - `VIDEO_LIBRARY_SEARCH_ANALYZER`: `ik_max_word`
  - `VIDEO_LIBRARY_SEARCH_LOCAL_FALLBACK`: `false`
- Docker services relevant to this change were running and healthy at baseline:
  - `chemistry-admin-backend-1`
  - `chemistry-admin-elasticsearch-1`
  - `chemistry-admin-bge-rag-1`
  - `chemistry-admin-postgres-1`
  - `chemistry-admin-web-teacher-1`

## Existing ES Snapshot

- ES cluster health: `yellow`, single-node with one unassigned replica.
- Current index: `student-video-library`.
- Current indexed document count: `31`.
- Current mapping already contains point-placement identity fields and generic chemistry fields:
  - `id`, `result_type`, `node_id`, `placement_node_id`, `canonical_point_id`
  - `chapter_id`, `chapter_ids`, `catalog_path`, `category_text`
  - `title`, `subtitle`, `snippet`, `search_text`
  - `principle`, `phenomenon_explanation`, `safety_note`, `related_text`
  - `formulae`, `aliases`, `reaction_features`
  - `has_video`, `video_count`, `target`, `badges`, `updated_at`
- The current index is still the older smaller projection. It does not yet reflect the authoritative 76-record point-content seed.

## Current Diagnostics Snapshot

`video_library_index_diagnostics()` in Compose reported:

- Settings:
  - enabled: `true`
  - backend: `elasticsearch`
  - index: `student-video-library`
  - analyzer: `ik_max_word`
  - local fallback: `false`
- Analyzer assets:
  - all configured ES/IK analyzer files existed
  - total dictionary lines: `257`
  - assets included manifest, IK config, HIT stopwords, project chemistry stopwords, chemistry custom dictionary, ES stopwords, and chemistry synonyms
- PostgreSQL:
  - published point content count: `30`
  - sync status counts: `synced=23`, `pending=19`
  - retryable rows included pending delete actions from the old 30-record attempt
- Elasticsearch:
  - configured: `true`
  - document count: `31`

Representative query baseline before this change:

- `H2O2 KMnO4` returned older hits including `过氧化氢的酸性`, `H₂O₂ + KI | 酸性体系`, and `钠加热燃烧实验`.
- Chinese synonym/phenomenon queries were unreliable because the runtime index still contains the old smaller projection and the query path lacks route explanations.

## 76-Record Import Contract

The authoritative seed is `data/seed/experiment_catalog/point_content_seed.json`.

Required counts from `scripts/validate_experiment_catalog_seed.py`:

- catalog nodes: `569`
- directory nodes: `176`
- point placements: `393`
- canonical points: `357`
- duplicate groups: `32`
- duplicate placement surplus: `36`
- chapter 21 nodes: `0`
- point content records: `76`
- equation-mode records: `71`
- text-mode records: `5`
- reaction equation rows: `122`
- unique target seed keys: `76`
- unique target canonical point ids: `76`
- semantic mapped records: `76`

Each record must preserve:

- `record_id`
- `target_seed_key`
- `target_canonical_point_id`
- `target_path_titles` and `target_path`
- `point_title`
- `principle_mode`
- text-mode `principle_text`
- equation-mode `reaction_equations[].raw_text` and `row_order`
- `phenomenon_explanation`
- `safety_note`
- `sources`
- `normalization_notes`
- `semantic_mapping`

During import, equation-mode rows are passed through `normalize_reaction_equations()` and persisted in `experiment_catalog_point_reaction_equations`, preserving raw text while adding canonical display/search fields, parser warnings/errors, validation status, formulae, participants, conditions, and reaction features.

## Replacement Plan For The Retired 30-Record Attempt

- The retired artifact is `data/seed/experiment_catalog/point_content_examples.json`.
- The old 30-example design imported all principles as text and was only suitable for smoke testing.
- The current authoritative seed replaces it with 76 reviewed records and must not flatten equation principles into `principle_text`.
- Import validation must reject:
  - legacy identity keys such as `experiment_id` and `point_key`
  - equation-mode records without `reaction_equations`
  - text-mode records without `principle_text`
  - duplicate target seed keys
  - duplicate target canonical point ids
  - records without a matched semantic mapping report
- A fresh import should reset retired seed-derived catalog/search state, import the current catalog tree, import the 76 point-content records as published content, persist 122 normalized reaction rows, and queue 76 ES upsert states/jobs for the point-placement documents.

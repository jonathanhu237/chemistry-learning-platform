# Productionization Final Notes

`data/seed` now contains only current runtime/import/rebuild data. The authoritative boundary is `data/seed/manifests/core_resources.json` and `scripts/validate_production_resources.py`.

Protected current resources include formal experiments, knowledge framework JSON, the current catalog tree, the 76-record catalog point-content seed, catalog-node textbook evidence seed, the current 54-bank / 1,965-question catalog-node question-bank seed, canonical textbook chunks, runtime search dictionaries including `chemistry_vocabulary.json`, ES/IK analyzer assets, student learning profiles, and the current manifest.

Retired resources are intentionally absent: old 300-point inventories, old manual point evidence, old 2,310-question bank artifacts, generated import/validation reports under `data/seed`, normalized three-element audit drafts, and local BGE dense/sparse embedding seed files. Canonical chunks remain current corpus data; local BGE embeddings and populated `chunk_embeddings` are not current restore requirements.

## Restore Path

```powershell
python scripts/apply_migrations.py
python scripts/publish_reviewed_curriculum.py
python scripts/seed_formal_experiments.py --skip-migrations
python scripts/import_canonical_evidence.py --skip-migrations
python scripts/import_experiment_knowledge_framework.py --skip-migrations
python scripts/generate_experiment_catalog_seed.py
python scripts/validate_experiment_catalog_seed.py --write-report
python scripts/import_experiment_catalog_seed.py --skip-migrations
python scripts/seed_catalog_point_evidence.py import
python scripts/seed_current_question_bank.py import --skip-migrations
python scripts/rebuild_video_library_index.py --recreate
python scripts/validate_production_resources.py
python scripts/seed_current_question_bank.py validate
python scripts/validate_experiment_points.py
```

Expected restored counts:

- 77 active formal experiments.
- 11 chapters, 133 units, 385 knowledge points.
- 569 catalog nodes: 176 directories, 393 point placements, and 357 canonical experiment points.
- 76 published catalog point-content seed records.
- 54 published generated question banks and 1,965 published questions.
- 2 source documents and 3,637 canonical source chunks.
- 0 legacy point evidence bindings.

## Validation Chain

```powershell
python scripts/validate_production_readiness.py --install-frontend
git status --short
```

Generated artifacts, review packets, logs, caches, and build outputs remain outside the protected seed boundary.

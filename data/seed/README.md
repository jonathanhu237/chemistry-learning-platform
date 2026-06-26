# Production Seed Resources

`data/seed` is a strict current-resource boundary. Files here must be required to restore, import, rebuild, or validate the current application baseline. Historical generation packets, audit drafts, local review reports, retired local BGE embeddings, and old `experiment_id + point_key` seed outputs do not belong here.

Protected current resources:

- `formal_experiments.json`: 77 current formal experiments.
- `knowledge_framework/`: 11 chapters, 133 knowledge units, 385 knowledge points, plus reviewed curriculum source.
- `experiment_catalog/catalog_tree.json`: current catalog tree seed with 569 nodes, 176 directories, 393 point placements, and 357 canonical experiment points.
- `experiment_catalog/point_content_seed.json`: 76 reviewed catalog point-content records, including 71 equation-mode records and 122 structured reaction-equation rows.
- `experiment_catalog/full_point_content_seed.json`: full current catalog point-content seed with 393 published point descriptions and structured reaction equations.
- `experiment_catalog/point_textbook_evidence_seed.json`: current catalog-node textbook evidence state and bindings, keyed by catalog node/canonical point identities.
- `question_banks/current_catalog_node_question_bank_seed_v1.json`: current published generated question-bank baseline with 78 banks and 2,311 real published questions.
- `canonical_rag/chunks/*.jsonl`: canonical textbook chunks used to recreate `source_documents` and `source_chunks`.
- `textbook_rag_precomputed/`: precomputed Qwen `text-embedding-v4` Elasticsearch documents for `canonical-rag-chunks-qwen-v1`; importing this bundle does not call Qwen or any other external API.
- `search/**`: runtime chemistry search dictionaries and ES/IK analyzer assets, including `chemistry_vocabulary.json`.
- `student_learning/element_profiles.json`: curated student-facing family and element learning profiles.
- `manifests/core_resources.json`: count, size, SHA256, and database expectation manifest for the current whitelist.

Forbidden retired seed artifacts:

- `experiment_points/`, `point_evidence/`, and old `question_bank/` directories.
- `canonical_rag/embeddings/**`, BGE dense/sparse vectors, row maps, embedding manifests, and embedding reports.
- `import_reports/`, cleanup plans, generated validation reports, review notes, and audit drafts under `data/seed`.
- Any question/evidence seed keyed only by legacy `experiment_id + point_key` identities.

Current restore order:

```bash
python scripts/bootstrap_production_seed.py --bootstrap-admin
```

The bootstrap command creates or updates the optional local admin account as `admin / 123456` only when `--bootstrap-admin` is supplied. Override the password with `--admin-password` or `SEED_ADMIN_PASSWORD` for non-local deployments.

Equivalent expanded restore order:

```bash
python scripts/apply_migrations.py
python scripts/publish_reviewed_curriculum.py --skip-migrations
python scripts/seed_formal_experiments.py --skip-migrations
python scripts/import_canonical_evidence.py --skip-migrations
python scripts/import_experiment_knowledge_framework.py --skip-migrations
python scripts/import_experiment_catalog_seed.py --skip-migrations
python scripts/seed_full_catalog_point_content.py import --skip-migrations
python scripts/seed_catalog_point_evidence.py import --skip-migrations
python scripts/seed_current_question_bank.py import --skip-migrations
python scripts/import_precomputed_textbook_rag.py --recreate
```

If teacher catalog search and student video-library search are also configured for Elasticsearch, run:

```bash
python scripts/bootstrap_production_seed.py --rebuild-search-indexes
```

Validation:

```bash
python scripts/validate_production_resources.py
python scripts/validate_experiment_catalog_seed.py --write-report
python scripts/seed_full_catalog_point_content.py validate
python scripts/import_precomputed_textbook_rag.py --dry-run
python scripts/seed_current_question_bank.py validate
python scripts/validate_experiment_points.py
```

Regenerate `manifests/core_resources.json` only after intentionally changing current seed resources:

```bash
python scripts/validate_production_resources.py --write-manifest
```

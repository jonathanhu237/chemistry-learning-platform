# Productionization Final Notes

`data/seed` contains only resources required to restore or validate the current product. The authoritative whitelist and expected database counts are `data/seed/manifests/core_resources.json`; enforcement belongs to `scripts/validate_production_resources.py`.

Protected resources include formal experiments, the knowledge framework, the catalog tree and full point content, catalog-point textbook evidence, the current question bank, demo identities, reviewed media, canonical textbook chunks, the precomputed Qwen textbook RAG bundle, teacher-search dictionaries/IK assets, and student element profiles.

Retired generation packets, audit reports, old point-keyed evidence/question data, and local BGE embedding artifacts remain outside the protected boundary. The product has one textbook RAG vector projection. Student Home feed/search is relational and has no Elasticsearch seed or rebuild step; teacher catalog search remains a separate rebuildable Elasticsearch projection.

## Canonical Restore

On a configured blank deployment:

```bash
python scripts/bootstrap_production_seed.py
```

To also rebuild the retained teacher catalog-authoring index:

```bash
python scripts/bootstrap_production_seed.py --rebuild-search-indexes
```

Current manifest expectations include:

- 77 active formal experiments.
- 11 chapters, 133 knowledge units, and 385 knowledge points.
- 569 catalog nodes: 176 directories and 393 point placements.
- 393 published point-content records.
- 52 question banks and 1,785 published questions.
- 2 source documents and 3,637 canonical source chunks.
- 393 point-evidence states and 3,537 evidence bindings.

Provider keys are not seed data. Configure MinerU OCR, embedding, rerank, and LLM endpoints through runtime environment values or the teacher settings page; never add real credentials to Git.

## Validation

```bash
python scripts/validate_production_resources.py
python scripts/validate_complete_seed_bootstrap.py
python scripts/validate_teacher_catalog_search.py
python scripts/validate_production_readiness.py --install-frontend
git status --short
git diff --check
```

Generated reports, uploads, extracted textbook pages/chunks, logs, caches, database dumps, and frontend builds remain outside the committed seed boundary.

# Production Seed Resources

`data/seed` is a strict current-resource boundary. Files here must be required to restore, import, rebuild, or validate the current application baseline. Historical generation packets, audit drafts, local review reports, retired local BGE embeddings, and old `experiment_id + point_key` seed outputs do not belong here.

Protected current resources:

- `formal_experiments.json`: 77 current formal experiments.
- `knowledge_framework/`: 11 chapters, 133 knowledge units, 385 knowledge points, plus reviewed curriculum source.
- `experiment_catalog/catalog_tree.json`: current catalog tree seed with 569 nodes, 176 directories, 393 point placements, and 357 canonical experiment points.
- `experiment_catalog/point_content_seed.json`: retained 76-record reviewed content sample for focused search/equation tests; it is not imported by the complete bootstrap.
- `experiment_catalog/full_point_content_seed.json`: authoritative current catalog point-content seed with 393 published point descriptions and structured reaction equations.
- `experiment_catalog/point_textbook_evidence_seed.json.zip`: current catalog-node textbook evidence state and bindings for all 393 active point placements, keyed by catalog node/canonical point identities.
- `question_banks/current_catalog_node_question_bank_seed_v1.json.zip`: current published generated question-bank baseline with 52 catalog-root banks and 1,785 real published point questions, five per canonical point.
- `identity/demo_identity_seed_v1.json`: default demo teacher-console account, one active class, and 30 active student roster/accounts. Defaults are demo credentials only and can be overridden at bootstrap time.
- `media/video_inventory_v1.json`: checksummed inventory for the reviewed experiment videos and generated placeholder video.
- `media/experiment_video_seed_v1.json`: media asset and point-video binding seed. Four real videos cover five point placements; one generated placeholder video covers the remaining 388 point placements.
- `media/experiment-videos-new-v1/**`: protected media seed package restored into `MEDIA_ROOT/seed/experiment-videos-new-v1/**`.
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
- Raw unreviewed video dumps. Reviewed seed videos must be referenced by `media/video_inventory_v1.json` and `media/experiment_video_seed_v1.json`.

Current restore order:

```bash
python scripts/bootstrap_production_seed.py
```

The bootstrap command creates or updates the demo teacher-console account as `admin / 123456`, creates `seed-class-2026`, creates 30 active student accounts `SEED001` through `SEED030` with default password `123456`, restores seed videos into `MEDIA_ROOT`, imports precomputed RAG evidence/questions, and finishes with complete seed validation.

Recommended blank-server flow:

```bash
cp .env.example .env
# Edit .env with deployment-only secrets and URLs:
# - DATABASE_URL, MEDIA_ROOT, API_PUBLIC_BASE_URL, AUTH_SECRET_KEY, WEB_ADMIN_ACCESS_TOKEN
# - AGENT_LLM_API_KEY for DeepSeek and AGENT_LLM_MODEL, for example deepseek-chat
# - TEXTBOOK_RAG_EMBEDDING_API_KEY / TEXTBOOK_RAG_RERANK_API_KEY for Alibaba Cloud Model Studio
# - TEXTBOOK_RAG_ELASTICSEARCH_URL and search Elasticsearch URLs
python scripts/bootstrap_production_seed.py
```

The `.env.example` file documents the current provider template without real secrets: Alibaba Cloud Model Studio/DashScope `text-embedding-v4` for embedding, `qwen3-rerank` for rerank, and DeepSeek's OpenAI-compatible chat provider for LLM generation.

Credential overrides are supported without editing committed seed JSON:

```bash
SEED_TEACHER_PASSWORD='change-me' SEED_STUDENT_PASSWORD='change-me' \
python scripts/bootstrap_production_seed.py
```

Equivalent CLI flags are available: `--teacher-username`, `--teacher-password`, `--teacher-display-name`, `--class-id`, `--class-name`, `--student-password`, and `--media-root`.

Equivalent expanded restore order. `import_experiment_catalog_seed.py` imports the directory/point structure and canonical point ids; `seed_full_catalog_point_content.py` imports the authoritative 393 point descriptions.

```bash
python scripts/apply_migrations.py
python scripts/seed_demo_identities.py import --skip-migrations
python scripts/publish_reviewed_curriculum.py --skip-migrations
python scripts/seed_formal_experiments.py --skip-migrations
python scripts/import_canonical_evidence.py --skip-migrations
python scripts/import_experiment_knowledge_framework.py --skip-migrations
python scripts/import_experiment_catalog_seed.py --skip-migrations
python scripts/seed_full_catalog_point_content.py import --skip-migrations
python scripts/seed_experiment_videos.py import --skip-migrations
python scripts/seed_catalog_point_evidence.py import --skip-migrations
python scripts/seed_current_question_bank.py import --skip-migrations
python scripts/import_precomputed_textbook_rag.py --recreate
python scripts/validate_complete_seed_bootstrap.py
```

If teacher catalog search and student video-library search are also configured for Elasticsearch, run:

```bash
python scripts/bootstrap_production_seed.py --rebuild-search-indexes
```

Validation:

```bash
python scripts/validate_production_resources.py
python scripts/validate_experiment_catalog_seed.py --write-report
python scripts/seed_demo_identities.py validate --skip-migrations
python scripts/seed_experiment_videos.py validate --skip-migrations
python scripts/seed_full_catalog_point_content.py validate
python scripts/import_precomputed_textbook_rag.py --dry-run
python scripts/seed_current_question_bank.py validate
python scripts/validate_complete_seed_bootstrap.py
python scripts/validate_experiment_points.py
```

Regenerate `manifests/core_resources.json` only after intentionally changing current seed resources:

```bash
python scripts/validate_production_resources.py --write-manifest
```

Manual runtime configuration after seed import:

- AI question generation: configure provider, base URL, API key, and model name through environment/platform settings, for example `AGENT_LLM_PROVIDER`, `AGENT_LLM_BASE_URL`, `AGENT_LLM_API_KEY`, and `AGENT_LLM_MODEL`.
- Textbook RAG refresh/generation: configure `TEXTBOOK_RAG_ELASTICSEARCH_URL`, `TEXTBOOK_RAG_ELASTICSEARCH_INDEX`, Qwen embedding base URL/API key/model, and Qwen rerank base URL/API key/model. Seed restore does not call these APIs.
- Search: configure teacher catalog and student video-library search backends/URLs if Elasticsearch search is required in the deployment.
- Deployment URLs and secrets: configure `DATABASE_URL`, `MEDIA_ROOT`, `API_PUBLIC_BASE_URL`, `AUTH_SECRET_KEY`, and `WEB_ADMIN_ACCESS_TOKEN` outside seed files.

Adding later video seed versions:

1. Put reviewed video files under a new versioned folder such as `data/seed/media/experiment-videos-new-v2/`.
2. Generate a new inventory and media seed manifest with stable media ids, file checksums, reviewed point/canonical bindings, and placeholder coverage for still-unfilmed points.
3. Import only the media seed with `python scripts/seed_experiment_videos.py import --manifest-path <new-manifest>`. This does not rerun RAG embeddings or replace the question bank.
4. Regenerate `data/seed/manifests/core_resources.json` and run `python scripts/validate_complete_seed_bootstrap.py`.

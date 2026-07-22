# Production Operations

This document is the runbook for the canonical chemistry learning platform. The supported product topology has one student H5, one teacher console, and one backend.

## Service Topology

`docker-compose.yml` defines the deployable application graph:

- `postgres`: canonical application facts, identities, assessment state, Home recommendations/favorites, textbook metadata, and job state.
- `elasticsearch`: IK-enabled teacher catalog search and textbook RAG projections.
- `backend`: FastAPI `/health` and `/api/*` owner.
- `web-student`: the green five-tab student H5.
- `web-teacher`: the Ant Design teacher console.
- `tusd`: resumable local video uploads.
- `video-worker`: local video probe, rendition, thumbnail, subtitle, and duplicate-candidate processing.
- `textbook-ingestion-worker`: queued PDF extraction, MinerU OCR when required, chunking, embedding, and Elasticsearch indexing.

Student Home is not an Elasticsearch consumer. Its default feed, focused search, explicit recommendation ordering, and favorite state are read from PostgreSQL. Elasticsearch outages must not be described as a Home-feed outage.

The two remaining Elasticsearch consumers are independent:

- the teacher catalog-authoring index, configured with `TEACHER_CATALOG_SEARCH_*`; and
- the textbook RAG index, configured with `TEXTBOOK_RAG_*` or from the teacher AI settings page.

## Environment And Secrets

Start from the committed template:

```bash
cp .env.example .env
```

At minimum, production must replace development database/auth values and configure the public origins appropriate to the deployment:

```text
CHEMISTRY_APP_ENV=production
DATABASE_URL=postgresql+psycopg://...
AUTH_SECRET_KEY=<long-random-secret>
MEDIA_ROOT=/app/data/media
FRONTEND_ALLOWED_ORIGINS=https://student.example,https://teacher.example
STUDENT_PREVIEW_APP_BASE_URL=https://student.example
```

Never commit `.env`, provider API keys, uploaded PDFs, generated textbook data, or production database dumps. AI settings saved in the teacher console are persisted by the backend and API responses redact the secret value; database backups must still be treated as secret-bearing material.

Online textbook processing is opt-in:

```text
TEXTBOOK_INGESTION_ENABLED=true
TEXTBOOK_STORAGE_ROOT=/app/data/textbooks
MAX_TEXTBOOK_UPLOAD_MB=200
TEXTBOOK_UPLOAD_PROXY_MAX_MB=210
TEXTBOOK_RAG_ENABLED=true
TEXTBOOK_RAG_ELASTICSEARCH_URL=http://elasticsearch:9200
TEXTBOOK_RAG_ELASTICSEARCH_INDEX=canonical-rag-chunks-qwen-v1
```

`TEXTBOOK_UPLOAD_PROXY_MAX_MB` must remain greater than `MAX_TEXTBOOK_UPLOAD_MB` because the proxy measures the complete multipart request.

The teacher **System Settings → AI and textbook RAG** surface is the normal owner for OCR, embedding, and rerank endpoints, protocols, models, API keys, dimensions, batch sizes, timeouts, and retrieval limits. Environment variables bootstrap the same provider-neutral contract before settings have been saved. MinerU is the default OCR provider label, but the endpoint and model remain configuration, not source-code constants. Embedding and rerank accept the configured compatible provider, including Qwen endpoints.

## Deploy And Upgrade

Validate configuration, build the required services, remove retired containers, and run the Compose smoke check:

```bash
python scripts/deploy_compose_stack.py
```

Useful options:

```bash
python scripts/deploy_compose_stack.py --skip-build
python scripts/deploy_compose_stack.py --skip-smoke
python scripts/deploy_compose_stack.py --skip-index-rebuild
python scripts/deploy_compose_stack.py --gpu
```

The default stack has no GPU requirement and lets `video-worker` fall back to CPU transcoding. Use `--gpu` only on an NVIDIA host with the Container Toolkit configured; it layers `docker-compose.gpu.yml` over the default Compose file.

`textbook-ingestion-worker` remains an optional Compose-profile service. `deploy_compose_stack.py` and the manual command below name it explicitly, which starts it without enabling every service in that profile. For a partial stack, omit it unless online textbook jobs should run.

For a controlled manual upgrade:

```bash
docker compose config --quiet
docker compose up -d --build --remove-orphans backend web-student web-teacher postgres elasticsearch tusd video-worker textbook-ingestion-worker
docker compose exec -T backend python scripts/apply_migrations.py
python scripts/validate_compose_stack.py --skip-up
```

Migrations are ordered, forward-only files under `server/migrations`. Back up PostgreSQL and persistent files before applying a migration that rewrites or removes data. Never rename an applied migration or run ad-hoc DDL as an application startup fallback.

Health checks:

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:9200/_cluster/health
docker compose ps
docker compose logs --tail=200 backend
docker compose logs --tail=200 video-worker
docker compose logs --tail=200 textbook-ingestion-worker
```

Default Compose host bindings are controlled by `.env`; do not assume the development Vite ports are the deployed ports.

## Identity Operations

Bootstrap the first supervisor teacher with a temporary password supplied outside source control:

```bash
python scripts/bootstrap_admin.py --username admin
```

The internal `admin` role means **supervisor teacher**. It is not a separate platform-operations product. Inside the teacher Settings page:

- every teacher can change their own password;
- a supervisor teacher can list, create, reset, enable, or disable teacher accounts;
- account creation/reset requires a password change at next login;
- reset/disable revokes affected sessions; and
- historical ownership is preserved, so accounts are not deleted or role-edited from the product.

Classes, roster imports, shared initial passwords, and archived-class behavior are owned by the teacher Classes page. Student accounts created from an initial roster password must complete the required password change before entering learning APIs.

## Student Home Operations

The canonical endpoint is:

```http
GET /api/student/home-video-feed?q=<query>&limit=<1..30>&cursor=<cursor>
```

Only published catalog point placements with published, playable media are eligible. Ordering is deterministic: explicit teacher recommendations first, followed by catalog order. Cursors are bound to the normalized query and current result pool; clients should restart from the first page after a stale-cursor response.

Teachers author recommendation status and non-negative order from the current catalog editor. The backend stores this in `student_home_video_recommendations`. Ordinary catalog videos must not be labeled as recommended.

The only persisted Home save type is `favorite`:

```http
PUT    /api/student/video-saves/favorite
DELETE /api/student/video-saves/favorite
GET    /api/student/video-saves/favorite/feed
```

There is no separate Home index to rebuild. Diagnose missing cards by checking catalog/content publication, media binding publication, media processing readiness, and the recommendation/favorite rows in PostgreSQL.

## Teacher Catalog Search

Teacher catalog search indexes active directory and point nodes for authoring, including draft context, teacher notes, status facets, paths, equations, formulae, and aliases. PostgreSQL remains the fact owner; Elasticsearch is a rebuildable projection.

Rebuild and validate it with the current scripts:

```bash
python scripts/rebuild_teacher_catalog_search_index.py --recreate
python scripts/validate_teacher_catalog_search.py
```

Targeted diagnostics:

```bash
python scripts/rebuild_teacher_catalog_search_index.py --diagnostics
python scripts/rebuild_teacher_catalog_search_index.py --dry-run
```

The teacher catalog UI also exposes index/query diagnostics through authenticated catalog endpoints. Do not write Elasticsearch documents by hand. A failed catalog projection must not mutate PostgreSQL or the textbook RAG index.

## Online Textbook Ingestion And RAG

The teacher **Textbook Knowledge Base** page owns the online workflow:

1. Upload a PDF and optional logical textbook/version labels.
2. The worker extracts native text and sends only pages that fail quality checks to the configured MinerU HTTP service.
3. The pipeline normalizes pages, creates stable chunks, calls the configured embedding endpoint, and writes a verified projection to the configured textbook RAG index.
4. A teacher reviews page/chunk counts and quality issues, then publishes the version.
5. Atom, teacher learning-assistant, and question-evidence retrieval use the active published corpus with the configured reranker.

Processing stages are visible as uploaded, extracting, awaiting OCR, OCR, structuring, chunking, embedding, indexing, review-ready, ready, failed, or cancelled. Use the teacher UI to inspect events, cancel, retry, publish, deactivate, or delete according to the returned allowed actions.

Readiness requires all configured components to agree on endpoint, model, embedding dimension, index metadata, and active projection. Check the teacher AI settings and:

```http
GET /api/admin/textbooks/upload-policy
GET /api/admin/learning-assistant/runtime
```

For a blank deployment with protected precomputed RAG resources:

```bash
python scripts/import_precomputed_textbook_rag.py --recreate
python scripts/import_precomputed_textbook_rag.py --dry-run
```

For an intentional rebuild from canonical chunks or current online textbook rows, use the existing projection scripts after taking an index snapshot:

```bash
python scripts/rebuild_online_textbook_projections.py
python scripts/index_textbook_rag_chunks.py
```

Do not create a second vector store for student video discovery. The textbook RAG index is the vector projection owner.

Back up `data/textbooks` with PostgreSQL and Elasticsearch snapshots when online uploads are in use. The PDF files, database metadata, and index documents are a coordinated unit; a database-only restore cannot recreate deleted source PDFs.

## Local Video Processing

Video upload and processing remain supported. Back up `data/media` with PostgreSQL. Common operations:

```bash
docker compose up -d --build backend tusd video-worker postgres
docker compose run --rm -e VIDEO_WORKER_BACKFILL=1 video-worker
docker compose stop video-worker
```

Stopping the worker pauses new processing but does not remove ready media. Detailed GPU/CPU transcoding, subtitle, duplicate-detection, retry, and rollback instructions live in `docs/local_video_processing.md`.

## Assessment Compatibility

The active student entry points are smart assessment and hierarchical custom assessment. A student without a completed smart assessment receives the one smart baseline flow. Custom assessment expands selected published chapter/directory/point scope to usable leaf points and accepts exactly 1, 2, or 3 questions per point.

Historical pretest rows, report types, and report labels are retained for read-only compatibility. There is no supported operation to start or submit a new pretest. Do not drop historical pretest tables merely because the active route is absent.

## Backup And Restore

A recoverable backup includes at least:

- PostgreSQL;
- `data/media`;
- `data/textbooks` when online ingestion is enabled;
- Elasticsearch snapshots for teacher search and textbook RAG; and
- the deployed `.env`/secret manager values stored outside the repository.

Example logical PostgreSQL backup from Compose:

```bash
docker compose exec -T postgres pg_dump -U chemistry -d chemistry_exam -Fc > chemistry_exam.dump
```

Verify backups in an isolated environment. Do not overwrite a live database or media/textbook directory as a routine validation step.

To restore the committed blank-server baseline instead of production data:

```bash
python scripts/bootstrap_production_seed.py
```

The expanded seed order and protected-resource boundary are documented in `data/seed/README.md`.

## Release Validation

Run the full repository gate:

```bash
python scripts/validate_production_readiness.py --install-frontend
```

Run the real Compose smoke when Docker, ports, provider-independent search prerequisites, and sufficient resources are available:

```bash
python scripts/validate_production_readiness.py --run-compose-smoke --skip-frontend --skip-backend-tests
```

The Compose validator checks the required service set, rejects retired services, validates PostgreSQL, Elasticsearch/IK assets and analyzer behavior, checks both frontend/API proxies, applies migrations, rebuilds teacher catalog search, and runs its production-style validator.

Focused recovery checks:

```bash
python scripts/validate_backend_architecture.py
python scripts/validate_production_resources.py
python scripts/validate_complete_seed_bootstrap.py
python scripts/validate_teacher_catalog_search.py
docker compose config --quiet
git diff --check
```

If a gate cannot run because a provider, browser, GPU, or Docker dependency is unavailable, report it as skipped with the missing prerequisite. Do not treat an unexecuted environment-dependent check as passing.

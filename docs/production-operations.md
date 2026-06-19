# Production Operations Baseline

This document records the operational baseline for turning the admin platform into a maintainable production project. It does not change feature behavior; it defines how to validate, deploy, back up, restore, and extend the current system safely.

## Application Structure Standard

Whole-application structural changes are governed by `docs/application-engineering-structure.md` and the OpenSpec change `standardize-application-engineering-structure`.

The current application is treated as three coupled engineering surfaces plus a validation/service graph:

- student H5 frontend: `apps/student-web`
- teacher/admin frontend: `apps/admin-web`
- backend service: `server/app`
- required Compose and validation scripts: `docker-compose.yml` and `scripts/`

Before moving files across these surfaces, or before splitting a major shell/API/domain owner, create or update an OpenSpec change that names the touched surfaces, owner map, validation gate, and rollback posture. Destructive refactors are allowed when git history, OpenSpec scope, and validation output make rollback clear; do not preserve obsolete wrappers only for old internal compatibility.

## Protected Resources

Current system data is protected under `data/seed` and validated by:

```powershell
python scripts/validate_production_resources.py
```

The manifest at `data/seed/manifests/core_resources.json` covers the formal experiment catalog, knowledge framework, experiment point inventory, current point-aware question bank, question-bank schema, canonical chunks, canonical embeddings, manually reviewed point evidence bindings, and current import reports.

Destructive cleanup must run only after this validation passes. The cleanup script intentionally excludes `data/media` because uploaded media requires a database/UI consistency plan.

## Migration Discipline

Historical migrations are append-only. Do not rename or renumber existing files, including the two historical `010_*.sql` files. They have already become part of the migration identity recorded in `schema_migrations`.

This productionization baseline now includes `014_student_h5_login.sql`, `015_student_pretest_sessions.sql`, and `016_student_posttest_sessions.sql`. New migrations after this baseline must use the next unambiguous prefix:

```text
017_<short_description>.sql
018_<short_description>.sql
...
```

Rules for new migrations:

- Add exactly one new numeric prefix at a time.
- Do not introduce another duplicate number.
- Keep migrations idempotent where practical.
- Test with `python scripts/apply_migrations.py` against a disposable database before merging.
- If a historical migration needs correction, add a new follow-up migration instead of editing the old file.

## Environment Configuration

Copy `.env.example` to `.env` for local Docker Compose or production-like runs:

```powershell
Copy-Item .env.example .env
```

Production deployments must set:

- `CHEMISTRY_APP_ENV=production`
- `DATA_BACKEND=postgres`
- `DATABASE_URL`
- `MEDIA_ROOT`
- `API_PUBLIC_BASE_URL`
- `FRONTEND_ALLOWED_ORIGINS`
- `AUTH_SECRET_KEY` with a long random value
- `AGENT_LLM_PROVIDER=disabled` when no LLM provider is configured, or provider credentials/model when enabled
- `VIDEO_LIBRARY_SEARCH_ENABLED=true` for the student H5 experiment video library search entry
- `VIDEO_LIBRARY_SEARCH_BACKEND=elasticsearch`; production video-library search requires Elasticsearch with IK analysis
- `VIDEO_LIBRARY_SEARCH_URL`, `VIDEO_LIBRARY_SEARCH_INDEX`, `VIDEO_LIBRARY_SEARCH_ANALYZER`, and `VIDEO_LIBRARY_SEARCH_TIMEOUT_SECONDS`
- `VIDEO_LIBRARY_SEARCH_BOOTSTRAP_INDEX=true` when the backend or rebuild command should create the index mapping
- `VIDEO_LIBRARY_SEARCH_LOCAL_FALLBACK=false` in production; local fallback is only for explicit local or test runs
- `VIDEO_LIBRARY_SEARCH_REQUIRE_ES_IN_PRODUCTION=true` so startup/readiness fails when ES/IK is missing

Do not commit real `.env` files or secrets.

## Docker Expectations

Compose owns the production-like application graph. Build and start all required default services together:

```powershell
docker compose up -d --build backend student-web admin-web postgres elasticsearch tusd video-worker
```

Default Compose services:

- `postgres`: pgvector Postgres with `pg_isready` health check.
- `elasticsearch`: Elasticsearch with the IK analyzer plugin. Compose builds `chemistry-admin-elasticsearch-ik:8.11.3` from Elastic's official `docker.elastic.co/elasticsearch/elasticsearch:8.11.3` image and installs INFINI Labs `analysis-ik` `8.11.3`. It disables security for local development, exposes port `9200`, and health-checks the HTTP endpoint.
- `backend`: FastAPI API service. It serves `/health` and `/api/*` only.
- `student-web`: student H5 frontend service at `http://127.0.0.1:5173`, serving SPA routes from its own nginx runtime and proxying `/api/*` to `backend:8000`.
- `admin-web`: teacher/admin frontend service at `http://127.0.0.1:5174`, serving canonical root routes such as `/login`, `/overview`, `/experiments`, and `/videos` from its own nginx runtime and proxying `/api/*` to `backend:8000`.
- `tusd`: resumable upload receiver sharing `data/media`.
- `video-worker`: local video processing worker sharing `data/media`.

The backend depends on the PostgreSQL and Elasticsearch health checks. The frontend services depend on backend health. If a production-like run swaps the search image, verify the replacement image provides the `ik_max_word` tokenizer before bootstrapping the `student-video-library` index.

The Compose Postgres service is available to other containers as `postgres:5432`. Its host binding defaults to `127.0.0.1:15432` to avoid collisions with a developer's local Postgres. Override `POSTGRES_HOST_PORT` only when the host port is known to be free.

Frontend host bindings default to `127.0.0.1:5173` for `student-web` and `127.0.0.1:5174` for `admin-web`. Override `STUDENT_WEB_HOST_PORT` or `ADMIN_WEB_HOST_PORT` only when the host port is already occupied. Rollback for this topology uses git or deployment rollback; do not restore backend SPA fallbacks as a compatibility layer.

## Student Video-Library Search Operations

Student video-library search is a PostgreSQL-to-Elasticsearch projection. PostgreSQL point tables are the fact source:

- `experiment_video_points`: stable `(experiment_id, point_key)` identities
- `experiment_point_learning_content`: teacher-authored principle, phenomenon explanation, safety note, publication audit
- `experiment_point_related_links`: manual related point links and hidden default overrides
- `experiment_video_point_search_index_state`: retryable desired search actions and sync status

Elasticsearch stores derived point documents only. Do not edit ES documents by hand and do not treat ES hit sources as student page content.

Bootstrap or rebuild the search index from PostgreSQL:

```powershell
python scripts/rebuild_video_library_index.py --recreate
```

Preview the document count without writing to ES:

```powershell
python scripts/rebuild_video_library_index.py --dry-run
```

Validate ES/IK readiness in production mode:

```powershell
python scripts/validate_video_library_search.py
```

Inspect admin-facing index state through the backend:

```powershell
Invoke-RestMethod http://localhost:8000/api/admin/video-library/index/diagnostics -Headers @{ Authorization = "Bearer <token>" }
```

The chemistry search seed files live under `data/seed/search/`:

- `chemical_aliases.json`: formula and common-name aliases such as HCl/salt acid and Na2S2O3/sodium thiosulfate
- `chemical_stopwords.txt`: high-frequency workflow words that should carry less search meaning

Admin point content edits write PostgreSQL first. Saving drafts queues a delete from search; publishing queues an upsert; unpublishing, archiving, or video binding changes queue the affected point for refresh. A failed ES write must leave the PostgreSQL content intact and visible in `experiment_video_point_search_index_state` for retry or full rebuild.

Optional RAG reranking service:

```powershell
docker compose --profile rag up --build
```

The `rag` profile expects local BGE model files mounted at `E:/models/BAAI` and exposes `/health` on port `8010`.

## Media Lifecycle Operations

`data/media` is operational upload state, not protected seed data. It can be backed up, archived, or cleaned only with database consistency in mind because `media_assets`, `media_bindings`, processing jobs, and review rows may still reference local files.

Inspect the current media lifecycle state with a dry run:

```powershell
python scripts/media_lifecycle_cleanup.py --json --limit 500 --orphan-limit 200
```

The script reports asset dependency counts, missing files, existing referenced files, and unreferenced orphan files. Database-backed asset deletion intentionally refuses by default:

```powershell
python scripts/media_lifecycle_cleanup.py --delete-asset-files
```

Only unreferenced orphan files under `MEDIA_ROOT` may be removed directly:

```powershell
python scripts/media_lifecycle_cleanup.py --delete-orphans --limit 500 --orphan-limit 200
```

Before deleting media for production, back up any media that should remain available and confirm the admin UI shows missing or partial files intentionally instead of broken playback links. See `docs/production-media-cleanup.md` for the detailed cleanup procedure.

## One-Command Validation

Run the full local validation chain with frontend dependency installation:

```powershell
python scripts/validate_production_readiness.py --install-frontend
```

The command checks protected resources, video-library ES/IK readiness, experiment point identity validation, OpenSpec strict validation, backend import smoke, backend tests, admin frontend typecheck/tests/build, student H5 typecheck/tests/build, and the admin build chunk report.
The default OpenSpec target is `backend-slim-domain-architecture`; use `--change <name>` to validate a different active or historical change.
The backend stage also runs:

```powershell
python scripts/validate_backend_architecture.py
```

This validates slim import boundaries, deleted compatibility paths, and the canonical route inventory.
The admin frontend stage also runs `npm run build:report` after `npm run build` so large production chunks stay classified by owner.

For backend/resource-only environments:

```powershell
python scripts/validate_production_readiness.py --skip-frontend
```

Skipping frontend validation is acceptable only for a scoped backend/resource phase. A production release gate should run the full command.

Run the real Docker Compose application smoke check when deployment wiring changes or when a change makes a service required:

```powershell
python scripts/validate_production_readiness.py --run-compose-smoke --skip-frontend --skip-backend-tests
```

This starts or verifies the required default Compose services, verifies backend and frontend health, verifies both frontend `/api/*` proxies, verifies PostgreSQL reachability, verifies `ik_max_word` through Elasticsearch `_analyze`, applies migrations, rebuilds the video-library index, and runs the ES/IK readiness validator with production fallback disabled.

To also rebuild images as part of the smoke check, run the lower-level command explicitly:

```powershell
python scripts/validate_compose_stack.py --build
```

Browser e2e smoke is opt-in because it requires a running backend, a running admin frontend on the allowed local origin, and a local browser runtime:

```powershell
Set-Location apps/admin-web
npm run dev
# In another shell, with the Docker backend running:
npm run e2e:smoke
Set-Location ..\..
```

The smoke script defaults to:

- admin frontend: `http://localhost:5174`
- backend API: `http://localhost:8000`
- local admin: `codex_smoke_admin`

If `E2E_ADMIN_PASSWORD` is not set, the script prepares a disposable local smoke admin through the Docker backend container. For an existing admin account, set `E2E_ADMIN_USERNAME` and `E2E_ADMIN_PASSWORD`. To run the same check through the validation chain:

```powershell
python scripts/validate_production_readiness.py --run-e2e
```

The student H5 mobile route-stack QA defaults to `http://127.0.0.1:5173` through `STUDENT_H5_URL`. It covers direct root routes, nested detail routes, and the video library detail route `/video-library` when run with a student account or `STUDENT_H5_QA_MOCK=1`.

## Local Smoke Tests

After rebuilding the backend and optional RAG service, verify the runtime before handoff:

```powershell
docker compose --profile rag up -d --build backend bge-rag
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8010/health
```

Run representative authenticated API checks:

```powershell
# Log in with a local-only admin account, then reuse the bearer token.
Invoke-RestMethod http://localhost:8000/api/admin/media/assets?limit=3 -Headers @{ Authorization = "Bearer <token>" }
Invoke-RestMethod http://localhost:8000/api/admin/learning-assistant/ask -Method Post -Headers @{ Authorization = "Bearer <token>" } -ContentType "application/json" -Body '{"question":"Explain a representative experiment point.","allow_rag_lookup":false}'
```

Browser-smoke the main admin paths after the frontend service or dev server is running:

- `/overview`
- `/videos`
- `/learning-assistant`
- `/question-banks`
- `/analytics`

## Local Smoke Admin Account

Temporary admin accounts created for smoke testing, such as `codex_smoke_admin`, are local-only developer database state. They are not seed data, are not protected resources, and must not be shipped or documented with shared passwords.

Production environments should create named administrator accounts through the deployment bootstrap or identity-management process, then rotate or remove any smoke-only credentials before real users are admitted. For local test databases, recreate a smoke admin with `scripts/bootstrap_admin.py` and a local password manager entry when needed.

## Restore From Declared Resources

For a fresh database with declared seed resources available:

```powershell
python scripts/apply_migrations.py
python scripts/publish_reviewed_curriculum.py
python scripts/seed_formal_experiments.py --skip-migrations
python scripts/import_canonical_evidence.py --skip-migrations
python scripts/import_experiment_knowledge_framework.py --skip-migrations
python scripts/point_aware_question_bank.py import --bank-kind default --bank-status published --question-status published --skip-migrations
python scripts/import_manual_reviewed_point_evidence.py --skip-migrations
python scripts/validate_production_resources.py
python scripts/validate_experiment_points.py
```

Expected protected baseline counts:

- 77 formal experiments
- 11 chapters, 133 units, 385 knowledge points
- 300 experiment points
- 77 question banks, 2310 questions
- 3637 canonical chunks and embeddings
- 300 point evidence bindings

## Database Backup And Restore

Create a compressed backup from the Compose Postgres container:

```powershell
docker compose exec postgres pg_dump -U chemistry -d chemistry_exam -Fc -f /tmp/chemistry_exam.dump
docker compose cp postgres:/tmp/chemistry_exam.dump .\backups\chemistry_exam.dump
```

Restore into a disposable or replacement database:

```powershell
docker compose cp .\backups\chemistry_exam.dump postgres:/tmp/chemistry_exam.dump
docker compose exec postgres dropdb -U chemistry --if-exists chemistry_exam
docker compose exec postgres createdb -U chemistry chemistry_exam
docker compose exec postgres pg_restore -U chemistry -d chemistry_exam --clean --if-exists /tmp/chemistry_exam.dump
```

Back up `data/media` separately if uploaded media should be preserved. Do not delete media files while database `media_assets` or `media_bindings` records still point to them.

Point learning content is ordinary PostgreSQL state and is covered by the database dump above. After restoring a database, rebuild the derived video-library index instead of restoring stale ES data:

```powershell
python scripts/rebuild_video_library_index.py --recreate
python scripts/validate_video_library_search.py
```

If the ES volume is corrupted or intentionally cleared, keep PostgreSQL and protected seed data intact, recreate the index, and run the rebuild command. Do not delete `experiment_video_point_evidence`, `source_chunks`, or `data/seed/point_evidence/manual_reviewed_point_evidence.jsonl`; those resources remain the assistant/RAG evidence path and are separate from teacher-authored point content.

## Search Rollback Notes

If the point editor or search projection must be rolled back during a release:

- Disable or hide the admin point editor at the frontend/API routing layer while keeping `experiment_video_points` and point content tables in place.
- Set `VIDEO_LIBRARY_SEARCH_ENABLED=false` only as an emergency product rollback; production readiness should fail until ES/IK search is restored for normal releases.
- Clear or recreate the ES index with `python scripts/rebuild_video_library_index.py --recreate` after the issue is fixed.
- Never roll back by deleting manual-reviewed point evidence or canonical chunks; those are protected assistant resources, not search projection cache.

Local developers may set `VIDEO_LIBRARY_SEARCH_BACKEND=local` and `VIDEO_LIBRARY_SEARCH_LOCAL_FALLBACK=true` only for isolated fallback tests. Production-like development should run `docker compose up elasticsearch backend` and use the same ES/IK projection path as production.

## Release Gate

Before declaring a phase production-ready, run:

```powershell
python scripts/validate_production_readiness.py --install-frontend
openspec validate backend-slim-domain-architecture --strict
git status --short
```

The worktree should be clean after generated local outputs are either ignored or intentionally cleaned.

## Continuous Integration

The repository includes a GitHub Actions workflow at `.github/workflows/production-readiness.yml`.
It is manually triggered with `workflow_dispatch` so ordinary pushes do not send automatic GitHub Actions notifications.

CI performs the same readiness gates as the local script:

- checkout with Git LFS enabled so protected seed resources are present
- Python dependency installation and backend tests
- frontend `npm ci`, typecheck, tests, production build, and chunk report
- OpenSpec strict validation for the active quality change
- protected resource manifest validation
- admin app import smoke

If an environment-specific phase needs to skip a stage locally, use the explicit script flags such as `--skip-frontend`, `--skip-backend-tests`, `--skip-openspec`, or `--skip-resource-validation`. Use `--run-e2e` only when the local browser smoke prerequisites are running. Production release gates should run the full chain and may add `--run-e2e` when validating an interactive runtime.

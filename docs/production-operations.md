# Production Operations Baseline

This document records the operational baseline for turning the admin platform into a maintainable production project. It does not change feature behavior; it defines how to validate, deploy, back up, restore, and extend the current system safely.

## Protected Resources

Current system data is protected under `data/seed` and validated by:

```powershell
python scripts/validate_production_resources.py
```

The manifest at `data/seed/manifests/core_resources.json` covers the formal experiment catalog, knowledge framework, experiment point inventory, current point-aware question bank, question-bank schema, canonical chunks, canonical embeddings, manually reviewed point evidence bindings, and current import reports.

Destructive cleanup must run only after this validation passes. The cleanup script intentionally excludes `data/media` because uploaded media requires a database/UI consistency plan.

## Migration Discipline

Historical migrations are append-only. Do not rename or renumber existing files, including the two historical `010_*.sql` files. They have already become part of the migration identity recorded in `schema_migrations`.

New migrations after this productionization baseline must use the next unambiguous prefix:

```text
014_<short_description>.sql
015_<short_description>.sql
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

Do not commit real `.env` files or secrets.

## Docker Expectations

Before starting the backend image, build the admin frontend:

```powershell
Set-Location apps/admin-web
npm ci
npm run build
Set-Location ..\..
docker compose up --build
```

Default Compose services:

- `postgres`: pgvector Postgres with `pg_isready` health check.
- `backend`: FastAPI admin service, serves `/health` and `/admin`.
- `tusd`: resumable upload receiver sharing `data/media`.
- `video-worker`: local video processing worker sharing `data/media`.

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

The command checks protected resources, OpenSpec strict validation, backend import smoke, backend tests, frontend typecheck, frontend tests, and frontend build.
During the third quality pass, the default OpenSpec target is `production-quality-iteration-three`; use `--change <name>` to validate a different active or historical change.
The frontend stage also runs `npm run build:report` after `npm run build` so large production chunks stay classified by owner.

For backend/resource-only environments:

```powershell
python scripts/validate_production_readiness.py --skip-frontend
```

Skipping frontend validation is acceptable only for a scoped backend/resource phase. A production release gate should run the full command.

Browser e2e smoke is opt-in because it requires a running backend, a running frontend dev server on the allowed local origin, and a local browser runtime:

```powershell
Set-Location apps/admin-web
npm run dev
# In another shell, with the Docker backend running:
npm run e2e:smoke
Set-Location ..\..
```

The smoke script defaults to:

- frontend: `http://localhost:5174`
- backend API: `http://localhost:8000`
- local admin: `codex_smoke_admin`

If `E2E_ADMIN_PASSWORD` is not set, the script prepares a disposable local smoke admin through the Docker backend container. For an existing admin account, set `E2E_ADMIN_USERNAME` and `E2E_ADMIN_PASSWORD`. To run the same check through the validation chain:

```powershell
python scripts/validate_production_readiness.py --run-e2e
```

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

Browser-smoke the main admin paths after the frontend dev server is running:

- `/admin/overview`
- `/admin/videos`
- `/admin/learning-assistant`
- `/admin/question-banks`
- `/admin/analytics`

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

## Release Gate

Before declaring a phase production-ready, run:

```powershell
python scripts/validate_production_readiness.py --install-frontend
openspec validate production-quality-iteration-three --strict
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

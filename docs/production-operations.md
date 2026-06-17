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

This productionization baseline now includes `014_student_h5_login.sql` and `015_student_pretest_sessions.sql`. New migrations after this baseline must use the next unambiguous prefix:

```text
016_<short_description>.sql
017_<short_description>.sql
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

Before starting the backend image, build both frontends:

```powershell
Set-Location apps/admin-web
npm ci
npm run build
Set-Location ../student-web
npm ci
npm run build
Set-Location ..\..
docker compose up --build
```

Default Compose services:

- `postgres`: pgvector Postgres with `pg_isready` health check.
- `backend`: FastAPI service, serves `/health`, the student H5 at `/`, and the admin console at `/admin`.
- `tusd`: resumable upload receiver sharing `data/media`.
- `video-worker`: local video processing worker sharing `data/media`.

Optional RAG reranking service:

```powershell
docker compose --profile rag up --build
```

The `rag` profile expects local BGE model files mounted at `E:/models/BAAI` and exposes `/health` on port `8010`.

## One-Command Validation

Run the full local validation chain with frontend dependency installation:

```powershell
python scripts/validate_production_readiness.py --install-frontend
```

The command checks protected resources, OpenSpec strict validation, backend import smoke, backend tests, admin frontend typecheck/tests/build, and student H5 typecheck/build.

For backend/resource-only environments:

```powershell
python scripts/validate_production_readiness.py --skip-frontend
```

Skipping frontend validation is acceptable only for a scoped backend/resource phase. A production release gate should run the full command.

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
openspec validate production-hardening-iteration-two --strict
git status --short
```

The worktree should be clean after generated local outputs are either ignored or intentionally cleaned.

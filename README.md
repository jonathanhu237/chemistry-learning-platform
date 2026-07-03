# SYSU Chemistry Legacy Learning Platform

This legacy branch keeps the old competition product line as the canonical runtime.

It contains:

- student web frontend in `apps/web-student`
- teacher/admin backoffice frontend in `apps/web-backoffice`
- shared FastAPI backend in `server`
- database migrations in `server/migrations`
- bootstrap/import/validation scripts in `scripts`
- protected seed data under `data/seed`

The legacy branch no longer ships standalone `web-admin`, current `web-teacher`, or current `web-student` frontend packages. Backoffice login uses normal username/password accounts; the canonical roles are `admin`, `teacher`, and `student`.

## Local Development

Install backend dependencies:

```powershell
python -m pip install -r requirements.txt
```

Use Node.js `^20.19.0 || >=22.12.0` for frontend workspaces.

Install frontend dependencies:

```powershell
Set-Location apps/web-student
npm install
Set-Location ../web-backoffice
npm install
```

Run the backend:

```powershell
python -m uvicorn server.app.app_runtime.main:app --host 127.0.0.1 --port 18000 --reload
```

Run the student frontend:

```powershell
Set-Location apps/web-student
npm run dev
```

Run the backoffice frontend:

```powershell
Set-Location apps/web-backoffice
npm run dev
```

The student dev server defaults to `http://127.0.0.1:5176/`, and the backoffice dev server defaults to `http://127.0.0.1:5177/`. Both proxy `/api` to the backend.

## Docker Compose

Copy the example environment:

```powershell
Copy-Item .env.example .env
```

Start the default legacy runtime:

```powershell
python scripts/deploy_compose_stack.py
```

The default Compose graph starts `postgres`, `backend`, `web-student`, and `web-backoffice`. It does not start the removed current-product frontend services and does not expose a standalone token-based operations console.

Default local endpoints:

- backend API: `http://127.0.0.1:18000`
- student frontend: `http://127.0.0.1:15176`
- backoffice frontend: `http://127.0.0.1:15177`

For routine development after the stack exists, rebuild only the service that owns your change:

```powershell
docker compose up -d --build backend
docker compose up -d --build web-student
docker compose up -d --build web-backoffice
```

## Bootstrap

Apply migrations:

```powershell
python scripts/apply_migrations.py
```

Create or update an admin/teacher account:

```powershell
python scripts/bootstrap_admin.py --username admin
```

Import formal data and canonical evidence when needed:

```powershell
python scripts/seed_formal_experiments.py
python scripts/publish_reviewed_curriculum.py
python scripts/import_canonical_evidence.py
python scripts/import_experiment_knowledge_framework.py --skip-migrations
python scripts/generate_experiment_catalog_seed.py
python scripts/validate_experiment_catalog_seed.py --write-report
python scripts/import_experiment_catalog_seed.py --skip-migrations
python scripts/rebuild_video_library_index.py --recreate
python scripts/verify_canonical_evidence.py
```

## Validation

Run focused frontend validation:

```powershell
Set-Location apps/web-student
npm run typecheck
npm test
npm run build
Set-Location ../web-backoffice
npm run typecheck
npm test
npm run build
```

Run backend tests:

```powershell
python -m pytest server/tests -q
```

Validate the active OpenSpec change:

```powershell
openspec validate trim-legacy-to-old-runtime --strict
```

Run the Compose smoke check when deployment wiring changes:

```powershell
python scripts/validate_compose_stack.py --build
```

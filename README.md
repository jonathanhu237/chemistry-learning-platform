# SYSU Chemistry Platform Console

This repository contains the standalone admin-management application and the student H5 login shell for the SYSU chemistry experiment learning platform.

It includes:

- React + Ant Design admin frontend in `apps/admin-web`
- React student H5 login frontend in `apps/student-web`
- FastAPI admin backend in `server`
- database migrations in `server/migrations`
- admin bootstrap/import scripts in `scripts`
- protected production seed data under `data/seed`

It intentionally excludes:

- WeChat/student mini-program source
- generated student app JSON bundles
- legacy courseware-derived demo chunks, guessed links, and generated placeholder question seeds
- raw PDF extraction inputs
- intermediate extraction output
- uploaded media files
- local logs, caches, dependency folders, and build output

## Local Development

Install backend dependencies:

```powershell
python -m pip install -r requirements.txt
```

Use Node.js `^20.19.0 || >=22.12.0` for the frontend workspaces. The repository includes `.nvmrc` for teams that use nvm-compatible tooling.

Install frontend dependencies:

```powershell
Set-Location apps/admin-web
npm install
Set-Location ../student-web
npm install
```

Run the admin backend:

```powershell
python -m uvicorn server.app.admin_main:app --host 127.0.0.1 --port 8000 --reload
```

Run the admin frontend:

```powershell
Set-Location apps/admin-web
npm run dev
```

Run the student H5 frontend:

```powershell
Set-Location apps/student-web
npm run dev
```

The student H5 runs at `http://127.0.0.1:5173/` and the admin frontend runs at `http://127.0.0.1:5174/admin/login`. Both proxy `/api` to the backend.

## Production-Style Local Run

Copy the example environment and build the frontend first:

```powershell
Copy-Item .env.example .env
```

```powershell
Set-Location apps/admin-web
npm ci
npm run build
Set-Location ../student-web
npm ci
npm run build
Set-Location ..\..
```

Then run the backend with the built student H5 mounted at `/` and the built admin frontend mounted at `/admin`:

```powershell
python -m uvicorn server.app.admin_main:app --host 0.0.0.0 --port 8000
```

For Docker Compose, copy `.env.example` to `.env`, adjust secrets and database settings, then run:

```powershell
docker compose up --build
```

See `docs/production-operations.md` for health checks, migration discipline, backup/restore, and restore-from-seed instructions.

## Bootstrap

Apply migrations:

```powershell
python scripts/apply_migrations.py
```

Create or update an admin user:

```powershell
python scripts/bootstrap_admin.py --username admin
```

Import formal admin data and canonical evidence when needed:

```powershell
python scripts/seed_formal_experiments.py
python scripts/publish_reviewed_curriculum.py
python scripts/import_canonical_evidence.py
python scripts/import_experiment_knowledge_framework.py --skip-migrations
python scripts/point_aware_question_bank.py import --bank-kind default --bank-status published --question-status published --skip-migrations
python scripts/import_manual_reviewed_point_evidence.py --skip-migrations
python scripts/verify_canonical_evidence.py
```

## Validation

Run the production-readiness validation chain:

```powershell
python scripts/validate_production_readiness.py --install-frontend
```

For backend/resource-only phases:

```powershell
python scripts/validate_production_readiness.py --skip-frontend
```

For focused frontend validation:

```powershell
Set-Location apps/admin-web
npm run typecheck
npm test
npm run build
Set-Location ../student-web
npm run typecheck
npm run build
```

The student H5 currently has no separate test script; its focused validation is typecheck plus build.

Validate OpenSpec:

```powershell
openspec validate production-hardening-iteration-two --strict
```

## GitHub Publishing

After the local repository has been created and committed, add the GitHub remote and push:

```powershell
git remote add origin <github-repo-url>
git push -u origin main
```

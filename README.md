# SYSU Chemistry Platform Console

This repository contains the standalone admin-management application and the student H5 login shell for the SYSU chemistry experiment learning platform.

It includes:

- React + Ant Design platform operations frontend in `apps/web-admin`
- React + Ant Design teacher console frontend in `apps/web-teacher`
- React student H5 frontend in `apps/web-student`
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
Set-Location apps/web-admin
npm install
Set-Location ../web-teacher
npm install
Set-Location ../web-student
npm install
```

Run the admin backend:

```powershell
python -m uvicorn server.app.app_runtime.main:app --host 127.0.0.1 --port 8000 --reload
```

Run the platform operations frontend:

```powershell
Set-Location apps/web-admin
npm run dev
```

Run the teacher console frontend:

```powershell
Set-Location apps/web-teacher
npm run dev
```

Run the student H5 frontend:

```powershell
Set-Location apps/web-student
npm run dev
```

The student H5 runs at `http://127.0.0.1:5173/`, the teacher console runs at `http://127.0.0.1:5174/login`, and the platform operations console runs at `http://127.0.0.1:5175/`. All three proxy `/api` to the backend.
The platform operations console uses the backend `WEB_ADMIN_ACCESS_TOKEN` value as its login token; it does not use an `app_users` username/password session.

## Production-Style Local Run

Copy the example environment:

```powershell
Copy-Item .env.example .env
```

For Docker Compose, adjust secrets and database settings, then deploy the default service graph:

```powershell
python scripts/deploy_compose_stack.py
```

The default Compose stack is the production-style application unit: Postgres, Elasticsearch with IK analysis, the FastAPI backend API, independent `web-student`, `web-teacher`, and `web-admin` frontend services, tusd uploads, and the local video worker. The optional RAG service is behind the `rag` profile.

For routine development after the stack already exists, rebuild only the service that owns your change:

```powershell
docker compose up -d --build backend
docker compose up -d --build web-teacher
docker compose up -d --build web-student
docker compose up -d --build web-admin
docker compose up -d --build video-worker
docker compose --profile rag up -d --build bge-rag
```

Do not clear Docker build cache or run no-cache/full-stack rebuilds as normal startup. Use cache prune only as an explicit recovery step for cache corruption or disk pressure.

See `docs/production-operations.md` for health checks, migration discipline, backup/restore, and restore-from-seed instructions. See `docs/catalog-tree-architecture.md` for the chapter catalog tree and point-node authoring model.

## Bootstrap

Apply migrations:

```powershell
python scripts/apply_migrations.py
```

Create or update a teacher-console account:

```powershell
python scripts/bootstrap_admin.py --username admin
```

Set the `web-admin` access token in configuration:

```powershell
$env:WEB_ADMIN_ACCESS_TOKEN = "<long-random-token>"
```

Import formal admin data and canonical evidence when needed:

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

Run the production-readiness validation chain:

```powershell
python scripts/validate_production_readiness.py --install-frontend
```

For a real Docker Compose application smoke check, including Postgres, Elasticsearch/IK, backend/frontend health, frontend API proxies, migrations, and video-library index readiness:

```powershell
python scripts/validate_production_readiness.py --run-compose-smoke --skip-frontend --skip-backend-tests
```

For backend/resource-only phases:

```powershell
python scripts/validate_production_readiness.py --skip-frontend
```

For focused frontend validation:

```powershell
Set-Location apps/web-admin
npm run typecheck
npm run build
Set-Location ../web-teacher
npm run typecheck
npm test
npm run build
Set-Location ../web-student
npm run typecheck
npm test
npm run build
```

Validate OpenSpec:

```powershell
openspec validate experiment-catalog-tree-point-architecture --strict
```

## GitHub Publishing

After the local repository has been created and committed, add the GitHub remote and push:

```powershell
git remote add origin <github-repo-url>
git push -u origin main
```

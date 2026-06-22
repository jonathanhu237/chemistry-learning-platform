# Historical Admin Repository Extraction Notes

This file is a historical note from the admin-only repository extraction phase. The current repository now includes the admin console, the student H5 login shell, production seed resources, and the production-readiness validation chain. Use `README.md` and `docs/production-operations.md` as the current operational references.

## Original Admin Console Snapshot

This repository originally described the standalone admin-management application for the SYSU chemistry experiment learning platform.

It includes:

- React + Ant Design platform operations frontend in `apps/web-admin`
- React + Ant Design teacher console frontend in `apps/web-teacher`
- React student H5 frontend in `apps/web-student`
- FastAPI admin backend in `server`
- database migrations in `server/migrations`
- admin bootstrap/import scripts in `scripts`
- seed and processed curriculum data needed for admin setup in `data/seed` and `data/processed`

It intentionally excludes:

- WeChat/student mini-program source
- generated student app JSON bundles
- raw PDF extraction inputs
- intermediate extraction output
- uploaded media files
- local logs, caches, dependency folders, and build output

## Local Development

Install backend dependencies:

```powershell
python -m pip install -r requirements.txt
```

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

The platform operations frontend runs at `http://127.0.0.1:5175/`, the teacher console runs at `http://127.0.0.1:5174/login`, the student H5 runs at `http://127.0.0.1:5173/`, and all three proxy `/api` to the backend in local development.
The platform operations frontend is opened with the configured `WEB_ADMIN_ACCESS_TOKEN`, not an `app_users` username/password login.

## Production-Style Local Run

For Docker Compose, copy `.env.example` to `.env`, adjust secrets and database settings, then run the whole application graph:

```powershell
python scripts/deploy_compose_stack.py
```

Compose builds and serves the `web-student`, `web-teacher`, and `web-admin` frontend images separately. The backend remains an API service and does not mount or serve frontend `dist` directories.

## Bootstrap

Apply migrations:

```powershell
python scripts/apply_migrations.py
```

Create or update a teacher-console account:

```powershell
python scripts/bootstrap_admin.py --username admin
```

Configure the platform operations token:

```powershell
$env:WEB_ADMIN_ACCESS_TOKEN = "<long-random-token>"
```

Import seed data when needed:

```powershell
python scripts/import_seed_to_postgres.py
python scripts/seed_formal_experiments.py
python scripts/publish_reviewed_curriculum.py
python scripts/generate_experiment_catalog_seed.py
python scripts/validate_experiment_catalog_seed.py --write-report
python scripts/import_experiment_catalog_seed.py --skip-migrations
```

## Validation

Validate backend import:

```powershell
python -c "import server.app.app_runtime.main as m; print(m.app.title)"
```

Validate the frontend:

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
npm run build
```

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

# Historical Admin Repository Extraction Notes

This file is a historical note from the admin-only repository extraction phase. The current repository now includes the admin console, the student H5 login shell, production seed resources, and the production-readiness validation chain. Use `README.md` and `docs/production-operations.md` as the current operational references.

## Original Admin Console Snapshot

This repository originally described the standalone admin-management application for the SYSU chemistry experiment learning platform.

It includes:

- React + Ant Design admin frontend in `apps/admin-web`
- React student H5 login frontend in `apps/student-web`
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

The admin frontend runs at `http://127.0.0.1:5174/admin/login`, the student H5 runs at `http://127.0.0.1:5173/`, and both proxy `/api` to the backend.

## Production-Style Local Run

Build both frontends first:

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

## Bootstrap

Apply migrations:

```powershell
python scripts/apply_migrations.py
```

Create or update an admin user:

```powershell
python scripts/bootstrap_admin.py --username admin
```

Import seed data when needed:

```powershell
python scripts/import_seed_to_postgres.py
python scripts/seed_formal_experiments.py
python scripts/publish_reviewed_curriculum.py
```

## Validation

Validate backend import:

```powershell
python -c "import server.app.admin_main as m; print(m.app.title)"
```

Validate the frontend:

```powershell
Set-Location apps/admin-web
npm run typecheck
npm test
npm run build
Set-Location ../student-web
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

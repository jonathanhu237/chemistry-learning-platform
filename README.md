# SYSU Chemistry Learning Platform

This repository contains one student H5 application, one teacher console, and their shared FastAPI backend.

## Product Surfaces

- `apps/web-student`: the canonical green mobile H5. Its five root tabs are Home, Learn, Atom, Assessment, and Profile.
- `apps/web-teacher`: the canonical Ant Design teacher console for textbooks, classes, catalog authoring, videos, questions, analytics, feedback, preview, and settings.
- `server`: FastAPI APIs, domain logic, PostgreSQL persistence, and workers.
- `server/migrations`: the ordered PostgreSQL migration chain.
- `scripts`: migrations, bootstrap, rebuild, validation, and deployment commands.
- `data/seed`: protected current resources used to restore and validate a blank deployment.

The student application is an H5 website, not a native WeChat Mini Program. Home keeps a finite experiment-video discovery feed with viewport-muted preview, focused search, explicit teacher recommendations, point navigation, and durable favorites. PostgreSQL owns this feed and its search; there is no separate student video-search Elasticsearch projection.

Elasticsearch remains in use for two distinct consumers:

- teacher catalog-authoring search; and
- the textbook RAG index used by Atom, question evidence, and teacher learning-assistant workflows.

Online textbook ingestion is managed from the teacher console. A PDF is uploaded, extracted natively or through configurable MinerU OCR, chunked, embedded, indexed, reviewed, and published. OCR, embedding, and rerank providers are administrator-configurable in the teacher settings; API keys must be supplied at runtime and must never be committed.

Assessment exposes one smart baseline/assembly path and an optional chapter → directory → point custom assessment with 1, 2, or 3 questions per point. The active two-stage pretest flow is retired; existing pretest reports remain readable as historical records.

## Local Development

Backend requirements:

```bash
python -m pip install -r requirements.txt
python scripts/apply_migrations.py
python -m uvicorn server.app.app_runtime.main:app --host 127.0.0.1 --port 8000 --reload
```

Use Node.js `^20.19.0 || >=22.12.0`. Install and start the two frontends in separate terminals:

```bash
cd apps/web-student
npm install
npm run dev
```

```bash
cd apps/web-teacher
npm install
npm run dev
```

Default development URLs:

- student H5: `http://127.0.0.1:5173/`
- teacher console: `http://127.0.0.1:5174/login`
- backend: `http://127.0.0.1:8000/health`

Both frontend development servers proxy `/api` to the backend.

## Production-Style Local Run

Copy the environment template, replace development credentials, and keep the resulting `.env` file out of Git:

```bash
cp .env.example .env
python scripts/deploy_compose_stack.py
```

The base Compose graph contains PostgreSQL, Elasticsearch/IK, the backend, the two canonical frontends, `tusd`, and `video-worker`. `textbook-ingestion-worker` is behind the optional `textbook-ingestion` profile; the deployment helper explicitly starts it so online textbook jobs are available in the production-style stack. The video worker starts without a GPU requirement and falls back to CPU transcoding. On an NVIDIA host, pass `--gpu` to `deploy_compose_stack.py` (or layer `docker-compose.gpu.yml` over the default file) to expose NVENC/NVDEC.

For routine changes, rebuild only the owning service:

```bash
docker compose up -d --build backend
docker compose up -d --build web-student
docker compose up -d --build web-teacher
docker compose up -d --build video-worker
docker compose up -d --build textbook-ingestion-worker
```

See `docs/production-operations.md` for deployment, health, backup, search, textbook-ingestion, and recovery procedures. See `docs/local_video_processing.md` for resumable upload and local video processing.

## Bootstrap

Restore the current protected seed baseline on a configured blank deployment:

```bash
python scripts/bootstrap_production_seed.py
```

Create or update the initial supervisor-teacher account separately when needed:

```bash
python scripts/bootstrap_admin.py --username admin
```

The internal `admin` role represents a supervisor teacher inside the teacher console. It is not a separate operations product. Every teacher can change their own password; only a supervisor teacher can list, create, reset, enable, or disable peer teacher accounts.

## Validation

Run the full production-readiness chain:

```bash
python scripts/validate_production_readiness.py --install-frontend
```

Run the Compose application smoke check when Docker prerequisites are available:

```bash
python scripts/validate_production_readiness.py --run-compose-smoke --skip-frontend --skip-backend-tests
```

Focused checks:

```bash
python scripts/validate_backend_architecture.py
python -m pytest server/tests -q
python scripts/validate_teacher_catalog_search.py

cd apps/web-student
npm run typecheck
npm test
npm run build
npm run qa:mobile

cd ../web-teacher
npm run validate:boundaries
npm run typecheck
npm test
npm run build
```

## GitHub Publishing

```bash
git remote add origin <github-repo-url>
git push -u origin main
```

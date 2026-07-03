# Production Operations Baseline

This document records the operational baseline for turning the admin platform into a maintainable production project. It does not change feature behavior; it defines how to validate, deploy, back up, restore, and extend the current system safely.

## Application Structure Standard

Whole-application structural changes are governed by `docs/application-engineering-structure.md` and the OpenSpec change `standardize-application-engineering-structure`.

The legacy branch application is treated as two frontend surfaces plus the backend and validation/service graph:

- student H5 frontend: `apps/web-student`
- backoffice frontend: `apps/web-teacher`
- backend service: `server/app`
- required Compose and validation scripts: `docker-compose.yml` and `scripts/`

Before moving files across these surfaces, or before splitting a major shell/API/domain owner, create or update an OpenSpec change that names the touched surfaces, owner map, validation gate, and rollback posture. Destructive refactors are allowed when git history, OpenSpec scope, and validation output make rollback clear; do not preserve obsolete wrappers only for old internal compatibility.

## Protected Resources

Current system data is protected under `data/seed` and validated by:

```powershell
python scripts/validate_production_resources.py
```

The manifest at `data/seed/manifests/core_resources.json` covers the formal experiment catalog, knowledge framework, current catalog tree/content/evidence seed, current catalog-node question-bank seed, canonical chunks, runtime search dictionaries including `chemistry_vocabulary.json`, ES/IK analyzer assets, student learning profiles, and the current manifest. Retired legacy point inventory, old question-bank seed files, old point-evidence bindings, generated reports, audit drafts, and local BGE embedding artifacts are intentionally outside the protected baseline.

Destructive cleanup must run only after this validation passes. The cleanup script intentionally excludes `data/media` because uploaded media requires a database/UI consistency plan.

## Migration Discipline

Historical migrations are append-only. Do not rename or renumber existing files, including the two historical `010_*.sql` files. They have already become part of the migration identity recorded in `schema_migrations`.

This productionization baseline now includes migrations through `041_collapse_teacher_student_roles.sql`. New migrations after this baseline must use the next unambiguous prefix:

```text
042_<short_description>.sql
043_<short_description>.sql
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
- `MAX_MEDIA_UPLOAD_MB` for the original video upload limit shown and enforced by the teacher video resource page
- `MAX_MEDIA_SUBTITLE_UPLOAD_MB` for external `.srt` / `.vtt` subtitle track uploads
- `VIDEO_DUPLICATE_DETECTION_COMMAND`, `VIDEO_DUPLICATE_DETECTION_COMPARE_COMMAND`, `VIDEO_DUPLICATE_DETECTION_ALGORITHM`, and `VIDEO_DUPLICATE_DETECTION_THRESHOLD` for worker duplicate checks
- `VIDEO_DUPLICATE_DEFAULT_INTERVAL_SECONDS=3`, `VIDEO_DUPLICATE_MIN_SAMPLES=12`, and `VIDEO_DUPLICATE_MIN_INTERVAL_SECONDS=0.5` for the duplicate-focused vPDQ sampling defaults
- `VIDEO_DUPLICATE_DURATION_TOLERANCE_RATIO=0.001`, `VIDEO_DUPLICATE_DURATION_TOLERANCE_FLOOR_SECONDS=0.5`, and `VIDEO_DUPLICATE_DURATION_TOLERANCE_CEILING_SECONDS=2.0` for near-equal duration gating
- `API_PUBLIC_BASE_URL`
- `FRONTEND_ALLOWED_ORIGINS`
- `STUDENT_PREVIEW_APP_BASE_URL` pointing to the student H5 origin used inside backoffice preview if it differs from the default student service origin
- `STUDENT_PREVIEW_ALLOWED_ORIGINS` listing the student H5 origins allowed to exchange preview tickets
- `STUDENT_PREVIEW_TICKET_EXPIRE_MINUTES` and `STUDENT_PREVIEW_SESSION_EXPIRE_MINUTES` for bootstrap ticket and preview student session lifetimes
- `AUTH_SECRET_KEY` with a long random value
- `AGENT_LLM_PROVIDER=disabled` when no LLM provider is configured, or provider credentials/model when enabled
- `VIDEO_LIBRARY_SEARCH_ENABLED=true` for the student H5 experiment video library search entry
- `VIDEO_LIBRARY_SEARCH_BACKEND=elasticsearch`; production video-library search requires Elasticsearch with IK analysis
- `VIDEO_LIBRARY_SEARCH_URL`, `VIDEO_LIBRARY_SEARCH_INDEX`, `VIDEO_LIBRARY_SEARCH_ANALYZER`, and `VIDEO_LIBRARY_SEARCH_TIMEOUT_SECONDS`
- `VIDEO_LIBRARY_SEARCH_BOOTSTRAP_INDEX=true` when the backend or rebuild command should create the index mapping
- `VIDEO_LIBRARY_SEARCH_LOCAL_FALLBACK=false` in production; local fallback is only for explicit local or test runs
- `VIDEO_LIBRARY_SEARCH_REQUIRE_ES_IN_PRODUCTION=true` so startup/readiness fails when ES/IK is missing
- `TEACHER_CATALOG_SEARCH_ENABLED=true` for teacher catalog authoring search
- `TEACHER_CATALOG_SEARCH_BACKEND=elasticsearch`, `TEACHER_CATALOG_SEARCH_URL`, `TEACHER_CATALOG_SEARCH_INDEX=teacher-catalog-admin-search`, `TEACHER_CATALOG_SEARCH_ANALYZER`, and `TEACHER_CATALOG_SEARCH_TIMEOUT_SECONDS`
- `TEACHER_CATALOG_SEARCH_LOCAL_FALLBACK=true` is acceptable for local authoring, but production operations should monitor fallback metadata because teacher synonyms and formula routes require ES

Do not commit real `.env` files or secrets.

## Docker Expectations

Compose owns the production-like application graph. Build and start all required default services together:

```powershell
python scripts/deploy_compose_stack.py
```

The deploy script runs `docker compose up -d --build --remove-orphans` for the canonical default services, then performs the Compose smoke validation. This intentionally removes obsolete service containers such as historical current-product or `*-old` frontend services.

For routine development after the stack already exists, rebuild and recreate only the service that owns the changed code or configuration:

```powershell
docker compose up -d --build backend
docker compose up -d --build web-student
docker compose up -d --build web-teacher
```

Reserve full-stack image rebuilds for initial setup, shared base-image or Compose-topology changes, multi-service dependency changes, release smoke checks, or explicitly requested full validation. Do not run `docker builder prune`, `docker buildx prune`, `docker system prune`, or no-cache rebuilds as routine development startup; use them only as documented recovery for cache corruption or disk pressure after service-scoped restart or rebuild has been tried.

Default Compose services:

- `postgres`: pgvector Postgres with `pg_isready` health check.
- `backend`: FastAPI API service. It serves `/health` and `/api/*` only.
- `web-student`: student frontend service at `http://127.0.0.1:15176`, serving SPA routes from its own nginx runtime and proxying `/api/*` to `backend:8000`.
- `web-teacher`: backoffice frontend service at `http://127.0.0.1:15177`, serving management routes from its own nginx runtime and proxying `/api/*` to `backend:8000`.

The backend depends on the PostgreSQL health check. The frontend services depend on backend health. The legacy default Compose stack does not start Elasticsearch; student video-library search uses local fallback unless a deployment explicitly adds an Elasticsearch service and enables it.

### Video-worker FFmpeg Archive Cache

The `video-worker` image installs static `ffmpeg` and `ffprobe` binaries during Docker build. By default the Dockerfile can download the pinned archive from GitHub, but deployment environments do not have to rely on build-time GitHub reachability.

For reproducible or network-restricted deployments, download the pinned archive on the host and place it in:

```text
server/vendor/ffmpeg/ffmpeg-N-125136-gb57ff00bcf-linux64-gpl.tar.xz
```

Expected SHA-256:

```text
e73c0658d2b778e92d5367d3b47368c86f1589ae93764ea74cdca9e213fbba59
```

Then build normally:

```powershell
docker compose build video-worker
docker compose up -d video-worker
```

The Dockerfile copies `server/vendor/ffmpeg/` into the `ffmpeg` build stage, verifies `FFMPEG_SHA256`, and only falls back to `FFMPEG_URL` when no local `*.tar.xz` archive exists. If multiple archives are present, select one explicitly:

```powershell
docker compose build --build-arg FFMPEG_LOCAL_ARCHIVE=ffmpeg-N-125136-gb57ff00bcf-linux64-gpl.tar.xz video-worker
```

See `docs/local_video_processing.md` for the video pipeline, NVENC probe, and CPU fallback details.

### Video Subtitle Operations

Generated student playback videos intentionally do not carry subtitles. The worker strips embedded subtitle, attachment, and data streams from the generated MP4; operators should not expect MKV/MP4 embedded subtitles to appear on the student side automatically.

Teachers attach external subtitle tracks to video assets. First-pass supported inputs are `.srt` and `.vtt`; the backend normalizes served tracks to WebVTT and enforces `MAX_MEDIA_SUBTITLE_UPLOAD_MB`. `.ass` and `.ssa` are rejected unless a future change adds a styled-subtitle renderer or an explicit burn-in workflow.

Student and teacher preview players load subtitles through browser-native `<track>` elements. Because `<track>` cannot send custom authorization headers, subtitle stream URLs must stay compatible with existing cookie/session auth or token query parameters, and must return `text/vtt; charset=utf-8`. Keep `API_PUBLIC_BASE_URL`, frontend origins, preview-token settings, and CORS policy aligned when deploying student and teacher frontends on different origins.

The Compose Postgres service is available to other containers as `postgres:5432`. Its host binding defaults to `127.0.0.1:15432` to avoid collisions with a developer's local Postgres. Host-side scripts and validation defaults should use `postgresql+psycopg://chemistry:chemistry@127.0.0.1:15432/chemistry_exam`. Override `POSTGRES_HOST_PORT` only when the host port is known to be free.

Frontend host bindings default to `127.0.0.1:15176` for `web-student` and `127.0.0.1:15177` for `web-teacher`. Override `WEB_STUDENT_HOST_PORT` or `WEB_TEACHER_HOST_PORT` only when the host port is already occupied. Rollback for this topology uses git or deployment rollback; do not restore backend SPA fallbacks as a compatibility layer.

Backoffice student-device preview loads the real `web-student` app in an iframe owned by `web-teacher`. In production-like deployments, keep `STUDENT_PREVIEW_APP_BASE_URL`, `STUDENT_PREVIEW_ALLOWED_ORIGINS`, and the student frontend `frame-ancestors` policy aligned so only the expected backoffice origin can embed the student app.

## Student Video-Library Search Operations

Student video-library search is a PostgreSQL-to-Elasticsearch projection. PostgreSQL catalog point tables are the fact source:

- `experiment_catalog_points`: canonical experiment point identity shared by one or more catalog point placements
- `experiment_catalog_nodes`: stable chapter catalog hierarchy, directory category/card metadata, and point-placement `node_id` values targeting `canonical_point_id`
- `experiment_catalog_point_content`: teacher-authored point title, teacher-only note, principle, phenomenon explanation, safety note, and publication audit keyed by canonical point identity with placement context
- `experiment_catalog_point_related_links`: manual related point links and hidden default overrides stored by canonical source/target point identity with placement display resolution
- `experiment_catalog_point_media_bindings`: video bindings keyed by canonical point identity with source placement context
- `experiment_catalog_point_search_index_state`: retryable desired search actions and sync status for placement documents

Elasticsearch stores derived published placement documents only. Directory nodes contribute ancestor category text to descendant point documents but never become standalone results. A canonical experiment with multiple published placements produces multiple ES documents that share `canonical_point_id` and differ by `placement_node_id`, chapter, and path. Teacher-only notes, raw media-library uploads that are not bound to published points, video resource titles, media asset titles, original file names, media ids, playback paths, thumbnail paths, upload/processing status, `source_chunks`, and `experiment_video_point_evidence` must stay out of the student video-library index. The only allowed media-derived readiness signals are `has_video` and `video_count`, where `video_count` is a 0/1 readiness flag because one video point has one current video resource. Do not edit ES documents by hand and do not treat ES hit sources as student page content.

The current catalog seed comes from `data/seed/experiment_catalog/catalog_tree.json`: 569 visible catalog nodes, 176 directory nodes, 393 point placements, and 357 canonical experiment points. Chapter 21 has no seeded catalog content. Reviewed exact duplicate leaves such as `Na2SiO3 + CO2`, `Al2(SO4)3 + NH3·H2O + NaOH`, and `BeSO4 + NH3·H2O + NaOH` are represented as multiple placements targeting one canonical point. The corrected sibling points `NaClO + MnSO₄` and `NaClO + 品红溶液` remain distinct canonical points. The current point-content seed imports 76 reviewed records for catalog point placements and canonical points, including 71 equation-mode records and 122 structured reaction-equation rows.

Catalog authoring only binds existing media assets to canonical experiment points through the selected placement. New uploads are owned by the media library workflow and then selected from the catalog editor after processing.

Bootstrap or destructively rebuild the search index from PostgreSQL:

```powershell
python scripts/rebuild_video_library_index.py --recreate
```

This recreates the index with the current pure mapping and refuses to write generated documents that contain forbidden video-resource fields. Use this after deploying code that changes index shape, after clearing stale ES data, or after any migration that changes point readiness semantics.

Preview the document count without writing to ES:

```powershell
python scripts/rebuild_video_library_index.py --dry-run
```

Validate ES/IK readiness in production mode:

```powershell
python scripts/validate_video_library_search.py
```

The validator checks the mapping version, generated document purity, and indexed `_source` purity. A production readiness run must fail if stale ES documents still contain video resource labels or metadata.

Inspect admin-facing index state through the backend:

```powershell
Invoke-RestMethod http://localhost:8000/api/teacher/video-library/index/diagnostics -Headers @{ Authorization = "Bearer <token>" }
```

The chemistry search seed files live under `data/seed/search/`:

- `chemical_aliases.json`: formula and common-name aliases such as HCl/salt acid and Na2S2O3/sodium thiosulfate
- `chemical_stopwords.txt`: high-frequency workflow words that should carry less search meaning

Admin point content edits write PostgreSQL first. Saving drafts queues a delete from search; publishing queues an upsert; unpublishing, archiving, video binding changes, or media asset archival queue the affected point for refresh. A failed ES write must leave the PostgreSQL content intact and visible in `experiment_catalog_point_search_index_state` for retry or full rebuild.

## Teacher Catalog Search Operations

Teacher catalog search is a separate PostgreSQL-to-Elasticsearch projection from the student video-library index. It indexes active directory nodes and point placements for teacher/admin authoring, including draft and unpublished nodes, teacher notes, legacy identifiers, status facets, path context, reaction equations, chemistry aliases, and formula routes. It must not share the `VIDEO_LIBRARY_SEARCH_INDEX` value or write teacher documents into `student-video-library`.

One catalog fact can enqueue independent projection work:

- student search job: `es_upsert` / `es_delete`, visible in `experiment_catalog_point_search_index_state`, limited to published student-visible point placement documents
- teacher search job: `teacher_search_upsert` / `teacher_search_delete`, visible in `experiment_catalog_teacher_search_index_state`, covering active teacher-visible directory and point documents

Failures are separate. A failed teacher search projection does not mark the student video-library projection failed, and a failed student projection should not hide teacher search if the teacher index is healthy.

Rebuild or inspect the teacher search index:

```powershell
python scripts/rebuild_teacher_catalog_search_index.py --recreate
python scripts/rebuild_teacher_catalog_search_index.py --dry-run
python scripts/rebuild_teacher_catalog_search_index.py --diagnostics
python scripts/validate_teacher_catalog_search.py
```

The admin catalog search endpoint returns metadata in each response indicating whether `elasticsearch` or `postgres_fallback` answered the query. Fallback responses are intentionally limited and should not be described as synonym or formula-aware search.

External textbook RAG:

Textbook RAG is configured through `TEXTBOOK_RAG_*` environment variables or the teacher AI settings page. It uses the configured Elasticsearch index plus external OpenAI-compatible embedding and rerank providers. There is no local `bge-rag` Compose profile, model mount, or port `8010` health check.

## Media Lifecycle Operations

`data/media` is operational upload state, not protected seed data. It can be backed up, archived, or cleaned only with database consistency in mind because `media_assets`, catalog point video bindings, legacy `media_bindings`, processing jobs, and review rows may still reference local files.

Teacher deletion in `/videos` is destructive resource deletion, not archive retention. The backend first makes the asset unavailable with `lifecycle_status='tombstoned'`, cancels queued/running media processing jobs, removes point video bindings while leaving point content, equations, related links, questions, assessments, and publication state intact, removes subtitle track records/artifacts, removes duplicate-candidate references, and then deletes source/playback/thumbnail/rendition/subtitle/fingerprint/temp artifacts under `MEDIA_ROOT` with path containment checks. If physical cleanup partially fails, the asset remains unavailable and stores cleanup diagnostics for maintenance.

Deleting only a subtitle track is a separate, narrow operation. It removes that track's source/WebVTT artifacts and metadata, but does not delete or archive the media asset, student playback file, point bindings, duplicate fingerprints, or thumbnail.

Inspect the current media lifecycle state with a dry run:

```powershell
python scripts/media_lifecycle_cleanup.py --json --limit 500 --orphan-limit 200
```

The script reports asset dependency counts, missing files, existing referenced files, and unreferenced orphan files. Database-backed maintenance file deletion is allowed only for archived or tombstoned asset rows:

```powershell
python scripts/media_lifecycle_cleanup.py --delete-asset-files
```

If an active asset still references files, the command reports `refused_active_asset_file_asset_ids` and does not delete those files.

Only unreferenced orphan files under `MEDIA_ROOT` may be removed directly:

```powershell
python scripts/media_lifecycle_cleanup.py --delete-orphans --limit 500 --orphan-limit 200
```

Before manual media cleanup in production, back up any media that should remain available, delete teacher resources through the `/videos` delete flow or deliberately tombstone old archived assets, confirm affected point bindings no longer point at deleted media, and confirm the admin UI shows unavailable or missing files intentionally instead of broken playback links. See `docs/production-media-cleanup.md` for the detailed cleanup procedure.

## One-Command Validation

Run the full local validation chain with frontend dependency installation:

```powershell
python scripts/validate_production_readiness.py --install-frontend
```

The command checks protected resources, video-library readiness, experiment point identity validation, OpenSpec strict validation, backend import smoke, backend tests, `web-teacher` typecheck/tests/build, and `web-student` typecheck/tests/build.
The default OpenSpec target is `trim-legacy-to-old-runtime`; use `--change <name>` to validate a different active or historical change.
The backend stage also runs:

```powershell
python scripts/validate_backend_architecture.py
```

This validates slim import boundaries, deleted compatibility paths, and the canonical route inventory.

For backend/resource-only environments:

```powershell
python scripts/validate_production_readiness.py --skip-frontend
```

Skipping frontend validation is acceptable only for a scoped backend/resource phase. A production release gate should run the full command.

Run the real Docker Compose application smoke check when deployment wiring changes or when a change makes a service required:

```powershell
python scripts/validate_production_readiness.py --run-compose-smoke --skip-frontend --skip-backend-tests
```

This starts or verifies the required default Compose services, verifies backend and frontend health, verifies both frontend `/api/*` proxies, verifies PostgreSQL reachability, and applies migrations.

To also rebuild images as part of the smoke check, run the lower-level command explicitly:

```powershell
python scripts/validate_compose_stack.py --build
```

Browser E2E smoke is opt-in because it runs a real browser against the Compose backend, `web-student`, and `web-teacher` services:

```powershell
python scripts/validate_legacy_e2e.py --build
```

The script discovers the actual Compose host ports, imports the production seed baseline with external Elasticsearch import skipped, and runs Playwright through `e2e/`. Use `--skip-seed-bootstrap` only when the target database is already seeded and you want a faster local rerun. Defaults are:

- teacher account: `teacher / 123456`
- student account: `26320001 / 123456`
- browser project: Playwright Chromium, or `PLAYWRIGHT_BROWSER_CHANNEL=chrome` to use local Chrome

It covers the student login plus learning/video/assessment/report journeys, the teacher login plus canonical workbench pages, and API boundaries proving student tokens cannot access `/api/teacher/*`, teacher tokens cannot access `/api/student/*`, and retired `/api/admin/*` and `/api/web-admin/*` routes are not available.

To run the same check through the validation chain:

```powershell
python scripts/validate_production_readiness.py --run-e2e
```

## Local Smoke Tests

After rebuilding the backend, verify the runtime before handoff:

```powershell
docker compose up -d --build backend
Invoke-RestMethod http://localhost:8000/health
```

For textbook RAG readiness, check `/api/teacher/learning-assistant/runtime` or the teacher AI settings page. Healthy status requires the external Elasticsearch index, embedding provider, rerank provider, and index metadata to match the configured model and dimension.

Run representative authenticated API checks:

```powershell
# Log in with a local-only teacher account, then reuse the bearer token.
Invoke-RestMethod http://localhost:8000/api/teacher/media/assets?limit=3 -Headers @{ Authorization = "Bearer <token>" }
Invoke-RestMethod http://localhost:8000/api/teacher/learning-assistant/ask -Method Post -Headers @{ Authorization = "Bearer <token>" } -ContentType "application/json" -Body '{"question":"Explain a representative experiment point.","allow_rag_lookup":false}'
```

## Local Smoke Teacher Account

Temporary teacher accounts created for smoke testing, such as `codex_smoke_teacher`, are local-only developer database state. They are not seed data, are not protected resources, and must not be shipped or documented with shared passwords.

Production environments should create named teacher accounts through the deployment bootstrap or identity-management process, then rotate or remove any smoke-only credentials before real users are admitted. For local test databases, recreate a smoke teacher with `scripts/bootstrap_teacher.py` and a local password manager entry when needed.

## Restore From Declared Resources

For a fresh database with declared seed resources available:

```powershell
python scripts/apply_migrations.py
python scripts/publish_reviewed_curriculum.py
python scripts/seed_formal_experiments.py --skip-migrations
python scripts/import_canonical_evidence.py --skip-migrations
python scripts/import_experiment_knowledge_framework.py --skip-migrations
python scripts/generate_experiment_catalog_seed.py
python scripts/validate_experiment_catalog_seed.py --write-report
python scripts/import_experiment_catalog_seed.py --skip-migrations
python scripts/seed_catalog_point_evidence.py import
python scripts/seed_current_question_bank.py import --skip-migrations
python scripts/rebuild_video_library_index.py --recreate
python scripts/validate_production_resources.py
python scripts/seed_current_question_bank.py validate
python scripts/validate_experiment_points.py
```

Expected protected baseline counts:

- 77 formal experiments
- 11 chapters, 133 units, 385 knowledge points
- 569 catalog nodes: 176 directories and 393 point placements
- 357 canonical experiment points
- 76 published catalog point-content seed records
- 54 published generated question banks and 1,965 published questions
- 3637 canonical source chunks
- 0 legacy point evidence bindings

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

If the ES volume is corrupted or intentionally cleared, keep PostgreSQL and protected seed data intact, recreate the index, and run the rebuild command. Do not delete `source_documents`, `source_chunks`, or `data/seed/canonical_rag/chunks/**`; those canonical corpus resources remain valid. Old `experiment_video_point_evidence` rows and old `data/seed/point_evidence/**` files are retired point-to-chunk bindings and must not be treated as current AI/question-bank evidence.

Catalog point ES sync and catalog-node evidence refresh use PostgreSQL-backed jobs in `experiment_catalog_point_jobs`. `experiment_catalog_point_search_index_state` is the ES projection status; `experiment_catalog_point_evidence_state` and `experiment_catalog_point_evidence_bindings` are the fallback/static evidence status and selected chunk bindings. These job tables may be retried with catalog-node awareness, but default catalog seed import must preserve current question banks, questions, catalog-node evidence state/bindings, media bindings, source documents, source chunks, search dictionaries, and the authoritative catalog seed. Redis/Rabbit/Celery/RQ should be introduced only after throughput or distributed scheduling requirements justify changing the worker backend.

## Search Rollback Notes

If the point editor or search projection must be rolled back during a release:

- Disable or hide the admin catalog point editor at the frontend/API routing layer while keeping catalog point tables in place.
- Set `VIDEO_LIBRARY_SEARCH_ENABLED=false` only as an emergency product rollback; production readiness should fail until ES/IK search is restored for normal releases.
- Clear or recreate the ES index with `python scripts/rebuild_video_library_index.py --recreate` after the issue is fixed.
- Never roll back by deleting canonical chunks or source documents; those are protected corpus resources, not search projection cache. Local BGE embeddings and legacy manual-reviewed point evidence are retired and should not be restored as current point evidence.

Local developers may set `VIDEO_LIBRARY_SEARCH_BACKEND=local` and `VIDEO_LIBRARY_SEARCH_LOCAL_FALLBACK=true` only for isolated fallback tests. Production-like development should run `docker compose up elasticsearch backend` and use the same ES/IK projection path as production.

## Release Gate

Before declaring a phase production-ready, run:

```powershell
python scripts/validate_production_readiness.py --install-frontend
openspec validate catalog-point-ai-platform-roadmap --strict
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
- teacher app import smoke

If an environment-specific phase needs to skip a stage locally, use the explicit script flags such as `--skip-frontend`, `--skip-backend-tests`, `--skip-openspec`, or `--skip-resource-validation`. Use `--run-e2e` when validating the interactive Compose runtime. Production release gates should run the full chain and may add `--run-e2e` when browser infrastructure is available.

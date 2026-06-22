# Implementation Notes

## Baseline Captured

- FastAPI app imports from `server.app.app_runtime.main:app`.
- Route table after canonical cleanup has 132 entries, including static mounts for `/admin/assets` and `/assets`.
- Removed legacy media binding aliases:
  - `POST /api/admin/media/bindings/{binding_id}/delete`
  - `POST /api/admin/media/bindings/{binding_id}/archive`
- Canonical route inventory lives at `server/tests/contracts/backend_route_inventory.json`.

## Backend Ownership Changes

- Runtime moved to `server/app/app_runtime/main.py`.
- Auth routes moved to `server/app/api/auth/routes.py`.
- Admin routers moved to `server/app/api/admin/`.
- Student routers moved to `server/app/api/student/`.
- Settings and database moved to `server/app/infrastructure/`.
- Video worker moved to `server/app/workers/video_worker.py`.
- Media ownership split into `domains/media/assets.py`, `bindings.py`, `processing_queue.py`, `lifecycle.py`, `files.py`, and `visibility.py`.
- Experiment point ownership split into `domains/experiment_points/canonical_points.py`, `learning_content.py`, `related_links.py`, `workspace.py`, `student_detail.py`, and `index_events.py`.
- Student video-library search, document building, ES index management, and sync state live under `domains/video_library/`.
- Student learning read models live under `domains/student_learning/`.
- Assistant/RAG runtime, policy, retrieval, output normalization, evidence shaping, and student assistant behavior live under `domains/assistant/`.
- Question bank, point-aware suggestions, generation, drafts, and workbench behavior live under `domains/questions/`.
- Pretest, posttest, student experiment attempts, and mastery updates live under `domains/assessments/`.
- Roster/class logic lives in `domains/roster/classes.py`.
- Analytics read models live in `domains/analytics/read_models.py`.
- Feedback administration lives in `domains/feedback/admin_feedback.py`.
- Platform settings and AI configuration live in `domains/platform/settings.py`.
- Formal experiment catalog and learning resources live under `domains/catalog/`.
- Domain errors live in `domains/errors.py`; API/runtime translates them through `api/error_translation.py`.

No compatibility wrappers were kept for deleted old paths.

## Search, Media, And Worker Boundaries

- Teacher media asset uploads remain generic media library records.
- Student video-library documents are point-centered projections from published point content and student-visible media state.
- Media binding create/publish/unpublish/delete queues point search projection state through `domains.experiment_points.index_events`.
- Video worker imports only worker-safe media file, processing queue, and infrastructure code.
- Video worker does not receive media binding or student search projection notifications.
- Worker job claiming, phase updates, failure/completion handling, legacy backfill enqueue, and processing-result persistence live in `domains/media/processing_queue.py`.
- Candidate point key generation and canonical point reference validation live in `domains/experiment_points/canonical_points.py`.
- Maintenance scripts that need point identity now import the canonical point owner.

## Domain Boundary Status

- `server/app/services/` has been deleted.
- Canonical imports now target `domains/*`, `api/*`, `infrastructure/*`, or `workers/*`.
- Reusable domain modules do not import FastAPI, Starlette responses, API routers, auth dependencies, app runtime, old routers, old services, or worker entrypoints.
- Domain tests that exercise validation errors assert `DomainHTTPException` instead of FastAPI `HTTPException`.
- API/runtime owns HTTP response translation for domain errors.
- File and CSV response objects are created in API modules from domain payloads.

## Frontend Audit Only

Admin frontend oversized modules:

- `LearningAssistantPage.tsx` 60 KB
- `ExperimentsPage.tsx` 57 KB
- `VideoResourcesPage.tsx` 54 KB
- `QuestionBanksPage.tsx` 53 KB
- `LearningResourcesPage.tsx` 39 KB
- `AnalyticsPage.tsx` 31 KB
- `ClassesPage.tsx` 29 KB
- `apps/admin-web/src/api/index.ts` 37 KB remains monolithic.

Recommended follow-up: split admin API by feature owner, then split each oversized page into route shell, API hooks, command dialogs, table/list read models, and feature tests. Verification gate: admin typecheck, feature tests, build, and e2e smoke.

Student H5 oversized modules:

- `AtomViewerZdog.tsx` 35 KB
- `StudentAiChatPanel.tsx` 33 KB
- `App.e2e.test.tsx` 29 KB
- `apps/student-web/src/api.ts` 24 KB
- `periodic.ts` 18 KB
- `VideoLibraryPage.tsx` 11 KB

Recommended follow-up: split student API by route domain, split atom viewer and assistant into feature owners, and keep route-stack navigation tests as the safety gate. Verification gate: student typecheck, tests, build, mobile viewport QA.

Frontend code edits in this backend slim pass were limited to endpoint/test compatibility from route canonicalization work and are not a frontend architecture rewrite.

## Validation Run During Implementation

Passing checks observed during implementation:

```powershell
python scripts/validate_backend_architecture.py
python -m pytest server/tests -q
python scripts/validate_production_readiness.py --skip-frontend --skip-resource-validation
python scripts/validate_compose_stack.py --skip-up --skip-index-rebuild
docker compose exec -T backend python scripts/rebuild_video_library_index.py --dry-run
docker compose exec -T backend python scripts/rebuild_video_library_index.py --recreate
docker compose exec -T -e CHEMISTRY_APP_ENV=production -e VIDEO_LIBRARY_SEARCH_LOCAL_FALLBACK=false -e VIDEO_LIBRARY_SEARCH_REQUIRE_ES_IN_PRODUCTION=true backend python scripts/validate_video_library_search.py
python scripts/validate_production_resources.py
docker compose exec -T backend python scripts/validate_experiment_points.py
docker compose exec -T backend python scripts/media_lifecycle_cleanup.py --json --limit 5 --orphan-limit 5
openspec validate backend-slim-domain-architecture --strict
git diff --check
python -c "from server.app.app_runtime.main import app; print(len(app.routes))"
```

Observed route count: `132`.

Observed backend tests: `183 passed`.

Observed Compose state after rebuild: backend healthy, Elasticsearch healthy, Postgres healthy, tusd running, video-worker running.

Observed ES rebuild result in the current local database: `indexed: 0, failed: 0`; the local database currently has no published point documents to project, but index creation and readiness validation passed.

Observed production resource manifest validation: `ok: true`, `resource_count: 21`.

Observed experiment point validation: `ok: true`, `point_count: 300`, `published_content_count: 0`.

Observed media cleanup dry-run: completed with current local media state and no deletion performed.

Admin frontend endpoint audit found no calls to the removed media binding aliases. Current admin code uses `DELETE /api/admin/media/bindings/{binding_id}`, so no extra frontend validation was required by this backend-only alias cleanup.

## Residual Risks

- Admin and student frontend structural cleanup is intentionally deferred by this change.
- Full frontend validation should run before a production release because this change is backend-focused.

# Backend Slim Architecture

This document is the backend owner map after `backend-slim-domain-architecture`.

## Package Shape

```text
server/app/
  app_runtime/          FastAPI construction, middleware, health, SPA/static mounts
  api/
    auth/               auth HTTP routes
    admin/              teacher/admin HTTP routes
    student/            student H5 HTTP routes
  domains/
    media/              media assets, bindings, file helpers, lifecycle, visibility, processing queue
    experiment_points/  canonical points, learning content, related links, workspace/detail read models, search events
    student_learning/   student learning pages and shared read-model inputs
    video_library/      point-centered search documents, search adapters, ES index client
    assistant/          assistant policy, retrieval, runtime, output normalization, evidence shaping
    questions/          question bank, drafts, generation, point-aware suggestions, workbench
    assessments/        pretest, posttest, student attempts, mastery updates
    roster/             classes and roster management
    analytics/          class/student analytics read models
    feedback/           feedback administration
    platform/           platform settings and AI configuration
    catalog/            formal experiments and learning resources
  infrastructure/       settings, database, migration-facing helpers
  workers/              process entrypoints such as video processing
  scripts_support/      reserved for CLI-only support code
```

## Dependency Rules

Allowed directions:

- `app_runtime -> api -> domains -> infrastructure`
- `workers -> domains -> infrastructure`
- `scripts -> domains/infrastructure/scripts_support`

Forbidden directions enforced by `python scripts/validate_backend_architecture.py`:

- `domains/*` must not import FastAPI, Starlette responses, `server.app.api`, `server.app.auth`, `server.app.routers`, `server.app.app_runtime`, `server.app.services`, or `server.app.workers`.
- `workers/*` must not import FastAPI, Starlette responses, API routers, app runtime, or broad `server.app.services`.
- `api/*` must not import worker entrypoints.
- Deleted legacy paths must not return as wrappers.

## Canonical Entrypoints

- FastAPI runtime: `server.app.app_runtime.main:app`
- Video worker: `python -m server.app.workers.video_worker`
- Architecture validation: `python scripts/validate_backend_architecture.py`
- Route inventory: `server/tests/contracts/backend_route_inventory.json`

## Route Inventory

The canonical inventory currently contains 132 entries:

- runtime/static/docs/health: 13
- auth API: 6
- admin API: 95
- student API: 18

Removed aliases:

- `POST /api/admin/media/bindings/{binding_id}/delete` -> use `DELETE /api/admin/media/bindings/{binding_id}`
- `POST /api/admin/media/bindings/{binding_id}/archive` -> use `DELETE /api/admin/media/bindings/{binding_id}`

## Domain Owner Map

- Media assets: `server/app/domains/media/assets.py`
- Media bindings and point-search event emission: `server/app/domains/media/bindings.py`
- Media processing queue and worker-safe job persistence: `server/app/domains/media/processing_queue.py`
- Media lifecycle cleanup: `server/app/domains/media/lifecycle.py`
- Media file helpers: `server/app/domains/media/files.py`
- Media visibility: `server/app/domains/media/visibility.py`
- Experiment point identity and reference validation: `server/app/domains/experiment_points/canonical_points.py`
- Experiment point learning content commands: `server/app/domains/experiment_points/learning_content.py`
- Experiment point related links: `server/app/domains/experiment_points/related_links.py`
- Experiment point admin workspace: `server/app/domains/experiment_points/workspace.py`
- Experiment point student detail payload: `server/app/domains/experiment_points/student_detail.py`
- Experiment point search events: `server/app/domains/experiment_points/index_events.py`
- Student learning pages and media payloads: `server/app/domains/student_learning/point_detail.py`
- Student learning shared read model: `server/app/domains/student_learning/read_models.py`
- Student video-library search: `server/app/domains/video_library/search.py`
- Student video-library ES index client/sync state: `server/app/domains/video_library/index_client.py`
- Experiment catalog tree structure: `server/app/domains/catalog_tree/nodes.py`
- Experiment catalog directory/card semantics: `server/app/domains/catalog_tree/directories.py`
- Experiment catalog point content: `server/app/domains/catalog_tree/points.py`
- Experiment catalog media bindings: `server/app/domains/catalog_tree/media_bindings.py`
- Experiment catalog related links: `server/app/domains/catalog_tree/related_links.py`
- Experiment catalog search documents: `server/app/domains/catalog_tree/search_documents.py`
- Experiment catalog student read models and files: `server/app/domains/catalog_tree/student_read_models.py`, `server/app/domains/catalog_tree/files.py`
- Assistant/RAG: `server/app/domains/assistant/`
- Questions: `server/app/domains/questions/`
- Assessments: `server/app/domains/assessments/`
- Roster/classes: `server/app/domains/roster/classes.py`
- Analytics: `server/app/domains/analytics/read_models.py`
- Feedback: `server/app/domains/feedback/admin_feedback.py`
- Platform settings: `server/app/domains/platform/settings.py`
- Catalog/resources: `server/app/domains/catalog/`

## Removed Legacy Paths

These paths were intentionally deleted rather than kept as compatibility barrels:

- `server/app/admin_main.py`
- `server/app/main.py`
- `server/app/config.py`
- `server/app/database.py`
- `server/app/platform_settings.py`
- `server/app/formal_experiments.py`
- `server/app/agent.py`
- `server/app/media.py`
- `server/app/video_worker.py`
- `server/app/db.py`
- `server/app/rag.py`
- `server/app/report.py`
- `server/app/recommendation.py`
- `server/app/routers/`
- `server/app/services/`

Rollback should use git/deployment rollback, not new wrapper modules.

## Validation

Recommended backend gate:

```powershell
python scripts/validate_backend_architecture.py
python -m pytest server/tests -q
openspec validate backend-slim-domain-architecture --strict
```

Production readiness now includes architecture validation through:

```powershell
python scripts/validate_production_readiness.py --change backend-slim-domain-architecture
```

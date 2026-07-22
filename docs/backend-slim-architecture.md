# Backend Slim Architecture

This document is the current backend owner map.

## Package Shape

```text
server/app/
  app_runtime/          FastAPI construction, middleware, health
  api/
    auth/               login, logout, session, password routes
    admin/              teacher-console HTTP routes
    student/            student-H5 HTTP routes
    preview/            short-lived teacher student-preview exchange
  domains/
    analytics/          element-family and evidence read models
    assessments/        smart/custom/point/posttest sessions, mastery, reports
    assistant/          policy, retrieval, runtime, guardrails, evidence shaping
    catalog/            formal experiments and learning resources
    catalog_tree/       tree, content, Home recommendation, teacher search, RAG jobs
    experiment_points/  canonical point identity and textbook imports
    feedback/           teacher feedback administration
    media/              assets, bindings, files, lifecycle, subtitles, processing queue
    platform/           roles, settings, AI configuration, supervisor teacher accounts
    preview/            teacher-owned student preview lifecycle
    questions/          banks, drafts, generation, evidence, withdrawal/republication
    roster/             classes, rosters, student account lifecycle
    student_learning/   student point detail read models
    textbook_ingestion/ PDF extraction/OCR/chunking/embedding/indexing pipeline
    textbook_rag/       active corpus, clients, index, retrieval, evidence
  infrastructure/       settings, database, migration-facing helpers
  workers/              video and textbook-ingestion entrypoints
  scripts_support/      CLI-only support helpers
```

Cross-domain student read models with no package subtree currently live in:

- `server/app/domains/student_home_feed.py`
- `server/app/domains/student_video_saves.py`

Provider-neutral Elasticsearch transport shared by retained consumers lives in `server/app/search_index.py`.

## Dependency Rules

Allowed directions:

- `app_runtime -> api -> domains -> infrastructure`
- `workers -> domains -> infrastructure`
- `scripts -> domains/infrastructure/scripts_support`

Forbidden directions enforced by `python scripts/validate_backend_architecture.py`:

- `domains/*` must not import FastAPI, Starlette response owners, API routers, app runtime, or workers.
- `workers/*` must not import HTTP/runtime owners.
- `api/*` must not import worker entrypoints.
- Deleted legacy wrappers, old runtime adapters, and retired seed/script paths must not return.

## Canonical Entrypoints

- FastAPI: `server.app.app_runtime.main:app`
- Video worker: `python -m server.app.workers.video_worker`
- Textbook ingestion worker: `python -m server.app.workers.textbook_ingestion_worker`
- Migrations: `python scripts/apply_migrations.py`
- Architecture validation: `python scripts/validate_backend_architecture.py`
- Route contract: `server/tests/contracts/backend_route_inventory.json`

The route inventory is authoritative; this document intentionally does not duplicate a count that changes with supported endpoints.

## Owner Map

### Student discovery and learning

- Home feed and focused search: `domains/student_home_feed.py`
- Favorite persistence and favorite feed: `domains/student_video_saves.py`
- Catalog tree/student point views: `domains/catalog_tree/student_read_models.py`
- Point detail composition: `domains/student_learning/point_detail.py`
- Home recommendation authoring: `domains/catalog_tree/home_recommendations.py`

PostgreSQL is the fact/read-model owner for Home. There is no student video-library Elasticsearch domain, search route, index-state table, rebuild script, diagnostics contract, or background projection.

### Catalog, search, and RAG

- Catalog structure/status: `domains/catalog_tree/nodes.py`, `tree.py`, `directories.py`
- Shared point content/equations: `domains/catalog_tree/points.py`, `equations.py`
- Media bindings/related links: `domains/catalog_tree/media_bindings.py`, `related_links.py`
- Teacher catalog search: `domains/catalog_tree/teacher_search.py`
- Teacher-search and point-evidence jobs: `domains/catalog_tree/jobs.py`
- Catalog RAG context/probe: `domains/catalog_tree/ai_context.py`
- Textbook RAG corpus/index/retrieval: `domains/textbook_rag/`

Teacher catalog search and textbook RAG may both use Elasticsearch, but their indexes, documents, state, and failure domains are separate. Textbook RAG is the single retained vector projection.

### Online textbooks

- Upload/repository/views: `domains/textbook_ingestion/repository.py`, `views.py`
- Native extraction and MinerU adapter: `domains/textbook_ingestion/extraction.py`, `mineru.py`
- Chunking/embedding/projection: `domains/textbook_ingestion/chunking.py`, `embedding.py`, `projection.py`
- Queue/recovery/lifecycle: `domains/textbook_ingestion/queue.py`, `recovery.py`, `lifecycle.py`
- End-to-end worker pipeline: `domains/textbook_ingestion/pipeline.py`

The teacher settings owner supplies provider-neutral OCR, embedding, rerank, and LLM configuration. Callers must not hard-code provider keys or models in route/domain code.

### Assessment and reporting

- Smart baseline/assembly and custom-scope expansion: `domains/assessments/smart_assessment.py`
- Session submission/mastery: `domains/assessments/student_experiment.py`, `mastery.py`
- Student context: `domains/assessments/student_context.py`
- Reports: `domains/assessments/reports.py`
- Retained later assessment: `domains/assessments/posttest.py`

The active baseline is a smart assessment. Historical pretest report rows and labels remain readable; there is no active pretest start/submit domain or router.

### Teacher administration

- Roles and supervisor boundary: `domains/platform/roles.py`
- Supervisor teacher accounts: `domains/platform/teacher_accounts.py`
- Platform/AI settings: `domains/platform/settings.py`
- Classes/roster/student lifecycle: `domains/roster/classes.py`
- Question review lifecycle: `domains/questions/`
- Analytics: `domains/analytics/read_models.py`
- Student preview: `domains/preview/student_device_preview.py`

The internal `/api/admin/*` prefix denotes teacher-console APIs. It does not imply a standalone platform-operations application.

## Removed Compatibility Surfaces

The following categories must remain absent:

- old top-level backend wrappers and broad `routers/` or `services/` compatibility packages;
- student/teacher legacy adapter routers and domains;
- standalone platform-operations routes;
- duplicate teacher route families;
- active pretest start/submit routes; and
- student video-library Elasticsearch projection code and scripts.

Historical database migrations and read-only report compatibility are not runtime owners and must not be deleted merely because an active route was retired.

## Validation

```bash
python scripts/validate_backend_architecture.py
python -m pytest server/tests -q
python scripts/validate_production_readiness.py
```

Any API change also requires updating and testing `server/tests/contracts/backend_route_inventory.json`.

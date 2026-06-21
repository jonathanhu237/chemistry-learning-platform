## Context

The backend has already moved toward the documented shape `app_runtime -> api -> domains -> infrastructure`, and architecture validation prevents several deleted compatibility wrappers from returning. A follow-up scan found four root-level modules that are not imported by production runtime, API routers, scripts, or tests:

- `server/app/db.py`
- `server/app/rag.py`
- `server/app/report.py`
- `server/app/recommendation.py`

These modules belong to an older JSON-backed demo/RAG/report flow. Current behavior uses `server/app/data_loader.py` through repositories for seed-backed read models, `server/app/domains/assistant/*` plus `server/app/hybrid_rag.py` for assistant retrieval, and assessment/analytics domains for reports.

Some root-level modules that look similar are still live through non-import entrypoints or runtime references. `server/app/bge_service.py` is a Docker/uvicorn service entrypoint, and `server/app/video_similarity.py` is invoked through configured worker shell commands. Those are excluded from this cleanup.

## Goals / Non-Goals

**Goals:**

- Delete the unused JSON/RAG/report/recommendation modules.
- Add explicit validation so these retired modules cannot be reintroduced as root-level compatibility paths.
- Correct the FastAPI tool entrypoint to `server.app.app_runtime.main:app`.
- Keep route inventory, API behavior, Docker services, seed resources, and database schema unchanged.

**Non-Goals:**

- Do not move or rewrite live root-level modules such as `auth.py`, `data_loader.py`, `repositories.py`, `hybrid_rag.py`, `bge_service.py`, or `video_similarity.py`.
- Do not refactor the learning assistant, BGE service, media worker, or analytics implementation.
- Do not delete local/generated artifacts as part of this code change.
- Do not change any public API path, request schema, response schema, or frontend route.

## Decisions

1. Delete only modules with no live references.

   Rationale: This keeps the change safe and reviewable. The deleted modules form a self-contained historical chain and are not used by current route inventory or tests. Modules with Docker command or uvicorn string entrypoints are kept even if static Python import counting reports zero imports.

   Alternative considered: delete every root-level module that is outside `domains` or `infrastructure`. Rejected because several root-level modules are still current migration debt or valid process entrypoints, and removing them would mix cleanup with broader architecture migration.

2. Enforce retired module removal in backend architecture validation.

   Rationale: The repository already uses `scripts/validate_backend_architecture.py` as the backend ownership gate. Extending that gate is simpler and more reliable than relying on documentation alone.

   Alternative considered: add a standalone test with hardcoded paths. Rejected because it would duplicate the existing validation mechanism.

3. Treat `pyproject.toml` as configuration drift, not behavior.

   Rationale: README, Dockerfile, tests, and route inventory already use `server.app.app_runtime.main:app`. Updating `[tool.fastapi]` aligns tool metadata with the existing canonical runtime without changing runtime behavior.

## Risks / Trade-offs

- [Risk] A hidden manual workflow imports a retired module directly. -> Mitigation: the scan checked repository imports and runtime references; rollback is straightforward through git if an external caller is discovered.
- [Risk] Static import counting can miss string entrypoints. -> Mitigation: exclude known string-entrypoint modules and validate Docker/README references before deletion.
- [Risk] Adding more paths to architecture validation could block intentional future experiments. -> Mitigation: future experiments should live in an explicitly named domain, script, or tool owner rather than reviving retired root-level modules.

## Migration Plan

1. Delete the retired modules.
2. Update backend architecture validation and tests to assert the retired modules stay removed.
3. Update `pyproject.toml` to the canonical app runtime entrypoint.
4. Run backend architecture validation and focused tests.
5. Rollback, if required, uses git; no data migration or deployment compatibility layer is needed.

## Open Questions

None.

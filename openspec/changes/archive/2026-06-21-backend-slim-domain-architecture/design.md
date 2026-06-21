## Context

The repository already has two physically separate frontends (`apps/admin-web` and `apps/student-web`) and a FastAPI backend that serves both APIs and built frontend assets. Recent experiment point and video-library work exposed a structural backend problem: a worker entrypoint imported `server.app.media` for a checksum helper, but that module also owned media bindings and search-index notifications, so the worker became vulnerable to unrelated FastAPI/admin-service imports.

This is not isolated to media. Current backend modules include several 700-1200 line files and many `server/app/services/*` modules import FastAPI `HTTPException` directly. That means code intended to be reusable by CLI scripts, workers, maintenance commands, or domain tests can accidentally depend on the web runtime. The backend also mixes multiple bounded contexts in single modules: generic media assets, media bindings, experiment point learning content, student video-library read models, AI/RAG evidence, question workbench flows, analytics, roster management, and platform settings.

The product boundary is now clearer than the code boundary:

```text
Teacher/admin commands
  -> PostgreSQL facts
    -> student read APIs
    -> ES/IK derived search projections
    -> worker/CLI maintenance flows

AI/RAG evidence flows
  -> assistant/question diagnostics
  -> not student page body content

Media asset library
  -> teacher upload/storage/processing workspace
  -> not directly searchable by students

Experiment point content
  -> student point pages
  -> student video-library search documents
```

The frontends have maintainability issues too: admin has very large page modules and a monolithic API file; student has a large API file and some large feature components. However, this change intentionally limits frontend work to audit and follow-up planning so the backend slim refactor can land without mixing concerns.

## Goals / Non-Goals

**Goals:**

- Refactor the backend into a slim architecture with explicit application, API, domain, infrastructure, projection, and worker boundaries.
- Allow destructive backend changes: old internal import paths, compatibility wrappers, and route aliases may be removed.
- Keep behavior confidence through route inventory, backend tests, Compose smoke, ES/IK validation, and e2e gates rather than old compatibility layers.
- Make domain logic safe for web, worker, CLI, and test consumers by removing FastAPI dependencies from reusable domain modules.
- Split media assets, media bindings, experiment point content, video-library search, AI/RAG evidence, question/assessment, roster, analytics, and platform settings into clearer backend ownership boundaries.
- Preserve authoritative data boundaries: PostgreSQL facts remain canonical; ES remains a derived read model; generic media assets are not student search documents; AI evidence is not student display copy.
- Document admin and student frontend maintainability risks as follow-up inputs, without refactoring frontend code in this change.

**Non-Goals:**

- Do not redesign admin or student frontend UI in this change.
- Do not split admin or student frontend API modules in this change except for documentation/audit references.
- Do not introduce old compatibility barrels or wrapper modules to keep previous backend import paths alive.
- Do not change the product model of experiment point content, student video-library search, or AI/RAG evidence.
- Do not add a second backend service for student/admin APIs unless the implementation proves it is necessary; this is a package/layer architecture change first.
- Do not preserve deleted endpoint aliases merely to avoid frontend or test updates. Update clients/tests to the canonical route inventory instead.

## Decisions

### Decision 1: Use a slim layered backend package shape

Target shape:

```text
server/app/
  app_runtime/
    main.py
    routes.py
    lifespan.py
  api/
    admin/
    student/
    auth/
  domains/
    media/
      assets.py
      bindings.py
      processing_queue.py
      lifecycle.py
      visibility.py
    experiment_points/
      canonical_points.py
      learning_content.py
      related_links.py
      index_events.py
    video_library/
      documents.py
      search.py
      index_client.py
      sync.py
    assistant/
    questions/
    assessments/
    roster/
    analytics/
    platform/
  infrastructure/
    database.py
    settings.py
    files.py
    elasticsearch.py
  workers/
    video_worker.py
  scripts_support/
```

Rationale: The current flat `server/app` plus broad `services` folder makes ownership hard to infer. A slim package shape makes import direction visible in paths.

Alternative considered: leave the package layout mostly as-is and only split `media.py`. Rejected because the same dependency smell exists across services and would reappear.

### Decision 2: Domain modules must not import FastAPI

Reusable domain modules must return domain results or raise domain exceptions. Routers translate those exceptions into `HTTPException` and response models.

Allowed:

```text
api/admin/experiments.py -> domains/experiment_points/learning_content.py
api/student/video_library.py -> domains/video_library/search.py
workers/video_worker.py -> domains/media/processing_queue.py
```

Forbidden:

```text
domains/* -> fastapi
domains/* -> api/*
workers/* -> api/*
workers/* -> app_runtime/*
```

Rationale: Workers and CLI scripts should not become web apps by import accident.

Alternative considered: keep `HTTPException` in services because it is convenient. Rejected because it is the exact pattern that caused worker fragility.

### Decision 3: Replace compatibility with canonical baselines

This refactor may remove legacy endpoint aliases, old module paths, and compatibility wrappers. Instead of preserving them, the implementation must produce an updated route inventory and update clients/tests/e2e flows to canonical paths.

Rationale: The user explicitly allows destructive refactoring and does not want old compatibility layers. Keeping wrappers would preserve the current dependency ambiguity.

Alternative considered: migrate through compatibility barrels and route aliases. Rejected because it would hide whether the new architecture is actually used.

### Decision 4: Split media by responsibility

`server/app/media.py` should disappear as a mixed-purpose owner. Responsibilities should be separated:

- media file validation and path helpers
- media asset CRUD and upload completion
- processing queue and job status
- media binding commands
- media visibility rules
- duplicate detection and lifecycle cleanup

`video_worker` must depend only on media processing/file helpers and database infrastructure. Binding publication and student search projection must not be reachable through worker imports unless explicitly needed through a small event module.

Rationale: Asset storage, point binding, and student projection are different consumers of media state.

Alternative considered: keep `media.py` and continue extracting small helper modules. Rejected because the monolith remains the default import target.

### Decision 5: Separate command facts, student read models, and search projections

Experiment point learning content, student point detail payloads, and video-library ES documents should live in separate modules:

```text
domains/experiment_points/learning_content.py  -> canonical point facts
domains/student_learning/point_detail.py       -> student API read model
domains/video_library/documents.py             -> ES/search document model
domains/video_library/sync.py                  -> index state/outbox behavior
```

Rationale: Student detail rendering reads PostgreSQL facts; ES documents are retrieval projections; they should not share a giant service that also owns admin commands.

Alternative considered: keep `student_video_library_service.py` importing private helpers from `student_learning_service.py`. Rejected because it couples two read models through incidental helper functions.

### Decision 6: Preserve data contracts, not code paths

The refactor should preserve database facts and protected resources unless a task explicitly calls out a schema cleanup. Existing migrations must not be rewritten. Derived artifacts such as ES indexes may be rebuilt from PostgreSQL.

Rationale: Destructive code architecture is acceptable; destructive data migration is not implied.

Alternative considered: redesign tables while reorganizing code. Rejected because it would mix architecture cleanup with product/data-model changes.

### Decision 7: Architecture validation becomes a first-class gate

Add or extend validation that checks import direction and compatibility-layer removal. The validation should run in the backend test/quality workflow and should catch:

- `domains/*` importing FastAPI or routers
- `workers/*` importing FastAPI, routers, or app runtime
- `api/*` importing worker modules
- deleted legacy modules returning as wrappers
- route aliases not present in the canonical inventory

Rationale: Without automated guardrails, a later feature can reintroduce the same cross-layer shortcut.

Alternative considered: document conventions only. Rejected because the current problem came from undocumented convenience imports.

### Decision 8: Frontend work is audit-only in this change

The admin and student frontends should be audited for:

- oversized page modules
- monolithic API files
- route shell eager imports
- feature/private helper leakage
- backend endpoint coupling that will need updates after route canonicalization

The implementation should produce audit notes and follow-up OpenSpec recommendations, but should not reorganize frontend modules in this backend pass.

Rationale: Frontend maintainability matters, but mixing a backend package rewrite with frontend decomposition raises blast radius without improving the backend boundary outcome.

Alternative considered: refactor frontends at the same time. Rejected for scope control.

## Risks / Trade-offs

- [Risk] Destructive route cleanup can break admin/student calls. -> Mitigation: generate route inventory, update frontend calls/tests, and run backend plus e2e validation.
- [Risk] Large backend moves can create import cycles. -> Mitigation: migrate by bounded context, run architecture validation frequently, and keep infrastructure dependencies one-way.
- [Risk] Removing compatibility paths makes rollback harder. -> Mitigation: rollback through git and Compose image/version control, not through runtime compatibility wrappers.
- [Risk] Tests may assert old private helper imports. -> Mitigation: update tests to target public domain module contracts or approved test support helpers.
- [Risk] Frontend API coupling may surface during backend route cleanup. -> Mitigation: audit and update only necessary endpoint calls; defer frontend structural cleanup.
- [Risk] Product behavior could drift during restructuring. -> Mitigation: use existing characterization tests, route inventory, Compose smoke, ES/IK validation, and e2e flows as gates.
- [Risk] The refactor may reveal unrelated stale code. -> Mitigation: delete dead compatibility code when covered by inventory, but record larger product questions as follow-up tasks.

## Migration Plan

1. Capture current backend entrypoints, route table, worker imports, CLI imports, and large-module ownership map.
2. Define the canonical route inventory and explicitly list removed legacy aliases.
3. Add architecture validation before major moves, initially reporting current violations.
4. Create the target backend package skeleton and migrate infrastructure/config/database imports first.
5. Split media ownership and move `video_worker` to worker-safe dependencies.
6. Split experiment point, student point detail, and video-library search/index modules.
7. Migrate remaining large backend service domains in controlled slices: auth/platform, roster/classes, experiments/catalog, questions/workbench, assessment, assistant/RAG, analytics/feedback.
8. Remove legacy modules/wrappers once no canonical import remains.
9. Update route registration, scripts, backend tests, and e2e calls to the canonical inventory.
10. Produce admin/student frontend audit notes and follow-up recommendations.
11. Run validation: OpenSpec strict validation, backend tests, architecture validation, route inventory, Compose smoke, ES/IK checks, and e2e flows.

Rollback strategy:

- Use git revert or reset to a previous commit/image if the slim architecture fails validation.
- Rebuild ES from PostgreSQL if search index projections are affected.
- Do not add compatibility wrappers as rollback mechanisms inside the codebase.

## Open Questions

- Should the final package name be `domains` or `modules`? The design recommends `domains` because ownership is domain-driven rather than framework-driven.
- Should `server/app/admin_main.py` remain as the single FastAPI runtime entrypoint after slimming, or should runtime wiring move to `server/app/app_runtime/main.py` with `admin_main.py` deleted?
- Should route inventory be stored as a JSON fixture committed under `server/tests/contracts/`, or generated by a script and compared against an inline expected set?
- Should architecture validation use a lightweight custom AST script first, or adopt a dependency rule tool later?

## Why

The backend has reached the point where feature work is exposing structural coupling rather than isolated bugs: worker code can be pulled into FastAPI dependencies, media assets and student projections share modules, and large service files mix HTTP errors, SQL, domain rules, and read-model assembly. Because the repository already has git hygiene, Compose smoke, backend tests, and e2e validation gates, this change can deliberately perform a breaking backend slim refactor instead of preserving old compatibility layers.

## What Changes

- **BREAKING** Reorganize the backend into slim application, API, domain, infrastructure, and worker layers with explicit dependency direction.
- **BREAKING** Remove legacy compatibility modules, import paths, and endpoint aliases that only exist to preserve older internal structure.
- **BREAKING** Replace mixed-purpose modules such as `server/app/media.py` with domain-owned modules for media assets, media bindings, processing queues, lifecycle cleanup, and visibility rules.
- **BREAKING** Refactor backend services so reusable domain logic does not import FastAPI, routers, or HTTP response classes.
- **BREAKING** Make worker and CLI entrypoints depend only on domain/infrastructure modules that are safe outside the web app runtime.
- Split student-facing read models, admin command services, search projection builders, and AI/RAG evidence flows into separate backend boundaries.
- Keep PostgreSQL as the authoritative fact source and Elasticsearch/IK as a derived read model for student video-library search.
- Add architecture guardrails and tests that fail when disallowed import directions or compatibility layers return.
- Update backend docs with the new owner map, entrypoint map, and dependency rules.
- For the teacher/admin frontend and student H5 frontend, perform only a problem audit in this change: record oversized modules, API monoliths, route-shell risks, and recommended follow-up changes without restructuring frontend code.

## Capabilities

### New Capabilities

- `backend-slim-domain-architecture`: Defines the target backend architecture, dependency boundaries, destructive refactor rules, worker/CLI safety, domain ownership, and architecture verification gates.

### Modified Capabilities

- `backend-admin-router-ownership`: Changes the prior compatibility posture so destructive removal of legacy endpoint aliases and old module paths is allowed when route inventory, tests, and e2e baselines are updated deliberately.
- `production-engineering-quality`: Adds architecture-boundary validation to the production quality gates and requires backend refactors to pass Compose smoke, backend tests, and route inventory checks.
- `frontend-admin-maintainability`: Adds a teacher/admin frontend audit-only requirement for this backend slim pass, without requiring frontend restructuring in the same change.
- `student-web-frontend-maintainability`: Adds a student H5 frontend audit-only requirement for this backend slim pass, without requiring frontend restructuring in the same change.

## Impact

- Backend package layout, imports, service ownership, and internal APIs under `server/app`.
- FastAPI app wiring, router registration, route inventory tests, and any endpoint aliases that existed only for old internal compatibility.
- Worker and CLI scripts that currently import broad web/service modules.
- Media asset, media binding, experiment point, student video-library search, assessment, question bank, AI/RAG, analytics, class roster, and platform settings backend domains.
- Backend tests, architecture validation scripts, Compose smoke validation, OpenSpec docs, and production operations docs.
- Admin and student frontend code is not refactored in this change, but their current maintainability risks are documented as follow-up inputs.

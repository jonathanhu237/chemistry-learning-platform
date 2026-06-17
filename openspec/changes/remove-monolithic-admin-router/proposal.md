## Why

The admin backend still depends on `server.app.admin` as a mixed-purpose router for platform settings, AI configuration, learning assistant runtime, RAG assets, feedback, classes, registration, curriculum review, and media workflows. The rest of the project has moved toward production-oriented ownership, but this remaining monolith keeps unrelated domains coupled and makes future maintenance risky.

## What Changes

- Remove `server.app.admin` as an endpoint owner from the FastAPI application.
- Split the current admin API surface into feature-owned routers for platform/AI settings, learning assistant admin operations, media, feedback, class roster/registration, and curriculum review.
- Extract SQL-heavy or stateful logic from moved endpoints into focused service modules so routers remain thin.
- Preserve every existing admin API path, method, auth dependency, response field, error message intent, and compatibility alias.
- Add route-registration and contract-preservation tests for the moved endpoint groups.
- Keep protected chemistry resources, database schema/migrations, frontend routes, CI triggers, and deployment workflow unchanged.
- Document the final owner map and validation results so future work can continue without relying on chat context.

## Capabilities

### New Capabilities

- `backend-admin-router-ownership`: Defines how backend admin endpoints are grouped into domain routers, how monolithic endpoint ownership is retired, and how route contracts are protected during refactors.

### Modified Capabilities

None.

## Impact

- Backend application wiring: `server/app/admin_main.py`.
- Backend routers: new or updated modules under `server/app/routers/`.
- Backend services and schemas: new focused modules under `server/app/services/` and possibly `server/app/schemas/`.
- Tests: route-registration and compatibility tests under `server/tests/`.
- Documentation/OpenSpec: owner map, baseline, tasks, and final verification under this change.
- No intended impact on public API contracts, database migrations, protected seed resources, frontend workflows, GitHub Actions triggers, or Docker service topology.

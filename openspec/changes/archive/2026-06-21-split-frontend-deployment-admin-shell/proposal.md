## Why

The product is no longer one web surface under the backend: the student H5 and teacher/admin console are two different applications with different users, routes, validation gates, and deployment lifecycles. Keeping both SPAs served by the backend on one port hides that boundary and keeps the teacher console tied to `/admin` routing assumptions inside `App.tsx`.

This change makes the architecture match the real product shape: backend owns API only, student web owns the student SPA, admin web owns the teacher SPA, and Docker Compose owns the service topology. The refactor is intentionally breaking and does not preserve old internal compatibility layers.

## What Changes

- **BREAKING** Split production-like frontend deployment into independent `student-web` and `admin-web` services with separate containers and ports.
- **BREAKING** Remove backend static hosting of `apps/admin-web/dist` and `apps/student-web/dist`; backend no longer serves SPA fallback routes such as `/admin/{full_path}` or `/{full_path}`.
- **BREAKING** Remove `/admin` as the teacher console basename. The teacher console becomes its own app root with canonical routes such as `/overview`, `/experiments`, `/videos`, `/question-banks`, and `/login`.
- **BREAKING** Delete the root `apps/admin-web/src/App.tsx` compatibility owner and move teacher app ownership to `apps/admin-web/src/app/*`.
- **BREAKING** Remove legacy teacher route aliases such as `/curriculum` and `/review` unless a route is explicitly kept as canonical in the new route registry.
- Add frontend runtime containers that serve each built SPA and forward `/api` traffic to the backend service, so browsers can use same-origin API calls inside each frontend container.
- Update backend runtime and Docker image so it exposes API, health, media/auth routes, and backend-only behavior without frontend dist mounts.
- Update CORS, environment examples, production operations docs, and validation scripts so `backend`, `student-web`, and `admin-web` are required application services.
- Refactor teacher shell by responsibility: providers/theme, auth/login, route registry, navigation model, protected shell layout, sidebar/header, and route outlet.
- Keep the existing admin API client monolith stable for this change except where auth/login imports must move; splitting `api/index.ts` remains a separate follow-up.
- Update e2e smoke and production readiness gates to validate both frontend services and the new admin canonical routes.

## Capabilities

### New Capabilities

- `split-frontend-deployment`: Defines the independent student/admin frontend deployment topology, backend API-only runtime posture, and required Compose service graph.
- `admin-shell-architecture`: Defines the destructive teacher console shell split, canonical route registry, basename removal, and validation requirements.

### Modified Capabilities

- `frontend-admin-maintainability`: Teacher/admin frontend maintainability now requires an app-owned shell structure and no root `App.tsx` compatibility layer.
- `student-web-frontend-maintainability`: Student H5 maintainability now requires its SPA deployment to be owned by the student frontend service rather than the backend runtime.
- `backend-admin-router-ownership`: Backend runtime ownership changes because admin/student SPA fallback routes are removed from the backend route table.
- `production-engineering-quality`: Production quality validation now treats `admin-web` and `student-web` as required services when running Compose smoke for full application validation.
- `production-readiness-governance`: Release validation must distinguish backend API readiness from frontend SPA readiness and run e2e against the appropriate frontend service origins.

## Impact

- `docker-compose.yml` service topology, ports, health checks, and frontend service dependencies.
- New frontend runtime Dockerfiles or equivalent container build definitions for `apps/admin-web` and `apps/student-web`.
- `server/Dockerfile`, backend runtime static mounts, backend route inventory, CORS/default allowed origins, and production operations docs.
- `apps/admin-web/src/main.tsx`, `apps/admin-web/src/App.tsx`, teacher route basename, teacher route registry, auth shell, nav model, and admin e2e smoke paths.
- `apps/admin-web/vite.config.ts` base path and preview/dev assumptions.
- `apps/student-web` deployment packaging and frontend container serving behavior.
- `scripts/validate_compose_stack.py`, `scripts/validate_production_readiness.py`, admin e2e smoke, and any tests asserting backend-hosted frontend fallbacks.

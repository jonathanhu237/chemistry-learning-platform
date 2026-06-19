## 1. Baseline And Inventory

- [x] 1.1 Capture current backend-hosted frontend routes, static mounts, and route inventory entries for admin and student SPA fallback.
- [x] 1.2 Capture current Compose required services and published ports before introducing frontend services.
- [x] 1.3 Capture current admin frontend route paths, basename usage, Vite base, and e2e smoke paths.
- [x] 1.4 Capture current admin `App.tsx` responsibilities and map each responsibility to the target `src/app/*` owner.
- [x] 1.5 Capture current frontend build and preview assumptions for both student and admin apps.
- [x] 1.6 Decide and document final local published ports for `student-web` and `admin-web`; default to 5173 and 5174 unless blocked.

## 2. Frontend Runtime Containers

- [x] 2.1 Add a reusable frontend runtime pattern or separate Dockerfiles for serving built student/admin SPA assets.
- [x] 2.2 Configure the student frontend runtime to serve `apps/student-web/dist`.
- [x] 2.3 Configure the admin frontend runtime to serve `apps/admin-web/dist`.
- [x] 2.4 Configure both frontend runtimes to return `index.html` for deep SPA routes.
- [x] 2.5 Configure both frontend runtimes to proxy `/api/*` to `backend:8000`.
- [x] 2.6 Add a simple frontend runtime health or reachability endpoint/check for validation.
- [x] 2.7 Ensure frontend runtime configs do not encode the backend host as `localhost` inside containers.
- [x] 2.8 Ensure frontend images can be built after `npm ci`/build without requiring backend image rebuilds.

## 3. Compose Service Topology

- [x] 3.1 Add `student-web` as a default Compose service with its own build, port, and dependency on backend readiness.
- [x] 3.2 Add `admin-web` as a default Compose service with its own build, port, and dependency on backend readiness.
- [x] 3.3 Remove frontend dist volume mounts from the backend service.
- [x] 3.4 Keep backend, postgres, elasticsearch, tusd, and video-worker as required default services.
- [x] 3.5 Update backend CORS default origins to include dev and Compose frontend origins without treating same-origin proxy as a substitute for dev origins.
- [x] 3.6 Update `.env.example` and docs for frontend origin/port variables if new variables are introduced.
- [x] 3.7 Verify `docker compose config --quiet` succeeds after topology changes.

## 4. Backend API-Only Runtime

- [x] 4.1 Remove frontend dist copies from `server/Dockerfile`.
- [x] 4.2 Remove admin and student frontend static mounts from `server/app/app_runtime/main.py`.
- [x] 4.3 Remove backend-served admin logo/favicon routes tied to frontend dist unless a backend-owned replacement is explicitly needed.
- [x] 4.4 Remove `/admin` and `/admin/{full_path:path}` backend SPA fallback routes.
- [x] 4.5 Remove `/` and `/{full_path:path}` backend student SPA fallback routes.
- [x] 4.6 Preserve backend `/health` and all canonical `/api/*` routes.
- [x] 4.7 Move or delete any frontend-dist settings that are no longer backend-owned.
- [x] 4.8 Update backend route inventory to remove frontend fallback/static routes.
- [x] 4.9 Update backend tests that previously asserted SPA fallback behavior.
- [x] 4.10 Run backend architecture validation and backend tests after backend runtime cleanup.

## 5. Admin Frontend Root Route Migration

- [x] 5.1 Change admin Vite build base from `/admin/` to `/`.
- [x] 5.2 Remove `BrowserRouter basename="/admin"` from the admin entrypoint.
- [x] 5.3 Update admin app canonical routes to root paths such as `/overview`, `/experiments`, `/videos`, and `/login`.
- [x] 5.4 Remove legacy aliases `/curriculum` and `/review` unless explicitly added as canonical routes in the registry.
- [x] 5.5 Update admin asset references such as `sysu-logo.svg` so they work from the admin frontend service root.
- [x] 5.6 Update tests and e2e smoke paths from `/admin/*` to admin frontend root paths.
- [x] 5.7 Verify admin dev server and production build both use the same route semantics.

## 6. Admin App Shell Refactor

- [x] 6.1 Create `apps/admin-web/src/app/AdminApp.tsx` as the canonical app entrypoint.
- [x] 6.2 Create `apps/admin-web/src/app/providers.tsx` for Query/Router/Ant Design provider composition where appropriate.
- [x] 6.3 Create `apps/admin-web/src/app/theme.ts` for the Ant Design theme currently embedded in `App.tsx`.
- [x] 6.4 Create `apps/admin-web/src/app/routes.tsx` for canonical route definitions, lazy page loaders, fallback behavior, and route metadata.
- [x] 6.5 Create `apps/admin-web/src/app/nav.tsx` or equivalent if navigation metadata is separated from route rendering while remaining registry-derived.
- [x] 6.6 Create `apps/admin-web/src/app/auth/LoginPage.tsx` for login UI and login submission behavior.
- [x] 6.7 Create `apps/admin-web/src/app/auth/useAdminSession.ts` for token/session loading and `/api/auth/me` handling.
- [x] 6.8 Create `apps/admin-web/src/app/auth/RequireAdmin.tsx` for protected-route and role guard behavior.
- [x] 6.9 Create `apps/admin-web/src/app/shell/AdminShell.tsx` for protected shell composition.
- [x] 6.10 Create `apps/admin-web/src/app/shell/AdminSidebar.tsx` for sidebar, brand toggle, nav rendering, collapse state, and localStorage persistence.
- [x] 6.11 Create `apps/admin-web/src/app/shell/AdminHeader.tsx` for current user display and logout action.
- [x] 6.12 Create `apps/admin-web/src/app/shell/AdminRouteOutlet.tsx` or equivalent for rendering lazy routes with the existing loading fallback.
- [x] 6.13 Update `apps/admin-web/src/main.tsx` to import `./app/AdminApp`.
- [x] 6.14 Delete `apps/admin-web/src/App.tsx`; do not leave a compatibility re-export.
- [x] 6.15 Verify no admin source file imports the deleted root App path.
- [x] 6.16 Preserve existing auth token storage behavior and query cache clearing behavior.
- [x] 6.17 Preserve lazy chunk boundaries for top-level admin pages.

## 7. Student Frontend Deployment Ownership

- [x] 7.1 Keep student H5 browser routes owned by the student frontend service.
- [x] 7.2 Verify student Vite base and router behavior remain compatible with service-root deployment.
- [x] 7.3 Update student mobile QA configuration defaults if the production-like origin changes.
- [x] 7.4 Verify student `/api/*` calls work through the student frontend runtime proxy.

## 8. Validation Script Updates

- [x] 8.1 Update `scripts/validate_compose_stack.py` required service set to include `student-web` and `admin-web`.
- [x] 8.2 Update Compose smoke to discover frontend service ports and verify student/admin frontend reachability.
- [x] 8.3 Add a representative API-through-frontend proxy check for both frontend services.
- [x] 8.4 Update Compose smoke documentation and command examples.
- [x] 8.5 Update `scripts/validate_production_readiness.py` so e2e stages can target distinct backend, student frontend, and admin frontend origins.
- [x] 8.6 Update admin e2e smoke defaults to the admin frontend origin and root canonical routes.
- [x] 8.7 Update student mobile QA documentation/defaults to target the student frontend origin.
- [x] 8.8 Update CI or workflow docs if they reference backend-hosted frontend paths.

## 9. Documentation

- [x] 9.1 Update `docs/application-engineering-structure.md` with the split frontend deployment topology.
- [x] 9.2 Update `docs/production-operations.md` to remove backend-served frontend deployment instructions.
- [x] 9.3 Document how to build and start backend, student-web, admin-web, postgres, elasticsearch, tusd, and video-worker together.
- [x] 9.4 Document canonical admin routes after `/admin` basename removal.
- [x] 9.5 Document that rollback uses git/deployment rollback, not old backend SPA fallback restoration.

## 10. Verification

- [x] 10.1 Run `openspec validate split-frontend-deployment-admin-shell --strict`.
- [x] 10.2 Run `python scripts/validate_backend_architecture.py`.
- [x] 10.3 Run `python -m pytest server/tests -q`.
- [x] 10.4 Run admin frontend `npm run typecheck`.
- [x] 10.5 Run admin frontend `npm test`.
- [x] 10.6 Run admin frontend `npm run build`.
- [x] 10.7 Run admin frontend `npm run build:report`.
- [x] 10.8 Run student frontend `npm run typecheck`.
- [x] 10.9 Run student frontend `npm test`.
- [x] 10.10 Run student frontend `npm run build`.
- [x] 10.11 Run `docker compose config --quiet`.
- [x] 10.12 Build/restart required Compose services including `backend`, `student-web`, `admin-web`, `postgres`, `elasticsearch`, `tusd`, and `video-worker`.
- [x] 10.13 Run Compose smoke validation with frontend services included.
- [x] 10.14 Run admin e2e smoke against the admin frontend root origin.
- [x] 10.15 Run student mobile QA against the student frontend origin.
- [x] 10.16 Run full production readiness with e2e when services are running.
- [x] 10.17 Run `git diff --check`.

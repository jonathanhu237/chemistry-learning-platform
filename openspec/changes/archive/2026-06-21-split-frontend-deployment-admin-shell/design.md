## Context

The current application is structurally one backend service that also serves two frontend builds:

```text
backend:8000
  /api/*                 backend API
  /health                backend health
  /admin/*               teacher/admin SPA fallback
  /admin/assets/*        teacher/admin built assets
  /assets/*              student H5 built assets
  /*                     student H5 SPA fallback
```

This no longer matches the product. The student H5 and teacher/admin console are separate applications with separate users, route semantics, QA gates, and release risks. The backend should not be the owner of their SPA fallback behavior.

The current teacher console also keeps all app-level concerns inside `apps/admin-web/src/App.tsx`: Ant Design providers/theme, login page, auth guard, navigation metadata, shell layout, lazy page registry, and route aliases. Splitting deployment without splitting this shell would leave the old single-port assumption embedded in the frontend.

## Goals / Non-Goals

**Goals:**

- Make `backend`, `student-web`, and `admin-web` independent default Compose services.
- Make backend API-only: no frontend dist copy, no frontend static mounts, no SPA fallback routes.
- Serve student H5 and teacher/admin SPAs from their own containers and ports.
- Keep `/api` usable from both frontend origins through same-origin frontend reverse proxy or explicit dev proxy.
- Remove `/admin` from teacher/admin runtime routing and Vite build base.
- Replace root `apps/admin-web/src/App.tsx` with canonical `apps/admin-web/src/app/*` owners.
- Make route/nav metadata a single source of truth for the teacher console.
- Update validation so the full app smoke verifies backend API readiness and both frontend SPA readiness.

**Non-Goals:**

- Do not split the admin `api/index.ts` monolith in this change, except for minimal auth/login import movement required by the shell split.
- Do not decompose large teacher feature pages such as experiments, question bank, media resources, analytics, or learning assistant in this change.
- Do not change student H5 route-stack semantics or page design except for deployment ownership.
- Do not introduce a shared package/workspace layer.
- Do not preserve old `/admin/*`, backend-hosted `/assets/*`, `/curriculum`, or `/review` compatibility routes unless a route is explicitly listed as canonical.

## Decisions

### Decision: Frontend containers own SPA fallback

The student and admin frontend services will serve their own built `dist` directories and own fallback to `index.html`.

Target local/prod-like shape:

```text
backend:8000
  /api/*
  /health

student-web:5173 -> container :80
  /*
  /assets/*
  /api/* -> backend:8000

admin-web:5174 -> container :80
  /*
  /assets/*
  /api/* -> backend:8000
```

Rationale:

- It matches the product boundary: student app and teacher app are different deployments.
- It removes frontend-static concerns from FastAPI.
- It lets frontend e2e smoke validate the surface that actually serves the SPA.

Alternative considered: keep backend serving both SPAs and only split `App.tsx`. Rejected because it preserves the false one-service boundary and keeps deployment bugs hidden behind backend catch-all routes.

### Decision: Use frontend runtime servers with `/api` reverse proxy

Each frontend container should serve static files and reverse proxy `/api` to the backend service. Nginx is the preferred runtime because it is small, stable, and owns SPA fallback/proxy behavior clearly.

Rationale:

- Browser code can keep using relative `/api` URLs in production.
- CORS complexity is reduced for production-like Compose because requests are same-origin from the browser's point of view.
- Dev Vite proxies can keep matching the same `/api` contract.

Alternative considered: build frontends as static-only containers and force browser cross-origin calls to `http://localhost:8000`. Rejected because it increases CORS and environment coupling and makes local/prod-like behavior less similar.

### Decision: Backend becomes API-only

The backend Docker image must stop copying frontend dist directories. FastAPI runtime must remove:

- admin assets mount
- student assets mount
- admin logo/static route
- frontend favicon route tied to frontend dist
- `/admin` and `/admin/{full_path:path}` SPA fallback
- `/` and `/{full_path:path}` student SPA fallback

The backend may keep backend-owned routes such as `/health` and API routes under `/api/*`.

Rationale:

- Backend route inventory becomes simpler and less surprising.
- Frontend rebuilds no longer require rebuilding the backend image.
- Backend tests no longer need to characterize SPA fallback behavior.

### Decision: Teacher app canonical root is `/`

The teacher/admin app will remove `base: "/admin/"` from Vite and remove `basename="/admin"` from `BrowserRouter`. Its canonical routes become:

```text
/login
/overview
/classes
/experiments
/videos
/question-banks
/analytics
/feedback
/learning-assistant
/settings
/ai-config
```

The old backend-hosted browser URLs such as `/admin/overview` are not preserved.

Rationale:

- The teacher console is its own app root.
- It removes duplicated path reasoning between backend, Vite, BrowserRouter, e2e smoke, and route registry.
- It makes route behavior align with independent container deployment.

### Decision: Delete root `App.tsx` instead of wrapping it

The teacher shell refactor will introduce:

```text
apps/admin-web/src/app/
  AdminApp.tsx
  providers.tsx
  theme.ts
  routes.tsx
  nav.tsx
  auth/
    LoginPage.tsx
    RequireAdmin.tsx
    useAdminSession.ts
  shell/
    AdminShell.tsx
    AdminSidebar.tsx
    AdminHeader.tsx
    AdminRouteOutlet.tsx
```

`apps/admin-web/src/main.tsx` will import from `./app/AdminApp`. The old `apps/admin-web/src/App.tsx` file will be deleted, not kept as a compatibility re-export.

Rationale:

- The app owner becomes explicit.
- Changes to theme, auth, navigation, and page registry stop fighting inside one file.
- The destructive move matches the repository's established policy: no compatibility wrappers for old internal structure.

### Decision: Route registry owns nav metadata and lazy pages

The admin route registry should be the only source for:

- path
- page lazy loader
- nav label
- nav icon
- selected key behavior
- role visibility
- fallback route

Rationale:

- The current `navItems` and `<Routes>` are parallel lists with implicit coupling.
- A single registry lets e2e smoke and chunk reporting follow the same canonical route list.

### Decision: Validation is updated before declaring done

This change affects all three surfaces and the Compose graph. Completion requires:

- OpenSpec strict validation.
- Backend architecture validation and backend tests.
- Admin frontend typecheck, tests, build, chunk report, and e2e smoke against the admin frontend service root.
- Student H5 typecheck, tests, build, and mobile QA against the student frontend service root.
- Compose smoke that starts and verifies `backend`, `student-web`, `admin-web`, `postgres`, `elasticsearch`, `tusd`, and `video-worker`.
- Production readiness chain with e2e when dev servers or frontend containers are running.

## Risks / Trade-offs

- **Route breakage for old `/admin/*` bookmarks** -> Accepted as a breaking change. The deployment boundary changed; old URLs are not canonical.
- **CORS confusion during migration** -> Keep dev and production-like frontends using `/api` proxy; retain allowed origins for explicit dev cross-origin cases.
- **Nginx/proxy config mistakes can hide API failures** -> Compose smoke must verify frontend health, backend health, and representative `/api` reachability through both frontend services.
- **Backend route inventory churn** -> Update route inventory in the same change and keep exact-route tests.
- **Admin shell refactor can cause auth regressions** -> Run admin e2e smoke and keep login/auth guard behavior covered.
- **Two frontend services increase local startup cost** -> Accepted because this reflects the true deployment architecture.

## Migration Plan

1. Add frontend runtime container definitions and local runtime configs for both SPAs.
2. Move admin app ownership under `apps/admin-web/src/app/*`.
3. Update admin Vite base/router basename/e2e paths to root canonical routes.
4. Remove backend frontend dist copies, static mounts, and SPA fallback routes.
5. Update Docker Compose required services and validation scripts.
6. Update tests and route inventory to reflect backend API-only posture.
7. Run full validation and e2e.

Rollback uses git/deployment rollback. Do not restore old compatibility routes or wrapper files as the rollback mechanism.

## Open Questions

- Which exact host ports should production-like Compose expose by default? The proposed local defaults are `5173` for student and `5174` for admin to match current dev ports.
- Should frontend health endpoints be served by Nginx as `/health` or should validation use `GET /` and representative route loads? A dedicated `/health` is preferable if the runtime config stays simple.

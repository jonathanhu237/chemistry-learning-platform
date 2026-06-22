# Application Engineering Structure

This document records the current whole-application structure contract after `standardize-application-engineering-structure`.
It is intentionally about ownership and validation, not feature behavior.

## Surfaces

```text
chemistry-admin
  apps/web-student     Student H5 mobile learning experience
  apps/web-teacher     Teacher console
  apps/web-admin       Platform operations console
  server/app           Backend runtime, APIs, domains, infrastructure, workers
  docker-compose.yml   Required local/prod-like service graph with separate frontend services
  scripts/             Validation, migrations, imports, rebuilds, maintenance
```

Structural work must name the surfaces it touches. If a change touches two or more surfaces, the OpenSpec proposal should explain which surface owns:

- user interaction
- teacher/admin editing
- canonical database facts
- derived projections such as Elasticsearch
- validation and rollback

## Student H5

Canonical starting shape:

```text
apps/web-student/src/
  app/
    router/        route definitions, typed route search, navigation helpers, route visibility
    shell/         authenticated layout, header, bottom tabs, detail frame
    appConfig.ts   app-level configuration helpers
  routes/          route-level pages that compose feature components
  features/        domain UI, formatting, hooks, adapters, and feature-specific components
  shared/          reusable UI/utilities with no route ownership
  mobile/          H5/mobile primitives, viewport helpers, and tokens
  styles/          global and legacy styles with explicit ownership
```

Student H5 page hierarchy is semantic, not a direct measure of URL depth.

Root tab pages:

- `/home`
- `/learn`
- `/ai`
- `/assessment`
- `/profile`

Reusable second-level pages:

- chapter study
- element detail
- experiment point detail
- video library
- AI chat
- assessment session/report
- feedback

An experiment point detail page may be opened from a learning card, video-library result, related point link, or assessment flow. It remains a reusable second-level page because the route is shared across entry points.

Rules:

- Cross-page navigation should use `apps/web-student/src/app/router/navigation.ts` or an equivalent typed owner.
- Route pages should remain composition boundaries and move reusable display logic into `features/*`.
- Shared modules must not import route or feature owners.
- New endpoint clients should move toward domain-specific client/schema modules instead of expanding one monolithic `api.ts`.
- Route-stack, shell, bottom-tab, and detail-page changes require student mobile viewport QA.

Current follow-up debt:

- `apps/web-student/src/api.ts` is a split candidate.
- `features/atom-viewer/AtomViewerZdog.tsx` is a split candidate.
- `features/assistant/StudentAiChatPanel.tsx` is a split candidate.
- Large global CSS files should be gradually moved toward feature or shell ownership.

## Teacher/Admin Web

Target shape:

```text
apps/web-teacher/src/
  app/             app providers, auth guard, route registry, nav model, shell layout, theme
  api/             HTTP primitives plus domain-specific clients and schemas
  features/        teacher/admin workflows by business capability
  components/      shared UI primitives used across features
  lib/             shared non-React or cross-feature helpers
  styles.css       shell/global styles only after migration
```

Rules:

- Global shell behavior belongs in app-level owners, not feature pages.
- Route metadata and navigation metadata should be centralized instead of duplicated in page modules.
- The admin frontend is deployed at its service root. Canonical admin routes are `/login`, `/overview`, `/classes`, `/experiments`, `/videos`, `/question-banks`, `/analytics`, `/feedback`, `/learning-assistant`, `/settings`, and `/ai-config`.
- Feature pages should split into page orchestration, hooks, panels, forms, tables, adapters, and display helpers when they grow.
- Cross-feature components must not import feature-specific API clients or data types.
- Shared request primitives live in `api/http.ts`; auth/session token ownership lives in `api/auth.ts`; common response envelopes live in `api/common.ts`.
- Domain schemas and endpoint helpers live in explicit modules such as `api/classes.ts`, `api/settings.ts`, `api/feedback.ts`, `api/analytics.ts`, `api/resources.ts`, `api/learningAssistant.ts`, `api/media.ts`, `api/questionBank.ts`, and `api/experiments.ts`.
- The deleted `api/index.ts` barrel must not return as a compatibility layer. Admin source imports must reference concrete `api/*` modules.
- Shell, auth, navigation, route registry, or top-level lazy-route changes require admin e2e smoke.

Current experiment feature baseline:

```text
apps/web-teacher/src/features/experiments/
  ExperimentsPage.tsx        route-level composition only
  experimentHooks.ts         React Query queries, mutations, and invalidation
  experimentFilters.ts       pure point filtering helpers
  experimentList/            filters and list table
  experimentDetail/          detail drawer and basic form
  pointContent/              point-content modal, related links, request mappers, tests
  videoBindings/             point video resources, binding modal, preview modal
```

Cross-feature helper baseline:

- Reusable resource/catalog display helpers live in `apps/web-teacher/src/lib/resourceUtils.ts`, not inside a sibling feature folder.
- Feature pages should not import sibling feature private UI/helper modules. Promote stable cross-feature helpers to `lib/` or a shared component owner first.

Current follow-up debt:

- Large feature pages such as learning assistant, question bank, media resources, and analytics should be decomposed inside their feature folders.
- `apps/web-teacher/src/styles.css` and large feature CSS files should be reduced toward explicit style ownership.

## Backend

Canonical shape:

```text
server/app/
  app_runtime/      FastAPI construction, middleware, health
  api/              auth/admin/student HTTP translation
  domains/          business rules, commands, read models, projections, adapters
  infrastructure/   settings, database, connection primitives
  workers/          process entrypoints
  scripts_support/  CLI-only support helpers
```

Dependency direction:

```text
app_runtime -> api -> domains -> infrastructure
workers     -> domains -> infrastructure
scripts     -> domains/infrastructure/scripts_support
```

Rules:

- Domain modules must not import FastAPI, Starlette response classes, API routers, app runtime, or worker entrypoints.
- API route modules translate domain results and domain errors into HTTP responses; they do not own domain rules.
- Worker entrypoints import worker-safe domain and infrastructure owners only.
- Deleted legacy wrappers stay deleted; rollback uses git or deployment rollback.
- The backend owns `/health` and `/api/*` only. Student and admin SPA assets, deep-route fallbacks, and frontend health endpoints are owned by their frontend runtime containers.
- Large domain files should split by commands, read models, projections, adapters, and worker-safe helpers when they become structural hotspots.

Current follow-up debt:

- Large domain files such as question workbench, student learning detail, assistant agent runtime, analytics read models, roster classes, and assessment modules should be evaluated before they become new service-layer monoliths.
- Root-level backend modules that remain outside `domains` and `infrastructure` are migration candidates, process entrypoints, or seed-backed support modules, not compatibility owners. Retired demo/RAG/report modules must stay deleted rather than returning as wrappers.

## Validation Gates

Default gates by surface:

- Backend package ownership: `python scripts/validate_backend_architecture.py` and backend tests.
- Backend service graph or required service changes: Compose smoke through `python scripts/validate_production_readiness.py --run-compose-smoke`, covering `backend`, `web-student`, `web-teacher`, `web-admin`, `postgres`, `elasticsearch`, `tusd`, and `video-worker`.
- Student H5 routing/shell/layout: typecheck, tests, build, and `npm run qa:mobile`.
- Admin shell/routing/top-level pages: import-boundary validation, typecheck, tests, build, chunk report, and `npm run e2e:smoke`.
- Multi-surface structural changes: full production readiness with e2e when the local runtime prerequisites are available.

Elasticsearch/IK is part of the application contract for student video-library search. Local fallback must not hide production search failures in production-like validation.

## Frontend Boundary Validation Direction

The admin frontend owns a lightweight path-boundary check through `npm run validate:boundaries`. It fails on legacy directory imports that resolve to the removed `api/index.ts`, on React imports inside `src/api/*`, and on feature imports from API modules. Consider ESLint import rules or TypeScript project references only after the final module shape stabilizes.

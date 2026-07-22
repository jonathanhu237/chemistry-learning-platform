# Application Engineering Structure

This document records current application ownership and validation boundaries. Feature behavior is described in the product and domain-specific documents.

## Runtime Surfaces

```text
chemistry-learning-platform/
  apps/web-student     canonical green five-tab student H5
  apps/web-teacher     canonical Ant Design teacher console
  server/app           FastAPI APIs, domains, infrastructure, and workers
  server/migrations    ordered PostgreSQL migrations
  docker-compose.yml   production-style service graph
  scripts              migrations, bootstrap, rebuild, validation, maintenance
  data/seed            protected current restore resources
```

A cross-surface change must identify which owner is responsible for:

- user interaction;
- teacher authoring;
- canonical PostgreSQL facts;
- rebuildable projections;
- asynchronous jobs; and
- validation and rollback.

## Student H5

Canonical source shape:

```text
apps/web-student/src/
  app/
    router/        routes, typed search state, navigation, visibility
    shell/         authenticated layout, header, bottom tabs, detail frame
    preview/       teacher-preview sandbox boundaries
  routes/          route-level composition
  features/        domain UI, hooks, adapters, formatting
  shared/          reusable UI and utilities without route ownership
  mobile/          H5 primitives, viewport helpers, and tokens
  styles/          shell/global and feature styles with explicit ownership
```

The five root tabs and paths are:

- Home — `/home`
- Learn — `/learn`
- Atom — `/ai`
- Assessment — `/assessment`
- Profile — `/profile`

Home owns the finite experiment-video feed, focused search, viewport-muted preview, explicit recommendation label, and navigation into a point. It does not own a separate video-library route. The same PostgreSQL catalog/video read model answers the default and searched feed.

Reusable detail routes include chapter, element, catalog directory, experiment point, Atom chat/artifact, assessment session/report, Profile reports, and feedback. The experiment point page is shared by Home, Learn, related-point, favorite, and assessment navigation.

Rules:

- Cross-page navigation belongs in `app/router/navigation.ts` or another typed router owner.
- Route pages are composition boundaries; reusable behavior belongs in `features/*`.
- Shared modules must not import route or feature owners.
- A visible persistent action must call a durable backend owner. Student video saves support `favorite` only.
- Root shell, tabs, route-stack, and detail-frame changes require mobile viewport QA.
- The current green visual system is canonical; legacy competition styling is not a fallback.
- The 3D atom/orbital experience and persisted Profile favorites are retained capabilities.

The remaining large `api.ts`, Atom viewer, assistant panel, and global style files are refactor candidates, not compatibility owners.

## Teacher Console

Canonical source shape:

```text
apps/web-teacher/src/
  app/             providers, auth guard, route registry, navigation, shell, theme
  api/             HTTP primitives plus domain clients and schemas
  features/        workflows by business capability
  components/      cross-feature UI primitives
  lib/             shared non-React helpers
  styles.css       shell/global styles only
```

Canonical routes are `/login`, `/overview`, `/textbooks`, `/classes`, `/experiments`, `/videos`, `/question-banks`, `/analytics`, `/feedback`, `/learning-assistant`, `/student-preview`, `/settings`, and `/ai-config`.

The teacher console owns:

- online textbook upload, review, publish/deactivate/delete, and job recovery;
- class/roster management and global/per-class assessment settings;
- catalog tree authoring, Home recommendation flags, media bindings, and teacher catalog search diagnostics;
- local video upload and processing workflows;
- question evidence, withdrawal-to-draft, editing, validation, and republication;
- element-family analytics plus experiment/point/attempt/report drilldowns;
- student preview, feedback, learning assistant, and AI monitoring; and
- self-service password change plus supervisor-teacher account controls in Settings.

Rules:

- Shell behavior and route/navigation metadata belong to `app/*`, not feature pages.
- Shared request primitives live in `api/http.ts`; authentication ownership lives in `api/auth.ts`.
- API modules must not import React or feature owners.
- Feature modules may use shared `components/*` and `lib/*`; they must not reach into sibling feature-private modules.
- Source imports target concrete `api/*` modules; deleted compatibility barrels must stay deleted.
- The internal `admin` identity is presented as a supervisor teacher. It does not imply another frontend.
- Shell, authentication, navigation, or top-level lazy-route changes require teacher e2e smoke.

The current Ant Design shell and tokens are canonical. Approved legacy behavior is implemented inside these owners, not by restoring an older monolith.

## Backend

Canonical shape:

```text
server/app/
  app_runtime/      FastAPI construction, middleware, health
  api/              auth/admin/student/preview HTTP translation
  domains/          business rules, commands, read models, projections, adapters
  infrastructure/   settings, database, connection primitives
  workers/          video and textbook-ingestion process entrypoints
  scripts_support/  CLI-only support helpers
```

Dependency direction:

```text
app_runtime -> api -> domains -> infrastructure
workers     -> domains -> infrastructure
scripts     -> domains/infrastructure/scripts_support
```

Rules:

- Domain modules do not import FastAPI, Starlette response classes, API routers, app runtime, or worker entrypoints.
- API modules translate domain results/errors into HTTP; business rules stay in domains.
- Worker entrypoints import worker-safe domain and infrastructure owners only.
- The backend owns `/health` and `/api/*`; frontend containers own SPA assets, deep-route fallback, and frontend health.
- Deleted legacy adapters and runtime wrappers stay deleted. Rollback uses Git/deployment rollback.

Important data/projection ownership:

- PostgreSQL is canonical for Home feed/search, recommendations, favorites, catalog facts, identities, assessments, questions, and textbook/job metadata.
- Teacher catalog Elasticsearch is a rebuildable authoring projection.
- Textbook RAG Elasticsearch is the single vector projection used by retained RAG consumers.
- Online textbook PDFs live under the configured shared `TEXTBOOK_STORAGE_ROOT` and are processed by `textbook-ingestion-worker`.
- Video files live under `MEDIA_ROOT` and are processed by `video-worker`.
- Historical pretest data remains report-readable, but no active pretest HTTP workflow exists.

## Validation Gates

Backend:

```bash
python scripts/validate_backend_architecture.py
python -m pytest server/tests -q
```

Student H5:

```bash
cd apps/web-student
npm run typecheck
npm test
npm run build
npm run qa:mobile
```

Teacher console:

```bash
cd apps/web-teacher
npm run validate:boundaries
npm run typecheck
npm test
npm run build
npm run build:report
```

Service graph and multi-surface release:

```bash
python scripts/validate_production_readiness.py
python scripts/validate_production_readiness.py --run-compose-smoke --skip-frontend --skip-backend-tests
```

The Compose smoke covers `backend`, `web-student`, `web-teacher`, `postgres`, `elasticsearch`, `tusd`, `video-worker`, and `textbook-ingestion-worker`. It validates teacher catalog Elasticsearch/IK; it does not build a student video-search index.

## Boundary Validation Direction

`apps/web-teacher` owns a lightweight path-boundary check through `npm run validate:boundaries`. The backend architecture validator enforces layer imports and guards deleted compatibility paths. Route inventory is maintained at `server/tests/contracts/backend_route_inventory.json` and must change whenever a supported endpoint is added or retired.

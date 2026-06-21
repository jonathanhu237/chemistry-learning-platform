## Design Intent

This change is a structure standard, not a feature implementation. It captures the current good parts of the repository and names the places where the next refactor should tighten boundaries.

The guiding idea is simple:

```text
Whole app
  |
  +-- student H5: learning experience and mobile route-stack semantics
  +-- admin web: teacher operations, authoring, diagnostics, and resource management
  +-- backend: canonical facts, domain rules, derived read models, workers, and service integrations
  +-- compose/validation: the system contract that proves the pieces still run together
```

## Page Semantics

Student H5 page hierarchy should be described by navigation meaning, not by nested URL depth.

```text
Root tab pages
  home
  learn
  ai
  assessment
  profile

Reusable second-level pages
  video library
  chapter study
  element detail
  experiment point detail
  AI chat
  assessment session/report
  feedback
```

An experiment point detail may look like a "third" step when opened from a library card, but architecturally it remains a reusable second-level detail page because any root tab or second-level listing can open it. That is the same practical pattern used by many large apps: the tab root owns broad destinations, while profile/detail/content pages sit in a shared navigable layer above the tab root.

## Surface Owner Map

### Student H5

```text
apps/student-web/src/
  app/
    router/        route definitions, typed route search, navigation helpers, route visibility
    shell/         authenticated layout, header, bottom tabs, detail frame
    appConfig.ts   app-level configuration helpers
  routes/          route-level pages only; orchestrates feature components and loaders
  features/        domain UI and feature-specific formatting/hooks/components
  shared/          reusable UI/utilities with no route ownership
  mobile/          H5/mobile primitives and tokens
  styles/          legacy/global styles with an explicit migration path
```

The student app already largely follows this pattern. The main follow-up is to prevent `api.ts`, global styles, and complex feature components from becoming the new monoliths.

### Admin Web

```text
apps/admin-web/src/
  app/             desired owner for shell, auth guard, route registry, app providers, theme
  api/             desired owner for HTTP primitives plus domain-specific clients/schemas
  features/        teacher/admin workflows grouped by business capability
  components/      shared UI primitives used by multiple features
  lib/             shared non-React or cross-feature helpers
  styles/          app shell/global styles only
```

The admin app currently has the right high-level feature folder, but `App.tsx` and `api/index.ts` still centralize too much. The next frontend refactor should split those without changing product behavior.

### Backend

```text
server/app/
  app_runtime/      FastAPI construction, middleware, static mounts, health
  api/              auth/admin/student HTTP translation
  domains/          business rules, read models, commands, projections, adapters
  infrastructure/   settings, database, connection primitives
  workers/          process entrypoints
  scripts_support/  CLI-only support helpers
```

The backend now has hard import rules. The next improvement is to make large domain files split by sub-responsibility before they become service-layer monoliths again.

## Dependency Direction

The dependency shape should stay boring and predictable:

```text
frontend route page -> feature components/hooks -> frontend api client -> backend api
backend api route   -> domain owner -> infrastructure
backend worker      -> domain owner -> infrastructure
scripts             -> domain/infrastructure/scripts_support
```

Forbidden directions:

- Feature modules should not import route-only modules.
- Shared UI/utils should not import feature or route modules.
- Student feature modules should not manually assemble cross-route URLs when a navigation helper exists.
- Admin feature modules should not add new unrelated schemas to one global API barrel.
- Backend domain modules should not import FastAPI, Starlette response classes, API routers, app runtime, or worker entrypoints.
- Worker entrypoints should not import API routers or app runtime.

## Validation Strategy

The current validation system is strong enough to support destructive cleanup:

- Backend architecture import validation.
- Backend tests.
- Protected resource and experiment point validators.
- Video-library ES/IK readiness validation.
- Admin frontend typecheck, tests, build, chunk report, and e2e smoke.
- Student H5 typecheck, tests, build, and mobile viewport QA.
- Compose stack smoke for the required application services.

This change should turn those into the default gate for future structural refactors, then add focused validators for frontend boundaries when the frontend refactor begins.

## Non-Goals

- Do not implement the frontend restructuring in this change.
- Do not introduce shared packages or a monorepo workspace layer unless a later proposal proves the need.
- Do not add compatibility wrappers for removed backend module paths.
- Do not make page URL depth the source of truth for student H5 page semantics.

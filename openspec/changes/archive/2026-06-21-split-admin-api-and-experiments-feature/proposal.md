## Why

The admin shell has been split, but the teacher frontend still has a monolithic `api/index.ts` and large feature pages that mix transport types, query orchestration, mutations, forms, tables, modals, and business mapping. This blocks safe iteration on the experiment management page, especially upcoming changes to experiment-point content editing.

## What Changes

- Split the admin frontend API layer into domain-owned clients and type modules while preserving the existing HTTP behavior and auth token semantics.
- Keep shared HTTP primitives centralized, but stop adding feature/domain schemas and endpoint helpers to one global `api/index.ts`.
- Refactor the experiment management feature into explicit owners for page orchestration, hooks/query state, list filtering, experiment detail, point-content editing, video binding, and preview/publish actions.
- Preserve teacher-visible behavior for `/experiments`, including experiment CRUD, chapter bindings, point learning content editing, related point links, video resource binding, publication state, and media preview.
- Add validation expectations so the API/domain split and experiments feature split are checked through typecheck, tests, build, admin e2e smoke, and focused unit tests for request mappers.
- **BREAKING**: Internal imports from `apps/admin-web/src/api/index.ts` as a catch-all domain type barrel are not preserved as a compatibility layer. Feature code must import from canonical domain clients/types after migration.

## Capabilities

### New Capabilities

- `admin-api-domain-clients`: Defines domain-owned admin frontend API clients, shared HTTP primitives, auth token ownership, and import boundaries.
- `admin-experiments-feature-architecture`: Defines the experiment management feature structure, point-content editor ownership, video binding ownership, and behavior-preserving extraction requirements.

### Modified Capabilities

- `frontend-admin-maintainability`: Adds concrete maintainability requirements for avoiding global API growth and splitting feature pages by orchestration, data hooks, UI panels, and pure mappers.

## Impact

- Affected frontend code:
  - `apps/admin-web/src/api/index.ts`
  - `apps/admin-web/src/api/*`
  - `apps/admin-web/src/features/experiments/*`
  - admin feature imports that currently depend on the global API barrel
- Affected tests and validation:
  - admin frontend typecheck, tests, build, build report
  - admin e2e smoke against `/experiments`
  - focused tests for point-content request mapping and related-links mapping
  - optional lightweight import-boundary validation for admin API ownership
- No backend API contract, database schema, Docker topology, or student frontend behavior should change in this refactor.

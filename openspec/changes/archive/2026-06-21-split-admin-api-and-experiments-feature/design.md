## Context

The teacher/admin frontend now has a canonical `src/app/*` shell, but feature code still depends on a single global API barrel:

- `apps/admin-web/src/api/index.ts`: 1326 lines, 72 exported domain types, shared HTTP primitives, auth token helpers, stream helpers, and unrelated utilities.
- `apps/admin-web/src/features/experiments/ExperimentsPage.tsx`: 1201 lines, owning experiment list state, experiment edit form, video-point content editor, related-link mapping, video binding, media preview, publish/unpublish/archive actions, and modal layout.
- Other admin feature pages such as learning assistant, question bank, media resources, resources, and analytics are also large, but upcoming product work needs the experiment page first.

This change is intentionally a structural refactor. It prepares the admin codebase for later experiment-page content changes without changing backend APIs, database schema, route paths, or teacher-visible workflows.

## Goals / Non-Goals

**Goals:**

- Replace the global admin API barrel with explicit domain client modules.
- Preserve shared HTTP/auth behavior while making domain endpoint ownership visible by file path.
- Migrate existing admin feature imports to canonical API modules.
- Refactor the experiment management feature into page orchestration, data hooks, pure mappers, point-content editor, video binding/preview UI, and list/detail UI owners.
- Preserve `/experiments` route behavior, query keys, mutation effects, form validation semantics, point-content request payloads, and video binding workflows.
- Add focused tests for point-content and related-link request mapping before later content changes.
- Keep the current admin app shell, route registry, independent frontend deployment, and backend API-only posture intact.

**Non-Goals:**

- Do not redesign the experiment management UI in this change.
- Do not change backend endpoint paths or response/request shapes.
- Do not change database tables, migrations, Elasticsearch behavior, or video-worker behavior.
- Do not split all large admin pages in this change; question bank, media, learning assistant, resources, and analytics remain follow-up candidates.
- Do not introduce a shared workspace package or new external dependency.
- Do not keep `apps/admin-web/src/api/index.ts` as a compatibility re-export for old feature imports.

## Decisions

### Decision: Split API by domain before splitting experiments UI

Target admin API shape:

```text
apps/admin-web/src/api/
  http.ts                apiBase, api, postJson, patchJson, putJson, postJsonStream
  auth.ts                User, login/me helpers, token storage helpers
  common.ts              ApiList and narrow shared API types
  classes.ts             class, roster, registration clients/types
  experiments.ts         experiment catalog, experiment video points, point content, related links
  media.ts               media assets, processing jobs, duplicate candidates, upload completion
  questionBank.ts        question bank, drafts, workbench clients/types
  learningAssistant.ts   assistant runtime, ask/stream, source asset types
  analytics.ts           class dashboard/report clients/types
  feedback.ts            feedback clients/types
  settings.ts            platform and AI configuration clients/types
  resources.ts           learning resource overview/framework clients/types
```

Rationale:

- Feature pages should import from their domain instead of knowing every type in the app.
- The experiment-page split will be smaller once experiment/media/chapter/point-content API ownership is explicit.
- The no-compatibility rule keeps old `../../api` imports from becoming a permanent hidden barrel.

Alternative considered: split `ExperimentsPage.tsx` first and leave `api/index.ts` in place. Rejected because extracted experiment subcomponents would still depend on the same global type barrel, making the page split mostly cosmetic.

### Decision: Keep HTTP/auth primitives shared and behavior-preserving

`api/http.ts` owns fetch, JSON body conventions, stream parsing, auth header injection, 401 token clearing, and error propagation. `api/auth.ts` owns token storage and session/login types.

Rationale:

- HTTP mechanics are cross-cutting and should stay central.
- Domain modules should declare endpoint paths and payload types, not duplicate fetch mechanics.
- Existing token key behavior and query-cache clearing behavior must remain compatible with the shell split.

Alternative considered: each domain client wraps `fetch` independently. Rejected because it risks inconsistent auth, streaming, and error behavior.

### Decision: Domain clients own endpoint paths and exported schemas

Each domain API module exports:

- request/response types for that domain
- functions for endpoint calls used by admin features
- query-key helpers when they are stable enough to share inside that domain

Domain modules must not import React components. React Query hooks may live in the feature folder when they depend on UI state.

Rationale:

- Endpoint ownership becomes searchable and reviewable.
- Domain clients remain testable without rendering React.
- Feature folders can own UI-specific query composition without polluting transport modules.

### Decision: Delete or empty the catch-all API barrel

Implementation should remove `apps/admin-web/src/api/index.ts` or reduce it to a non-imported legacy-free path only if tooling requires the file to exist. No admin source file should import `../api` or `../../api` as a directory barrel after migration.

Rationale:

- Keeping a re-export barrel would preserve the old coupling.
- Future reviewers need import paths to reveal domain ownership.

### Decision: Experiments feature gets explicit internal owners

Target experiment feature shape:

```text
apps/admin-web/src/features/experiments/
  ExperimentsPage.tsx
  experimentHooks.ts
  experimentFilters.ts
  experimentMappers.ts
  experimentList/
    ExperimentFilters.tsx
    ExperimentListTable.tsx
  experimentDetail/
    ExperimentDetailDrawer.tsx
    ExperimentBasicForm.tsx
  pointContent/
    PointContentModal.tsx
    pointContentMapper.ts
    pointContentMapper.test.ts
    RelatedLinksEditor.tsx
  videoBindings/
    VideoBindingModal.tsx
    VideoPreviewModal.tsx
    videoBindingActions.ts
```

The exact filenames may vary if implementation discovers a better local boundary, but the ownership must remain explicit:

- `ExperimentsPage.tsx`: route-level orchestration and composition only.
- hooks: React Query calls and mutation invalidation.
- mappers: pure request/response mapping and form hydration.
- point-content owner: principle mode, equation/text validation, phenomenon explanation, safety note, related links, and publication actions.
- video-binding owner: asset selection, bind/publish/unpublish/delete, preview URL/poster handling.
- list/detail owner: filters, table columns, drawer form, create/edit controls.

Rationale:

- Upcoming point-content UI changes should touch point-content modules, not the entire experiment page.
- Current behavior can be preserved while shrinking review blast radius.
- Pure mappers can get focused tests without browser e2e.

### Decision: Validation follows the touched surface

Completion requires:

- OpenSpec strict validation.
- Admin frontend typecheck, tests, build, and build report.
- Focused unit tests for experiment point-content request mapping and related-link mapping.
- Admin e2e smoke against root admin routes, including `/experiments`.
- Full production readiness with e2e when the current Compose/frontend runtime is available.

Rationale:

- API module movement is best caught by TypeScript and imports.
- Experiment feature behavior is best covered by focused mapper tests plus browser smoke for route rendering.
- The deployment topology should remain unchanged and must not regress.

## Risks / Trade-offs

- **Import churn across many feature files** -> Move shared primitives first, then domain modules in small batches, running typecheck after each batch.
- **Accidental API behavior change** -> Preserve function semantics and add focused tests for high-risk mappers before moving UI.
- **Large feature extraction can create prop drilling** -> Prefer feature-level hooks and small owner components over deeply nested generic abstractions.
- **Duplicate types during migration** -> Keep one canonical exported type per domain and delete old duplicates in the same change.
- **E2E smoke may miss subtle form behavior** -> Add unit tests around request payload mappers and run admin e2e for route-level health.
- **No compatibility barrel means a larger one-time edit** -> Accepted because the repository policy favors canonical ownership and git rollback over old internal wrappers.

## Migration Plan

1. Create `api/http.ts`, `api/auth.ts`, and `api/common.ts`; migrate app shell/auth imports.
2. Create domain API modules and move types/functions from the global barrel by feature group.
3. Migrate admin feature imports from `../../api` to explicit domain modules.
4. Delete the catch-all `api/index.ts` or verify no source imports it.
5. Add/adjust import-boundary validation for admin API modules.
6. Extract experiment request mappers and add focused tests.
7. Extract experiment hooks and React Query mutation invalidation.
8. Extract experiment list/detail/point-content/video-binding components.
9. Run the full validation chain.

Rollback uses git/deployment rollback. Do not reintroduce a compatibility `api/index.ts` barrel or merge experiment submodules back into a monolithic page as the rollback mechanism.

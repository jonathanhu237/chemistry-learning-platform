## 1. Baseline And Import Inventory

- [x] 1.1 Capture the current export groups in `apps/admin-web/src/api/index.ts`, including shared HTTP helpers, auth helpers, common types, and each domain type cluster.
- [x] 1.2 Capture all current admin source imports that resolve to the global API barrel.
- [x] 1.3 Capture current `/experiments` feature responsibilities, including queries, mutations, forms, modals, table columns, filters, preview behavior, and request mappers.
- [x] 1.4 Capture current experiment-related tests and identify which tests must move with extracted mapper/filter modules.
- [x] 1.5 Record current admin build chunk owners before API and experiments feature extraction.

## 2. Shared API Foundation

- [x] 2.1 Create `apps/admin-web/src/api/http.ts` for `apiBase`, `api`, `postJson`, `patchJson`, `putJson`, and `postJsonStream`.
- [x] 2.2 Create `apps/admin-web/src/api/auth.ts` for `User`, login/session response types where appropriate, `getAuthToken`, and `setAuthToken`.
- [x] 2.3 Create `apps/admin-web/src/api/common.ts` for `ApiList` and narrowly shared API response helpers.
- [x] 2.4 Move non-API formatting helpers such as `formatBytes` out of the API layer into a UI-neutral helper or feature-owned helper.
- [x] 2.5 Migrate app-shell auth imports from the old API barrel to `api/auth` and `api/http`.
- [x] 2.6 Run admin frontend typecheck after the shared API foundation migration.

## 3. Domain API Clients

- [x] 3.1 Create `api/classes.ts` with class, roster, registration, import, and password reset types/functions.
- [x] 3.2 Create `api/settings.ts` with platform settings and AI configuration types/functions.
- [x] 3.3 Create `api/feedback.ts` with feedback list, summary, detail, update, and attachment URL helpers.
- [x] 3.4 Create `api/analytics.ts` with dashboard, weak-point, student report, and export URL/header helpers.
- [x] 3.5 Create `api/resources.ts` with learning resource overview and framework types/functions.
- [x] 3.6 Create `api/learningAssistant.ts` with assistant runtime, request/response/source types, stream helper calls, and RAG asset URL helpers.
- [x] 3.7 Create `api/media.ts` with media asset, processing, duplicate, upload, thumbnail, stream, and retry/decision types/functions.
- [x] 3.8 Create `api/questionBank.ts` with question bank, question, draft, point-aware suggestion, and workbench types/functions.
- [x] 3.9 Create `api/experiments.ts` with experiment catalog, chapter binding, video point, point-content, related-link, publication, and resource binding types/functions.
- [x] 3.10 Ensure domain API modules do not import React components or feature UI modules.
- [x] 3.11 Run admin frontend typecheck after domain API modules are created.

## 4. Feature Import Migration

- [x] 4.1 Migrate classes, settings, feedback, analytics, resources, and AI configuration feature imports to explicit domain API modules.
- [x] 4.2 Migrate learning assistant feature imports to `api/learningAssistant`, `api/settings`, and shared HTTP/auth modules.
- [x] 4.3 Migrate media feature imports to `api/media` and shared HTTP/auth modules.
- [x] 4.4 Migrate question bank feature imports to `api/questionBank`, `api/experiments`, and `api/learningAssistant` as needed.
- [x] 4.5 Migrate experiments feature imports to `api/experiments`, `api/media`, and shared HTTP/auth modules.
- [x] 4.6 Migrate shared components and markdown helpers to explicit API/auth/http imports.
- [x] 4.7 Delete `apps/admin-web/src/api/index.ts` or ensure it is unused and does not export domain schemas if tooling requires it to exist.
- [x] 4.8 Add or update a lightweight validation check that fails when admin source imports from the old API barrel path.
- [x] 4.9 Run admin frontend typecheck and tests after all imports are migrated.

## 5. Experiments Mapper Extraction

- [x] 5.1 Create `features/experiments/pointContent/pointContentMapper.ts` for point-content form hydration and request payload mapping.
- [x] 5.2 Move `PointContentFormValues`, related-link form payload types, `buildPointContentRequest`, and `buildPointRelatedLinksRequest` into point-content mapper ownership.
- [x] 5.3 Add focused tests covering equation mode, text mode, optional values, related-link target parsing, relation type, sort order, and hidden links.
- [x] 5.4 Move experiment filter pure helpers into `features/experiments/experimentFilters.ts` or equivalent owner.
- [x] 5.5 Preserve and relocate existing experiment filter tests to the canonical helper owner.
- [x] 5.6 Run admin frontend tests after mapper/filter extraction.

## 6. Experiments Hooks And Data Ownership

- [x] 6.1 Create or update `features/experiments/experimentHooks.ts` to own experiment list, chapter list, selected experiment, video points, and media asset queries.
- [x] 6.2 Move experiment create/update mutations into feature-owned hooks that call the experiments domain API client.
- [x] 6.3 Move point-content save, related-link save, and point publication mutations into feature-owned hooks.
- [x] 6.4 Move video binding publish, unpublish, delete, and bind mutations into feature-owned hooks.
- [x] 6.5 Preserve existing React Query keys and invalidation/refetch behavior for changed experiment, video point, and media data.
- [x] 6.6 Run admin frontend typecheck after hooks extraction.

## 7. Experiments UI Component Extraction

- [x] 7.1 Extract experiment list filters and table display into `features/experiments/experimentList/*`.
- [x] 7.2 Extract experiment detail drawer and basic experiment form into `features/experiments/experimentDetail/*`.
- [x] 7.3 Extract point-content modal into `features/experiments/pointContent/PointContentModal.tsx`.
- [x] 7.4 Extract related-link editing UI into `features/experiments/pointContent/RelatedLinksEditor.tsx`.
- [x] 7.5 Extract video binding modal into `features/experiments/videoBindings/VideoBindingModal.tsx`.
- [x] 7.6 Extract media preview modal and authenticated preview URL handling into `features/experiments/videoBindings/VideoPreviewModal.tsx` or a closely named owner.
- [x] 7.7 Keep `ExperimentsPage.tsx` as route-level orchestration and composition only.
- [x] 7.8 Verify teacher-visible experiment list, drawer, point-content editor, video binding, and preview workflows remain unchanged.
- [x] 7.9 Run admin frontend typecheck and tests after UI extraction.

## 8. Boundary Cleanup And Documentation

- [x] 8.1 Remove duplicate experiment/media/question/settings types left behind after API migration.
- [x] 8.2 Verify no feature page imports a sibling feature's private UI/helper module.
- [x] 8.3 Update `docs/application-engineering-structure.md` if the final API/domain layout needs to be recorded as the new admin frontend baseline.
- [x] 8.4 Update any existing refactor map or production notes that still describe `api/index.ts` as the source of all admin types.
- [x] 8.5 Run a source search proving old API barrel imports and old experiment mapper locations are gone.

## 9. Verification

- [x] 9.1 Run `openspec validate split-admin-api-and-experiments-feature --strict`.
- [x] 9.2 Run admin frontend `npm run typecheck`.
- [x] 9.3 Run admin frontend `npm test`.
- [x] 9.4 Run admin frontend `npm run build`.
- [x] 9.5 Run admin frontend `npm run build:report`.
- [x] 9.6 Run admin frontend `npm run e2e:smoke` against the admin frontend root origin.
- [x] 9.7 Run `python scripts/validate_production_readiness.py --run-compose-smoke --run-e2e` when the Compose/frontend runtime is available.
- [x] 9.8 Run `git diff --check`.

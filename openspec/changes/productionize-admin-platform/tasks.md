## 1. Resource Consolidation

- [x] 1.1 Create a protected core resource manifest covering formal experiments, knowledge framework, point inventory, current point-aware question bank, schema, canonical chunks, embeddings, point evidence bindings, and import reports.
- [x] 1.2 Move or mirror current in-repo core artifacts into stable seed/resource paths without changing their content.
- [x] 1.3 Decide and document whether external canonical chunks and embeddings are mirrored into the repo, placed in a versioned external package, or manifest-referenced by source path.
- [x] 1.4 Add resource validation that checks required paths, counts, sizes, and SHA256 values before any cleanup task can run.
- [x] 1.5 Update import/rebuild scripts so default inputs use stable production resource paths or manifest-declared external locations.

## 2. Legacy Artifact Cleanup

- [x] 2.1 Classify current `artifacts/` contents into protected resources, historical audit material, generated intermediates, screenshots, and disposable caches.
- [x] 2.2 Add a dry-run cleanup report listing files/directories to preserve, archive, or delete, including byte-size impact.
- [x] 2.3 Remove or archive obsolete point-aware question-bank review packets, rebuilt packages, semantic work packets, pilot reviews, and old releases after validation passes.
- [x] 2.4 Remove or archive obsolete video-point raw candidates, rerank scratch outputs, smoke packages, and review packets while preserving final manually reviewed point evidence.
- [x] 2.5 Clean generated local outputs such as screenshots, `.tmp`, logs, pytest caches, frontend `dist`, frontend `node_modules`, and Vite logs.
- [x] 2.6 Handle `data/media` only with an explicit database/UI consistency plan for existing `media_assets` records.

## 3. Frontend Modularization

- [x] 3.1 Map current `App.tsx` routes, page state, feature state, API calls, and shared UI components before moving code.
- [x] 3.2 Extract admin pages and feature modules for question bank, learning assistant, videos/media, classes/students, analytics, and shared layout.
- [x] 3.3 Split API helpers and assistant markdown/rendering utilities into focused modules with existing tests preserved or expanded.
- [x] 3.4 Split global CSS into feature/page/component styles while keeping visual behavior equivalent.
- [x] 3.5 Add route-level or feature-level code splitting for charts, KaTeX, Uppy/tus, learning assistant, and other heavy optional modules.

## 4. Backend Router And Service Split

- [x] 4.1 Map `experiment_admin.py` endpoints, dependencies, permissions, database access, and response shapes.
- [x] 4.2 Extract routers for experiments, question banks, workbench, analytics, learning resources/media, and student submissions while preserving endpoint paths.
- [x] 4.3 Extract domain services for question-bank import/validation, point evidence, knowledge framework, analytics, and media handling.
- [x] 4.4 Keep API contracts stable and add focused regression tests for moved endpoints.
- [x] 4.5 Review `agent.py` after resource consolidation and split reusable policy/RAG/normalization helpers where behavior can remain equivalent.

## 5. Production Operations Hardening

- [x] 5.1 Normalize migration discipline from the next migration forward and document how duplicate historical numbers are handled.
- [x] 5.2 Add or update `.env.example`, Docker health expectations, local production-like run instructions, and backup/restore notes.
- [x] 5.3 Add a one-command production-readiness validation script or documented command chain.
- [x] 5.4 Run backend tests, frontend typecheck, frontend tests, frontend build, resource validation, and OpenSpec strict validation after each phase.
- [ ] 5.5 Capture final productionization notes that explain what was removed, what is protected, and how to restore the current system from declared resources.

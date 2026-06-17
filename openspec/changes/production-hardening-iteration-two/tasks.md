## 1. Baseline And Guardrails

- [x] 1.1 Confirm `codex/productionize-admin-platform` is clean, pushed, and aligned with `origin/codex/productionize-admin-platform`.
- [x] 1.2 Run the current production-readiness validation chain to capture the second-pass baseline.
- [x] 1.3 Capture current frontend build output and identify oversized chunks by file, dependency family, and route owner.
- [x] 1.4 Confirm current backend warning surface for FastAPI `on_event` deprecation in admin and BGE services.
- [x] 1.5 Add or update notes that this hardening pass must not change core resources, API contracts, question data, or evidence semantics.

## 2. Frontend Build Splitting

- [x] 2.1 Add route-level lazy loading for page modules that are not required for the first admin shell render.
- [x] 2.2 Split heavyweight feature-only imports such as charts, KaTeX/Markdown rendering, Uppy/tus upload code, and assistant/video utilities behind page or component boundaries.
- [x] 2.3 Configure Vite `manualChunks` for stable vendor families including React/router/query, Ant Design/icons, charts, markdown/math, and upload utilities.
- [x] 2.4 Add a lightweight build-output report or documented check that maps large chunks to owners and budgets.
- [x] 2.5 Run frontend typecheck, tests, and build; verify that remaining chunk warnings are eliminated or explicitly documented as named vendor budgets.
- [x] 2.6 Browser-smoke the main admin shell plus lazy-loaded learning assistant, question bank, analytics, and media pages.

## 3. FastAPI Lifespan Migration

- [x] 3.1 Replace `admin_main.py` `@app.on_event("startup")` with an async lifespan context that preserves database startup checks and media-root creation.
- [x] 3.2 Replace `bge_service.py` startup warmup `on_event` with a lifespan context that preserves background warmup behavior.
- [x] 3.3 Add or adjust tests/import smoke checks so deprecated FastAPI startup warnings are not emitted by project code.
- [x] 3.4 Run backend import smoke, backend tests, Docker health checks, and BGE warmup health verification.

## 4. Validation And CI

- [x] 4.1 Update `scripts/validate_production_readiness.py` so its default change points at `production-hardening-iteration-two` during this pass while keeping `--change` override.
- [x] 4.2 Add a CI workflow that runs protected resource validation, OpenSpec strict validation, backend import smoke, backend tests, frontend typecheck, frontend tests, and frontend build.
- [x] 4.3 Document CI/local validation usage, dependency expectations, and any acceptable environment-specific skips.
- [x] 4.4 Run the validation script locally with the active hardening change and confirm failures stop on the first failed required stage.

## 5. Media Lifecycle Hardening

- [x] 5.1 Map `media_assets`, `media_bindings`, local files, thumbnails, playback files, processing jobs, review rows, and derived candidates into a cleanup dependency model.
- [x] 5.2 Implement a media cleanup dry-run that reports candidate files, database dependencies, action type, and byte impact without deleting anything.
- [x] 5.3 Add guarded destructive cleanup modes that refuse active referenced files unless an archive/tombstone state is explicitly applied.
- [x] 5.4 Update admin API/UI behavior so archived or missing media is represented intentionally instead of exposing broken playback/thumbnail links.
- [x] 5.5 Add tests or smoke checks covering active media, archived media, missing files, and cleanup refusal cases.
- [x] 5.6 Document the production media cleanup procedure and when `data/media` may be removed.

## 6. Assistant Runtime Modularization

- [x] 6.1 Characterize current learning-assistant behavior with focused tests or fixtures for representative point-aware, RAG, guardrail, and normalization scenarios.
- [x] 6.2 Map `server/app/agent.py` responsibilities into runtime orchestration, retrieval/rerank coordination, prompt/context construction, output normalization, and evidence/citation shaping.
- [x] 6.3 Extract output normalization and citation/evidence shaping helpers first, reusing existing `agent_output_normalization` where appropriate.
- [x] 6.4 Extract retrieval/rerank and source-context construction into focused services or helpers with dependency injection that is testable without changing endpoints.
- [x] 6.5 Extract runtime orchestration into a smaller public facade while preserving existing endpoint imports and response schemas.
- [x] 6.6 Run assistant-focused tests, backend tests, and authenticated learning-assistant smoke checks to confirm equivalent behavior.

## 7. Migration And Operations Polish

- [x] 7.1 Confirm no existing migration files are renamed, removed, reordered, or rewritten during this pass.
- [x] 7.2 If media lifecycle work needs schema changes, add the next migration as `014_...` or later.
- [x] 7.3 Update operations docs to restate migration numbering policy, media lifecycle policy, CI gates, and local smoke-test steps.
- [x] 7.4 Remove or rotate the temporary local smoke admin account if it is no longer needed, or document it as local-only test data.

## 8. Final Verification And Handoff

- [x] 8.1 Run protected resource validation and confirm core resource counts/checksums are unchanged.
- [x] 8.2 Run OpenSpec strict validation for `production-hardening-iteration-two`.
- [x] 8.3 Run backend import smoke and backend tests.
- [x] 8.4 Run frontend typecheck, frontend tests, and frontend production build.
- [x] 8.5 Rebuild/restart Docker Compose with the RAG profile and verify backend/BGE health.
- [x] 8.6 Run authenticated admin API smoke and browser smoke for representative pages.
- [x] 8.7 Commit the completed hardening work in coherent phases and push the branch.
- [x] 8.8 Update final notes with remaining known risks and mark the OpenSpec tasks complete only after validation passes.

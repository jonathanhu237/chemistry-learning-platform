## Context

The previous productionization pass completed the largest structural cleanup: core resources were consolidated under `data/seed`, validation scripts were added, legacy artifacts were cleaned, frontend pages/styles were split, backend admin routes moved into routers/services, and the deployed Docker stack was smoke-tested successfully.

The remaining work is narrower but still cross-cutting:

- The frontend production build still emits Vite chunk-size warnings, mostly from vendor-heavy modules such as Ant Design, charts, KaTeX/Markdown rendering, and Uppy/tus.
- `server/app/admin_main.py` and `server/app/bge_service.py` still use deprecated FastAPI `on_event` startup hooks.
- `data/media` cannot be deleted safely without a database/UI lifecycle plan for `media_assets`, `media_bindings`, processing jobs, review rows, and derived files.
- `scripts/validate_production_readiness.py` exists, but it still defaults to the first productionization change and is not yet wired into CI.
- `server/app/agent.py` remains a large module and is the next likely maintenance hotspot.

This pass should treat all work as behavior-preserving hardening. Current core resources, question content, evidence bindings, API paths, permissions, and admin workflows must remain stable.

## Goals / Non-Goals

**Goals:**
- Make frontend build output easier to reason about by splitting route-only and heavyweight optional dependencies into named chunks.
- Remove FastAPI `on_event` deprecation warnings by moving startup behavior to lifespan contexts.
- Add a safe media lifecycle model so local media cleanup is tied to database state and admin UI behavior.
- Make the validation chain CI-ready and point it at the current active hardening change.
- Split `server/app/agent.py` into stable assistant services/helpers without changing response semantics.
- Keep each phase independently reviewable, testable, and revertible.

**Non-Goals:**
- Do not change teacher/admin/student feature behavior.
- Do not change question-bank content, knowledge framework resources, canonical chunks, embeddings, or point evidence bindings.
- Do not rewrite historical migrations or renumber already-applied migration files.
- Do not delete `data/media` by file path alone.
- Do not introduce new frontend frameworks, backend frameworks, queue systems, or observability vendors in this pass.

## Decisions

### Use Named Vendor Chunks Instead Of Raising The Warning Limit First

The first frontend step should inspect the current build output and introduce explicit `manualChunks` groups for stable heavy dependencies: React/router/query, Ant Design/icons, charts, markdown/math/KaTeX, upload/tus/hash utilities, and optional assistant/video modules. Route-level `React.lazy` should be used where the user experience can tolerate page loading boundaries.

Rationale: raising `chunkSizeWarningLimit` would hide the signal without improving code ownership. Named chunks make future regressions visible and allow large dependencies to be cached independently.

Alternative considered: silence Vite warnings globally. Rejected for now because the project is entering production hardening and warnings are useful quality gates.

### Convert Both FastAPI Apps To Lifespan In One Focused Phase

`admin_main.py` should wrap the existing startup database check and media-root creation in an async lifespan context. `bge_service.py` should move warmup triggering into a lifespan context while preserving the current background-thread warmup behavior and `/health` warmup state.

Rationale: converting only one app would leave the warning partially unresolved and make validation ambiguous.

Alternative considered: suppress deprecation warnings in tests. Rejected because the migration is small and aligns with FastAPI's current API.

### Treat Media Cleanup As A State Transition, Not A Delete Command

Media cleanup should be implemented around explicit states and consistency checks. A cleanup command may archive or delete files only when it has verified related database rows and bindings. If media rows remain for user-facing history, the admin UI must display an intentional archived/missing state rather than a broken file link.

Rationale: the current database has media records. File-only cleanup would create silent broken references.

Alternative considered: keep `data/media` forever. Rejected because it leaves local uploads as unmanaged production debt.

### Make CI Reuse The Local Production Validation Script

The local validation script should remain the source of truth. CI should call it or mirror its stages: protected resources, OpenSpec strict validation, backend import smoke, backend tests, frontend typecheck/tests/build. The script should default to the active change when used during this pass, while still allowing `--change` override.

Rationale: one validation contract avoids drift between local and remote checks.

Alternative considered: write separate CI commands only. Rejected because developers would have two subtly different definitions of readiness.

### Split `agent.py` By Responsibility, Not By Call Stack Noise

The split should identify stable seams before moving code:

- request/runtime orchestration
- RAG retrieval and reranking coordination
- prompt/context construction
- output normalization and citation/evidence shaping
- lightweight value objects/config helpers

Existing tests should be expanded around observable behavior before large moves. The public assistant API should continue to return equivalent structures for existing scenarios.

Rationale: `agent.py` is large, but a mechanical split without responsibility boundaries can make future changes harder.

Alternative considered: rewrite the assistant runtime. Rejected because the current system works and this pass is hardening, not redesign.

## Risks / Trade-offs

- [Risk] Vendor chunks may still exceed 500 KB after proper splitting. -> Mitigation: require named chunk groups and a build report; only adjust warning budgets if the remaining large chunks are stable third-party vendor chunks and documented.
- [Risk] Lazy loading can alter perceived navigation behavior. -> Mitigation: keep route-level loading states minimal and verify key admin pages in browser smoke tests.
- [Risk] Lifespan migration can accidentally skip startup checks. -> Mitigation: add smoke tests/import checks and verify Docker health after migration.
- [Risk] Media cleanup can remove files still referenced by rows or bindings. -> Mitigation: default cleanup to dry-run, require database/file consistency checks, and cover destructive cleanup with explicit flags.
- [Risk] Agent split can subtly change assistant responses. -> Mitigation: characterize current behavior with focused tests before moving logic, then compare normalized outputs.

## Migration Plan

1. Commit this OpenSpec change and push it so the next phase has durable context.
2. Run the current validation chain before code changes to establish the second-pass baseline.
3. Implement frontend build splitting first because it is isolated and easy to verify with `npm run build`.
4. Migrate FastAPI lifespan hooks and verify backend import smoke, pytest, Docker health, and BGE warmup state.
5. Add CI workflow and update validation script defaults/docs.
6. Design and implement media cleanup as dry-run first, then add guarded destructive modes only after validation.
7. Split `agent.py` in small commits with tests around each extracted responsibility.

Rollback is commit-level for most phases. Media destructive operations must remain opt-in and should not be run automatically in CI or normal deployment.

## Open Questions

- Should the build budget be enforced as "no Vite warnings" or as a custom named-chunk report with thresholds per chunk family?
- Should media cleanup archive files to a local external directory first, or delete only after a second explicit confirmation?
- Should CI use GitHub Actions only, or also provide a local `make`/PowerShell wrapper for Windows-first development?

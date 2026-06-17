## Why

The first productionization pass made the project clean, rebuildable, and modular enough to run as a serious internal beta. The remaining known issues are now production-quality concerns: frontend bundle weight, deprecated FastAPI lifecycle hooks, media record/file consistency, automated validation, and one remaining large backend assistant module.

This change captures the second hardening pass so the next refactor does not rely on chat memory. It should improve maintainability and deploy confidence without changing teacher/admin/student feature behavior, core question data, knowledge resources, point evidence, or API contracts.

## What Changes

- Add production-quality requirements for build budgets, runtime lifecycle, media cleanup consistency, CI/local validation, and behavior-preserving modularization.
- Reduce frontend production build warnings by splitting heavyweight optional dependencies and lazy-loading page-specific modules where practical.
- Migrate FastAPI startup/shutdown behavior from deprecated `on_event` handlers to `lifespan`, preserving current health checks, migrations, Docker startup behavior, and RAG runtime behavior.
- Define and implement a safe media lifecycle path for `data/media`, `media_assets`, and media bindings so local video cleanup never leaves broken admin records.
- Add CI or CI-ready validation commands that run backend tests, frontend typecheck/tests/build, OpenSpec strict validation, production resource validation, and backend import smoke checks.
- Analyze and split `server/app/agent.py` along stable assistant boundaries while preserving response semantics and existing learning-assistant contracts.
- Keep migration history intact; any new database migration must continue from `014_...` and must not rewrite existing migration files.

## Capabilities

### New Capabilities

- `production-quality-hardening`: Defines second-pass production quality requirements for bundle budgets, FastAPI lifespan, media lifecycle consistency, CI validation, and behavior-preserving module boundaries.

### Modified Capabilities

None.

## Impact

- Frontend: `apps/admin-web/src/App.tsx`, route declarations, feature modules, Vite configuration, lazy imports, and production build output.
- Backend: FastAPI app startup configuration, health/runtime initialization, `server/app/agent.py`, assistant services/helpers, and tests around moved assistant behavior.
- Data/media: `data/media`, `media_assets`, media bindings, cleanup scripts, documentation, and admin empty/error states for missing or archived media.
- Operations: GitHub Actions or equivalent CI entry points, validation scripts, production docs, OpenSpec validation, and smoke-test command chains.
- Compatibility: No breaking API, route, permission, question-bank, RAG evidence, knowledge-framework, or database contract changes are intended.

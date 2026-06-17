## Why

The second production hardening pass made the platform rebuildable, documented, and much easier to validate. The remaining risks are now narrower engineering-quality issues: frontend deprecation warnings, one browser-smoke 404, repeatable e2e coverage, and continued assistant module maintainability.

This change captures the third quality pass so the remaining work is not dependent on chat memory and can be implemented without changing product behavior or protected chemistry resources.

## What Changes

- Remove known Ant Design 6 deprecation warnings from representative admin pages while keeping UI behavior equivalent.
- Diagnose and fix the generic 404 observed during browser smoke, or document it precisely if it is harmless local-only behavior.
- Add a repeatable Playwright e2e smoke script that covers authenticated admin navigation for overview, videos, learning assistant, question banks, and analytics.
- Integrate e2e smoke into local validation as an explicit opt-in stage so it does not slow normal validation or unexpectedly require a running browser/runtime.
- Continue behavior-preserving assistant modularization, shrinking `server/app/agent.py` by moving stable endpoint/runtime helpers into focused service modules.
- Reassess media archive/tombstone needs and add a future `014_...` migration only if the implementation truly requires schema support.
- Keep protected question bank, knowledge framework, experiment point, canonical chunk, embedding, and evidence-binding resources unchanged.

## Capabilities

### New Capabilities

- `production-engineering-quality`: Defines third-pass engineering quality requirements for warning-free representative admin pages, repeatable e2e smoke, diagnosed browser-smoke failures, behavior-preserving assistant modularization, and safe media lifecycle follow-through.

### Modified Capabilities

None.

## Impact

- Frontend: Ant Design component props, static assets, Vite/dev-server smoke behavior, `apps/admin-web` scripts, and optional Playwright e2e support.
- Backend: learning assistant service boundaries, tests for moved assistant behavior, and optional smoke-test bootstrap usage.
- Validation: `scripts/validate_production_readiness.py`, e2e smoke scripts, OpenSpec notes, and final verification docs.
- Operations: local smoke account handling remains local-only; GitHub Actions stays manual-only via `workflow_dispatch`.
- Compatibility: No breaking API, route, permission, database, question-bank, RAG evidence, knowledge-framework, or protected resource changes are intended.

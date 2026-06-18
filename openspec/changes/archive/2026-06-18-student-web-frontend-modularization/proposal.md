## Why

The student H5 frontend has just absorbed a large mobile-app-shell refactor (`d0998a1 Add student bottom tab navigation shell`) and now concentrates almost every student experience inside `apps/student-web/src/App.tsx` and `styles.css`. This makes future student-side work risky: adding or adjusting one small surface can accidentally cross login, learning, periodic-table, experiments, assistant, feedback, or assessment behavior.

This change proposes a behavior-preserving modularization of the student frontend so future product work can land in clear feature areas without losing the newly completed bottom-tab, full-page assistant, profile feedback, and mobile QA context.

## What Changes

- Split the monolithic student H5 frontend into feature-oriented modules while preserving the current React + Vite H5 deployment model.
- Establish stable module ownership for app shell/routing, auth/onboarding, learning, periodic table, experiments, assistant, feedback, assessment, and shared mobile primitives.
- Move student-specific pure formatting and domain helpers out of `App.tsx` into named utility modules with focused tests where useful.
- Move feature styles out of the single large `styles.css` into importable, feature-scoped CSS files while preserving existing visual output.
- Keep public behavior, backend contracts, app-config semantics, bottom tab labels, assistant context handoff, feedback submission, and posttest flow unchanged.
- Keep the existing e2e and mobile viewport QA as the safety rail for the refactor, and extend them only where they help prove non-regression.
- Remove or quarantine obsolete floating-overlay primitives only after all authenticated student usage has been proven gone.
- **Non-behavioral:** this change is a maintainability refactor; it MUST NOT introduce a new product feature, new backend endpoint, database migration, or UI redesign.

## Capabilities

### New Capabilities

- `student-web-frontend-maintainability`: Defines student H5 frontend module boundaries, behavior-preserving refactor constraints, CSS organization, shared helper ownership, and verification expectations.

### Modified Capabilities

- None. Existing student H5 behavior requirements are not changing; this change should preserve the completed `student-h5-platform-shell`, `student-h5-mobile-design-system`, `student-h5-learning-experience`, `student-chat-guardrails`, and `ai-access-configuration` behavior.

## Impact

- `apps/student-web/src/App.tsx`: reduce from a monolithic feature host into an application composition/root plus thin shell wiring.
- `apps/student-web/src/styles.css`: reduce from a single all-feature stylesheet into base plus feature-specific style imports.
- `apps/student-web/src/api.ts`: may be split or wrapped into domain API modules only if doing so does not change request paths, payloads, error handling, auth token behavior, or streaming semantics.
- `apps/student-web/src/mobile/primitives.tsx`: clarify which primitives remain shared and whether obsolete floating overlay helpers should be removed, renamed, or kept for future dialog/sheet use.
- `apps/student-web/src/periodic.ts`: keep periodic element data stable; periodic table rendering and chemistry-specific helper logic may move around it.
- `apps/student-web/src/App.e2e.test.tsx` and `apps/student-web/scripts/mobile-viewport-qa.mjs`: continue to verify login/pretest gates, bottom tabs, learning flow, assistant tab, profile feedback, assessment handoff, disabled feature flags, and common phone viewport behavior.
- OpenSpec context: this proposal builds directly on the completed `student-h5-bottom-tab-navigation` change and must not discard its decisions.

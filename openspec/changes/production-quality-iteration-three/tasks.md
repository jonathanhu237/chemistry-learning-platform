## 1. Baseline And Context Capture

- [x] 1.1 Confirm the branch is clean, aligned with `origin/codex/productionize-admin-platform`, and GitHub production readiness remains manual-only.
- [x] 1.2 Run or inspect the current production-readiness baseline without e2e to confirm protected resources, tests, and builds start green.
- [x] 1.3 Capture the current browser-smoke warning and 404 surface with request-level diagnostics.
- [x] 1.4 Commit the OpenSpec proposal, design, specs, and task list before implementation begins.

## 2. Frontend Warning And 404 Cleanup

- [x] 2.1 Locate all call sites that emit known Ant Design 6 deprecation warnings: `Space.direction`, `Tooltip.overlayClassName`, `Alert.message`, `Spin.tip`, and `Drawer.width`.
- [x] 2.2 Update those call sites to the current Ant Design props while preserving layout and behavior.
- [x] 2.3 Diagnose the browser-smoke 404 request by URL, method, status, and owning page.
- [x] 2.4 Fix the 404 if it is caused by a missing committed static asset, bad public path, missing favicon, thumbnail URL, or broken route.
- [x] 2.5 Run frontend typecheck, tests, build, and browser smoke to confirm representative pages load without the known deprecation warnings.

## 3. Repeatable E2E Smoke

- [x] 3.1 Add a committed e2e smoke script that authenticates with a local-only admin and visits `/admin/overview`, `/admin/videos`, `/admin/learning-assistant`, `/admin/question-banks`, and `/admin/analytics`.
- [x] 3.2 Make the e2e script report console warnings/errors, page errors, failed requests, 404s, login redirects, text length, and route-specific counters.
- [x] 3.3 Add a package script or root script entry for running e2e smoke without changing normal frontend test behavior.
- [x] 3.4 Add an explicit opt-in e2e flag to `scripts/validate_production_readiness.py`; default validation must not require a running browser or frontend server.
- [x] 3.5 Document local e2e prerequisites and smoke admin handling in production operations docs.

## 4. Assistant Module Quality

- [x] 4.1 Map remaining `server/app/agent.py` sections after the second-pass extraction and identify one low-risk behavior-preserving slice to move.
- [x] 4.2 Add or extend assistant characterization tests for the selected slice before moving it.
- [x] 4.3 Move the selected helpers or endpoint facade code into a focused service module while preserving existing imports and response schemas.
- [x] 4.4 Run assistant-focused tests and full backend tests after extraction.

## 5. Media Lifecycle Follow-Through

- [ ] 5.1 Reassess whether archive/tombstone behavior requires durable schema support beyond the current dry-run and missing-file summaries.
- [ ] 5.2 If no schema change is required, document the decision and avoid adding a migration.
- [ ] 5.3 If schema support is required, add the next migration as `014_...` or later without touching existing migrations.
- [ ] 5.4 Run media lifecycle tests and dry-run cleanup after any media-related changes.

## 6. Final Validation And Handoff

- [ ] 6.1 Run protected resource validation and OpenSpec strict validation for `production-quality-iteration-three`.
- [ ] 6.2 Run backend import smoke, assistant-focused tests, and full backend tests.
- [ ] 6.3 Run frontend typecheck, frontend tests, production build, and build chunk report.
- [ ] 6.4 Run Docker backend/BGE health checks if runtime-impacting backend changes were made.
- [ ] 6.5 Run authenticated API smoke and the committed e2e browser smoke.
- [ ] 6.6 Update final notes with completed work, validation results, and any remaining known risks.
- [ ] 6.7 Commit coherent phases and push `codex/productionize-admin-platform`.

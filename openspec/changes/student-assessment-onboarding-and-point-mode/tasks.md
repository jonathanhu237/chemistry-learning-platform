## 1. Backend APIs and Domain

- [x] 1.1 Extend assessment schemas to include `assessment_mode = "point"` and a student assessment status response.
- [x] 1.2 Add status and baseline-prompt dismissal backend functions and routes.
- [x] 1.3 Add point-assessment start request/route and point-scoped composition logic.
- [x] 1.4 Ensure point assessment reuses existing open sessions and rejects zero-question points without creating sessions.

## 2. Student H5 Runtime

- [x] 2.1 Add student API client methods and types for assessment status, baseline dismissal, and point assessment start.
- [x] 2.2 Add H5 shell baseline/open-assessment prompt behavior with persisted dismissal.
- [x] 2.3 Change point detail "测一测" to start point assessment with the current `point_node_id`.
- [x] 2.4 Show a clear message when point entry continues an existing open assessment instead of creating a point paper.

## 3. Tests and Verification

- [x] 3.1 Add backend coverage for status, dismissal, point assessment composition, open-session reuse, and zero-question rejection.
- [x] 3.2 Add student H5 e2e coverage for baseline prompt behavior and point-scoped assessment entry.
- [x] 3.3 Run OpenSpec validation and relevant backend/frontend tests.
- [x] 3.4 Inspect the implemented UI flow in browser preview and iterate until the experience is acceptable.

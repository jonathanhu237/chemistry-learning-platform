## 1. OpenSpec And Baseline

- [x] 1.1 Confirm branch cleanliness and current remote alignment.
- [x] 1.2 Record the current `server/app/admin.py` endpoint groups, existing router structure, service reuse candidates, and validation constraints.
- [x] 1.3 Create proposal, design, specs, tasks, and baseline artifacts for `remove-monolithic-admin-router`.
- [x] 1.4 Run strict OpenSpec validation for `remove-monolithic-admin-router`.
- [x] 1.5 Commit the OpenSpec artifacts before implementation begins.

## 2. Contract Guardrails

- [ ] 2.1 Add route-registration tests for every path/method currently owned by `server/app/admin.py`.
- [ ] 2.2 Ensure route tests assert moved admin path/method pairs are registered exactly once.
- [ ] 2.3 Ensure route tests cover media binding compatibility aliases.
- [ ] 2.4 Add or update tests that prove `server.app.admin_main` no longer imports the monolithic admin endpoint owner after the split.

## 3. Low-Risk Router Extraction

- [ ] 3.1 Move platform settings and AI configuration endpoints to `server/app/routers/admin_platform.py`.
- [ ] 3.2 Move curriculum version and review item endpoints to `server/app/routers/admin_curriculum_review.py`.
- [ ] 3.3 Update `server/app/admin_main.py` router includes for the moved low-risk groups.
- [ ] 3.4 Run focused backend tests and route-registration tests.

## 4. Learning Assistant And Media Extraction

- [ ] 4.1 Move learning assistant runtime, RAG asset listing, ask, and ask stream endpoints to `server/app/routers/admin_learning_assistant.py`.
- [ ] 4.2 Preserve assistant request/response schemas, SSE event formatting, runtime payload shape, and RAG asset fallback behavior.
- [ ] 4.3 Move media asset, upload, duplicate candidate, file/stream/thumbnail, retry, replace, and binding endpoints to `server/app/routers/admin_media.py`.
- [ ] 4.4 Preserve all media compatibility aliases and existing media service calls.
- [ ] 4.5 Run assistant-focused tests, media lifecycle tests, backend tests, and route-registration tests.

## 5. Feedback And Class/Roster Extraction

- [ ] 5.1 Move feedback summary/list/detail/update endpoints to `server/app/routers/admin_feedback.py`.
- [ ] 5.2 Extract feedback database filtering, counting, and update behavior into `server/app/services/feedback_service.py` or equivalent focused service.
- [ ] 5.3 Move class, teacher assignment, registration settings, roster import, student CRUD, and password reset endpoints to `server/app/routers/admin_classes.py`.
- [ ] 5.4 Extract class/registration/roster database-heavy behavior into `server/app/services/class_roster_service.py` or equivalent focused service.
- [ ] 5.5 Run focused route tests and full backend tests.

## 6. Monolith Removal And Documentation

- [ ] 6.1 Remove `server.app.admin` from production app imports and router registration.
- [ ] 6.2 Delete `server/app/admin.py` when no imports remain.
- [ ] 6.3 Update backend split/owner documentation with the final admin owner map and accepted compatibility aliases.
- [ ] 6.4 Confirm protected chemistry resources, seed manifests, and CI workflow trigger posture were not changed.

## 7. Final Validation And Handoff

- [ ] 7.1 Run `openspec validate remove-monolithic-admin-router --strict`.
- [ ] 7.2 Run backend tests with `python -m pytest server\tests -q`.
- [ ] 7.3 Run production readiness validation without changing CI triggers.
- [ ] 7.4 Run frontend typecheck/test/build only if imports or generated contracts affect frontend-facing behavior.
- [ ] 7.5 Run opt-in e2e smoke if runtime behavior, route boundaries, or app startup changed enough to warrant browser verification.
- [ ] 7.6 Write final verification notes for this OpenSpec change.
- [ ] 7.7 Commit implementation phases coherently and push `codex/productionize-admin-platform`.

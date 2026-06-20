## 1. Specification And Data Model

- [ ] 1.1 Confirm existing assessment, mastery, class settings, and admin settings contracts before implementation.
- [ ] 1.2 Add a migration for smart assessment sessions with strategy snapshots, selected experiments, question ids, mastery snapshots, report payloads, status, and timestamps.
- [ ] 1.3 Add storage for per-class smart assessment strategy overrides while preserving global defaults in platform settings.
- [ ] 1.4 Define Pydantic schemas for smart assessment strategy, start response, public question payload, submit request, report, composition summary, and mastery changes.

## 2. Strategy Resolution And Composition Service

- [ ] 2.1 Implement effective strategy resolution: class override first, global default fallback.
- [ ] 2.2 Implement untested experiment detection using missing mastery rows or `evidence_count = 0`.
- [ ] 2.3 Implement measured experiment ticket calculation from `mastery_score` and weak tendency.
- [ ] 2.4 Implement experiment-first selection with untested quota, measured ticket draw, max questions per experiment, and deterministic session seeding.
- [ ] 2.5 Implement question selection inside selected experiments without exposing answer keys.
- [ ] 2.6 Implement backfill and warning metadata when pools or experiments lack enough published questions.
- [ ] 2.7 Add focused unit tests for strategy resolution, ticket calculation, untested quota, max-per-experiment limits, and backfill behavior.

## 3. Student Smart Assessment API

- [ ] 3.1 Add `POST /api/student/smart-assessment/start` that creates or returns the current in-progress session.
- [ ] 3.2 Add `POST /api/student/smart-assessment/submit` that validates exact submitted question ids, grades answers, and completes the session.
- [ ] 3.3 Persist attempts to `experiment_question_attempts` with `attempt_kind = 'smart_assessment'`.
- [ ] 3.4 Reuse experiment mastery update logic for smart assessment attempts.
- [ ] 3.5 Store report, composition summary, and mastery before/after changes on completed sessions.
- [ ] 3.6 Add backend tests for no-mastery students, mixed mastery students, in-progress reuse, submit validation, and mastery updates.

## 4. Admin Global Defaults

- [ ] 4.1 Extend global platform settings with smart assessment enabled state, question count, untested ratio, weak tendency, and max questions per experiment.
- [ ] 4.2 Update typed admin API clients for the new settings shape.
- [ ] 4.3 Add global smart assessment controls to system settings using teacher-facing labels.
- [ ] 4.4 Add the strategy curve visualization for mastery score to relative draw tickets.
- [ ] 4.5 Add validation so ratios and numeric limits stay within supported ranges.
- [ ] 4.6 Add frontend tests for settings form serialization and validation where existing patterns support it.

## 5. Class Strategy Overrides

- [ ] 5.1 Add class-level API routes to read and update effective smart assessment strategy and class override state.
- [ ] 5.2 Enforce permissions: admins can manage all class overrides; teachers can manage assigned classes only.
- [ ] 5.3 Add smart assessment strategy controls to the selected-class settings modal.
- [ ] 5.4 Show whether a class is inheriting global defaults or using a class override.
- [ ] 5.5 Add a class preview that estimates untested quota and measured experiment draw distribution from current class data.
- [ ] 5.6 Add backend and frontend tests for inheritance, override updates, and permission boundaries.

## 6. Student Assessment UI

- [ ] 6.1 Make the student `测评` root page focus on smart assessment for the first version.
- [ ] 6.2 Add start flow using the new smart assessment API.
- [ ] 6.3 Render smart assessment questions through existing mobile assessment primitives where practical.
- [ ] 6.4 Show a concise composition explanation before or during the paper.
- [ ] 6.5 Render the completed smart assessment report with score, composition summary, mastery changes, and wrong answers.
- [ ] 6.6 Preserve bottom-tab and detail-route navigation behavior.

## 7. Validation

- [ ] 7.1 Run backend tests covering assessment, mastery, and class strategy permissions.
- [ ] 7.2 Run admin frontend typecheck/tests for settings and class pages.
- [ ] 7.3 Run student frontend typecheck/tests for assessment flow.
- [ ] 7.4 Run student H5 mobile QA for the assessment page and report.
- [ ] 7.5 Run `openspec validate student-smart-assessment-composition --strict`.
- [ ] 7.6 Run `git diff --check`.

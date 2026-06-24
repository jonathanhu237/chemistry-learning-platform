## 1. Specification And Data Model

- [x] 1.1 Confirm existing assessment, mastery, class settings, and admin settings contracts before implementation.
- [x] 1.2 Add or adjust storage for `student_point_mastery` keyed by `student_id + point_node_id`, including BKT probability, score, evidence count, class id, experiment id, canonical point id, metadata, and timestamps.
- [x] 1.2a Add a migration for smart assessment sessions with strategy snapshots, selected experiments, selected point nodes, question ids, point mastery snapshots, report payloads, status, and timestamps.
- [x] 1.2b Add `assessment_mode` to distinguish system-composed smart assessment from student-selected custom assessment.
- [x] 1.3 Add storage for per-class smart assessment strategy overrides while preserving global defaults in platform settings.
- [x] 1.3a Extend global and class settings schemas with custom assessment enabled/default question count/max question count/max questions per experiment.
- [x] 1.4 Define Pydantic schemas for smart assessment strategy, custom assessment settings/options/start request, public question payload, submit request, report, point-level composition summary, experiment-derived summaries, and point mastery changes.

## 2. Strategy Resolution And Composition Service

- [x] 2.1 Implement effective strategy resolution: class override first, global default fallback.
- [x] 2.2 Load only published, student-visible, valid point-backed assessment candidates from the full question bank.
- [x] 2.3 Implement untested point detection using missing `student_point_mastery` rows or `evidence_count = 0`.
- [x] 2.4 Implement measured point ticket calculation from point `mastery_score` and weak tendency.
- [x] 2.5 Implement point-first smart selection with untested quota, measured ticket draw, max one question per point by default, max questions per root experiment, and deterministic session seeding.
- [x] 2.6 Implement point-backed question selection without exposing answer keys.
- [x] 2.7 Implement backfill and warning metadata when pools, points, or experiments lack enough published questions.
- [x] 2.8 Add focused unit tests for strategy resolution, ticket calculation, untested point quota, point cap, max-per-experiment limits, and backfill behavior.

## 3. Student Smart Assessment API

- [x] 3.1 Add `POST /api/student/smart-assessment/start` that creates or returns the current in-progress session.
- [x] 3.2 Add `POST /api/student/smart-assessment/submit` that validates exact submitted question ids, grades answers, and completes the session.
- [x] 3.3 Persist attempts to `experiment_question_attempts` with `attempt_kind = 'smart_assessment'`.
- [x] 3.4 Add point mastery BKT update logic for smart assessment attempts, including multi-point questions updating every bound point.
- [x] 3.5 Store report, composition summary, experiment-derived summaries, and point mastery before/after changes on completed sessions.
- [x] 3.6 Add backend tests for no-mastery students, mixed point mastery students, in-progress reuse, submit validation, multi-point updates, and mastery updates.

## 3A. Student Custom Assessment API

- [x] 3A.1 Add `GET /api/student/custom-assessment/options` returning enabled state, question count options, effective custom settings, and selectable root/first-level experiments with eligible point-backed question counts.
- [x] 3A.2 Add `POST /api/student/custom-assessment/start` accepting selected experiment ids and fixed question count.
- [x] 3A.3 Validate selected experiments against the student's visible, published, question-backed root/first-level experiment set.
- [x] 3A.4 Compose custom papers by evenly allocating slots across selected experiments, expanding to descendant points, stable-shuffling within point buckets, and prioritizing point coverage.
- [x] 3A.5 Allow underfilled custom papers with warning metadata, but reject zero-question papers.
- [x] 3A.6 Reuse shared assessment submit/report/point mastery update behavior with `assessment_mode = 'custom'`.
- [x] 3A.7 Enforce one in-progress assessment session across smart and custom modes.
- [x] 3A.8 Add backend tests for options filtering, invalid experiment ids, question count validation, balanced sampling, underfilled warnings, and open-session reuse across modes.

## 4. Admin Global Defaults

- [x] 4.1 Extend global platform settings with smart assessment enabled state, question count, untested point ratio, weak tendency, and max questions per experiment.
- [x] 4.1a Extend global platform settings with custom assessment enabled state, default question count, max question count, and max questions per experiment.
- [x] 4.2 Update typed admin API clients for the new settings shape.
- [x] 4.3 Add global smart and custom assessment controls to system settings using teacher-facing labels.
- [x] 4.4 Add the strategy curve visualization for point mastery score to relative draw tickets.
- [x] 4.5 Add validation so ratios and numeric limits stay within supported ranges.
- [x] 4.6 Add frontend tests for settings form serialization and validation where existing patterns support it.

## 5. Class Strategy Overrides

- [x] 5.1 Add class-level API routes to read and update effective smart assessment strategy and class override state.
- [x] 5.2 Enforce permissions: admins can manage all class overrides; teachers can manage assigned classes only.
- [x] 5.3 Add smart assessment strategy controls and custom assessment controls to the selected-class settings modal.
- [x] 5.4 Show whether a class is inheriting global defaults or using a class override for smart/custom assessment settings.
- [x] 5.5 Add a class preview that estimates untested point quota and measured point draw distribution grouped by experiment from current class data.
- [x] 5.6 Add backend and frontend tests for inheritance, override updates, and permission boundaries.

## 6. Student Assessment UI

- [x] 6.1 Make the student `测评` root page show two separate entry cards: smart assessment first, custom assessment second.
- [x] 6.2 Add start flow using the new smart assessment API.
- [x] 6.3 Render smart assessment questions through existing mobile assessment primitives where practical.
- [x] 6.4 Show a concise composition explanation before or during the paper.
- [x] 6.5 Render the completed smart assessment report with score, composition summary, experiment cards, point mastery changes, and wrong answers.
- [x] 6.6 Preserve bottom-tab and detail-route navigation behavior.
- [x] 6.7 Add `/assessment/custom` selection page with experiment search, multi-select, fixed question-count choices, selected-count summary, and start action.
- [x] 6.8 Hide custom assessment question-count choices above the effective max question count and preselect the effective default.
- [x] 6.9 Show custom underfilled-paper warning when actual generated question count is below requested count.
- [x] 6.10 Keep custom assessment v1 free of weak filters, wrong-answer filters, status filters, and point selection.

## 7. Validation

- [x] 7.1 Run backend tests covering assessment, mastery, and class strategy permissions.
- [x] 7.2 Run admin frontend typecheck/tests for settings and class pages.
- [x] 7.3 Run student frontend typecheck/tests for assessment flow.
- [x] 7.4 Run student H5 mobile QA for the assessment page, custom selection page, session page, and report.
- [x] 7.5 Run `openspec validate student-smart-assessment-composition --strict`.
- [x] 7.6 Run `git diff --check`.

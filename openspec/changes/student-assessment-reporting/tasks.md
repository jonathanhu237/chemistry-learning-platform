## 1. Data Model And Report Domain

- [x] 1.1 Add migration for `student_assessment_reports` with student/class/type/source indexes and snapshot JSON columns.
- [x] 1.2 Add backend schemas for report summaries, report detail, generated report text, prompt settings, and prompt update payloads.
- [x] 1.3 Implement report prompt defaults, supported variables, global settings, class override lookup, validation, and restore-default behavior.
- [x] 1.4 Implement report snapshot builders for pretest, smart, custom, and point assessments.
- [x] 1.5 Implement submission-time LLM summary and wrong-answer explanation generation with deterministic fallback persistence.

## 2. Student And Teacher APIs

- [x] 2.1 Update pretest submission to create and return a durable pretest report on final completion.
- [x] 2.2 Update smart/custom/point assessment submission to create and return durable reports.
- [x] 2.3 Add student report list and detail endpoints authorized to the current student.
- [x] 2.4 Add teacher report list/detail access for students in accessible classes.
- [x] 2.5 Add admin/global and class-level report prompt settings endpoints following existing permission boundaries.

## 3. Student H5 UI

- [x] 3.1 Update student API types and assessment completion navigation to use persisted report ids.
- [x] 3.2 Replace session-storage-only report detail with backend-loaded durable report detail.
- [x] 3.3 Add `我的` report entry, full report list page, and report detail route.
- [x] 3.4 Adjust report UI to support pretest, smart, custom, and point reports with unified structure.

## 4. Teacher Console UI

- [x] 4.1 Add report history and detail access to the teacher student analytics/report surface.
- [x] 4.2 Render teacher report detail as structured-first with generated summary/explanation folded or secondary by default.
- [x] 4.3 Add global report prompt settings UI in system settings with defaults, supported variables, validation, and restore defaults.
- [x] 4.4 Add class-level report prompt override UI in class settings with inherited/override state and restore inheritance.

## 5. Tests And Verification

- [x] 5.1 Add backend tests for report creation across pretest, smart, custom, and point assessment flows, including LLM fallback.
- [x] 5.2 Add backend tests for report list/detail authorization and prompt inheritance/override behavior.
- [x] 5.3 Add student H5 e2e tests for completing assessment, opening durable report detail, and viewing report history from `我的`.
- [x] 5.4 Add teacher console tests for report visibility and prompt settings UI.
- [x] 5.5 Run typechecks and relevant backend/frontend test suites.
- [x] 5.6 Start local apps, inspect student and teacher report UI in browser, and adjust visual issues before delivery.

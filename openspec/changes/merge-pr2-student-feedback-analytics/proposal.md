## Why

PR #2 (`[codex] Add student page feedback`) was built on the old `main` before the student H5 learning surface became a current-family, two-tab chapter experience. The PR is valuable, but a direct merge would reintroduce old student-page assumptions, duplicate the student feedback endpoint, and risk losing the new H5 route, feedback-overlay, and chapter experiment grouping contracts now on `main`.

This change makes the merge explicit and reproducible: `main` remains the source of truth for the student H5 architecture, while PR #2 contributes analytics, experiment mastery, feedback attachment, Markdown rendering, tests, and migrations in a controlled integration.

## What Changes

- Integrate PR #2's teacher analytics enhancements:
  - experiment mastery dashboard data,
  - experiment-family grouping,
  - student report drilldowns,
  - posttest report detail display,
  - class analytics export refinements.
- Integrate PR #2's experiment mastery persistence:
  - add the `student_experiment_mastery` persistence model,
  - update pretest and posttest submissions to update experiment-level mastery,
  - use experiment mastery as an optional recommendation signal without breaking seed-backed H5 chapter selection.
- Integrate PR #2's feedback attachment support:
  - add image attachment storage and metadata,
  - expose attachment counts and attachment details in admin feedback workflows,
  - allow authenticated students to submit one optional screenshot from the existing H5 feedback entry.
- Preserve the current `main` student H5 architecture:
  - keep the periodic-table entry,
  - keep current-family chapter pages,
  - keep facts/experiments segmented views,
  - keep chapter experiment grouping by parent experiment and point,
  - keep the existing `StudentFeedbackFab` overlay governance.
- Resolve route/API conflicts deliberately:
  - do not mount two separate `POST /api/student/feedback` handlers,
  - keep `/api/student/app-config`,
  - keep authenticated identity derivation and feature-flag rejection,
  - extend the existing student feedback contract to support multipart attachments.
- Add PR #2's student-web test setup and Markdown/LaTeX rendering where it complements current H5 flows without replacing mobile primitives.
- Add integration verification so future work can prove that analytics, feedback attachment, H5 chapter learning, assessment, and mobile QA all survived the merge.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `student-h5-learning-experience`: student feedback gains optional screenshot attachment support while preserving authenticated identity, feature flags, and the current H5 chapter/point context contract.
- `student-h5-mobile-design-system`: the existing mobile feedback overlay must absorb attachment controls without creating a second floating feedback widget or overlapping AI, finish actions, segmented switchers, or point cards.
- `student-h5-assessment-flow`: pretest and posttest completion must update experiment-level mastery and preserve report data used by student and teacher review.
- `class-learning-analytics`: teacher analytics must support experiment mastery, experiment-family grouping, student report drilldowns, and feedback attachment visibility.
- `assistant-chem-latex-rendering`: student-facing posttest summaries and mistake explanations rendered in the H5 report must use the math-capable Markdown renderer when AI/fallback content contains chemistry notation.

## Impact

- Student frontend:
  - `apps/student-web/package.json`
  - `apps/student-web/package-lock.json`
  - `apps/student-web/vite.config.ts`
  - `apps/student-web/src/App.tsx`
  - `apps/student-web/src/api.ts`
  - `apps/student-web/src/styles.css`
  - `apps/student-web/src/components/AiMarkdown.tsx`
  - optional adaptation of PR #2's `PageFeedback` logic into the existing `StudentFeedbackFab`
  - `apps/student-web/src/App.e2e.test.tsx`
- Admin frontend:
  - `apps/admin-web/src/api/index.ts`
  - `apps/admin-web/src/features/analytics/AnalyticsPage.tsx`
  - `apps/admin-web/src/features/feedback/FeedbackPage.tsx`
  - `apps/admin-web/src/features/feedback/feedback.css`
  - `apps/admin-web/src/styles.css`
- Backend:
  - `server/app/admin_main.py`
  - `server/app/feedback.py`
  - `server/app/mastery.py`
  - `server/app/routers/admin_feedback.py`
  - `server/app/routers/student_platform.py`
  - `server/app/services/analytics_service.py`
  - `server/app/services/experiment_mastery_service.py`
  - `server/app/services/feedback_service.py`
  - `server/app/services/student_learning_service.py`
  - `server/app/services/student_pretest_service.py`
  - `server/app/services/student_posttest_service.py`
  - `server/app/student_app_schemas.py`
  - `server/app/student_posttest_schemas.py`
  - `server/app/schemas.py`
- Database migrations:
  - `server/migrations/017_student_experiment_mastery.sql`
  - `server/migrations/018_feedback_attachments.sql`
- Tests and validation:
  - backend analytics, assessment, feedback, and router tests,
  - student-web typecheck/build/tests,
  - production resource validation,
  - mobile viewport QA for 360x780, 390x844, and 430x932.

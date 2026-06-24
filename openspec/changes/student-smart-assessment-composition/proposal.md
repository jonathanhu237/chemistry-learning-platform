## Why

The student H5 `测评` tab currently behaves like a thin post-learning entry: it can start the existing posttest flow, but the backend only creates a paper when the student has learning activity after the previous posttest. This does not support the product goal that students can enter the assessment page directly and receive a useful diagnostic paper.

The assessment product model now treats catalog point nodes as the smallest diagnostic unit. Students and teachers still reason about "experiments" through the catalog root/first-level entries, but mastery evidence, smart composition, and report attribution need to be point-level so the system can diagnose the actual weak locations instead of collapsing an entire experiment into one score.

## What Changes

- Add a student smart assessment capability that starts directly from the student H5 `测评` page.
- Add a separate student custom assessment capability where students choose experiments and question count themselves.
- Create a dedicated smart-assessment session concept instead of overloading the existing posttest session.
- Compose smart papers from all published, point-backed questions in the full question bank; students do not choose a smart-assessment range.
- Store and update mastery by `student_id + point_node_id`; derive experiment mastery for display by aggregating descendant point mastery.
- Treat untested points as a separate pool, not as fake 50-point mastery.
- Let admins define global default composition settings and let teachers override them per class.
- Let teachers configure total question count, untested-point ratio, weak-mastery tendency, and maximum questions per first-level experiment; composition MUST NOT hard-code the ratio.
- Keep the measured-point strategy explainable through an admin strategy curve showing mastery score to relative draw tickets.
- Show a class preview that estimates the paper source distribution under the current point-level strategy.
- Show students a concise composition explanation and post-submit point mastery changes grouped by experiment.
- Keep custom assessment v1 intentionally simple: experiment search, experiment multi-select, fixed question-count options, experiment-balanced allocation, and point-coverage-first sampling inside selected experiments.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-assessment-flow`: add the smart assessment session lifecycle, point-level composition strategy, report, and mastery update behavior.
- `student-h5-assessment-flow`: add custom assessment options/start behavior as a separate student-selected assessment mode.
- `class-roster-management`: add per-class smart assessment strategy overrides owned by admins and assigned teachers.
- `class-roster-management`: add per-class custom assessment availability and question-count boundaries.
- `react-ant-design-admin-console`: add explainable smart-assessment controls, custom-assessment controls, and preview visualizations to admin settings/class settings.

## Impact

- `server/app/domains/assessments/*`: add a smart assessment domain service that composes by point mastery and persists session strategy snapshots.
- `server/app/api/student/*`: add smart-assessment start/submit endpoints for students.
- `server/app/api/student/*`: add custom-assessment options/start endpoints for students while reusing the shared submit/report path.
- Database migrations: add assessment sessions, point mastery storage, and class-level strategy override storage, while reusing `experiment_question_attempts` for graded attempts where practical.
- `apps/student-web/src/routes/assessment/*`: make the assessment page present smart assessment and custom assessment as separate entry cards.
- `apps/admin-web/src/features/settings/SettingsPage.tsx`: expose global smart assessment defaults.
- `apps/admin-web/src/features/classes/ClassesPage.tsx`: expose per-class smart assessment overrides.
- `apps/admin-web`: use existing `@ant-design/plots` charting for strategy curve and preview visualizations.

## Non-Goals

- Do not add a parallel "learning posttest" product surface in this first version.
- Do not add专项练习,错题本, custom weak-point shortcuts, custom status filters, or student-facing point selection.
- Do not let custom assessment v1 select by point, wrong-answer set, or mastery threshold.
- Do not use whether a student has opened or viewed an experiment as a composition criterion.
- Do not expose internal formulas as required teacher knowledge; formulas exist to drive explainable previews.
- Do not preserve `student_experiment_mastery` as a long-term fact source; this pre-release change may migrate or replace it with point-level mastery.

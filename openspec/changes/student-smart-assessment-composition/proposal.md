## Why

The student H5 `测评` tab currently behaves like a thin post-learning entry: it can start the existing posttest flow, but the backend only creates a paper when the student has learning activity after the previous posttest. This does not support the product goal that students can enter the assessment page directly and receive a useful diagnostic paper.

The platform already stores experiment-level mastery in `student_experiment_mastery`, and the experiment question bank is organized around formal experiments. This makes experiment-level intelligent composition the right first version: use experiment mastery to decide which experiments are more likely to appear, let teachers control how much untested content is included, and make the strategy explainable through admin previews and student reports.

## What Changes

- Add a student smart assessment capability that starts directly from the student H5 `测评` page.
- Create a dedicated smart-assessment session concept instead of overloading the existing posttest session.
- Compose papers by first selecting experiments, then selecting questions inside those experiments.
- Treat untested experiments as a separate pool, not as fake 50-point mastery.
- Let admins define global default composition settings and let teachers override them per class.
- Let teachers configure total question count, untested-experiment ratio, weak-mastery tendency, and maximum questions per experiment.
- Show an admin strategy curve that explains how mastery score maps to relative draw tickets.
- Show a class preview that estimates the paper source distribution under the current strategy.
- Show students a concise composition explanation and post-submit mastery changes.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-assessment-flow`: add the smart assessment session lifecycle, composition strategy, report, and mastery update behavior.
- `class-roster-management`: add per-class smart assessment strategy overrides owned by admins and assigned teachers.
- `react-ant-design-admin-console`: add explainable smart-assessment controls and preview visualizations to admin settings/class settings.

## Impact

- `server/app/domains/assessments/*`: add a smart assessment domain service that composes by experiment mastery and persists session strategy snapshots.
- `server/app/api/student/*`: add smart-assessment start/submit endpoints for students.
- Database migrations: add smart-assessment sessions and class-level strategy override storage, while reusing `experiment_question_attempts` for graded attempts.
- `apps/student-web/src/routes/assessment/*`: make the assessment page's first version focus on smart assessment rather than adding multiple assessment modes.
- `apps/admin-web/src/features/settings/SettingsPage.tsx`: expose global smart assessment defaults.
- `apps/admin-web/src/features/classes/ClassesPage.tsx`: expose per-class smart assessment overrides.
- `apps/admin-web`: use existing `@ant-design/plots` charting for strategy curve and preview visualizations.

## Non-Goals

- Do not add a parallel "learning posttest" product surface in this first version.
- Do not add专项练习,错题本, or knowledge-point-level smart composition.
- Do not use whether a student has opened or viewed an experiment as a composition criterion.
- Do not expose internal formulas as required teacher knowledge; formulas exist to drive explainable previews.

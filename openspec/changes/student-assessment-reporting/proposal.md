## Why

Student assessments currently produce partial, session-local reports: smart/custom/point reports are displayed from browser session storage, pretest completion has no report surface, and AI summary generation is tied to the legacy posttest path. Students and teachers need a durable, shared report record for pretest, custom assessment, smart assessment, and point assessment, with prompt-governed LLM summaries generated at submission time.

## What Changes

- Add a unified assessment report record for student assessment completions, covering `pretest`, `custom`, `smart`, and `point` report types.
- Generate a fixed report snapshot when an assessment is submitted, including score, correctness, mastery changes, involved experiments/points, wrong answers, LLM summary, and LLM wrong-answer explanation.
- Persist LLM-generated report summary and wrong-answer explanation so historical reports reuse the saved result.
- Treat LLM failures as non-blocking: assessment submission remains successful and a deterministic fallback report text is saved.
- Add student-facing report history under `我的`, with a full report list and report detail page that no longer depends on browser session storage.
- Expose the same report snapshots in the teacher console, with structured results first and generated text available in a folded/secondary section.
- Add teacher-console report-generation prompt settings with default prompts, fixed template variables, global defaults, and class-level overrides.

## Capabilities

### New Capabilities
- `student-assessment-reporting`: Durable student assessment reports, report history/detail surfaces, teacher visibility, and report prompt behavior.

### Modified Capabilities
- `student-h5-assessment-flow`: Assessment submissions must create unified report snapshots and return/route to durable report detail.
- `class-learning-analytics`: Teacher-facing student reports must include durable assessment reports.
- `ai-access-configuration`: System settings must include report-generation prompt configuration with feature ownership separate from runtime monitoring.

## Impact

- Backend: assessment submission domains, student report APIs, teacher report/analytics APIs, report-generation prompt settings, migrations, schemas, and tests.
- Student H5: assessment completion navigation, report detail loading, `我的` report entry/list/detail UI, and e2e coverage.
- Teacher console: prompt settings UI, class override UI, student report display, and tests.
- Data: new persistent report storage plus prompt configuration saved with existing platform settings/class settings patterns.

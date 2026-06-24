## Context

Student assessment reporting is split across several paths today. Pretest submission persists attempts and mastery updates but does not expose a report. Posttest reporting has an AI-summary cache path tied to `student_posttest_sessions`. Smart, custom, and point assessments build report JSON at submit time, but the student report page reads that report from browser `sessionStorage`, making history, refresh, cross-device access, and teacher review unreliable.

The product direction is now a durable report system shared by students and teachers. Reports must be generated when assessments are submitted, include LLM-produced summary and wrong-answer explanation when available, fall back deterministically when LLM generation fails, and preserve a fixed snapshot for historical review. Teachers must also be able to configure report-generation prompts globally and per class.

## Goals / Non-Goals

**Goals:**
- Store one durable report record for every completed pretest, custom assessment, smart assessment, and point assessment.
- Generate report summary and wrong-answer explanation during submission and persist the generated or fallback text.
- Use the same report snapshot for student history/detail and teacher review.
- Add configurable report prompts with defaults, global settings, class overrides, two prompt roles, and fixed variables.
- Keep report text neutral enough for both student and teacher audiences.
- Add focused backend, student H5, teacher console, and e2e coverage.

**Non-Goals:**
- Do not add Atom follow-up chat or per-question conversational tutoring from reports.
- Do not add prompt preview/test-generation in the first version.
- Do not regenerate historical reports automatically when prompts, questions, or catalog content change.
- Do not move all assessment session state into the report table; session tables remain the source for in-progress assessment lifecycle.

## Decisions

### Store reports in a unified report table

Create a `student_assessment_reports` read model keyed by report id, student id, class id, report type, and source session id. The source assessment session tables remain responsible for in-progress state and grading, while the report table stores the completed snapshot consumed by students and teachers.

Alternative considered: query and merge `student_pretest_sessions`, `student_posttest_sessions`, and `student_smart_assessment_sessions` on every history/detail request. This keeps fewer tables but spreads prompt cache, report permissions, and history ordering across different schemas. A unified table better matches the product model and makes cross-surface report retrieval stable.

### Generate LLM report text synchronously but non-blockingly for submission success

Assessment submit handlers will grade and persist attempts first, then build the report snapshot, then attempt LLM summary and wrong-answer explanation. If the model is unavailable or errors, the submission still succeeds and the report stores fallback text with source/status metadata.

Alternative considered: open the report page first and generate asynchronously. The user explicitly wants generation at submit time and persisted for reuse, so report retrieval should be read-only in normal use.

### Preserve prompt and report content as a fixed snapshot

The report payload stores the question text, answers, explanations, experiments/points, mastery data, generated text, prompt identity/version metadata, and generation status as they existed at submission time. Historical report detail never changes because a teacher later edits prompts or catalog content.

Alternative considered: always render reports from current question/catalog/prompt data. That risks historical drift and makes teacher/student references unstable.

### Put prompt configuration in settings and class settings surfaces

Global report prompts belong with system settings because they are AI feature behavior, not runtime monitoring. Class prompt overrides belong with class assessment settings because they alter the class's assessment/report policy. The monitoring page remains read-only/diagnostic.

Alternative considered: add a separate prompt-management page. That is heavier than needed and splits assessment strategy controls across too many locations.

### Keep report UI structured-first

Student and teacher detail views show score/correctness, involved experiments/points, mastery movement, and wrong answers before generated text. Teacher UI folds generated summary/explanation by default. Student UI may show generated text inline because the report is the primary destination after submission.

Alternative considered: make LLM text the primary report body. That would hide measurable assessment facts and make teacher scanning worse.

## Risks / Trade-offs

- LLM generation can slow assessment submission -> keep prompts short, cap output length, catch all generation errors, and save deterministic fallback text.
- Prompt customization can produce poor or unsafe text -> allow only fixed variables, keep backend-owned structural context, and preserve fallback generation.
- New report table can diverge from source sessions -> write the report in the same submission transaction scope where practical, include source session id/type, and add tests for every report type.
- Teacher access can expose another student's report -> enforce existing class/student access checks on every teacher report list/detail endpoint.
- UI can become text-heavy -> make list cards compact, keep detail sections structured, and fold teacher generated text by default.

## Migration Plan

1. Add the unified report table and indexes.
2. Add report prompt defaults to platform settings and optional class override storage.
3. Update assessment submit flows to create reports for new completions.
4. Add student report list/detail APIs and teacher report access.
5. Update student and teacher UI to use report APIs.
6. Keep old session-storage report fallback only where necessary during transition, then stop depending on it.

Rollback is additive: existing assessment sessions and attempts remain intact. If report creation fails unexpectedly during rollout, submission should fail only after grading has not been committed; generated reports can be recreated from source sessions in a later repair script if needed.

## Open Questions

- Whether the legacy `posttest` report path should be listed as a fifth report type if it remains a student-visible flow after this change. The primary committed scope is `pretest`, `custom`, `smart`, and `point`.

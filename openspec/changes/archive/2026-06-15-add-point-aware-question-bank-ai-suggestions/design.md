## Context

The published default bank is now imported from a point-aware artifact. The artifact groups questions by formal experiment and video point, then flattens questions into `experiment_questions` while storing diagnostic metadata in `metadata`. The admin question-bank page already reads this metadata for browsing, but the existing assistant preview is chapter-first and the existing generation path validates only basic question fields, dropping metadata.

## Goals / Non-Goals

**Goals:**

- Make AI suggestions operate from the selected formal experiment, optional selected video point, and existing point-aware question metadata.
- Support both adding new draft questions and repairing an existing question through draft replacement suggestions.
- Preserve metadata through validation, draft storage, and draft publication.
- Expose the workflow in the current question-bank page without direct mutation of published default-bank questions.

**Non-Goals:**

- Do not replace or rewrite the imported default bank automatically.
- Do not add AI semantic grading for student answers.
- Do not implement full enhanced-bank generation in this change.
- Do not remove historical chapter-first endpoints unless they block the new workflow.

## Decisions

### Decision: Persist suggestions as existing question drafts

AI suggestions will reuse `experiment_question_generations` and `experiment_question_drafts`. This keeps suggestions auditable, lets teachers reject or publish them later, and avoids introducing a parallel review table.

Alternative considered: return transient preview-only suggestions. That is simpler but loses lineage and makes teacher review fragile across page refreshes.

### Decision: Preserve point-aware metadata as first-class payload data

The validation and insert paths must carry a `metadata` object. Suggestion payloads include `point_aware_question_bank`, point keys/titles, source audit, option links, coverage tags, quality flags, and review lineage.

Alternative considered: derive metadata again on publish. That risks drift because AI suggestions may intentionally change point bindings or option diagnostics.

### Decision: Use local deterministic fallback when LLM settings are unavailable

The API will attempt configured LLM generation when possible, but it must return usable draft suggestions in local/dev environments. Fallback suggestions should be visibly generic draft material but still valid and point-aware.

Alternative considered: fail when no provider is configured. That makes the UI hard to test and breaks current local workflows.

## Risks / Trade-offs

- AI output may omit required point metadata -> validate and normalize metadata, and keep invalid drafts visible with validation errors.
- Publishing a repair suggestion could coexist with the original question -> mark lineage as a repair suggestion and leave final disable/replace policy explicit.
- Current source refs can be sparse -> include warning text and preserve existing source audit where possible.

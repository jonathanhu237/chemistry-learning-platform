## Why

The current question bank has moved to a point-aware default bank, but the AI assistant paths still assume the older chapter-first question-bank shape. Teachers need AI add and repair suggestions that use the current experiment, video-point bindings, source audit, and option diagnostic metadata without directly mutating published questions.

## What Changes

- Add point-aware AI suggestion behavior for the experiment question-bank page.
- Allow teachers to request new question suggestions for the selected experiment and optional video point.
- Allow teachers to request repair suggestions from an existing point-aware question detail view.
- Persist suggestions as reviewable drafts rather than directly changing the default bank.
- Preserve point-aware metadata in generated drafts and published generated questions, including primary and secondary point keys, source audit, option diagnostic links, coverage tags, and review lineage.
- Keep legacy chapter-first assistant behavior out of the new point-aware question-bank workflow.

## Capabilities

### New Capabilities

- `point-aware-question-bank-ai-suggestions`: Defines AI add/repair suggestions grounded in the current point-aware experiment question bank.

### Modified Capabilities

- `experiment-question-bank-management`: Adds teacher-facing AI suggestion entry points to the point-aware experiment question-bank page while preserving review-before-publication behavior.

## Impact

- Affects admin API request/response contracts for question-bank suggestions and drafts.
- Affects `experiment_questions.metadata` preservation for generated and imported/generated bank rows.
- Affects the admin web question-bank page and TypeScript API types.
- Adds backend and frontend verification for point-aware AI suggestion flows.

## 1. Backend Suggestion Support

- [x] 1.1 Preserve `metadata` in question validation, draft update, insert, and generated draft publication paths.
- [x] 1.2 Add a point-aware suggestion request flow for adding questions to an experiment or repairing an existing question.
- [x] 1.3 Build suggestion context from formal experiment data, selected point metadata, current question metadata, and source refs.
- [x] 1.4 Ensure local fallback suggestions are valid objective drafts with point-aware metadata.

## 2. Frontend Question-Bank Workflow

- [x] 2.1 Extend admin web API types for point-aware suggestion requests, metadata fields, and draft payloads.
- [x] 2.2 Add AI add-suggestion controls to the selected experiment question-bank page.
- [x] 2.3 Add AI repair-suggestion controls to the question detail modal.
- [x] 2.4 Show returned suggestion drafts with validation errors, point metadata, and publish/reject actions.

## 3. Verification

- [x] 3.1 Add or update backend tests covering metadata preservation and point-aware suggestion draft creation.
- [x] 3.2 Run backend tests for point-aware question-bank behavior.
- [x] 3.3 Run admin web typecheck/build.
- [x] 3.4 Run `openspec validate add-point-aware-question-bank-ai-suggestions --strict`.

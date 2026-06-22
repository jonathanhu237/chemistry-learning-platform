## 1. Status And Preview Semantics

- [x] 1.1 Tighten backend catalog point status so `student_available` requires both placement and shared content publication.
- [x] 1.2 Allow teacher preview token/detail reads for renderable draft or unpublished points while preserving archived shared-content protection.
- [x] 1.3 Add or update focused tests for status availability and preview behavior.

## 2. Header Action Hierarchy

- [x] 2.1 Add a frontend helper that derives the selected-point primary action from resolved status, shared content state, video readiness, and visibility.
- [x] 2.2 Refactor `CatalogEditorHeader` so preview, diagnostics, unpublish, and archive live in `更多`, with at most one primary state action.
- [x] 2.3 Add header title edit affordance that updates point title as selected-point identity and keeps existing form/save compatibility.

## 3. Content Tab Hierarchy

- [x] 3.1 Remove shared-experiment identity copy and visible point title from the routine content form body.
- [x] 3.2 Rename/normalize the content section heading and field visual weight for teacher note, principle, phenomenon explanation, and safety note.
- [x] 3.3 Adjust CSS for the calmer header/menu/content hierarchy without changing unrelated panels.

## 4. Validation

- [x] 4.1 Update frontend contracts/tests for the new header/content semantics.
- [x] 4.2 Run focused frontend/backend tests and OpenSpec validation.

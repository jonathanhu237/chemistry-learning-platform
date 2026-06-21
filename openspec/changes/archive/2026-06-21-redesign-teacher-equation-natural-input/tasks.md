## 1. OpenSpec And Baseline

- [x] 1.1 Run `openspec validate redesign-teacher-equation-natural-input --strict` before implementation.
- [x] 1.2 Review the existing completed equation UI change and decide whether to replace or supersede its component structure.
- [x] 1.3 Capture current dirty worktree state and avoid mixing unrelated video-library or seed changes into this implementation.

## 2. Backend Natural Equation Normalization

- [x] 2.1 Add deterministic token cleanup for arrows, equals signs, missing spaces, and Unicode reaction symbols.
- [x] 2.2 Add periodic-table based element casing canonicalization for likely formulas such as `CL2`, `h2`, and `hcl`.
- [x] 2.3 Add a first-pass high-school chemistry alias dictionary for common Chinese substance names.
- [x] 2.4 Return correction diagnostics and teacher-readable Chinese warnings without silently rewriting raw input.
- [x] 2.5 Add simple inorganic reaction balancing suggestions where coefficients can be inferred safely.
- [x] 2.6 Ensure invalid or uncertain rows do not emit misleading AI/ES/RAG derived fields.

## 3. Preview And Suggestion API Contract

- [x] 3.1 Extend the equation preview response schema with suggestion/correction metadata while preserving existing normalized row fields.
- [x] 3.2 Support previewing multiline text by splitting non-empty lines into ordered raw row inputs.
- [x] 3.3 Keep save behavior backend-authoritative by normalizing current raw rows on save rather than persisting frontend preview objects.
- [x] 3.4 Add backend tests for loose casing, no-space input, Chinese aliases, equals-as-arrow, imbalance suggestions, and invalid rows.

## 4. Explicit AI Assistance

- [x] 4.1 Define API/service contract for AI equation assistance using point title, catalog path, phenomenon explanation, safety note, and current raw equations.
- [x] 4.2 Implement AI assistance as draft candidates only; candidates must not directly save point content.
- [x] 4.3 Add provider-unavailable behavior so deterministic authoring still works without AI.
- [x] 4.4 Add tests for AI draft acceptance boundaries and unavailable-provider behavior where feasible.

## 5. Teacher Natural Input UI

- [x] 5.1 Replace per-row equation input cards with one primary multiline reaction text area.
- [x] 5.2 Hydrate the multiline input from existing stored raw equation rows in display order.
- [x] 5.3 Add debounced preview requests and ignore stale preview responses.
- [x] 5.4 Render compact "系统理解为" preview rows below the text area in the same order as input lines.
- [x] 5.5 Add explicit "采用" actions for corrected or balanced suggestions.
- [x] 5.6 Move chemistry symbols/snippets out of the main workflow or remove them if they are not clearly helpful.
- [x] 5.7 Add explicit AI actions such as "AI 修正" and "AI 生成反应式" only when provider state allows.
- [x] 5.8 Ensure the text-principle path and non-equation content fields remain unchanged.

## 6. Frontend Tests And Polish

- [x] 6.1 Update catalog tree contract tests for natural multiline input labels and removal of symbol-picker-first workflow.
- [x] 6.2 Add frontend tests or component-level coverage for debounced preview, stale response handling, and suggestion acceptance where practical.
- [x] 6.3 Verify UI text is fully Chinese and teacher-facing; no backend-centric labels appear in the main workflow.
- [x] 6.4 Verify compact desktop layout and mobile/narrow viewport behavior for the multiline editor and preview rows.

## 7. Validation And Build

- [x] 7.1 Run targeted backend equation tests.
- [x] 7.2 Run targeted teacher frontend tests.
- [x] 7.3 Run `web-teacher` typecheck and build.
- [x] 7.4 Run final `openspec validate redesign-teacher-equation-natural-input --strict`.
- [x] 7.5 Rebuild and restart `web-teacher` Docker service for user testing if implementation is requested.

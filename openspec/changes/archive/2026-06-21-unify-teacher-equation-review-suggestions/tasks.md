## 1. Contracts And Review Model

- [x] 1.1 Extend equation assist response schemas/types to expose normalized candidate display fields, source, row order, status, replacement text, and rationale.
- [x] 1.2 Define a frontend review model that merges preview rows, deterministic suggestions, and AI candidates by row order.
- [x] 1.3 Add contract tests for row-attached AI candidates, unmatched supplemental candidates, and duplicate parser/AI candidate merging.

## 2. Backend Candidate Normalization

- [x] 2.1 Normalize AI draft text through the existing reaction equation parser before returning it from the assist endpoint.
- [x] 2.2 Filter non-normalizable AI drafts out of adoptable results while preserving deterministic parser fallback behavior.
- [x] 2.3 Preserve row-order attachment for AI corrections and mark unmatched generated candidates as supplemental.
- [x] 2.4 Add backend tests covering valid AI candidates, invalid AI candidates, AI unavailable fallback, and row-order candidate replacement.

## 3. Frontend Row-Centered Suggestions

- [x] 3.1 Replace the separate AI suggestion block with per-row candidate rendering inside the existing reaction preview panel.
- [x] 3.2 Render adoptable candidates with the chemistry renderer using normalized display fields rather than showing raw draft text as the main content.
- [x] 3.3 Show merged source labels such as `系统校对`, `AI 校对`, and `系统 + AI` after de-duplication.
- [x] 3.4 Keep raw text, formula tokens, parser warnings, and AI rationale in compact secondary details.

## 4. AI Actions And Adoption Flow

- [x] 4.1 Replace separate AI fix/generate semantics with one contextual primary action: `AI 校对全部` when input exists and `AI 生成候选` when input is empty.
- [x] 4.2 Add row-local AI assistance for invalid, warning, or needs-confirmation rows without moving the action away from the row.
- [x] 4.3 Update candidate adoption so row-attached candidates replace the row, supplemental candidates append a row, and preview re-runs immediately.
- [x] 4.4 Ensure accepting a candidate does not save, publish, index, or expose student content outside the normal save flow.

## 5. Visual Polish And Accessibility

- [x] 5.1 Compact the review panel so rendered equations and statuses are the primary visual hierarchy.
- [x] 5.2 Remove text-heavy AI/system prompt cards that duplicate row-level meaning.
- [x] 5.3 Verify desktop and narrow viewport layouts keep row actions adjacent and avoid overlap.
- [x] 5.4 Keep all visible teacher-facing copy in Chinese.

## 6. Validation

- [x] 6.1 Run backend equation tests for parser, preview, assist, and save behavior.
- [x] 6.2 Run frontend catalog-tree tests and typecheck.
- [x] 6.3 Run the web-teacher build.
- [x] 6.4 Run `openspec validate unify-teacher-equation-review-suggestions --strict`.

## 1. Parser and Normalization

- [x] 1.1 Add a reaction-line splitter that separates `equation_core` and `annotation_text` at the first `//` delimiter while preserving the full `raw_text`.
- [x] 1.2 Update natural multiline preview/save normalization so each non-empty input line remains one reaction row even when it contains `//`.
- [x] 1.3 Normalize Unicode ion charge notation before chemistry token extraction for both equation cores and annotation text.
- [x] 1.4 Derive `annotation_formulae` and `condition_tags` from annotation text without merging them into core `formulae`, `reactants`, or `products`.
- [x] 1.5 Ensure invalid equation cores preserve raw text and annotation text while suppressing misleading core-derived chemistry metadata.

## 2. Persistence and API Contracts

- [x] 2.1 Extend reaction row response/request mapping to expose `equation_core`, `annotation_text`, `annotation_formulae`, and `condition_tags`.
- [x] 2.2 Persist new annotation fields in existing reaction row metadata where possible, without requiring a schema migration unless code inspection proves metadata is insufficient.
- [x] 2.3 Ensure point content hydration rebuilds teacher multiline input from full raw rows including `//` annotation suffixes.
- [x] 2.4 Update preview, save, and student payload serializers so annotation fields round-trip consistently.

## 3. Search, AI, and RAG Consumers

- [x] 3.1 Add annotation text, annotation formulae, and condition tags to ES/search text or metadata for published points.
- [x] 3.2 Update AI and RAG context builders to include annotation data attached to the correct reaction row.
- [x] 3.3 Verify evidence-query and reaction participant hints still use only equation-core reactants/products and core formulae.
- [x] 3.4 Update AI equation assistance prompts/application logic so generated notes use `//` and core-only corrections preserve existing annotation suffixes by default.

## 4. Teacher Editor

- [x] 4.1 Render backend annotation text visibly attached to the same equation card or preview row as its equation core.
- [x] 4.2 Prevent annotation suffixes from appearing as separate invalid reaction candidates in preview/check results.
- [x] 4.3 Preserve annotation suffixes during AI correction acceptance when only the equation core changes.
- [x] 4.4 Update teacher-facing guidance for equation mode so `//` is documented as the way to attach conditions or notes on the same line.

## 5. Student H5 Display

- [x] 5.1 Include annotation text in student point detail payloads for equation-mode principles.
- [x] 5.2 Render annotation text with its corresponding reaction equation in the student H5 point detail view.
- [x] 5.3 Confirm unannotated reactions continue to display without extra annotation UI.

## 6. Verification

- [x] 6.1 Add backend parser tests for annotated rows, unannotated backward compatibility, annotation formula extraction, condition tag extraction, and Unicode charge normalization.
- [x] 6.2 Add API tests for preview/save/hydration payloads that contain `//` annotations.
- [x] 6.3 Add search/AI/RAG tests proving annotations are included in context but excluded from core participants.
- [x] 6.4 Add frontend tests or manual Playwright checks for teacher preview display, AI suffix preservation, and student H5 annotation rendering.
- [x] 6.5 Run `openspec validate support-inline-equation-annotations --strict` and the relevant backend/frontend test commands before marking the change complete.

## 1. Baseline And Scope

- [x] 1.1 Run `openspec validate contextualize-catalog-editor-summary-header --strict` before implementation.
- [x] 1.2 Inspect current `CatalogEditorHeader` summary construction and existing CSS primitives.
- [x] 1.3 Confirm existing action handlers, publication behavior, and tab filtering remain out of scope.

## 2. Contextual Header Content

- [x] 2.1 Add directory and point leading icons in the title row without replacing the status dot or actions.
- [x] 2.2 Replace the fixed five-block summary construction with directory-specific structure/readiness summary items.
- [x] 2.3 Replace the fixed five-block summary construction with point-specific resource/readiness checklist items.
- [x] 2.4 Demote or remove the large `节点类型` summary block and merge redundant directory counts.
- [x] 2.5 Derive student-card readiness from existing node card fields without new API calls.

## 3. Presentation

- [x] 3.1 Update `catalogTree.css` so contextual summary items are compact and not forced into identical metric boxes.
- [x] 3.2 Make healthy states visually calm and warning/missing states more prominent.
- [x] 3.3 Verify long titles and summary labels wrap or truncate without overlap.

## 4. Verification

- [x] 4.1 Run focused catalog/admin frontend tests or typecheck for the touched feature.
- [x] 4.2 Run `openspec validate contextualize-catalog-editor-summary-header --strict` after implementation.
- [x] 4.3 Run browser or screenshot QA for selected directory and selected point states if the admin dev server can run locally.
- [x] 4.4 Review `git diff` to confirm changes remain scoped to OpenSpec files and catalog-tree frontend modules.

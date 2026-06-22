## 1. Baseline And Scope

- [x] 1.1 Run `openspec validate refine-catalog-editor-title-card-and-tab-view --strict` before implementation.
- [x] 1.2 Inspect current catalog editor markup and styles for selected-node header, title duplication, tab nav, and panel sections.
- [x] 1.3 Confirm existing behavior entry points for node actions, tab filtering, form save, media binding, and validation remain unchanged.

## 2. Title Summary Card

- [x] 2.1 Refactor `CatalogEditorHeader` to render a prominent selected-node title summary card instead of tiny primary status tags.
- [x] 2.2 Move node kind, publication state, child count, and relevant content indicators into readable information blocks.
- [x] 2.3 Preserve existing archive, restore, publish, cancel-publish, and preview action behavior and loading states.
- [x] 2.4 Remove or soften duplicated dominant title text in the active content panel while preserving editable title fields and labels.

## 3. Workbench Tab View

- [x] 3.1 Restyle the selected-node tab navigation as a clear workbench switcher with a visible active state.
- [x] 3.2 Keep existing directory/point tab filtering and active-key behavior intact.
- [x] 3.3 Ensure active tab content remains visually attached to the same right-side workbench surface.
- [x] 3.4 Verify long titles, action buttons, and tab labels wrap or truncate without overlap.

## 4. Verification

- [x] 4.1 Run focused catalog/admin frontend tests or typecheck for the touched feature.
- [x] 4.2 Run `openspec validate refine-catalog-editor-title-card-and-tab-view --strict` after implementation.
- [x] 4.3 Run browser or screenshot QA for selected directory and selected point states if the admin dev server can run locally.
- [x] 4.4 Review `git diff` to confirm the change stays scoped to OpenSpec files and catalog-tree frontend modules.

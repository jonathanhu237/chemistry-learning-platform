## Why

The current catalog editor right panel is functionally stable, but its selected-node header still reads like a row of tiny tags above a repeated title, and the tab switcher looks visually underpowered for a multi-form workbench. Teachers need the editor to make the selected catalog object, its status, and its available editing surfaces obvious at first glance.

## What Changes

- Replace the selected-node header's small status tags with a title summary card inspired by mature app patterns: prominent title, concise subtitle/breadcrumb, and status/count information blocks.
- Remove the duplicate title presentation from the active form body when the title is already established by the summary card.
- Restyle the editor tab navigation as a clear workbench switcher for mutually exclusive form panels, using a segmented/card-like treatment rather than loose text tabs.
- Keep selected-node actions, tab availability, save forms, publication checks, validation, media binding, and backend API behavior unchanged.
- Preserve the previous left-side chapter-title switcher and no-selection shell polish from `polish-catalog-workspace-editor-ui`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: Refine the selected-node editor so the right workbench uses a title summary card with information blocks and a clearer tab/view switcher.
- `frontend-admin-maintainability`: Keep the new editor presentation feature-local without introducing broad shell changes, global design-system abstractions, or behavioral rewrites.

## Impact

- Affected frontend code:
  - `apps/admin-web/src/features/catalog-tree/CatalogTreeEditor.tsx`
  - `apps/admin-web/src/features/catalog-tree/CatalogEditorHeader.tsx`
  - `apps/admin-web/src/features/catalog-tree/CatalogNodeContentPanel.tsx`
  - `apps/admin-web/src/features/catalog-tree/catalogTree.css`
  - focused catalog editor tests where visible structure or selectors are affected
- No backend API, database, route, auth, query-key, or dependency changes are expected.
- Visual QA should cover selected directory and selected point states, with attention to long titles, status/action alignment, and tab switching.

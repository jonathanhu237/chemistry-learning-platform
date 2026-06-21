## Why

The teacher catalog workspace is functionally correct, but the first-screen authoring experience still has two visible UI seams: the left panel repeats the selected chapter title in both the heading and the chapter dropdown, and the right editor reads as several disconnected cards rather than a cohesive workbench. This makes a frequently-used management page feel less polished than the rest of the admin console even though the underlying workflows are stable.

## What Changes

- Replace the left panel's duplicate chapter dropdown with a title-level chapter switcher so teachers can change chapters directly from the current chapter heading.
- Keep the left search field focused on directory, point, note, and identity search rather than chapter switching.
- Redesign the right editor shell as a single cohesive workbench surface with integrated selected-node header, tabs, and content area.
- Redesign the no-selection state so it uses the same workbench surface and feels like part of the page instead of a large detached empty card.
- Preserve existing catalog tree behavior, selected-node editing workflows, publication actions, validation, tab filtering, and backend API usage.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: Refine the teacher catalog workspace so chapter switching is integrated into the left heading and the right selected-node editor/empty state present as one polished workbench.
- `frontend-admin-maintainability`: Keep the polish feature-local by updating catalog workspace/editor components and styles without broad admin shell changes or new shared abstractions.

## Impact

- Affected frontend code:
  - `apps/admin-web/src/features/catalog-tree/CatalogTreeWorkspacePage.tsx`
  - `apps/admin-web/src/features/catalog-tree/CatalogTreeEditor.tsx`
  - `apps/admin-web/src/features/catalog-tree/CatalogEditorHeader.tsx`
  - `apps/admin-web/src/features/catalog-tree/catalogTree.css`
  - focused catalog editor tests where selectors or visible text are affected
- No backend API, database, dependency, route, or auth changes are expected.
- Visual QA should cover both selected-node and no-selection states at common admin desktop widths.

## Why

The teacher catalog tree currently looks like a sidebar tree but does not behave like a modern online file directory: drag preview is weak, drop intent is unclear, collapsed targets do not expand while dragging, and moved nodes can remain stale until a manual refresh. Teachers are using this tree as a high-frequency authoring surface, so its movement behavior must match expectations set by Google Drive, Apple Finder, VS Code, and Figma-style outline views.

## What Changes

- Modernize catalog tree drag-and-drop so dragging has continuous feedback: source dragging state, cursor-following preview, visible before/after/into-directory targets, and invalid-drop feedback.
- Auto-expand collapsed directory targets when a dragged node hovers over them long enough, then lazy-load children as needed.
- Update local tree state immediately after valid move/reorder operations and reconcile with server responses, including rollback on failure.
- Refresh both source and target parents after move/reorder/create/archive/restore/status changes so loaded lazy branches do not remain stale.
- Preserve selected-node focus, open ancestors, scroll position where practical, and current editor context after moving a node.
- Add verification that exercises real drag behavior, hover expansion, optimistic update, rollback, and stale-branch refresh instead of relying only on payload mapping tests.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: strengthen tree movement requirements from "persist move/reorder" to modern file-directory interaction behavior with drag preview, drop-target semantics, hover expansion, optimistic UI, and reliable refresh.
- `frontend-admin-maintainability`: require drag/drop implementation to remain feature-local, decomposed, and covered by focused behavior tests plus browser QA.

## Impact

- Admin frontend catalog tree modules under `apps/admin-web/src/features/catalog-tree/`, especially `CatalogTreeNodeList.tsx`, `CatalogTreeRow.tsx`, `catalogTreeData.ts`, `catalogTreeHooks.ts`, and `catalogTree.css`.
- Existing `react-arborist` integration and lazy child-loading behavior.
- Existing catalog move/reorder/create/status mutation invalidation paths.
- Test coverage in catalog tree unit/contract tests and browser visual/interaction QA artifacts.
- No database migration, backend API shape change, or tree-engine replacement is intended for this change.

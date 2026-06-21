## Baseline Notes

- `CatalogArboristDragPreview` currently renders a generic "移动节点" chip and ignores Arborist `offset`/`mouse`, so the preview is not a true cursor-following file-tree preview.
- `CatalogTreeNodeList` currently calls move/reorder mutations after `resolveCatalogArboristMove()` but does not optimistically update `treeData`.
- Lazy branch children are stored locally in `treeData`; query invalidation alone does not refresh already-loaded source and target branches after a move.
- Collapsed directory targets do not auto-expand while a dragged node hovers over them.
- Existing tests focus on helper payload construction and row rendering, not real pointer drag behavior, hover expansion, optimistic update, or rollback.
- Pre-existing uncommitted teaching-note/summary changes are present and must be preserved while implementing this change.

## Implementation Notes

- Added pure optimistic move helpers for same-parent reorder, cross-parent move, root moves, loaded/unloaded parent detection, stale target marking, and immutable tree updates.
- `CatalogTreeNodeList` now snapshots local tree state, applies optimistic movement, persists with the existing move/reorder APIs, rolls back on failure, and refreshes affected branches in source-before-target order to avoid reconciliation races.
- `CatalogTreeRow` now renders source dragging state, cursor-following metadata previews, stronger drop feedback, and a 500ms hover auto-expand path for collapsed directory targets.
- Browser QA used temporary catalog nodes under `/experiments` on a fresh dev server and verified real pointer reorder, preview position, source dragging class, insertion cursor, directory hover highlight, auto-expansion, post-drop visible list update, and invalid point-target feedback suppression.

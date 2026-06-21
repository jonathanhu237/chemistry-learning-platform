## 1. Baseline And Scope

- [x] 1.1 Read this change's `proposal.md`, `design.md`, and spec delta files before editing implementation code.
- [x] 1.2 Run `openspec validate modernize-catalog-tree-drag-drop-interactions --strict` before implementation.
- [x] 1.3 Inspect current `CatalogTreeNodeList.tsx`, `CatalogTreeRow.tsx`, `catalogTreeData.ts`, `catalogTreeHooks.ts`, and `catalogTree.css` for existing Arborist drag/drop behavior.
- [x] 1.4 Confirm unrelated uncommitted teaching-note/summary edits are preserved and not reverted.
- [x] 1.5 Capture or record the current failing states: weak/no cursor-following preview, no hover expansion, stale list after move, and unclear drop target feedback.

## 2. Tree Data Movement Helpers

- [x] 2.1 Add helper coverage for detecting source parent, target parent, loaded source branch, loaded target branch, and root-level moves.
- [x] 2.2 Add pure helper support for optimistic same-parent reorder without mutating previous tree state.
- [x] 2.3 Add pure helper support for optimistic cross-parent move into a loaded directory.
- [x] 2.4 Add pure helper support for moving into chapter root.
- [x] 2.5 Add stale-branch handling for moves into unloaded or unknown destination parents.
- [x] 2.6 Add rollback snapshot helpers or equivalent transaction state for restoring the previous tree after failed persistence.
- [x] 2.7 Extend invalid drop tests for point target, descendant target, multi-node drag, missing dragged node, missing target parent, and cross-chapter target.

## 3. Drag Preview And Drop Feedback

- [x] 3.1 Update `CatalogArboristDragPreview` to position from Arborist `offset` or `mouse` coordinates so it follows the pointer.
- [x] 3.2 Render dragged node icon, title, and multi-node count in the preview when metadata is available.
- [x] 3.3 Add visible source-row dragging styling for the node being dragged.
- [x] 3.4 Strengthen before/after insertion cursor styling so reorder placement is obvious against the sidebar background.
- [x] 3.5 Strengthen directory drop-target styling for move-into-directory feedback.
- [x] 3.6 Ensure invalid targets do not show a valid cursor or valid directory target highlight.
- [x] 3.7 Add focused tests for preview content, cursor component styling hooks, `will-receive-drop` classes, and invalid target suppression where practical.

## 4. Hover Auto-Expansion

- [x] 4.1 Add cancellable hover timer logic for valid collapsed directory drop targets.
- [x] 4.2 Use an approximately 500ms delay before auto-expanding a hovered directory.
- [x] 4.3 Trigger lazy child loading when an unloaded directory auto-expands during drag.
- [x] 4.4 Cancel pending auto-expand timers when hover leaves, drag ends, node opens, or component unmounts.
- [x] 4.5 Keep directories expanded after drag completes once auto-expanded.
- [x] 4.6 Add tests or component-level coverage for timer start, cancellation, and load trigger behavior.

## 5. Optimistic Move Transactions

- [x] 5.1 Refactor move/reorder handling in `CatalogTreeNodeList.tsx` so valid drops start a local movement transaction.
- [x] 5.2 Apply optimistic tree updates immediately after same-parent reorder drops.
- [x] 5.3 Apply optimistic tree updates immediately after cross-parent move drops.
- [x] 5.4 Preserve selected node id and scroll/focus the moved node into view after optimistic update when visible.
- [x] 5.5 Persist same-parent reorder through the existing reorder API.
- [x] 5.6 Persist cross-parent moves through the existing move API.
- [x] 5.7 Roll back optimistic state and show a controlled error if persistence fails.
- [x] 5.8 Ensure fallback menu commands for move before/after use the same optimistic transaction and rollback path.

## 6. Refresh And Reconciliation

- [x] 6.1 Refresh root nodes after successful moves involving the chapter root.
- [x] 6.2 Refresh source parent children after successful moves when the source parent is loaded.
- [x] 6.3 Refresh target parent children after successful moves when the target parent is loaded or auto-expanded.
- [x] 6.4 Keep existing React Query invalidation for catalog roots, children, search, validation, media assets, and selected node detail.
- [x] 6.5 Avoid forcing a full tree reload when exact source/target branch reconciliation is sufficient.
- [x] 6.6 Verify moved nodes do not reappear in their old loaded branch after server success.
- [x] 6.7 Verify moved nodes appear in the destination branch without manual refresh when the destination branch is visible.

## 7. Browser Interaction QA

- [x] 7.1 Start or reuse the local admin dev server for `/experiments`.
- [x] 7.2 Use Playwright or available in-app browser tooling to perform a real pointer drag reorder within one parent.
- [x] 7.3 Capture or assert drag preview follows pointer coordinates during drag.
- [x] 7.4 Capture or assert source row dragging state and visible before/after insertion line during reorder.
- [x] 7.5 Perform a real pointer drag onto a collapsed directory and verify it auto-expands after the hover delay.
- [x] 7.6 Drop into the expanded directory and verify the list updates without pressing refresh.
- [x] 7.7 Perform or assert an invalid drop onto a point node and verify no valid-target feedback/persistence occurs.
- [x] 7.8 If browser drag tooling is unavailable, install/use available tooling or document a concrete blocker; do not replace this with payload-only unit tests.

## 8. Validation

- [x] 8.1 Run catalog tree focused tests.
- [x] 8.2 Run admin frontend typecheck.
- [x] 8.3 Run admin frontend production build if touched code affects bundled frontend behavior.
- [x] 8.4 Run `openspec validate modernize-catalog-tree-drag-drop-interactions --strict`.
- [x] 8.5 Run `git diff --check`.
- [x] 8.6 Review diff to confirm implementation remains scoped to OpenSpec files and catalog tree frontend modules unless a documented blocker requires otherwise.

## Context

The catalog tree already migrated from Ant Design Tree to `react-arborist`, but the current integration only covers the basic data adapter and `onMove` persistence path. Recent manual testing exposed several gaps that users immediately notice in a modern file-directory workflow:

- the drag preview does not behave like a cursor-following file/folder preview because the custom `CatalogArboristDragPreview` ignores Arborist's `offset`/`mouse` coordinates and only renders generic text;
- the tree does not auto-expand collapsed directory targets during drag hover, so teachers cannot navigate into a closed destination the way they can in Google Drive, Finder, VS Code, or Figma layer trees;
- the local `treeData` is manually hydrated for lazy branches, but move/reorder mutations only invalidate React Query, so already-loaded lazy branches can remain stale after a successful move;
- the existing tests verify move payload construction but do not exercise the interaction contract teachers feel: drag source state, target feedback, hover expansion, optimistic list update, rollback, and refresh of both source and destination branches.

External interaction references used for this design:

- Google Drive official help describes organizing through folders, dragging items over folders and releasing them, using the left panel as a move target, and keyboard move alternatives.
- Atlassian's Pragmatic Drag and Drop tree guidelines define tree drop intents as before, after, and combine, and call for expanding a collapsed item after hovering over it for about 500ms.
- NN/g's drag-and-drop guidance emphasizes clear signifiers and continuous feedback at every stage of the interaction.
- React Arborist's own README positions the library as a base for VS Code sidebar, Mac Finder, Windows Explorer, and Figma/Sketch layer-panel style trees, but controlled trees must update their own data in response to moves.

Current implementation anchors:

- `apps/admin-web/src/features/catalog-tree/CatalogTreeNodeList.tsx` owns local tree data, lazy child loading, Arborist integration, `onMove`, and parent component mutation callbacks.
- `apps/admin-web/src/features/catalog-tree/CatalogTreeRow.tsx` owns row rendering, drag preview, cursor rendering, and `willReceiveDrop` styling.
- `apps/admin-web/src/features/catalog-tree/catalogTreeData.ts` owns tree shape, move/reorder resolution, parent/sibling lookup, and fallback movement helpers.
- `apps/admin-web/src/features/catalog-tree/catalogTreeHooks.ts` owns mutation success invalidation.
- `apps/admin-web/src/features/catalog-tree/catalogTree.css` owns row, cursor, drop target, and preview styling.

## Goals / Non-Goals

**Goals:**

- Make drag-and-drop feel like a modern file directory tree rather than a thin reorder callback.
- Show a real cursor-following preview with node icon/title and multi-node count if Arborist ever emits multiple drag ids.
- Make source row, valid drop line, and valid folder/combine target visually clear while dragging.
- Auto-expand hovered collapsed directory targets after a short delay and lazy-load children before the teacher drops.
- Apply valid move/reorder changes optimistically to `treeData` immediately after drop.
- Reconcile optimistic state with server success by refreshing source parent, target parent, roots, selected detail, search, validation, and affected lazy branches.
- Roll back local tree state and show a controlled error if the server rejects or fails a move/reorder.
- Preserve the selected node and scroll it into view after a successful move where practical.
- Add tests and browser QA that cover the actual interaction states, not only payload mapping.

**Non-Goals:**

- Do not replace `react-arborist` with a new tree engine.
- Do not change database schema or backend catalog-node identity.
- Do not change the move/reorder API contract unless implementation reveals an unavoidable backend defect.
- Do not redesign the right editor layout.
- Do not implement multi-select moves beyond explicitly rejecting or gracefully representing them.
- Do not implement cross-chapter drag movement.
- Do not remove menu-based fallback movement; it remains the accessibility/precision fallback.

## Decisions

### Decision 1: Keep React Arborist and complete the controlled-tree integration

`react-arborist` already provides core primitives: visible node APIs, `willReceiveDrop`, renderable cursor, drag preview props, `open()`, `openParents()`, `scrollTo()`, and controlled `data`. The current problem is not the library choice; it is that controlled trees must update their own data and our integration stops too early.

Implementation direction:

- Keep the existing `Tree` integration.
- Extend feature-local helpers in `catalogTreeData.ts` to compute source parent, target parent, optimistic tree mutations, and rollback snapshots.
- Keep all tree behavior inside catalog tree modules so the admin shell remains untouched.

Alternatives considered:

- Replace Arborist with Atlassian Pragmatic Drag and Drop: rejected for this pass because it would rebuild the entire tree behavior stack. Atlassian's guidelines are valuable as the interaction target, but Arborist is still adequate.
- Depend solely on React Query refetch after move: rejected because lazy-loaded branch state is owned locally and visible stale state is exactly the user-reported failure.

### Decision 2: Treat each move as a local transaction

A valid move/reorder should be handled as a transaction:

```text
resolve drag intent
  -> snapshot current treeData
  -> optimistic treeData update
  -> persist via move/reorder mutation
  -> success: reconcile by refetching affected branches
  -> failure: restore snapshot and show error
```

The transaction should record:

- moved node id;
- source parent id (`null` for chapter root);
- target parent id (`null` for chapter root);
- target display order;
- whether the operation is same-parent reorder or cross-parent move;
- whether source/target branches were loaded before the operation.

Same-parent reorder can call the existing reorder API, but the local tree should reorder immediately. Cross-parent moves can call the existing move API, but the local tree should remove the node from the source sibling list and insert it into the target sibling list when the target parent is loaded.

If the target parent is not loaded, the optimistic update should still remove the source node from its visible source list and mark the target parent stale; when that parent opens, it must fetch fresh children.

### Decision 3: Refresh exact affected branches, not only global prefixes

The current mutation invalidation is too broad for React Query and too weak for local lazy branch state. The tree component needs a way to refresh loaded branches it owns.

Implementation direction:

- After move/reorder success, refresh:
  - root list when source or target parent is `null`;
  - source parent children when source parent is non-null and loaded;
  - target parent children when target parent is non-null and loaded or just auto-expanded;
  - selected node detail if it was moved or if its parent/title/status metadata changed;
  - existing catalog search/validation query prefixes through current invalidation helpers.
- Keep `invalidateCatalog()` for server-owned query caches, but add tree-local reconciliation in `CatalogTreeNodeList`.
- Avoid forcing full-tree reload unless an error or unknown state makes exact refresh unreliable.

### Decision 4: Auto-expand hover targets with a cancellable delay

Modern file trees let users navigate while dragging. Atlassian's tree guidance uses a 500ms hover delay for collapsed combine targets; that matches Google/Finder user expectations without causing accidental expansion on brief pass-through.

Implementation direction:

- Watch directory rows where `node.willReceiveDrop` is true and `node.isOpen` is false.
- Start a timer around 500ms.
- Cancel the timer if the row stops receiving drop, drag ends, or the node becomes open.
- On timer fire, call `node.open()` or `tree.open(node.id)` and trigger `loadDirectory(node.id)` for unloaded directories.
- Keep the directory open after drag ends.

Important nuance: opening via Arborist fires `onToggle`; `loadDirectory` already listens there. If implementation uses row-local `node.open()`, confirm it still triggers `onToggle` and lazy load. If not, call an explicit feature-local open/load helper.

### Decision 5: Make the drag preview and target language concrete

The preview should help teachers answer "what am I moving?" while the cursor/target state answers "where will it go?"

Drag preview:

- fixed overlay using Arborist `offset` or `mouse` coordinates;
- icon matching directory/point;
- dragged node title for single drag;
- count text for multiple ids if emitted;
- subtle shadow and opacity comparable to Google Drive/Finder style previews;
- no generic-only "移动节点" preview when the node title is available.

Drop target feedback:

- line above target row for `reorder-before`;
- line below target row for `reorder-after`;
- border/background around directory row for "move into this directory";
- invalid target should hide the cursor and, where practical, show a muted/blocked cursor state rather than implying success.

The existing Arborist cursor computes line placement, and `node.willReceiveDrop` provides folder highlight for combine targets. The CSS needs stronger, more legible states, and the renderer should not rely on a barely visible 2px line alone.

### Decision 6: Browser QA must simulate real drag behavior

Previous QA allowed "drag screenshot capture not reliable" and leaned on unit tests. That is no longer sufficient because the defect is experiential.

Required QA direction:

- Use Playwright or the in-app browser to simulate pointer drag between real rows.
- Capture or assert:
  - preview appears and follows pointer coordinates;
  - source row has dragging affordance;
  - before/after line appears for reorder;
  - directory target highlight appears for move-into-directory;
  - collapsed directory expands after hover delay;
  - after drop, the node appears in the new visible position without manual refresh;
  - after server success/refetch, the node remains in the correct position.
- If local Playwright browser binaries are missing, install or use the available in-app browser tooling rather than downgrading the QA requirement.

## Risks / Trade-offs

- [Risk] Optimistic moves can diverge from server ordering if the API normalizes order differently. -> Mitigation: reconcile affected parent branches after success and restore snapshot on failure.
- [Risk] Hover auto-expand can trigger too aggressively and open many folders. -> Mitigation: use a cancellable 500ms delay and only expand valid directory combine targets.
- [Risk] Lazy-loaded parents make source/target reconciliation tricky. -> Mitigation: track whether source/target branches are loaded and mark unknown branches stale for next open.
- [Risk] React Arborist's internal cursor semantics may not expose enough data to label every target action. -> Mitigation: use line cursor for before/after and `willReceiveDrop` directory highlight for combine; keep action labels in tests where the data is available.
- [Risk] Browser drag simulation can be flaky under virtualized rows. -> Mitigation: keep target rows visible, use deterministic test data, and combine browser QA with focused helper tests.
- [Risk] There are currently unrelated uncommitted edits around teaching-note/summary semantics. -> Mitigation: keep this change scoped to OpenSpec artifacts until apply, and do not revert or restage unrelated edits.

## Migration Plan

1. Add focused helper tests for optimistic tree move/reorder, source/target parent detection, rollback, and stale branch marking.
2. Fix the drag preview to use Arborist coordinates and real node metadata.
3. Add row/tree hover auto-expand with a 500ms delay and lazy loading.
4. Add optimistic local tree update and rollback around move/reorder mutation calls.
5. Add exact source/target branch refresh after server success.
6. Strengthen cursor/drop-target CSS and accessible labels for valid/invalid drop states.
7. Run catalog tree tests, admin typecheck, OpenSpec validation, and production build.
8. Run real browser drag QA, capturing normal reorder, move into collapsed directory, invalid point target, and post-drop refresh behavior.

Rollback is frontend-code only: remove the optimistic transaction layer and hover-expansion behavior, falling back to the previous Arborist move callback while preserving existing backend APIs.

## Open Questions

- Should hovering over any directory row expand it, or only when Arborist reports the middle/combine target? Preferred answer: only combine/move-into-directory targets.
- Should a successful move into an unloaded collapsed directory immediately expand the destination, or keep it closed and show a success toast? Preferred answer: if the user dropped onto a directory, keep/open it so the moved node is visible.
- Should menu-based "move before/after" also use the optimistic transaction layer? Preferred answer: yes, so fallback commands have the same refresh behavior as drag/drop.

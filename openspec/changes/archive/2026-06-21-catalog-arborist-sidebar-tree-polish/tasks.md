## 1. Baseline and Visual Target Lock

- [x] 1.1 Run `openspec validate catalog-arborist-sidebar-tree-polish --strict` before implementation and record the initial pass.
- [x] 1.2 Capture current catalog tree screenshots showing the bad states called out by the user: detached chevrons, always-visible six-dot grip, selected directory row, and directory editor showing point-only tabs.
- [x] 1.3 Save the user-provided Dribbble/sidebar screenshot path or a local visual-target note in the change implementation notes so the Arborist skin is judged against the right feeling.
- [x] 1.4 Record the `react-arborist` Gmail/sidebar demo as the practical open-source visual behavior target and note that exact Dribbble assets are not copied.
- [x] 1.5 Audit current files and note the intended ownership for `CatalogTreeNodeList.tsx`, `CatalogTreeRow.tsx`, `catalogTreeData.ts`, `catalogTree.css`, and `CatalogTreeEditor.tsx`.

## 2. Dependencies and Route Boundary

- [x] 2.1 Add `react-arborist` to `apps/admin-web/package.json`.
- [x] 2.2 Add `lucide-react` to `apps/admin-web/package.json` unless an equally suitable existing experiment/folder icon set is chosen and documented.
- [x] 2.3 Verify the package lock is updated and no unrelated dependency churn is introduced.
- [x] 2.4 Add or update import-boundary checks so `react-arborist` imports are limited to catalog tree modules.
- [x] 2.5 Add or update import-boundary checks so `lucide-react` imports are limited to catalog tree UI modules for this change.

## 3. Arborist Data Adapter

- [x] 3.1 Replace or extend `catalogTreeData.ts` with an Arborist-owned data shape containing `id`, `name`, `kind`, `catalogNode`, `loaded`, and `children`.
- [x] 3.2 Map directories to Arborist internal nodes even when children are not yet loaded, so directory chevrons and drop targets remain available.
- [x] 3.3 Map points to Arborist leaf nodes that never accept child nodes.
- [x] 3.4 Preserve previously loaded children when root nodes refresh.
- [x] 3.5 Implement helper functions to find nodes, parents, siblings, descendants, and old parent ids in the Arborist data shape.
- [x] 3.6 Implement move/reorder payload helpers for Arborist `onMove({ dragIds, parentId, index })`.
- [x] 3.7 Reject unsupported multi-node moves or explicitly handle only the first dragged node with a controlled warning.
- [x] 3.8 Add focused tests for directory internal mapping, point leaf mapping, unloaded directory mapping, loaded child merge, descendant detection, same-parent reorder, root move, directory move, and invalid point/descendant drops.

## 4. Arborist Tree Integration

- [x] 4.1 Replace Ant Design Tree usage in `CatalogTreeNodeList.tsx` with `react-arborist` while preserving the component's public props used by `CatalogTreeWorkspacePage.tsx`.
- [x] 4.2 Implement a local size measurement strategy for Arborist height/width without adding unnecessary global layout dependencies.
- [x] 4.3 Wire `selection` and `onActivate` so selecting a row still opens the right editor for the stable node id.
- [x] 4.4 Wire `onToggle` or equivalent open handling so opening an unloaded directory fetches `listCatalogChildren`.
- [x] 4.5 Preserve selected node and known open ancestor context after child load, move, reorder, create, archive, restore, publish, or unpublish refreshes where practical.
- [x] 4.6 Keep server search result selection working with the new tree, opening known ancestors and scrolling selected nodes into view when loaded context allows.
- [x] 4.7 Remove Ant Design Tree-specific switcher, titleRender, draggable, drop indicator, and class assumptions from catalog tree implementation.

## 5. Sidebar Row Skin and Iconography

- [x] 5.1 Replace `CatalogTreeRow.tsx` with an Arborist node renderer or split it into `CatalogArboristNode`, `CatalogArboristRow`, `CatalogArboristCursor`, and `CatalogArboristDragPreview` modules.
- [x] 5.2 Implement the sidebar row anatomy: guide area, chevron/spacer, icon, title/subtitle, trailing metadata, hover/selected actions.
- [x] 5.3 Align chevrons immediately before directory icons and reserve the same width for point leaf spacers.
- [x] 5.4 Use folder icons for directories and experiment-specific flask/test-tube icons for point nodes.
- [x] 5.5 Render video availability as trailing metadata for point rows instead of as the primary node icon.
- [x] 5.6 Implement full-row rounded selected state and quiet hover state without card-like borders.
- [x] 5.7 Implement soft nested guide lines or a stable equivalent hierarchy affordance for at least three visible levels.
- [x] 5.8 Remove always-visible six-dot drag grips; make the row itself draggable or show only a subtle hover/selected drag affordance.
- [x] 5.9 Ensure long chemistry titles truncate with tooltip/title text and do not overlap trailing status/actions.
- [x] 5.10 Update `catalogTree.css` so Arborist/sidebar styling is feature-local and does not globally override Ant Design tree styles.

## 6. Add, Drag, and Row Actions

- [x] 6.1 Replace visible "根节点/根目录" wording with teacher-facing wording such as "添加到本章".
- [x] 6.2 Provide top-level add menu/actions for new directory and new point under the current chapter root.
- [x] 6.3 Provide directory-only hover/selected child-add action for creating child directory or child point.
- [x] 6.4 Keep point rows from showing child-add actions.
- [x] 6.5 Move copy id, archive/restore, publish/unpublish, move before, move after, and move into directory fallback commands into the more-actions menu.
- [x] 6.6 Wire Arborist drag move within the same parent to the existing reorder API.
- [x] 6.7 Wire Arborist drag move into a valid directory parent to the existing move API.
- [x] 6.8 Reject drops onto point nodes, into descendants, and across unsupported chapter boundaries before persistence.
- [x] 6.9 Implement and style an Arborist drop cursor or valid drop-target state that is visible during drag.
- [x] 6.10 Add controlled warnings for invalid drops without losing current selection.

## 7. Directory and Point Editor Panel Filtering

- [x] 7.1 Build `CatalogTreeEditor` tab items from selected node kind rather than from a fixed unconditional list.
- [x] 7.2 For directory nodes, render only content, student-card, publish-checks, and advanced tabs.
- [x] 7.3 For point nodes, render content, video, related experiments, student-card, publish-checks, and advanced tabs.
- [x] 7.4 When a directory is selected while the active tab is video or related, automatically switch back to content.
- [x] 7.5 Gate `useCatalogMediaAssets` so it does not fetch for directory nodes.
- [x] 7.6 Gate related-point search so it does not fetch for directory nodes.
- [x] 7.7 Ensure directory selected headers do not show point video count/status.
- [x] 7.8 Ensure point selected headers still show compact video count/status.

## 8. Focused Tests

- [x] 8.1 Add tests for Arborist data adapter mapping and lazy loading merge behavior.
- [x] 8.2 Add tests for Arborist move/reorder payload construction and invalid drop rejection.
- [x] 8.3 Add tests that the catalog tree no longer imports or renders Ant Design Tree as its behavior engine.
- [x] 8.4 Add tests for sidebar row rendering: directory chevron, point spacer, experiment icon, selected row, trailing metadata, hidden action controls, and long title truncation affordance.
- [x] 8.5 Add tests for top-level add wording and directory-only child-add behavior.
- [x] 8.6 Add tests for directory editor tab filtering and point editor tab availability.
- [x] 8.7 Add tests that directory selection gates off media asset and related-point search queries.
- [x] 8.8 Update existing contract tests so they assert user-visible behavior and feature-local boundaries rather than Ant Design Tree internals.

## 9. Browser and Visual QA

- [x] 9.1 Run browser QA against the local admin dev server and capture the new Arborist sidebar tree at normal admin width.
- [x] 9.2 Capture the new Arborist sidebar tree at a narrow laptop-width viewport.
- [x] 9.3 Capture expanded directory, collapsed directory, selected directory, selected point, and nested point rows with experiment icons.
- [x] 9.4 Capture hover or focused row actions showing child-add and more menu without layout shift.
- [x] 9.5 Capture or assert Arborist drag cursor/drop-target state; if reliable drag screenshot capture is not possible, document the limitation and rely on focused move/drop tests.
- [x] 9.6 Capture a directory editor state with video and related experiment tabs absent.
- [x] 9.7 Capture a point editor state with video and related experiment tabs present.
- [x] 9.8 Run DOM overlap checks for chevrons, icons, title, trailing metadata, and actions.
- [x] 9.9 Record screenshots and accepted visual limitations in implementation notes.

## 10. Full Validation

- [x] 10.1 Run `openspec validate catalog-arborist-sidebar-tree-polish --strict`.
- [x] 10.2 Run `openspec validate --all --strict --no-interactive`.
- [x] 10.3 Run `git diff --check`.
- [x] 10.4 Run admin frontend `typecheck`.
- [x] 10.5 Run admin frontend tests.
- [x] 10.6 Run admin frontend `validate:boundaries`.
- [x] 10.7 Run admin frontend production build.
- [x] 10.8 Run admin frontend build report and document Arborist/lucide chunk impact.
- [x] 10.9 Run admin frontend smoke test against the local dev server or production preview.
- [x] 10.10 Search the repository to confirm no live catalog tree Ant Design Tree behavior path, generic file icon for point rows, always-visible six-dot drag grip, directory video tab, directory related tab, hybrid control, shortcut control, or catalog upload control remains outside tests/docs/archive allowances.

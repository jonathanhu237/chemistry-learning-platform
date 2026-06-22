## Baseline

Initial validation:

- `openspec validate refine-catalog-tree-editor-ux --strict`: passed before implementation.

Current catalog feature file sizes before this pass:

- `CatalogTreeWorkspacePage.tsx`: 225 lines. Owns route orchestration, chapter selection, search, create modal, tree placement, and selected editor placement.
- `CatalogTreeNodeList.tsx`: 216 lines. Owns Ant Design Tree rendering, lazy child loading, tree-data shaping, drop calculation, row rendering, and row actions.
- `CatalogTreeEditor.tsx`: 461 lines. Owns selected-node header, node basics, move controls, point content, related links, video binding, search preview, and publish validation.
- `catalogTreeMappers.ts`: 209 lines. Owns form hydration and request payload mapping for node basics, point content, related links, movement, labels, and status colors.
- `catalogTreeHooks.ts`: 247 lines. Owns catalog query/mutation hooks and invalidation.
- `catalogTree.css`: 362 lines. Owns workspace, tree, editor, related-link, media-binding, and responsive styles.

## Field Audit

Default content:

- Directory: title, summary, teacher-only note.
- Point: primary point title, teacher-only note, principle mode, equation or text principle, phenomenon explanation, safety note.

Video:

- Existing media selector, bind action, binding list, preview link, publish/unpublish binding, remove binding.
- Upload remains outside catalog management.

Related:

- Related target point, relation type, sort order, label, hidden flag when exposed.

Student card:

- Directory student description, card image asset id, icon key, accent, layout variant.
- Point short description, cover image asset id, icon key, accent, emphasis.

Publish checks:

- Validation errors and warnings, publish readiness, subtree checks.

Advanced:

- Raw node id, parent id, display order, search preview, index state, raw/debug metadata, title mismatch diagnostics.

## Safety Audit

Before implementation, repository search found:

- No live `hybrid` or `shortcut` catalog editor controls.
- No live `uploadCatalogPointMedia` API usage.
- No catalog editor file input.
- Existing `CatalogTreeNodeList.tsx` already removed imported `ArrowUpOutlined`/`ArrowDownOutlined`, but the tree still needed stronger visual and interaction separation.

## Tree Library Decision

`react-arborist` was reviewed as the preferred candidate from the spec. It provides a strong behavior boundary for custom tree visuals, drag/drop, virtualization, and custom renderers. Its trade-off is that the current catalog tree uses lazy server child loading through Ant Design Tree's `loadData`, and adopting Arborist now would require rebuilding the data-loading/open-state model around a fully controlled tree.

The implementation path for this pass keeps Ant Design Tree as the behavior engine and extracts the project-owned parts into feature-local modules:

- tree data shaping and drop calculations;
- row renderer and visual skin;
- fallback movement actions.

This satisfies the spec fallback: Ant Design Tree remains route-owned, avoids a new dependency, preserves lazy loading, and can still match the requested source-list visual model through custom row rendering, custom switcher icons, contextual actions, and a focused drop-validation layer. MUI X Tree View remains rejected because it would introduce a Material UI stack into the Ant Design admin shell.

## Visual QA

Browser QA was run against the local admin dev server at `http://localhost:5175` with Playwright. Screenshots are stored in `artifacts/catalog-tree-ux/`:

- `after-tree-default.png`
- `after-selected-point-content.png`
- `after-video-panel.png`
- `after-advanced-panel.png`
- `after-narrow-content.png`

The QA script covered expanded and collapsed tree states, a selected point row, the default point content panel, the video panel, the advanced panel, and a narrow laptop-width viewport. DOM overlap inspection reported `overlap: false`; console errors, page errors, and failed requests were empty. The default editor no longer renders the old `基础信息` block in the selected-node point view.

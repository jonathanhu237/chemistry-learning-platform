## Why

The directory/point data model and first editor split are in place, but the teacher catalog tree still does not read like a mature navigation tree. Current screenshots show Ant Design tree internals mixed with custom row rendering: disclosure arrows sit away from the node, drag grip dots are visually confusing, root/add actions expose implementation language, and directory rows can still lead teachers into point-only editor panels.

Teachers need a polished, calm sidebar navigation tree in the spirit of the shared Dribbble "Sidebar Navigation Tree" reference and `react-arborist`'s Gmail/sidebar demo: hierarchy should feel natural, experimental point nodes should use experiment-specific visuals, drag and add actions should be available without clutter, and directory nodes should not show point-only work surfaces.

## What Changes

- Replace the teacher catalog tree's Ant Design Tree rendering path with a `react-arborist`-based tree behavior adapter, keeping all code route-local to the catalog feature.
- Style the left tree as a sidebar navigation tree inspired by the user-provided Dribbble reference and `react-arborist` Gmail/sidebar demo:
  - soft nested guide lines;
  - chevrons aligned immediately before directory icons;
  - same-width leaf spacers for point nodes;
  - full-row rounded selected state;
  - quiet hover state;
  - trailing count/status/action area;
  - no always-visible drag-grip dots.
- Use chemistry/experiment iconography for point nodes instead of generic file/document icons, preferring `lucide-react` icons such as `FlaskConical` or `TestTubeDiagonal`.
- Keep directories as category/navigation/card nodes and points as video learning leaves; do not reintroduce hybrid or shortcut node concepts.
- Keep drag reorder and drag move, but make dragging feel native to the sidebar tree: row drag handle can be the row itself or a subtle hover-only affordance, with a clear drop cursor.
- Keep add actions, but place them in sidebar-appropriate locations:
  - top-level "add to chapter" action instead of "root node" implementation language;
  - directory-only hover/selected `+` action for adding child directory/point;
  - more menu for secondary actions.
- Hide point-only editor panels for directory nodes. Directory nodes must not show `视频` or `相关实验` tabs, and selecting a directory while on a point-only tab must return to `内容`.
- Prevent point-only media/related-link queries from running for directory nodes.
- Preserve existing backend API semantics, stable node/point identity, media binding-only behavior, publication flow, related links, and advanced diagnostics placement.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: Replace the catalog tree interaction/visual contract with an Arborist-backed sidebar navigation tree; tighten directory-vs-point editor panel visibility.
- `frontend-admin-maintainability`: Require the catalog tree behavior adapter, row skin, icon mapping, lazy loading bridge, and editor tab filtering to stay feature-local and covered by focused tests and visual QA.

## Impact

- Admin frontend dependencies: add `react-arborist` for tree behavior. Add `lucide-react` for experiment/folder/action iconography if the implementation does not reuse existing suitable icons.
- Admin catalog feature:
  - replace `CatalogTreeNodeList.tsx` Ant Design Tree usage with an Arborist adapter;
  - adapt current `catalogTreeData.ts` helpers to Arborist's `id`, `children`, `onMove`, `disableDrop`, `selection`, and open-state model;
  - replace `CatalogTreeRow.tsx` with a sidebar-tree row renderer and optional drag preview/drop cursor renderers;
  - adjust `catalogTree.css` for the Dribbble/Gmail sidebar style;
  - update `CatalogTreeEditor.tsx` tab construction so directory nodes cannot access point-only tabs.
- API usage remains unchanged: existing catalog children, node create/update/status, move/reorder, media binding, related-link, validation, and search endpoints stay the source of truth.
- Tests and validation:
  - add dependency/bundle checks confirming Arborist/lucide are route-owned by the catalog workspace;
  - add focused unit tests for Arborist data adaptation, drop validation, directory tab filtering, and query gating;
  - add Playwright/browser screenshots comparing the new tree against the requested sidebar navigation feel at normal and narrow admin widths;
  - run OpenSpec strict validation, admin typecheck/tests/boundary validation/build/build-report/smoke.

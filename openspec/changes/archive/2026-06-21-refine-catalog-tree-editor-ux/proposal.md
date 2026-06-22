## Why

The first directory/point split is functionally correct, but the teacher catalog workspace still feels like an exposed implementation table: the tree mixes visual languages and the right editor surfaces too many fields at once. Teachers need a calm, professional authoring surface that makes directory-vs-point identity obvious, keeps common work fast, and hides operational/debug detail until it is needed.

## What Changes

- Redesign the teacher catalog tree around a mature file/source-list interaction model inspired by Apple Finder sidebars/outline views, GitHub/VS Code-style repository trees, Carbon tree views, and PatternFly tree guidance.
- Replace the current visually heavy row treatment with a consistent tree language: unified chevrons/spacers, directory and point icons with the same stroke/size system, full-row selection, subtle guide lines, compact status, and hover/focus row actions.
- Use a mature drag tree behavior boundary instead of bespoke visible move controls. Implementation should prefer `react-arborist` with a custom admin visual skin unless an implementation spike proves Ant Design Tree can match the required polish with less risk.
- Keep directory and point creation, selection, expansion, search, drag reorder/move, drop validation, archive, publish, and accessible fallback actions available without cluttering every row.
- Restructure the selected-node editor into a focused document-style workspace: sticky selected-node header plus task tabs/sections for content, video, related experiments, student card, publish checks, and advanced/debug fields.
- Remove low-frequency or debug fields from the default point-content view, including raw Node ID, explicit parent/order controls, search-index diagnostics, and validation internals unless the teacher opens the relevant advanced/publish panel.
- Treat point title/name as one primary authoring concept in the UI, avoiding duplicate "node title" and "point name" fields unless there is a deliberate advanced override.
- Keep video upload outside the catalog editor. The catalog editor continues to bind, preview, publish/unpublish, or remove existing media bindings only.
- Preserve the existing backend/catalog semantics from `separate-catalog-directory-point-nodes`: chapters are roots, directories are navigation/category/card nodes, and points are video learning leaves.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: Refine the catalog workspace tree interaction, visual hierarchy, node editor information architecture, default/advanced field visibility, and video-binding presentation.
- `frontend-admin-maintainability`: Strengthen the implementation boundary for the tree interaction, selected-node editor tabs, presentation forms, drag adapter, and UI regression checks so the catalog workspace does not become another all-in-one component.

## Impact

- Admin frontend tree: catalog tree component(s), drag adapter, row renderer, icons, action menus, search/filter affordance, keyboard/fallback movement, CSS, and interaction tests.
- Admin selected-node editor: header, content/video/related/student-card/publish/advanced panels, point and directory form hydration, payload mappers, validation display, and low-frequency diagnostics placement.
- API usage: existing catalog node, point content, related links, media binding, publication, and validation endpoints remain the source of truth; no new upload endpoint is introduced.
- Dependencies: likely add or formalize a route-owned tree/drag dependency, with `react-arborist` as the preferred candidate after research because it separates tree behavior from row visuals and supports drag/drop, virtualization, and custom renderers.
- Validation: OpenSpec strict validation, admin typecheck/tests/build, focused tree/editor unit tests, Playwright or browser screenshot review for common admin widths, and boundary checks that keep tree/editor modules split.

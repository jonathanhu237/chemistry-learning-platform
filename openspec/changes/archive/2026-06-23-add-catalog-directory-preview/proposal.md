## Why

Teachers currently have two distinct preview systems: the full student-preview sandbox that simulates the student app, and the catalog-tree single-point preview that opens one catalog point in a phone frame. The catalog-tree preview is useful while authoring, but it only supports point nodes; selecting a directory cannot show what the student sees after entering that directory.

Directory authoring needs the same quick, local "does this look right in the student H5 catalog?" feedback that point authoring already has. This change extends the catalog-tree preview from point-only preview to node preview, so a selected directory can open directly to its student-facing second-level catalog page while a selected point continues to open the video/detail page.

## What Changes

- Expand the catalog-tree preview model from "point preview" to "catalog node preview" for both `directory` and `point` nodes.
- Add a teacher-authorized directory preview path that renders the selected directory as it appears inside the student H5 catalog browser, including parent path, selected directory state, child directories, child points, counts, and the same mobile layout conventions used by the real student catalog.
- Keep point preview behavior intact: selecting a point still opens the current point video/detail preview and continues to use the student point renderer.
- Reuse real student H5 catalog/detail components wherever practical so teacher preview remains WYSIWYG rather than a teacher-side mock.
- Preserve the product boundary between the two preview systems:
  - full student-preview sandbox remains the place to simulate the whole student app and route history;
  - catalog-tree node preview remains a short-lived, teacher-scoped authoring preview for one selected catalog node.
- Define route/back behavior for isolated catalog-tree previews:
  - a directory preview can navigate within preview-scoped catalog nodes;
  - a point preview reached from a previewed directory can return to that directory;
  - a root isolated preview with no preview-local parent should close the preview shell or fall back to browser history instead of using a no-op back action.
- Extend preview authorization and read APIs so preview tokens can be scoped to a selected directory subtree or selected point without requiring student login or creating student sessions.
- Keep preview mode non-mutating: no assessment, AI chat session, feedback, progress, analytics, or student session mutation may be created from catalog-tree node preview.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `teacher-catalog-student-preview`: Extend teacher-authorized catalog preview from point-only rendering to directory-or-point node rendering, with preview-local navigation and non-mutating student-facing output.
- `teacher-experiment-catalog-editor`: Allow the selected-node preview affordance to work for directory nodes as well as point nodes, while preserving point-specific authoring, video, related-link, and diagnostics behavior.
- `backend-slim-domain-architecture`: Preserve backend ownership gates while expanding catalog preview token and read routes from point-only preview to catalog node/subtree preview.

## Impact

- `apps/web-teacher`
  - Catalog tree selected-node header/editor preview affordance.
  - `/catalog-preview` phone-frame shell copy, URL handling, and device preview behavior.
- `apps/web-student`
  - Preview routes under `/preview/catalog/...`.
  - Preview data loaders for catalog nodes and point details.
  - Student catalog browser/detail components reused in preview mode.
- `server/app`
  - Teacher-authorized preview-token creation for catalog nodes.
  - Preview read endpoints for directory nodes, point details, and preview-scoped media.
  - Preview domain authorization rules and route inventory.
- Tests/spec validation
  - Teacher editor preview entry coverage for directory and point.
  - Student preview route coverage for directory node pages and point pages.
  - Backend preview token scope, directory subtree, point detail, media, and non-leakage tests.

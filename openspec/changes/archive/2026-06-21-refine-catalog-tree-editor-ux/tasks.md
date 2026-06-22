## 1. Baseline and Decision Record

- [x] 1.1 Run `openspec validate refine-catalog-tree-editor-ux --strict` before implementation and record the initial pass.
- [x] 1.2 Capture current teacher catalog tree/editor screenshots for the selected chapter, including expanded directory, selected point, right editor default point view, and video panel.
- [x] 1.3 Record current file sizes and responsibilities for `CatalogTreeWorkspacePage.tsx`, `CatalogTreeNodeList.tsx`, `CatalogTreeEditor.tsx`, `catalogTreeMappers.ts`, `catalogTreeHooks.ts`, and `catalogTree.css`.
- [x] 1.4 Audit current tree/editor visible fields and map each field to `content`, `video`, `related`, `student-card`, `publish-checks`, or `advanced`.
- [x] 1.5 Confirm no catalog editor upload controls, hybrid controls, or shortcut controls are being reintroduced before the UX rewrite starts.

## 2. Tree Library Spike and Dependency Decision

- [x] 2.1 Spike `react-arborist` in the admin catalog feature against controlled data, selection, open state, custom row rendering, drag reorder, drag move, invalid drop rejection, and route-local import behavior.
- [x] 2.2 Spike the current Ant Design Tree path against the same visual and interaction criteria, including custom chevrons/spacers, custom drop indicator, full-row selection, hover actions, and keyboard/fallback move support.
- [x] 2.3 Compare `react-arborist`, Ant Design Tree, and rejected MUI X Tree View against dependency cost, design-system fit, styling control, accessibility, virtualization, and testability.
- [x] 2.4 Choose the implementation path and document the decision in an implementation note or task review section.
- [x] 2.5 If a new dependency is selected, add it to `apps/admin-web/package.json` and verify admin build output does not eagerly load it outside the catalog route.

## 3. Catalog Tree Module Boundary

- [x] 3.1 Split tree data shaping helpers out of `CatalogTreeNodeList.tsx` into a catalog-tree owned module.
- [x] 3.2 Create a tree interaction module or adapter that owns expansion, selection, open state, drag/drop state, drop validation, move/reorder API payload creation, and fallback move commands.
- [x] 3.3 Create a tree row renderer module that owns directory/point icon treatment, chevron/spacer treatment, title/status layout, hover/focus actions, drag handle, and row menu.
- [x] 3.4 Keep `CatalogTreeWorkspacePage.tsx` as route orchestration for selected chapter, selected node, search, create modal, and mutations.
- [x] 3.5 Update import-boundary validation or focused tests so tree interaction code does not import point editor panels or media upload feature modules.

## 4. Polished Tree Interaction

- [x] 4.1 Implement the source-list row visual system with aligned chevrons/spacers, same-size directory/point icons, full-row selection, compact status, quiet guide lines, and stable row heights.
- [x] 4.2 Remove always-visible row move-up and move-down controls from the tree.
- [x] 4.3 Add contextual hover/focus/selected row actions for add child, archive/restore, publish action where supported, copy id, and more actions.
- [x] 4.4 Implement valid drag reorder within a parent and valid drag move into directory parents with clear drop indicators.
- [x] 4.5 Reject invalid drops onto point nodes, into descendants, or across disallowed chapter boundaries before persistence.
- [x] 4.6 Preserve selected node and expanded ancestor context after successful move/reorder refresh where practical.
- [x] 4.7 Add keyboard/menu fallback movement for accessible reorder/move flows.
- [x] 4.8 Verify long chemistry titles truncate without overlapping status, drag handles, disclosure controls, or action menus at narrow laptop admin widths.

## 5. Selected-Node Editor Information Architecture

- [x] 5.1 Split `CatalogTreeEditor.tsx` into a selected-node header and task-owned panels for content, video, related experiments, student card, publish checks, and advanced/debug.
- [x] 5.2 Implement a sticky selected-node header with status, node kind, title, breadcrumb path, compact point video status/count, preview action where available, publish/unpublish, and archive/restore.
- [x] 5.3 Make point default content prioritize point title, teacher-only note, principle mode, equation/text principle content, phenomenon explanation, and safety note.
- [x] 5.4 Make directory default content prioritize directory title, teacher-only note, student-visible description, and directory card presentation entry point.
- [x] 5.5 Move raw Node ID, parent id, display order, search-index diagnostics, validation internals, and debug JSON into advanced or publish-check panels.
- [x] 5.6 Move related-link selection, relation type, label, hidden flag, and sort order into the related experiments panel.
- [x] 5.7 Move existing-media selector, preview, bind, unbind, publish, and unpublish controls into the video panel.
- [x] 5.8 Keep the video panel binding-only and add a clear navigation hint to the media/video upload page for new uploads.

## 6. Title and Form Mapping

- [x] 6.1 Define deterministic UI mapping for point node title and point content title so teachers see one primary point-name field.
- [x] 6.2 Update point content form hydration to populate the primary point title from the documented mapping.
- [x] 6.3 Update point content and node-save payload builders to keep node title and point title synchronized by default.
- [x] 6.4 If loaded data contains divergent node and point titles, surface mismatch diagnostics only in advanced/debug context.
- [x] 6.5 Add mapper tests for point title synchronization, directory title behavior, and divergent-title handling.

## 7. Student Card Panel Boundaries

- [x] 7.1 Move directory card image, icon, accent, layout variant, and student-visible description controls into the student-card panel.
- [x] 7.2 Move constrained point card overrides into the student-card panel without allowing arbitrary point layout editing.
- [x] 7.3 Add defaults in the UI for point cards when cover/image/icon/accent overrides are absent.
- [x] 7.4 Add component or mapper tests that directory card controls and point card controls render only for the relevant node kind.

## 8. Tests and Visual QA

- [x] 8.1 Add focused tests for tree row rendering: expandable directory, collapsed directory, point leaf spacer, selected row, long title, status, and contextual actions.
- [x] 8.2 Add focused tests for valid reorder/move payloads and invalid drop rejection.
- [x] 8.3 Add focused tests for selected-node editor default point view, default directory view, video panel, related experiments panel, publish checks, and advanced/debug panel.
- [x] 8.4 Add browser or Playwright screenshot checks for catalog tree states at common admin widths, including a narrow laptop-width viewport.
- [x] 8.5 Add browser or Playwright screenshot checks for the selected-node editor default point view and video/advanced panels.
- [x] 8.6 Run a visual overlap inspection for tree rows and editor header/buttons, and document any accepted limitation.

## 9. Full Validation

- [x] 9.1 Run `openspec validate refine-catalog-tree-editor-ux --strict`.
- [x] 9.2 Run `openspec validate --all --strict --no-interactive`.
- [x] 9.3 Run `git diff --check`.
- [x] 9.4 Run admin frontend `typecheck`.
- [x] 9.5 Run admin frontend tests.
- [x] 9.6 Run admin frontend `validate:boundaries`.
- [x] 9.7 Run admin frontend production build and build-report.
- [x] 9.8 Run the catalog visual/browser QA checks and record the result.
- [x] 9.9 Smoke-test the running admin catalog page in the in-app browser at `http://localhost:5174/overview` or the catalog route used by the app.
- [x] 9.10 Confirm repository search finds no live catalog editor upload control, hybrid editor control, shortcut editor control, or always-visible tree move-up/down control outside tests/docs/archive allowances.

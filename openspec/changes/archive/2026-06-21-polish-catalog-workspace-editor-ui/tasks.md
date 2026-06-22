## 1. Baseline And Scope

- [x] 1.1 Run `openspec validate polish-catalog-workspace-editor-ui --strict` before implementation and record the initial pass.
- [x] 1.2 Confirm the working tree contains only expected pre-existing untracked artifact directories before editing.
- [x] 1.3 Audit current catalog workspace/editor component ownership for the chapter selector, empty state, selected-node header, tabs, and right-panel styling.

## 2. Left Chapter Switcher

- [x] 2.1 Replace the left panel's full-width chapter `Select` with a title-level chapter switcher in `CatalogTreeWorkspacePage.tsx`.
- [x] 2.2 Reuse the existing chapter options, loading state, `chapterId`, and `setChapterId` behavior without introducing a parallel chapter state model.
- [x] 2.3 Keep the search input dedicated to catalog node/content search and update markup/classes so the filter bar no longer reserves space for chapter switching.
- [x] 2.4 Add accessible labels, focus treatment, and long-title overflow handling for the chapter title switcher.

## 3. Right Workbench Surface

- [x] 3.1 Update `CatalogTreeEditor.tsx` so selected and no-selection states share a cohesive right-side workbench shell.
- [x] 3.2 Redesign the no-selection state with feature-local markup and copy that invites selecting a directory or point.
- [x] 3.3 Integrate `CatalogEditorHeader` visually into the workbench without changing publication, archive/restore, preview, or status behavior.
- [x] 3.4 Update tab and content-section styling so the selected-node header, tabs, and active panel read as one surface rather than disconnected cards.
- [x] 3.5 Preserve directory/point tab filtering, form hydration, save behavior, media binding, related-link, validation, and advanced-panel behavior.

## 4. Verification

- [x] 4.1 Run focused catalog/admin frontend tests or typecheck for the touched feature.
- [x] 4.2 Run `openspec validate polish-catalog-workspace-editor-ui --strict` after implementation.
- [x] 4.3 Run browser or screenshot QA for no-selection and selected-node states if the admin dev server can run locally.
- [x] 4.4 Search the touched code to confirm no duplicate full-width chapter dropdown remains in the catalog left panel.
- [x] 4.5 Review `git diff` to ensure changes remain scoped to the OpenSpec files and catalog-tree frontend modules.

## 1. Baseline And Scope

- [x] 1.1 Read `proposal.md`, `design.md`, and all spec delta files for this change before editing implementation code.
- [x] 1.2 Run `openspec validate catalog-sidebar-status-count-header-polish --strict` and record the initial pass.
- [x] 1.3 Inspect the current catalog tree row, tree header, workspace heading, catalog API type, and backend node card read-model files to confirm the exact edit surface.
- [x] 1.4 Capture or review the current browser state showing raw English status tags, duplicate add controls, small icons, and missing directory point counts.

## 2. Backend Recursive Point Count

- [x] 2.1 Add `descendant_point_count` to the backend catalog node card read-model query in the catalog tree domain.
- [x] 2.2 Define `descendant_point_count` as the count of non-archived descendant `point` nodes under a directory across all nested levels.
- [x] 2.3 Return `descendant_point_count: 0` for point node cards.
- [x] 2.4 Ensure root node, child node, selected detail, search/list, and any other admin `CatalogNodeCard` responses include the field consistently.
- [x] 2.5 Keep the field additive and avoid database migration unless existing schema or query constraints unexpectedly require one.
- [x] 2.6 Add or update backend tests for multi-level directory counts, empty directories, point cards, archived descendants, and moved subtrees.
- [x] 2.7 Verify the recursive count query does not introduce obvious N+1 behavior beyond the centralized read-model query path for the expected catalog size.

## 3. Admin API Contract And Fixtures

- [x] 3.1 Extend `CatalogNodeCard` in the admin catalog API client with `descendant_point_count: number`.
- [x] 3.2 Update catalog tree test fixtures, mapper fixtures, and mock node helpers with the new field.
- [x] 3.3 Add or update API/contract tests so missing `descendant_point_count` is caught during admin test runs.

## 4. Sidebar Status, Count, And Icon Rendering

- [x] 4.1 Add centralized Chinese status label mapping for `published`, `draft`, and `archived`.
- [x] 4.2 Add centralized status dot color/class mapping for published, draft, and archived states.
- [x] 4.3 Replace visible raw status text in the left tree row with the status-dot system and Chinese accessible labels/tooltips.
- [x] 4.4 Ensure selected, hovered, focused, and assistive states expose Chinese labels such as `已发布`, `草稿`, and `已归档` without visible raw backend enum text.
- [x] 4.5 Render directory `descendant_point_count` as quiet trailing metadata and ensure it is not derived from loaded client children.
- [x] 4.6 Render point-specific video completion metadata only for point rows and never as a directory descendant count.
- [x] 4.7 Increase and align folder and experiment point icons so they read clearly at sidebar density.
- [x] 4.8 Keep validation warning icons visually distinct from status dots.
- [x] 4.9 Update row CSS so counts, status dots, warnings, hover actions, and long titles do not shift or overlap each other.
- [x] 4.10 Confirm point rows do not show child-add controls and directory rows retain contextual child-add access.

## 5. Tree Header And Root Creation Simplification

- [x] 5.1 Remove the duplicate chapter-heading `目录 / 点位` root creation buttons from the left panel heading.
- [x] 5.2 Remove or demote any other visible page-level root creation button that competes with the chosen tree-toolbar add surface.
- [x] 5.3 Keep chapter heading focused on chapter context: `当前章节` and the formatted chapter title.
- [x] 5.4 Replace the tree header add button with a compact toolbar `+` action.
- [x] 5.5 Make the toolbar `+` menu provide Chinese entries for `新建目录` and `新建点位`.
- [x] 5.6 Move secondary tree commands such as refresh, expand all, or collapse all into a subtle icon or more menu if they remain visible.
- [x] 5.7 Ensure the tree header has one obvious root creation surface and no implementation wording such as `root node`.

## 6. Admin Frontend Tests

- [x] 6.1 Update tree row tests to assert directory status dot, Chinese status label accessibility, directory count rendering, and larger experiment icon rendering.
- [x] 6.2 Update point row tests to assert point icon rendering, point video metadata behavior, and absence of directory descendant count.
- [x] 6.3 Add tests that visible left-tree row text does not contain raw `published`, `draft`, or `archived`.
- [x] 6.4 Add tree header/workspace tests asserting a single root creation surface and Chinese menu entries for directory and point creation.
- [x] 6.5 Update catalog tree data or mapper tests for the new `descendant_point_count` field.
- [x] 6.6 Run admin frontend tests covering catalog tree modules.
- [x] 6.7 Run admin frontend typecheck.

## 7. Browser And Visual QA

- [x] 7.1 Start or reuse the local admin preview/dev server for the teacher catalog workspace.
- [x] 7.2 Capture the left tree at normal admin width with at least one selected directory and one visible point child.
- [x] 7.3 Capture the left tree at narrow laptop width to verify no title/count/action overlap.
- [x] 7.4 Verify visually that status dots replace English tags, directory counts appear as quiet trailing numbers, icons are legible, and root creation controls are not duplicated.
- [x] 7.5 Verify row hover/selected states keep actions available without shifting chevrons, icons, titles, counts, or status dots.

## 8. Final Validation

- [x] 8.1 Run backend tests covering the catalog tree recursive count read model.
- [x] 8.2 Run admin frontend tests, typecheck, and production build.
- [x] 8.3 Run any existing import-boundary or architecture validation relevant to admin catalog tree changes.
- [x] 8.4 Run `openspec validate catalog-sidebar-status-count-header-polish --strict`.
- [x] 8.5 Update `tasks.md` checkboxes as each task is completed and record any intentional deviations in implementation notes if needed.

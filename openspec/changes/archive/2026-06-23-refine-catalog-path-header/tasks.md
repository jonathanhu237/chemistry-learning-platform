## 1. Catalog Breadcrumb Rail

- [x] 1.1 Replace the old `章节学习目录` / protected-path header with a two-line catalog navigation rail.
- [x] 1.2 Keep the learning scope/root chip in the first row and keep `搜索` / `更多` fixed in the first-row action cluster.
- [x] 1.3 Render child directory breadcrumbs in a second horizontal rail only when the student is inside a nested directory.
- [x] 1.4 Highlight the current directory as the rightmost selected breadcrumb chip.
- [x] 1.5 Remove the old `上一级` action and make root/ancestor chips navigate directly to their directory level.
- [x] 1.6 Remove protective text truncation from breadcrumb chips so long names display at natural width and the rail scrolls horizontally.

## 2. Search Path Metadata

- [x] 2.1 Update unified search results to show direct parent directory as primary path metadata.
- [x] 2.2 Demote ancestor context to weak metadata and avoid rendering the result itself inside a long full-path string.

## 3. Tests

- [x] 3.1 Update student H5 route tests to assert that the catalog header no longer shows `章节学习目录`, `章节学习目录下`, or `上一级`.
- [x] 3.2 Add route test coverage for root-row separation, absence of a child breadcrumb row at root, nested child breadcrumb rendering, current-chip highlighting, and ancestor-chip jump navigation.
- [x] 3.3 Add search-result assertions for result title, `父目录：<direct parent>`, and weak ancestor context.

## 4. Verification

- [x] 4.1 Run the relevant student H5 tests, typecheck, and build.
- [x] 4.2 Update the running web-student container after a successful build.

## Why

The chapter catalog header previously tried to compress orientation into one protected text line. That matched neither the current implementation nor the desired mobile behavior: when a path can scroll horizontally, path chips should remain fully readable instead of being truncated. Students need to see the learning scope, current catalog depth, and actions without a separate `上一级` control.

## What Changes

- Replace the old `章节学习目录` label/path row with a two-line catalog navigation rail.
- Row 1 fixes the learning scope chip on the left and keeps `搜索` / `更多` actions on the right.
- Row 2 renders only child directory breadcrumbs from root to the current directory, left-to-right, in a horizontally scrollable rail.
- Breadcrumb chips render at natural text width without `max-width`, ellipsis, or protective truncation; overflow is handled by horizontal scrolling.
- The rightmost/current breadcrumb chip uses the selected style. Clicking any breadcrumb chip jumps directly to that directory, so `上一级` is not shown.
- Unified search results keep the result title first, emphasize the direct parent directory, and demote ancestor context to a weak hint.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-learning-flow`: chapter catalog pages must expose mobile orientation through a two-line, horizontally scrollable breadcrumb rail rather than a protected single-line path label.

## Impact

- Affects student H5 chapter catalog UI in `apps/web-student/src/routes/learn/FamilyCatalogShell.tsx`.
- Affects student H5 catalog/search styling in `apps/web-student/src/styles/learning.css`.
- Updates student H5 route tests covering catalog header, breadcrumb navigation, search path metadata, and removal of the old `上一级` / `章节学习目录` header contract.

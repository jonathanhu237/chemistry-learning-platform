## Why

The periodic-table learning entry already acts as the primary area selector, but tapping an area currently opens a plain second-level list page whose content is only another short chapter choice. Replacing that intermediate page with an anchored, collision-aware popover keeps selection in the same visual context and reserves route navigation for real chapter learning pages.

## What Changes

- Change the student learning root so area controls and element cells open an anchored area chapter popover instead of immediately navigating to `/learn/area/$areaId`.
- Render the filtered chapter/family list inside the current phone viewport without pushing, resizing, or extending the page layout.
- Position the popover relative to the tapped area control or element cell, while automatically flipping, shifting, and constraining size so the full list remains visible where possible.
- Dismiss the popover on outside tap, Escape, route change, or chapter selection.
- Navigate directly to the selected chapter/family route when a popover row is selected.
- Keep the existing selected-area detail route as a compatibility fallback for old links and browser history, but stop using it as the primary H5 learning entry flow.
- Add `@floating-ui/react` to student-web to handle anchored placement, viewport collision, dismissal, and focus-safe popover behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-learning-experience`: Changes periodic-table area selection from a separate selected-area chapter list page to an anchored in-place chapter selection popover on the learning root.
- `student-h5-learning-flow`: Changes the periodic-table handoff so chapter routes are opened directly from the anchored area popover, while selected-area routes remain fallback routes rather than the primary interaction.
- `student-h5-mobile-design-system`: Adds viewport-contained anchored popover behavior and styling requirements for touch-first learning selection overlays.
- `student-h5-route-stack-navigation`: Clarifies that the learning root can host an in-place transient selector without becoming a detail route, and that bottom navigation remains visible on the root while the selector is open.

## Impact

- Student frontend dependencies: add `@floating-ui/react` under `apps/web-student`.
- Student frontend code: `LearningEntryPanel`, `PeriodicTable`, `LearningAreaChapterList`, `LearnRootPage`, learning/periodic styles, and learning route tests.
- Existing selected-area route: remains available for direct URL fallback, but is no longer the primary tap target from `/learn`.
- QA and tests: update route expectations from area navigation to in-place popover display, verify chapter navigation from popover rows, and cover fixed-viewport behavior.

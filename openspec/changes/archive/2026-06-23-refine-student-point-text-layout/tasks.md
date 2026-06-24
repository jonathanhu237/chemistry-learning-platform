## 1. Baseline And Ordering

- [x] 1.1 Inspect `CatalogPointDetailPanel.tsx`, `PointVideoPlayer.tsx`, and `experiments.css` to confirm the fixed-player/body-scroll baseline before editing.
- [x] 1.2 Confirm current required point fields are available without API changes: catalog path, title, phenomenon explanation, principle content, safety note, and related points.
- [x] 1.3 Reorder the point detail body so the title area is followed by phenomenon, principle, safety, related experiments, then non-content actions.

## 2. Learning Text Structure

- [x] 2.1 Refactor the point body markup into explicit flat sections for title/path, phenomenon, principle, safety, and related experiments.
- [x] 2.2 Ensure text-mode principle content renders as readable body copy with intentional line breaks preserved.
- [x] 2.3 Ensure equation-mode principle content renders as reaction rows with each equation visually associated with its annotation text.
- [x] 2.4 Reduce repeated annotation-label dominance so `补充说明：` or equivalent labels do not visually overpower every reaction row.
- [x] 2.5 Keep empty or missing content states controlled and readable without collapsing remaining sections into a single paragraph.

## 3. Watch-Page Styling

- [x] 3.1 Update point detail styles to use a flat YouTube-like watch-page body with dividers instead of nested cards.
- [x] 3.2 Tune typography so section headings, body copy, equations, and annotations fit phone widths without looking uniformly bold.
- [x] 3.3 Restrict accent backgrounds to compact equation or safety treatments instead of large colored long-text panels.
- [x] 3.4 Style safety as a compact caution section with clear icon/header treatment and restrained visual weight.
- [x] 3.5 Ensure the scroll body starts below the fixed 16:10 player and section headings are not hidden behind the player.

## 4. Related Experiments And Actions

- [x] 4.1 Render related experiments as vertical video-style rows with a 16:10 placeholder/thumbnail area, title, and secondary relation label.
- [x] 4.2 Preserve existing related-point navigation and teacher-preview disabled behavior.
- [x] 4.3 Keep AI, practice, completion, and assessment handoff controls outside the required learning content hierarchy.
- [x] 4.4 Ensure bottom fixed/floating controls do not permanently cover related experiment rows or final learning content.

## 5. Verification

- [x] 5.1 Add or update focused tests for section order: path/title, phenomenon, principle, safety, related experiments, then actions.
- [x] 5.2 Add or update tests for equation rows with annotations and related experiment video-row classes.
- [x] 5.3 Add or update role-boundary/style contract checks for fixed player spacing and mobile-safe text layout.
- [x] 5.4 Run `npm run typecheck` in `apps/web-student`.
- [x] 5.5 Run focused student H5 tests such as `npm run test -- src/roleBoundaries.test.ts src/App.e2e.test.tsx`.
- [x] 5.6 Build `apps/web-student` and copy the production `dist` into `chemistry-admin-web-student-1:/usr/share/nginx/html` when implementation is requested.

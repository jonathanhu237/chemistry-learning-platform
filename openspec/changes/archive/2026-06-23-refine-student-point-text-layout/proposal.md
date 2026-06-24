## Why

The student point video page has moved to a YouTube-like model with a fixed 16:10 player and a scrollable learning body, but the authored text below the player still reads like undifferentiated blocks of heavy copy. Students need the required point information to be quickly scannable after watching the video: full title, catalog path, phenomenon, principle, safety note, and related experiments.

This change captures the current product decision: keep the point player fixed at the top, organize the content below it as a flat mobile watch page, and use learning-note hierarchy inspired by YouTube watch pages and Coursera mobile lecture notes rather than card-heavy lesson pages.

## What Changes

- Refine the student H5 point detail body below the fixed video player into a structured watch-page learning layout.
- Keep the required content visible in the page flow: full experiment title, catalog path, phenomenon explanation, experiment principle, safety note, and related experiment links.
- Reorder the learning copy so the student sees observation/phenomenon before the underlying principle, matching the post-video mental model of "what did I see" before "why did it happen".
- Render equation-mode principles as readable reaction rows with associated annotations, avoiding repeated heavy "补充说明：" labels as the dominant visual text.
- Keep the page flat and YouTube-like: use separators, compact section headers, and video-style related experiment blocks instead of nested cards or large colored panels.
- Treat AI, practice, and completion controls as actions, not part of the core learning content hierarchy.
- Preserve existing student/preview data contracts and related-point navigation behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `student-h5-learning-experience`: Refines the student point video detail page's required text hierarchy, section order, and related experiment presentation below the fixed player.

## Impact

- Affected frontend components:
  - `apps/web-student/src/features/catalog/CatalogPointDetailPanel.tsx`
  - `apps/web-student/src/features/catalog/PointVideoPlayer.tsx` only if player/body spacing needs coordination
  - `apps/web-student/src/styles/experiments.css`
- Affected tests:
  - `apps/web-student/src/App.e2e.test.tsx`
  - `apps/web-student/src/roleBoundaries.test.ts`
  - Any visual/mobile QA scripts that cover point detail pages
- No backend API changes are expected.
- No new dependencies are expected.
- Existing teacher preview behavior must remain read-only and visually aligned with normal student H5 where possible.

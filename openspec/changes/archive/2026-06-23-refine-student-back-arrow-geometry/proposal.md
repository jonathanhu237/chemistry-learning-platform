## Why

Student H5 second-level back arrows currently look too tall, too short-tailed, too thick, and too far from the left edge compared with mature mobile references such as X/Twitter and Bilibili. The issue affects navigation trust because ordinary detail pages, video detail pages, and search/detail-style pages should feel like the same route-stack back control even when the video player owns the top chrome.

## What Changes

- Replace Lucide's generic `ArrowLeft` usage for student H5 second-level back affordances with one shared, hand-authored SVG geometry.
- Draw the arrow from geometry derived from the reference screenshots rather than by cropping or embedding a bitmap.
- Preserve a phone-safe touch target while adjusting only the visual glyph and visual placement:
  - lower the arrow's visual height,
  - extend the horizontal tail,
  - slightly reduce stroke weight,
  - move the glyph/control visually left so the effective left whitespace is about 60% of the current student implementation.
- Use the same shared arrow source for React-rendered back buttons and ArtPlayer HTML-layer back buttons.
- Keep point-video player behavior unchanged: the back arrow is part of the video/player chrome and appears with the player controls, while the empty-video state still provides a visible back affordance.
- Add tests or source-level guards so future edits do not reintroduce inconsistent arrow sizes, independent SVG strings, excessive left offset, or Lucide-only geometry for these second-level controls.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-mobile-design-system`: Define the shared second-level back arrow geometry, sizing, touch-target, and placement contract for student H5 mobile screens.
- `student-h5-route-stack-navigation`: Require all non-tab/detail route back affordances, including video-player chrome and search/detail-style pages, to use the shared back control semantics and visual treatment.

## Impact

- Affected student-web code likely includes:
  - `apps/web-student/src/shared/mobile/PageBar.tsx`
  - a new or updated shared mobile arrow primitive/module
  - `apps/web-student/src/features/catalog/PointVideoPlayer.tsx`
  - `apps/web-student/src/routes/search/UnifiedSearchPage.tsx`
  - `apps/web-student/src/styles/app-shell.css`
  - `apps/web-student/src/styles/experiments.css`
  - `apps/web-student/src/styles/learning.css`
  - `apps/web-student/src/roleBoundaries.test.ts` or equivalent student-web regression tests
- No backend API changes.
- No new runtime dependency is expected.
- Existing ArtPlayer adoption remains in place; this change only standardizes the back arrow glyph and layout around it.
- Student container deployment must be refreshed after implementation so the LAN preview serves the new assets.

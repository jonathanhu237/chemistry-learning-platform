## Why

The student H5 home page should become the primary experiment-video discovery surface. Current home behavior is a generic recommendation/action hub, while the product model now treats home as a Bilibili/YouTube-style horizontal experiment video feed that lets students discover textbook experiments through muted autoplay previews and then enter point-level learning.

This is needed now because the catalog has been clarified as a classification/map model, not a guided-learning model. Recommendation and guidance should come from assessment and feed ranking, while the home page should show experiment phenomena directly without forcing a fixed multi-level learning path.

## What Changes

- Replace the current home hero/action-card composition with a student-visible experiment video feed as the main home experience.
- Add a dedicated student home video feed API that returns playable published point videos with catalog path, learning tags, media URLs, and point-detail targets.
- Render feed cards as single-column 16:9 horizontal video previews, not vertical Shorts or two-column thumbnails.
- Implement mature feed behavior inspired by Bilibili/YouTube:
  - only one visible card plays at a time;
  - autoplay is muted and inline;
  - videos start when the card becomes the primary visible item;
  - videos pause when leaving the primary viewport;
  - non-active cards render poster/metadata rather than loading full playback.
- Keep every feed item tied to the textbook catalog by showing the catalog path and routing to the existing experiment point detail page.
- Preserve the existing video-library search page as the precise search/browse surface, but stop treating it as the home page experience.
- Keep AI and assessment as contextual actions from feed items, without turning the feed into a pure entertainment stream.
- Add tests and docs/spec coverage for loading, empty, playback-selection, route, and mobile layout behavior.

## Capabilities

### New Capabilities
- `student-h5-home-video-feed`: Defines the student home experiment-video feed, its API contract, autoplay preview behavior, and catalog-backed learning context requirements.

### Modified Capabilities
- `student-h5-learning-experience`: Home must be an experiment-video discovery surface while learning remains the catalog/map surface.
- `student-h5-video-library-search`: Video library search remains a second-level search/browse tool and must not be the primary home feed implementation.
- `student-h5-mobile-design-system`: Home video cards must preserve mobile-safe 16:9 media layout, bottom navigation clearance, and non-overlapping controls.
- `student-h5-route-stack-navigation`: Feed actions must route to point detail, AI, or video-library search without corrupting root-tab identity or back behavior.

## Impact

- Backend:
  - Add student-facing home video feed schemas and API route.
  - Reuse published catalog point placements and student-visible media bindings.
  - Do not put `stream_path` or `thumbnail_path` into the Elasticsearch video-library search index.
- Student H5 frontend:
  - Replace `HomeRootPage` with a video feed implementation.
  - Add feed API types/client helpers.
  - Add a reusable autoplay/visibility controller for feed cards.
  - Add CSS for mobile 16:9 feed cards and safe bottom navigation spacing.
- Tests:
  - Extend student H5 e2e/unit coverage for home feed data loading, card rendering, navigation, and single-active-video behavior.
  - Add backend/API coverage for feed filtering and published-media resource fields where feasible.
- Documentation:
  - Use `docs/student-product-learning-model.md` as the product logic reference for the home/learn/AI/assessment/my mental model.


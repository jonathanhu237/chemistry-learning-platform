## Why

The home video feed header is part of the root browsing chrome, but the attempted title-height scroll interception made the page feel heavy and unpredictable on phone WebViews. We need to standardize the home title and recommendation tag rail on the same lightweight quick-return behavior used by the existing root navigation chrome.

## What Changes

- Treat the home logo/title area and horizontal recommendation tag rail as one collapsible header unit.
- Replace title-height scroll locking/interception with the existing direction-based quick-return pattern: scrolling down may compress the home header, and reverse scroll restores it.
- Keep the video feed as the native page scroll owner; the header must not require blocking `touchmove`, wheel interception, synthetic scroll replay, or nested-scroll transfer logic.
- Keep the recommendation rail visually and functionally attached to the home header, including the default `推荐` tag.
- Preserve second-level video-library search behavior and root-tab identity while changing only the home root chrome behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-platform-shell`: Home root header behavior changes to use lightweight quick-return compression/restore as root shell chrome.
- `student-h5-video-discovery`: Home video discovery owns a header-attached recommendation tag rail above the feed.
- `student-h5-mobile-design-system`: Mobile scroll chrome must remain native and performance-safe without active scroll interception for header collapse.

## Impact

- Affected frontend code is primarily under `apps/web-student/src/app/shell`, `apps/web-student/src/routes/home`, and shared student H5 styles.
- No backend API, search index, route contract, or data schema changes are required.
- Tests should cover the home header/tag rail rendering, default selected tag, native feed scrolling, and regression against reintroducing blocking scroll interception.

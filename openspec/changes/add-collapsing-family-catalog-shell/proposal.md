## Why

The current selected family/chapter page correctly combines element context and catalog navigation, but its large element cards push the catalog browser too far down the phone viewport. Students need the page to feel like one family-scoped catalog browser: the family elements stay visible as context, while the catalog tree remains the primary learning task.

## What Changes

- Redesign the student H5 chapter/family page as a Spotify/Apple Music inspired detail surface: an attractive expanded family context header at the top that collapses into a slim sticky element rail during catalog scrolling.
- Keep the selected family context stable while students open child catalog directories; opening a directory must update the catalog browser content without losing the family element rail.
- Make the catalog tree the main body of the family page by compressing the selected-element summary into short focus copy, compact chips, and a small detail affordance.
- Preserve the existing element-detail route for full atom/fact exploration and the existing point-detail route for video/detail learning.
- Update mobile visual QA and tests to lock the expanded/collapsed header behavior, catalog discoverability, and directory-shell continuity.

## Capabilities

### New Capabilities
- `student-h5-family-catalog-shell`: Defines the family-scoped catalog browser shell, including the collapsible element context header and persistent catalog navigation body.

### Modified Capabilities
- `student-h5-learning-experience`: Chapter/family pages must prioritize catalog navigation while keeping compact element context visible.
- `student-h5-learning-flow`: Directory navigation from a family page must remain inside the family catalog shell instead of dropping the family context.
- `student-h5-route-stack-navigation`: Catalog directory routes opened from chapter learning must preserve the selected profile context and render with the family shell when that context is available.
- `student-h5-mobile-design-system`: Mobile sticky/collapsing headers must remain small, responsive, and content-preserving on phone viewports.

## Impact

- Affects student H5 React routes/components around `ChapterStudyPage`, `CatalogDirectoryPage`, `LearningHomePanel`, `CatalogChapterPanel`, and catalog navigation helpers.
- Affects student H5 styles in learning/catalog/mobile CSS.
- No new backend APIs are expected; the implementation should reuse existing learning profile and catalog node endpoints.
- No teacher UI change is expected.

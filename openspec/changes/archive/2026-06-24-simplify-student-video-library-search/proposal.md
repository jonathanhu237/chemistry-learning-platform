## Why

The student video-library search default state is currently too heavy for a phone-first search surface: it renders multiple browse-category cards before students can act. The desired behavior is closer to a familiar mobile video search page: recent searches first, then recommended videos with thumbnails, plus only lightweight recommended terms when video recommendations are unavailable.

This is needed now because the home feed has become the visual experiment-video discovery surface, while `/video-library` should behave like a focused search page rather than another card-based catalog browser.

## What Changes

- Replace the no-query video-library default state with a simple list composition:
  - recent local search history at the top, limited to a few rows;
  - recommended experiment videos below history, rendered as compact rows with a thumbnail before the diagonal refill/search arrow affordance;
  - recommended search terms as a lightweight fallback or secondary section, not as categorized cards.
- Remove the current browse-category card grid from the no-query state; phenomenon/reagent/chapter/family chips may still provide the recommended-term source but MUST NOT render as the old two-column classification card grid.
- Preserve the current query/search-results behavior, result grouping, actionable route targets, back behavior, and hidden bottom navigation semantics.
- Keep recommended videos learning-oriented: rows open the existing point/chapter/AI targets and show student-facing point title, context, and available video thumbnail/poster.
- Persist only a small local search history for convenience; do not require backend user-history tracking for this change.
- Add tests and mobile layout checks for empty/default, history, recommended-video, recommended-term fallback, and query-result states.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-video-discovery`: Refine the video-library no-query/default state from broad browse-card organization to a simple mobile search default with recent searches, recommended video rows, and recommended terms.

## Impact

- Student H5 frontend:
  - Update `apps/web-student/src/routes/video-library/VideoLibraryPage.tsx`.
  - Update `apps/web-student/src/styles/video-library.css`.
  - Reuse the existing local-storage search-history approach from the chapter search page with a separate video-library key.
- Backend/API:
  - No new endpoint is required.
  - Existing `browse.recommended` and `browse.chips` can drive the new default state.
  - Existing recommendation result items may need thumbnail/poster metadata in a follow-up if current route targets cannot supply a usable image.
- Tests/QA:
  - Extend student H5 e2e/unit coverage for default-state history, recommended videos, fallback recommended terms, and search-result preservation.
  - Verify mobile widths around 360px, 390px, and 430px for non-overlapping rows, thumbnails, search input, and diagonal arrow actions.

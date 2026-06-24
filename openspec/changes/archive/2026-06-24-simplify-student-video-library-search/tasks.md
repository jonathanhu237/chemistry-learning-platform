## 1. Default-State Data

- [x] 1.1 Add video-library-specific local search history helpers with a separate `localStorage` key, capped and deduped like the chapter search page.
- [x] 1.2 Record only committed video-library searches: form submit, recommended-term selection, and opening a result for a non-empty query.
- [x] 1.3 Load a small existing home video feed payload on the no-query video-library page to provide thumbnail-backed recommended video rows.
- [x] 1.4 Build a recommendation source fallback order: home feed items with thumbnails or poster data first, then existing `browse.recommended`, then `browse.chips` as recommended terms.

## 2. Default-State UI

- [x] 2.1 Replace the current `DefaultBrowse` categorized card panels with a simple list-style default state.
- [x] 2.2 Render local recent search rows above recommendations, with a history icon and diagonal arrow action.
- [x] 2.3 Render recommended video rows with title, context, stable cover slot, and a diagonal arrow action immediately to the right of the thumbnail.
- [x] 2.4 Render recommended search terms as lightweight rows or compact text actions when video recommendations are empty or insufficient.
- [x] 2.5 Preserve existing non-empty query grouped result rendering and all point/chapter/AI route target behavior.

## 3. Mobile Styling

- [x] 3.1 Remove or stop using the no-query category card grid styles for `video-chip-panel`, `video-recommended-panel`, and `video-library-chip-grid`.
- [x] 3.2 Add stable row layouts for history rows, recommended video rows, thumbnail slots, cover fallbacks, and diagonal arrow actions.
- [x] 3.3 Verify 360px, 390px, and 430px widths keep search input, text, thumbnails, and arrows from overlapping.

## 4. Tests and QA

- [x] 4.1 Update student app test mocks so video-library default recommendations can use existing home video feed thumbnail data.
- [x] 4.2 Add or update e2e coverage for no-query history rows, recommended video rows, recommended search terms, and preserved query search results.
- [x] 4.3 Add assertions that local history is not polluted by every debounced keystroke.
- [x] 4.4 Run student frontend typecheck and relevant student e2e tests.

## 5. Acceptance Polish

- [x] 5.1 Simplify recommended video rows to title plus one fixed single-line path, with no snippet, badges, explanation text, or action text.
- [x] 5.2 Keep recommended video row height, thumbnail slot, and diagonal arrow alignment stable on narrow mobile widths.
- [x] 5.3 Add test coverage that recommended video rows do not render snippet or badge content in the no-query default state.

## 6. Learning Chapter Tag Polish

- [x] 6.1 Map recommended video targets to frontend learning page profiles by `profile_id` or `chapter_id`.
- [x] 6.2 Render one compact gold learning-page chapter tag as the third line of each mapped recommended video row.
- [x] 6.3 Add coverage that the default recommended video row shows the learning-page chapter tag and does not render backend textbook chapter badge text.

## 7. Query Result Scope Reuse

- [x] 7.1 Replace the query-filled video-library grouped card result state with a flat `关于“query”的实验视频` list.
- [x] 7.2 Reuse the video-library search shell for the learning `/search` route.
- [x] 7.3 Limit home video search results to videos while allowing learning search to show videos plus catalog directory results.
- [x] 7.4 Route learning catalog directory result taps to the corresponding learning catalog directory page.
- [x] 7.5 Add e2e coverage for learning search video and directory result behavior.

## 8. Query Result Polish

- [x] 8.1 Suppress the browser-native search clear affordance so the search bar shows only one clear action.
- [x] 8.2 Replace empty query-result banners/cards with a simple `这里什么都没有哦~` message.
- [x] 8.3 Make query-result video rows match the recommended-video standard: title, path, required learning chapter tag, optional thumbnail, and diagonal arrow.
- [x] 8.4 Remove thumbnail placeholder slots when no thumbnail is available.
- [x] 8.5 Add e2e coverage for empty query results and standardized query-result video rows.

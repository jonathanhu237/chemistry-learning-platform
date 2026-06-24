## Context

`/video-library` is a second-level student H5 page opened from home. It currently performs an empty query against `searchStudentVideoLibrary("")` and renders the no-query state as two card panels:

- a categorized two-column chip grid for phenomena, reagents, and chapters;
- a recommended experiment result-card panel.

This makes the page feel like another catalog browsing surface. The desired direction is a phone-native search page similar to mobile video search: search bar first, recent query rows, then recommended video rows with small cover thumbnails and a diagonal arrow refill affordance.

Existing relevant data sources:

- `searchStudentVideoLibrary(query)` returns grouped search results plus `browse.recommended` and `browse.chips`.
- `getStudentHomeVideoFeed(limit)` already returns playable feed items with `video.thumbnail_path`, stream paths, catalog path, and point route targets.
- The chapter search page already stores local search history in `localStorage`; the video library should use the same pattern with a separate key.

## Goals / Non-Goals

**Goals:**

- Make the no-query video-library state simple: history first, recommended videos second, recommended search terms as fallback/secondary.
- Remove the current default-state category card grid.
- Render recommended videos as compact suggestion rows with only title, one-line path/context, a thumbnail cover slot, and a diagonal arrow action on the right.
- Keep typed search, grouped results, result navigation, and back behavior unchanged.
- Preserve the existing search-index contract: video-library search documents remain point-learning documents, not media-resource documents.

**Non-Goals:**

- Do not redesign the home video feed.
- Do not add a global search tab or home search bar.
- Do not add backend per-user search-history tracking.
- Do not autoplay videos inside the video-library search default state.
- Do not expose media asset IDs, original filenames, or teacher-only video labels through search results.

## Decisions

1. Store recent searches locally, not on the backend.

   The page will add helpers mirroring `UnifiedSearchPage`: read, write, and remember recent queries under a new key such as `student.videoLibrarySearch.history.v1`. Store only trimmed non-empty strings, dedupe by exact text, and cap the list around 8 entries. The default view should render only the first few rows so it stays compact.

   Searches should be remembered on committed actions: pressing submit, tapping a recommended term, or opening a result for a non-empty query. The implementation should not save every debounced keystroke, because the current input updates the URL while typing.

2. Treat recommended videos as video rows, not browse cards.

   The default state should prefer actual recommended videos. Recommended video rows should open the existing point route target and keep the `from=video-library` source. The row shape should be:

   ```text
   [video/search icon]  title
                        one-line catalog/path         [thumbnail]  [arrow-up-left]
                        learning-page chapter tag
   ```

   Rows are full-width, transparent or lightly highlighted list items, not cards inside a card panel. Each row should have a stable height and should not show snippets, backend badges, explanatory text, or action labels. The small chapter tag is the only badge-like element, and it must be derived from the frontend learning page profile label by `profile_id`/`chapter_id`, not from backend textbook chapter badges such as "chapter 13" or "chapter 14". On narrow widths, the thumbnail remains a stable fixed-size slot before the arrow; title, path, and chapter tag truncate rather than pushing the arrow offscreen.

3. Use existing home-feed media data for thumbnails when possible.

   The cleanest implementation is to request a small `getStudentHomeVideoFeed` payload on the default video-library page and use those feed items as thumbnail-backed recommendations. This reuses an existing student-visible API that already contains `thumbnail_path`, avoids a new endpoint, and avoids putting video resource metadata into the Elasticsearch/search-document contract.

   If the feed is empty or fails, fall back to `payload.browse.recommended` without thumbnails. The UI must still render a nonblank cover slot, such as the existing video poster fallback, so the layout remains YouTube-like even when a real thumbnail is unavailable.

4. Recommended search terms are a fallback or lower-priority section.

   `payload.browse.chips` remains useful as a source of terms, but the UI should render them as simple rows or compact text buttons under a heading such as `推荐搜索`. It should not show category labels like `现象`, `试剂`, or `章节` as card metadata in the no-query state.

5. Preserve current query-result behavior.

   Once `query.trim()` is non-empty, the page switches from the default history/recommendation state to a direct result state headed by `关于“query”的实验视频` for the home/video scope. The result state should render flat video rows from the existing ES-backed video-library search payload, not the previous grouped card layout.

6. Reuse the same search page model for learning search.

   The learning `/search` route should reuse the video-library search shell and state model instead of maintaining a separate UI. Its scope differs from the home/video scope:

   - home/video scope shows only experiment-video results;
   - learning scope shows experiment-video results plus catalog directory results;
   - learning catalog results can be derived from the current chapter catalog index, including parent directories for matching point rows;
   - only learning scope can open catalog directory results, navigating to the corresponding learning catalog second-level page.

## Risks / Trade-offs

- [Risk] Fetching both empty search browse data and home feed data could add one extra request to the default page. → Mitigation: limit home feed recommendations to a small count and keep the existing search request because it still supplies status, fallback messages, and recommended terms.
- [Risk] Home feed recommendations and search `browse.recommended` may not contain the same ordering. → Mitigation: prefer home feed rows when thumbnails are available, and use search browse recommendations only as fallback; both sources route to point detail targets.
- [Risk] Recording debounced query changes would pollute history. → Mitigation: record only committed searches and selected recommended terms/results.
- [Risk] Thumbnail dimensions can squeeze text on 360px phones. → Mitigation: use fixed thumbnail and arrow columns, truncate text, and verify 360px, 390px, and 430px widths.
- [Risk] Search-result specs forbid relying on media metadata. → Mitigation: keep thumbnails scoped to the no-query recommendation rows and source them from the existing home feed API, not from ES/search document source.

## Open Questions

- If product later wants server-side personalized search history, that should be a separate change because it affects identity, privacy, and backend storage.

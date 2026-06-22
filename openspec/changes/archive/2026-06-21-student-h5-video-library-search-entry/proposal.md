## Why

The student H5 home page should not become a dry global search surface. The app is centered on experiment-video learning, so discovery should start from a focused experiment video library entry and let students search for experiment phenomena, reagents, video points, and related knowledge inside a dedicated second-level page.

This keeps the home page lightweight while giving the video-centered workflow enough room for browsing, Elasticsearch-backed search, and route-stack navigation into real learning pages.

## What Changes

- Add a home-page entry card for an experiment video library.
- Add a second-level video library page opened from the home page, with bottom navigation hidden and source-aware return behavior.
- Define "second-level page" as a semantic route role: any non-root, non-bottom-tab task/collection/detail page that can be opened from one or more sources, regardless of its current history-stack depth.
- Place the search box inside the video library page rather than on the home page.
- Scope the video-library search to experiment-video learning content:
  - experiment videos
  - video points / observation points
  - experiment phenomena
  - reagents / medicines / apparatus keywords
  - related chapters, elements, and knowledge points
- Back the search with Elasticsearch or an Elasticsearch-compatible service.
- Organize default library content so the page is useful before a search:
  - continue/recent learning where available
  - recommended experiment videos
  - browse by phenomenon, reagent, chapter, element family, or knowledge point
- Ensure every search result is actionable and routes to an existing or new second-level page, not to a passive text-only search result.
- Preserve route-stack behavior:
  - `/video-library` is a detail page, not a sixth root tab
  - result clicks push detail routes such as point detail, chapter experiments, AI chat, or future video-point detail pages
  - detail routes opened from `/video-library` remain semantic second-level/detail pages even when the runtime history stack is `home -> video-library -> point`
  - returning restores the video library or the root/source that opened the detail page
- Do not add a first-level global search tab or a large home-page search bar.

## Capabilities

### New Capabilities

- `student-h5-video-library-search`: Defines the second-level experiment video library, Elasticsearch-backed search scope, default browse organization, actionable result contract, and navigation behavior.

### Modified Capabilities

- `student-h5-route-stack-navigation`: Add the video library as a shared second-level detail page and define how result routes preserve source-aware return behavior.
- `student-h5-route-stack-navigation`: Define root-vs-detail route taxonomy so page level is based on navigation role, not directory depth or number of pushes.
- `student-h5-learning-flow`: Allow chapter/point learning flows to be reached from video-library search results without restoring an experiment root tab or changing root tab identity.
- `student-h5-platform-shell`: Require direct SPA fallback support for the video library route and any nested video-library result routes introduced by this change.

## Impact

- Affected student frontend routes:
  - `apps/student-web/src/app/router/*`
  - `apps/student-web/src/routes/home/*`
  - `apps/student-web/src/routes/video-library/*` or equivalent route-page folder
  - `apps/student-web/src/routes/learn/*`
- Affected student feature components:
  - experiment/video card display components
  - point detail navigation helpers
  - assistant context handoff helpers
- Backend impact:
  - new search API endpoint(s) for video-library search
  - Elasticsearch/OpenSearch client configuration or adapter
  - indexing pipeline for experiment/video-point searchable documents
  - optional local/no-index fallback behavior for development and disabled search
- Affected tests/QA:
  - route tests for `/video-library`
  - search API unit tests
  - result grouping and navigation tests
  - direct deep-link fallback tests
  - mobile viewport QA for video-library browse/search states

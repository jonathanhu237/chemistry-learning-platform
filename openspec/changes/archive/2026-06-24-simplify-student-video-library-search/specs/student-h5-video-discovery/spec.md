## MODIFIED Requirements

### Requirement: Video library page owns search and browse
The student H5 app SHALL provide a second-level video library page that owns experiment-video search, simple no-query discovery, and result display.

#### Scenario: Video library opens without query
- **WHEN** a student opens the video library page without a query
- **THEN** the page MUST show a simple no-query default state instead of an empty search-only screen
- **AND** default content MUST prioritize local recent search rows when history exists
- **AND** default content MUST show recommended experiment video rows when recommendation data exists
- **AND** default content MUST show recommended search terms as a fallback or lower-priority section when video recommendations are unavailable or insufficient
- **AND** default content MUST NOT render the previous categorized browse-card grid for phenomenon, reagent, chapter, element-family, or knowledge chips.

#### Scenario: Recommended video rows render with cover affordance
- **WHEN** the no-query default state shows recommended experiment videos
- **THEN** each recommended video row MUST include a student-facing title, one fixed single-line catalog path or context row, and a compact learning-page chapter tag when the route target maps to a learning profile
- **AND** the compact learning-page chapter tag MUST be derived from the frontend learning page profile label by `profile_id` or `chapter_id`
- **AND** the compact learning-page chapter tag MUST NOT use backend textbook chapter badge labels such as chapter 13 or chapter 14
- **AND** each row MUST reserve a thumbnail or poster slot immediately before the diagonal arrow action on the right
- **AND** the row MUST use a real student-visible video thumbnail or poster when available
- **AND** the row MUST render a stable nonblank cover fallback when no thumbnail is available
- **AND** the row MUST NOT render snippets, backend badges, explanatory text, or action-label text.

#### Scenario: Student selects a default recommendation
- **WHEN** a student taps a recommended video row in the no-query default state
- **THEN** the app MUST navigate to the existing point, chapter, or supported learning route target for that recommendation
- **AND** the route MUST preserve `from=video-library` or equivalent source context
- **AND** returning MUST preserve normal route-stack behavior.

#### Scenario: Student selects a history or recommended-term row
- **WHEN** a student taps a recent search row or recommended search term row
- **THEN** the page MUST populate the search query with that term and perform video-library search within experiment-video learning content
- **AND** the selected term MUST be remembered in local video-library search history.

#### Scenario: Student enters a query
- **WHEN** the student types a query in the video library search box
- **THEN** the page MUST search within experiment-video learning content
- **AND** it MUST NOT search unrelated admin, teacher draft, account, assessment-management, or global application content.

#### Scenario: Video library shows query results
- **WHEN** the student enters a non-empty query from the home video search entry
- **THEN** the page MUST replace the no-query history/recommendation state with a result state headed as `关于“<query>”的实验视频`
- **AND** the result state MUST render a flat experiment-video result list sourced from the video-library search response
- **AND** video result rows MUST use the same title, single-line path, compact learning-page chapter tag, thumbnail, and diagonal arrow structure as recommended video rows
- **AND** the compact learning-page chapter tag MUST be present whenever the target maps to a learning profile
- **AND** thumbnail slots MUST render only when a thumbnail is available and MUST NOT reserve empty placeholder space when unavailable
- **AND** the result state MUST NOT render catalog directory result rows for the home video search entry.

#### Scenario: Video library query has no results
- **WHEN** the student enters a non-empty query that returns no video results
- **THEN** the page MUST render a simple inline empty message
- **AND** the empty message SHOULD say `这里什么都没有哦~`
- **AND** the page MUST NOT render the backend empty-result message as a yellow warning banner
- **AND** the page MUST NOT render a large empty-state card for this result state.

#### Scenario: Learning search reuses the video search page model
- **WHEN** the student opens search from a learning chapter or catalog page
- **THEN** the app MUST reuse the same search shell, local-history behavior, query/default state model, and video result row behavior as the video library search page
- **AND** a non-empty query MUST render video results and catalog directory results
- **AND** catalog directory results MUST be available only in the learning search scope
- **AND** tapping a catalog directory result MUST navigate to the corresponding learning catalog directory page
- **AND** tapping a video result MUST navigate to the existing point learning page.

#### Scenario: Student clears a query
- **WHEN** the student clears the active search query
- **THEN** the page MUST return to the simple no-query video library default state
- **AND** it MUST keep route-stack navigation and page back behavior intact.

### Requirement: Video library mobile interaction states
The video library page SHALL remain usable on mobile widths and support loading, error, disabled, empty, no-query default, and result states.

#### Scenario: Search is loading
- **WHEN** a search request is in progress
- **THEN** the page MUST show a loading state that preserves the current query and page layout.

#### Scenario: Search fails
- **WHEN** a search request fails
- **THEN** the page MUST show an error state with retry or fallback browse affordances
- **AND** it MUST keep page back behavior available.

#### Scenario: Mobile viewport renders video library
- **WHEN** the page is viewed at 360px, 390px, or 430px mobile widths
- **THEN** the search input, recent-search rows, recommended-video thumbnail rows, recommended search terms, grouped results, and route actions MUST NOT overlap horizontally or vertically
- **AND** thumbnail slots and diagonal arrow actions MUST keep stable dimensions while text truncates or wraps safely
- **AND** recommended video rows MUST keep a consistent compact row height while title and path truncate to their fixed lines
- **AND** recommended video learning-page chapter tags MUST remain single-line and truncate without changing thumbnail or arrow alignment
- **AND** the hidden bottom navigation state MUST not leave unsafe-area gaps that obscure content.

### Requirement: Video library search remains distinct from home feed playback
The student experiment-video search capability SHALL remain a second-level search and simple discovery surface, not the playback data contract for the home video feed.

#### Scenario: Home needs playable media fields
- **WHEN** the home video feed needs stream paths, thumbnail paths, media ids, or duration for inline preview
- **THEN** those fields MUST come from the home feed API or point detail APIs
- **AND** they MUST NOT be added to the student video-library Elasticsearch search document source.

#### Scenario: Video library default renders recommendation covers
- **WHEN** the video-library no-query default state renders recommended video covers
- **THEN** thumbnail or poster data MUST come from existing student-visible feed or media APIs, or from a nonblank UI fallback
- **AND** thumbnail or poster data MUST NOT be required in the Elasticsearch search document source
- **AND** default recommendation rows MUST NOT autoplay inline video.

#### Scenario: Student opens search from home
- **WHEN** the student taps the home search action
- **THEN** the app MUST open the existing video-library search route with home source context
- **AND** the video-library page MUST continue to own query input, recent search rows, recommended videos, recommended search terms, and grouped result display.

#### Scenario: Search result is rendered
- **WHEN** the video-library page renders search results
- **THEN** results MUST remain actionable learning/search results
- **AND** they MUST NOT be required to autoplay inline like home feed cards
- **AND** grouped query results MUST remain usable even when no thumbnail or poster data is available.

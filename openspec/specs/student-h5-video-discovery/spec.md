# student-h5-video-discovery Specification

## Purpose
Define student H5 experiment-video discovery across the home feed and the second-level video search/browse page, while keeping discovery rooted in published catalog point learning content.
## Requirements
### Requirement: Student home video feed API
The backend SHALL provide an authenticated student home video feed API that returns playable, catalog-backed experiment video cards for the student H5 home root.

#### Scenario: Student requests the home video feed
- **WHEN** an authenticated student requests the home video feed
- **THEN** the response MUST include feed items with stable point placement identity, canonical point identity, chapter identity, student-visible title, summary or snippet, catalog path, display badges, video resource paths, and a point-detail route target
- **AND** each feed item MUST expose enough media data for inline preview, including stream path, optional thumbnail path, and optional duration

#### Scenario: Feed filters hidden or unplayable content
- **WHEN** catalog points, point content, ancestor directories, media bindings, or media assets are draft, unpublished, archived, unready, or otherwise hidden from students
- **THEN** the feed API MUST NOT include those items
- **AND** the feed MUST include only point placements with at least one published playable video

#### Scenario: Feed has no playable videos
- **WHEN** no published playable experiment videos are available
- **THEN** the API MUST return an empty item list with a controlled empty status or message
- **AND** the frontend MUST render an educational empty state rather than falling back to unrelated home action cards

### Requirement: Home renders horizontal experiment video cards
The student H5 home root SHALL render the experiment video feed as a single-column horizontal video card stream.

#### Scenario: Student opens home with feed items
- **WHEN** a student opens `/home` and feed items exist
- **THEN** the page MUST render each item as a 16:9 video preview or poster card
- **AND** the card MUST show experiment title, catalog path, learning tags or badges, and clear learning actions
- **AND** the card MUST NOT render as a vertical Shorts player or a two-column thumbnail grid

#### Scenario: Feed card preserves textbook context
- **WHEN** a feed card is displayed
- **THEN** the card MUST show catalog path or chapter context derived from the published point placement
- **AND** the primary action MUST route to the point video detail page rather than to a generic video-only player

#### Scenario: Home keeps root tab identity
- **WHEN** the student is viewing the home video feed
- **THEN** the bottom navigation MUST continue to identify `首页` as the active root tab
- **AND** the feed MUST leave safe space for the bottom navigation on phone viewports

### Requirement: Muted one-card autoplay preview
The student H5 home video feed SHALL support muted inline autoplay preview with only one active card playing at a time.

#### Scenario: A feed card becomes the primary visible item
- **WHEN** a feed card becomes the most visible card in the main viewport and passes the visibility threshold
- **THEN** the app MUST mark that card as active
- **AND** it MUST attempt to play that card's video muted and inline

#### Scenario: Active card changes
- **WHEN** another feed card becomes the active visible item
- **THEN** the previous active card MUST pause
- **AND** the new active card MAY start muted inline preview
- **AND** no more than one feed video SHOULD be playing at once

#### Scenario: Autoplay is blocked or unsupported
- **WHEN** the browser or WebView rejects the autoplay request
- **THEN** the card MUST remain usable with poster, title, catalog path, and detail navigation
- **AND** the app MUST NOT surface an intrusive playback error for muted preview failure

### Requirement: Feed actions stay learning-oriented
The student H5 home video feed SHALL route primary feed actions to learning destinations while rendering a compact video-stream action row that does not make entertainment-style social behavior required.

#### Scenario: Student opens a feed item
- **WHEN** the student taps the media area, title, or `查看实验` detail action on a feed item
- **THEN** the app MUST navigate to the existing point video detail route with `from=home` or equivalent source context
- **AND** returning MUST preserve normal route-stack behavior

#### Scenario: Student asks Atom from a feed item
- **WHEN** the Atom assistant is enabled and the student chooses the Atom action from a feed card
- **THEN** the app MUST open Atom chat with the item title, catalog path, point identity, and summary context
- **AND** the Atom action MUST NOT change the active root tab identity as a side effect

#### Scenario: Feed card renders compact video action row
- **WHEN** a home feed card is rendered
- **THEN** the card footer MUST render a single action row with `查看实验` as the left-aligned primary CTA
- **AND** the right side MUST render compact icon actions for like, favorite or bookmark, share, Atom, and more
- **AND** the Atom action MUST use the product Atom icon and a green primary visual treatment
- **AND** non-Atom icon actions MUST remain visually secondary to `查看实验` and Atom

#### Scenario: Feed card excludes per-card search action
- **WHEN** a home feed card action row is rendered
- **THEN** the row MUST NOT render a visible `搜索相关` action or another per-card query-launching search action
- **AND** experiment-video search MUST remain owned by the home header/video-library entry and the second-level video-library search page

#### Scenario: Feed avoids required entertainment chrome
- **WHEN** the home feed is rendered
- **THEN** the feed MUST NOT require likes, comments, creator channels, follower counts, or generic social engagement controls to complete the learning flow
- **AND** any like, favorite, share, or more icons rendered in the action row MUST NOT introduce counters, creator/channel dependencies, or ranking behavior unless a future spec defines those behaviors
- **AND** visible learning actions MUST prioritize point detail and Atom explanation over entertainment-style engagement

### Requirement: Home entry for experiment video library
The student H5 home page SHALL provide a focused entry into the experiment video library without turning the home page into a global search surface.

#### Scenario: Student sees video library entry on home
- **WHEN** an authenticated student opens the home root
- **THEN** the page MUST provide an experiment video library entry point
- **AND** the entry MUST communicate experiment-video or phenomenon discovery rather than generic site search.

#### Scenario: Home avoids global search bar
- **WHEN** the authenticated student opens the home root
- **THEN** the page MUST NOT show a large all-site search bar as the primary home affordance
- **AND** experiment-video search MUST be opened through the video library entry.

#### Scenario: Student opens video library from home
- **WHEN** the student taps the experiment video library entry
- **THEN** the app MUST push the video library detail route
- **AND** the bottom navigation MUST be hidden while the video library page is visible.

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

### Requirement: Elasticsearch-backed experiment-video search
The backend SHALL provide Elasticsearch or Elasticsearch-compatible search for the video library while preserving local/test fallback behavior.

#### Scenario: Search service is configured
- **WHEN** the video library search service is configured and healthy
- **THEN** search requests MUST query the configured Elasticsearch-compatible index
- **AND** responses MUST return typed, student-visible result groups.

#### Scenario: Search service is unavailable or disabled
- **WHEN** the search service is disabled, unavailable, or not configured in local development
- **THEN** the backend MUST return a controlled disabled/fallback response or use a deterministic local metadata search
- **AND** the frontend MUST render a non-blocking state rather than crashing.

#### Scenario: Search index is empty
- **WHEN** the search service is available but no student-visible documents match the query
- **THEN** the frontend MUST render an empty state with useful next steps such as browse chips, retry, or AI explanation entry when allowed.

### Requirement: Searchable document scope
The video library index SHALL represent student-visible experiment point learning material and searchable chemistry context.

#### Scenario: Experiment video document is indexed
- **WHEN** a student-visible catalog point placement is indexed
- **THEN** the searchable document MUST include stable identifiers needed for routing
- **AND** it MUST include student-facing catalog path, point title, principle, phenomenon explanation, safety note, related point titles, reagents, phenomena, chapter identifiers, element symbols, equations, formula text, and chemistry-derived recall fields when available.
- **AND** it MUST NOT include video resource titles, media asset titles, binding titles, original file names, media asset ids, playback paths, thumbnail paths, upload status, processing status, duplicate-candidate data, or other video resource metadata.

#### Scenario: Hidden content exists
- **WHEN** an experiment point, media resource, learning resource, or catalog placement is draft-only, archived, unpublished, unready, or not visible to students
- **THEN** the index and search response MUST NOT expose it to student H5 search.

#### Scenario: Later transcript data exists
- **WHEN** transcript or ASR segments become available for a published video
- **THEN** the index MUST NOT include those transcript segments unless a future spec explicitly promotes transcripts to student-facing point content
- **AND** transcript hits MUST not be introduced as an implicit side effect of media asset upload.

### Requirement: Actionable search result groups
The video library search results SHALL be grouped by learning action and every result SHALL route to a meaningful second-level destination.

#### Scenario: Video point result is selected
- **WHEN** a student selects a video point result
- **THEN** the app MUST navigate to the point video/detail route with enough catalog and point context to show the matching learning target
- **AND** returning MUST restore the video library search state where feasible.

#### Scenario: Catalog point result is selected
- **WHEN** a student selects a catalog point result
- **THEN** the app MUST navigate to an appropriate point detail destination
- **AND** it MUST NOT switch to a separate obsolete experiment root tab.

#### Scenario: Chapter or knowledge result is selected
- **WHEN** a student selects a chapter, element-family, or knowledge-point result
- **THEN** the app MUST navigate to the related chapter learning detail route or another supported route-stack learning page
- **AND** the route MUST preserve `from=video-library` or equivalent source context.

#### Scenario: AI explanation action is selected
- **WHEN** a student opens an AI explanation from a search result
- **THEN** the app MUST open the shared AI chat detail page with result context
- **AND** it MUST NOT change the active root tab identity as a side effect.

#### Scenario: Result lacks a route target
- **WHEN** a backend search hit cannot be mapped to a supported route target
- **THEN** the backend or frontend MUST omit it from actionable results or render it as unavailable
- **AND** it MUST NOT produce a dead-end passive result item.

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

### Requirement: Chemistry-aware search indexes point placements
The student experiment-video search index SHALL represent published catalog point placements, not raw video resources, generic media rows, canonical-only points, or generic text snippets.

#### Scenario: Published point placement is indexed
- **WHEN** a catalog point placement is active and its point content is published
- **THEN** the search document MUST include the placement node id, canonical point id, chapter id, catalog path, student-visible title, principle, phenomenon explanation, safety note, related point titles, aliases, formulae, reaction features, searchable text, and non-semantic video readiness signals
- **AND** the placement node id MUST be usable as the ES document identity.
- **AND** the document MUST NOT include video resource titles, original file names, media ids, thumbnail paths, stream paths, or video metadata in searchable text or ES source.

#### Scenario: Same experiment appears in multiple directories
- **WHEN** one canonical experiment point has multiple active placements
- **THEN** each searchable placement MUST keep its own catalog path and placement node id
- **AND** the canonical point id MUST allow grouping or deduplication without losing placement-specific context.

#### Scenario: Unpublished or hidden point content exists
- **WHEN** a point placement has draft-only content, unpublished content, archived state, hidden state, or only archived media bindings
- **THEN** student experiment-video search MUST NOT expose hidden point content or archived media resource data as a searchable result
- **AND** any previously indexed document for that placement MUST be deleted or rebuilt through the ES sync job contract.

### Requirement: Directory context can recall point placements
The student experiment-video search SHALL use catalog directories as context, filters, and weak recall evidence for point placements, without making directories the default final result object.

#### Scenario: Query matches a directory title
- **WHEN** a student searches for a chapter, section, or directory phrase
- **THEN** the search system MAY recall point placements under that matching directory context
- **AND** the returned learning results MUST remain point or video actions unless a separate directory-navigation mode is explicitly requested.

#### Scenario: Directory context contributes to ranking
- **WHEN** a point placement matches a query through its catalog path or ancestor directory
- **THEN** ranking MAY use that path match as supporting evidence
- **AND** the path match MUST be weaker than a direct title, strict chemical synonym, formula, or same-equation-row match.

#### Scenario: Chapter filter is applied
- **WHEN** the search request includes a chapter filter
- **THEN** the search system MUST constrain or boost results according to indexed chapter or path metadata
- **AND** it MUST keep canonical grouping semantics intact when the same point exists in more than one chapter.

### Requirement: Multi-route chemistry recall improves ranking
The student experiment-video search SHALL support chemistry-aware recall routes for text, strict synonyms, formulae, equation rows, conditions, phenomena, properties, directory context, and fallback search text.

#### Scenario: Query contains chemical formulae
- **WHEN** a query contains formula-like terms such as `KMnO4`, `H2O2`, `SO2`, or `FeCl3`
- **THEN** the search system MUST normalize the formula terms for exact keyword matching
- **AND** it SHOULD combine those exact matches with text/analyzer matches rather than relying only on generic tokenized search.

#### Scenario: Query contains strict chemical synonyms
- **WHEN** a query contains a reviewed alias such as a Chinese name, English name, common name, Unicode subscript formula, or ASCII formula for the same chemical entity
- **THEN** strict synonym expansion MAY contribute to text search and query normalization
- **AND** title or principle matches from the expanded entity SHOULD rank above broad phenomenon-only matches.

#### Scenario: Query contains multiple chemical entities
- **WHEN** a query contains multiple chemical entities
- **THEN** candidates where the entities appear in the same normalized equation row or participant set SHOULD rank above candidates where the terms only appear separately across unrelated fields
- **AND** the implementation MUST preserve a deterministic fallback when structured equation matching is unavailable.

### Requirement: Student responses hide retrieval internals
Student-facing video-library search SHALL keep result payloads actionable and safe while diagnostics remain teacher-only.

#### Scenario: Student receives search results
- **WHEN** a student search request returns experiment-video results
- **THEN** each result MUST expose only allowed learning metadata such as point title, snippet, catalog path, and allowed point route metadata
- **AND** it MUST NOT expose raw ES DSL, analyzer tokens, dictionary file state, route traces, sync-job payloads, rank-debug internals, media asset ids, video resource titles, original file names, thumbnail paths, or stream paths from ES.

#### Scenario: Teacher and student query the same term
- **WHEN** a teacher diagnostic and a student search use the same query
- **THEN** the diagnostic MAY show route reasons, scores, analyzer terms, and canonical/placement grouping
- **AND** the student response MUST remain stable and product-facing even if the same backend route contributed to the result.

### Requirement: Video resource labels are excluded from search semantics
The student experiment-video search SHALL treat the index as a published point library, not as a video resource library.

#### Scenario: Bound video has teacher-only labels
- **WHEN** a published point has a bound ready video with a media asset title, binding title, or original file name
- **THEN** those labels MUST NOT be included in ES searchable fields, local fallback searchable text, diagnostics route matching, or student search snippets
- **AND** queries matching only those labels MUST NOT recall the point.

#### Scenario: Point has a playable video
- **WHEN** a published point has an active ready video binding
- **THEN** the search document MAY include `has_video` and `video_count`
- **AND** `video_count` MUST be either `0` or `1`, because a video point has at most one current video resource
- **AND** those fields MUST be treated only as point readiness/filter signals, not as video semantic content.

#### Scenario: Search hit is rendered
- **WHEN** a student search result is rendered
- **THEN** the result MUST use point title, point snippet, catalog path, and route target from point data
- **AND** it MUST NOT display or depend on video resource title, media asset id, thumbnail path, stream path, or original file name from ES.

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

### Requirement: Home discovery header owns recommendation topic rail
The student H5 home video discovery surface SHALL render its recommendation topic rail as header-attached chrome above the video feed, with `推荐` as the default selected topic.

#### Scenario: Student opens home video discovery
- **WHEN** an authenticated student opens the home root
- **THEN** the page MUST show a horizontally scrollable recommendation topic rail attached to the home header
- **AND** the `推荐` topic MUST be selected by default
- **AND** the rail MUST be visually styled as part of the home title/header system rather than as a separate content card.

#### Scenario: Student changes topic selection
- **WHEN** the student taps a recommendation topic in the home rail
- **THEN** the tapped topic MUST become the visible active topic
- **AND** the interaction MUST NOT require a backend feed-filtering contract until a future change defines topic-specific results.

#### Scenario: Home feed starts below attached header rail
- **WHEN** home feed items are rendered below the recommendation rail
- **THEN** the first feed item MUST align directly under the header area with only the configured header/feed spacing
- **AND** unrelated background bands, hero cards, or explanatory title cards MUST NOT appear between the recommendation rail and the video stream.

#### Scenario: Home search remains video-library entry
- **WHEN** the student activates the home search affordance from the home header
- **THEN** the app MUST open the second-level video-library route with home source context
- **AND** the home recommendation rail MUST NOT replace the video-library page's query input, search results, browse chips, or grouped result behavior.


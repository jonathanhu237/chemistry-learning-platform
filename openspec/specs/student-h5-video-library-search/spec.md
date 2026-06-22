# student-h5-video-library-search Specification

## Purpose
TBD - created by archiving change student-h5-video-library-search-entry. Update Purpose after archive.
## Requirements
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
The student H5 app SHALL provide a second-level video library page that owns experiment-video search, browse organization, and result display.

#### Scenario: Video library opens without query
- **WHEN** a student opens the video library page without a query
- **THEN** the page MUST show browseable default content instead of an empty search-only screen
- **AND** default content MUST include at least one supported browse module when data exists, such as recommended videos, recent/continue learning, phenomenon chips, reagent chips, chapter chips, or element-family chips.

#### Scenario: Student enters a query
- **WHEN** the student types a query in the video library search box
- **THEN** the page MUST search within experiment-video learning content
- **AND** it MUST NOT search unrelated admin, teacher draft, account, assessment-management, or global application content.

#### Scenario: Student clears a query
- **WHEN** the student clears the active search query
- **THEN** the page MUST return to the default video library browse state
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
- **THEN** the app MUST navigate to the experiment point/detail route with enough experiment and point context to show the matching learning target
- **AND** returning MUST restore the video library search state where feasible.

#### Scenario: Experiment result is selected
- **WHEN** a student selects an experiment result
- **THEN** the app MUST navigate to an appropriate experiment or point detail destination
- **AND** it MUST NOT switch to a separate experiment root tab.

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
The video library page SHALL remain usable on mobile widths and support loading, error, disabled, empty, default, and result states.

#### Scenario: Search is loading
- **WHEN** a search request is in progress
- **THEN** the page MUST show a loading state that preserves the current query and page layout.

#### Scenario: Search fails
- **WHEN** a search request fails
- **THEN** the page MUST show an error state with retry or fallback browse affordances
- **AND** it MUST keep page back behavior available.

#### Scenario: Mobile viewport renders video library
- **WHEN** the page is viewed at 360px, 390px, or 430px mobile widths
- **THEN** search input, chips, grouped results, cards, and fixed actions MUST NOT overlap horizontally or vertically
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

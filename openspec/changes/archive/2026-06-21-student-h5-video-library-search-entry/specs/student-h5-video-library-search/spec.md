## ADDED Requirements

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
The video library index SHALL represent student-visible experiment-video learning material and searchable chemistry context.

#### Scenario: Experiment video document is indexed
- **WHEN** a student-visible experiment or video point is indexed
- **THEN** the searchable document MUST include stable identifiers needed for routing
- **AND** it SHOULD include available experiment title, code, aliases, module title, video point title, observation text, candidate point text, reagents, apparatus, phenomenon tags, chapter identifiers, element symbols, element-family labels, knowledge point identifiers, equations, and formula text.

#### Scenario: Hidden content exists
- **WHEN** an experiment, media resource, video point, or learning resource is draft-only, archived, unpublished, unready, or not visible to students
- **THEN** the index and search response MUST NOT expose it to student H5 search.

#### Scenario: Later transcript data exists
- **WHEN** transcript or ASR segments become available for a published video
- **THEN** the index MAY include those transcript segments
- **AND** transcript hits MUST still route through the same typed result contract.

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

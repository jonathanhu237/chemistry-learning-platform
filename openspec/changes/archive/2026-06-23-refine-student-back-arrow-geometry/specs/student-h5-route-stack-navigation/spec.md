## ADDED Requirements

### Requirement: Detail route back affordances use shared mobile arrow
The authenticated student H5 route stack SHALL render non-tab/detail page back affordances with the shared student mobile back-arrow treatment so route-stack return feels consistent across page types.

#### Scenario: Normal detail route renders shared back affordance
- **WHEN** a student opens a non-tab detail route that uses the shared page header, such as selected-area, chapter, catalog directory, element detail, AI chat, assessment report, or feedback where applicable
- **THEN** the visible back arrow MUST use the shared student mobile back-arrow geometry
- **AND** the route MUST preserve the existing source-aware return behavior.

#### Scenario: Search/detail-style route renders shared back affordance
- **WHEN** a student opens a search or collection-style page that behaves as a second-level/detail route
- **THEN** its back control MUST use the same shared arrow geometry and reference-like left spacing as ordinary detail pages
- **AND** it MUST NOT introduce a separate icon size, stroke, or left-margin standard.

#### Scenario: Point-video route renders player-owned shared back affordance
- **WHEN** a student opens an experiment point/video detail page
- **THEN** the page MUST keep the video-first layout where the video frame owns the top chrome and long video titles are rendered below the frame
- **AND** the player-owned back arrow MUST use the shared student mobile back-arrow geometry
- **AND** the player-owned back arrow MUST preserve route-stack return behavior when tapped.

#### Scenario: Point-video empty state remains navigable
- **WHEN** a student opens an experiment point/video detail page with no playable published video
- **THEN** the empty-video frame MUST still expose a visible shared back arrow affordance
- **AND** tapping it MUST return using the same route-stack behavior as the playable-video state.

### Requirement: Detail back affordance changes do not alter route role semantics
Student H5 navigation SHALL treat this arrow refinement as a visual/navigation-control standardization only, without changing which routes are roots or details.

#### Scenario: Bottom navigation remains hidden on detail routes
- **WHEN** the current route is a non-tab/detail route after the arrow refinement
- **THEN** the bottom navigation MUST remain hidden according to existing route-role rules
- **AND** the updated back arrow MUST NOT promote the page into a root tab or add a new intermediate route category.

#### Scenario: Return behavior remains source-aware
- **WHEN** the same detail page is opened from different roots, search results, catalog directory links, related-point links, or recent-learning entries
- **THEN** the updated shared back arrow MUST return to the opening source according to the existing route-stack policy
- **AND** visual placement changes MUST NOT replace source-aware navigation with a fixed destination.

#### Scenario: Browser and WebView back remain compatible
- **WHEN** a student uses browser back, Android/WebView back, or the visible shared back arrow from a detail route
- **THEN** the app MUST continue to restore the correct previous route state
- **AND** the visual arrow standardization MUST NOT introduce duplicate history entries or bypass route-layer navigation.

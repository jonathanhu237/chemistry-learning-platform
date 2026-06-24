## MODIFIED Requirements

### Requirement: Detail route back affordances use shared mobile arrow
The authenticated student H5 route stack SHALL render non-tab/detail page back affordances with the shared student mobile back-arrow treatment so route-stack return feels consistent across page types, while playable point-video routes SHALL place that shared arrow inside the custom active player shell only.

#### Scenario: Normal detail route renders shared back affordance
- **WHEN** a student opens a non-tab detail route that uses the shared page header, including selected-area fallback, chapter/family catalog, catalog directory, chapter element detail, video library, AI chat, assessment session, assessment report, and feedback pages
- **THEN** the visible back arrow MUST use the shared student mobile back-arrow geometry
- **AND** the page MUST use the shared detail header/PageBar contract or a documented equivalent that renders the same shared arrow and placement
- **AND** the route MUST preserve the existing source-aware return behavior.

#### Scenario: Search/detail-style route renders shared back affordance
- **WHEN** a student opens a search or collection-style page that behaves as a second-level/detail route
- **THEN** its back control MUST use the same shared arrow geometry and reference-like left spacing as ordinary detail pages
- **AND** it MUST NOT introduce a separate icon size, stroke, or left-margin standard.

#### Scenario: Playable point-video route renders player-owned shared back affordance
- **WHEN** a student opens a point video detail page with a playable published video
- **THEN** the page MUST keep the video-first layout where the video frame owns the top chrome and long video titles are rendered below the frame
- **AND** the player-owned back arrow MUST use the shared student mobile filled-outline back-arrow geometry
- **AND** the player-owned back arrow MUST be part of the custom active player shell
- **AND** the player-owned back arrow MUST NOT be visible or touchable while the playable player shell is inactive
- **AND** the player-owned back arrow MUST preserve route-stack return behavior when tapped
- **AND** tapping the back arrow MUST NOT also toggle playback, activate progress seeking, or leave the custom shell in a stuck active state.

#### Scenario: Current second-level routes keep one back standard
- **WHEN** the authenticated route tree contains P0 second-level pages for learning area fallback, chapter/family catalog, catalog directory, chapter element detail, video library, search, point video detail, AI chat, assessment session, assessment report, and feedback
- **THEN** all ordinary header-based pages MUST render through the shared detail header/PageBar back affordance
- **AND** search MUST render the same shared arrow inside its search-bar back affordance
- **AND** playable point video detail MUST render the same shared arrow inside the custom active player shell
- **AND** point video empty state MUST render the same shared arrow inside the empty-player header
- **AND** no current P0 second-level page MAY introduce a separate arrow icon, copied SVG geometry, bitmap-derived glyph, or alternate left-spacing standard without a future OpenSpec change.

#### Scenario: Point-video empty state remains navigable
- **WHEN** a student opens a point video detail page with no playable published video
- **THEN** the empty-video frame MUST still expose a visible shared back arrow affordance
- **AND** tapping it MUST return using the same route-stack behavior as the playable-video state
- **AND** the empty-video back affordance MUST NOT wait for active playback chrome because no playable chrome exists
- **AND** the empty-video frame MUST NOT render a fake custom playback shell just to reveal a back affordance.

#### Scenario: Detail route back remains source-aware
- **WHEN** the same point video detail page is opened from a chapter catalog, directory page, unified search result, home feed, related experiment link, or recent-learning entry
- **THEN** the custom player-shell back action MUST return according to the same source-aware route-stack policy as the ordinary detail back action
- **AND** moving the back control into the player shell MUST NOT replace source-aware return with a fixed destination.

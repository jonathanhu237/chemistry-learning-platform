## MODIFIED Requirements

### Requirement: Point detail uses edge-to-edge player header chrome
The student H5 point video detail page SHALL render the playable video as the page header, SHALL make that player span the full available mobile width, and SHALL avoid using the standard detail page title bar for point video pages.

#### Scenario: Student opens a point with a long title
- **WHEN** a student opens a visible catalog point whose title is longer than one normal mobile header line
- **THEN** the point detail page MUST keep the video player as the top page header
- **AND** the player MUST touch the top of the detail viewport without route padding above it
- **AND** the player MUST span the full width of the phone content area without side gutters, outer border, radius, shadow, or card background
- **AND** the page MUST render the catalog path and full point title below the player
- **AND** the title MUST be allowed to wrap without increasing or pushing down the player stage

#### Scenario: Playable player defaults to quiet video-first chrome
- **WHEN** a student opens a catalog point that has a playable video
- **THEN** the video frame or poster MUST be the dominant visible content in the player header
- **AND** the playable player MUST NOT render a persistent page-style back arrow while playback controls are inactive
- **AND** the playable player MUST NOT render a persistent full toolbar while playback controls are inactive
- **AND** the playable player MUST render only a subtle bottom mini progress indicator as persistent inactive chrome when progress data is available.

#### Scenario: Player controls reveal return action
- **WHEN** a student taps or otherwise activates the point video player controls
- **THEN** the return action MUST appear as part of the active player control chrome
- **AND** activating that return action MUST call the same source-aware route back behavior as the existing point detail back action
- **AND** the point detail page MUST NOT render a separate always-visible standard `PageBar` title above the player
- **AND** the return action MUST hide again when the playable player control chrome becomes inactive according to the player inactivity behavior.

#### Scenario: Active player controls use mobile video composition
- **WHEN** a playable point video's controls are active on a phone-width viewport
- **THEN** the player header MUST reveal the primary playback affordance inside the video footprint
- **AND** it MUST expose interactive progress inside the player footprint
- **AND** it MUST expose time feedback where duration/current-time data is available
- **AND** it MUST expose fullscreen or equivalent player affordances where the runtime supports them
- **AND** those controls MUST remain part of the player header rather than moving into the catalog title/content sections below.

#### Scenario: Page separates video header from learning content
- **WHEN** the point detail page is rendered
- **THEN** the page MUST NOT use the experiment grid-paper background behind the detail content
- **AND** the player and title area MUST NOT be presented as stacked floating cards
- **AND** the page MUST use flat sections and dividers below the video header for title, principle, explanation, safety, related links, AI handoff, and assessment handoff

#### Scenario: Point has no playable video
- **WHEN** a student opens a visible catalog point with no active ready video binding
- **THEN** the point detail page MUST keep the same edge-to-edge top video-header footprint
- **AND** it MUST show the existing graceful no-video state in that footprint
- **AND** the no-video state MUST keep a visible shared return affordance because there is no playback toolbar to reveal it
- **AND** the catalog path, title, learning content, related links, AI handoff, and assessment handoff MUST remain available

#### Scenario: Teacher previews point detail
- **WHEN** the teacher preview shell renders a student point detail page
- **THEN** the preview MUST use the same player-first layout and title-below-player composition
- **AND** playable-video return chrome MUST follow the same active/inactive player behavior as normal student H5
- **AND** preview media URLs MUST continue to resolve through preview-scoped media access

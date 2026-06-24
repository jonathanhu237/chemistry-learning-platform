## ADDED Requirements

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

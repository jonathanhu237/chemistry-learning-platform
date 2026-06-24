## ADDED Requirements

### Requirement: Video library search remains distinct from home feed playback
The student experiment-video search capability SHALL remain a second-level search and browse surface, not the playback data contract for the home video feed.

#### Scenario: Home needs playable media fields
- **WHEN** the home video feed needs stream paths, thumbnail paths, media ids, or duration for inline preview
- **THEN** those fields MUST come from the home feed API or point detail APIs
- **AND** they MUST NOT be added to the student video-library Elasticsearch search document source

#### Scenario: Student opens search from home
- **WHEN** the student taps the home search action
- **THEN** the app MUST open the existing video-library search route with home source context
- **AND** the video-library page MUST continue to own query input, search results, browse chips, and grouped result display

#### Scenario: Search result is rendered
- **WHEN** the video-library page renders search or browse results
- **THEN** results MUST remain actionable learning/search results
- **AND** they MUST NOT be required to autoplay inline like home feed cards


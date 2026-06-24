## ADDED Requirements

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
- **AND** the primary action MUST route to the experiment point detail page rather than to a generic video-only player

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
The student H5 home video feed SHALL route feed actions to learning destinations without introducing entertainment-style social behavior.

#### Scenario: Student opens a feed item
- **WHEN** the student taps the media area, title, or detail action on a feed item
- **THEN** the app MUST navigate to the existing experiment point detail route with `from=home` or equivalent source context
- **AND** returning MUST preserve normal route-stack behavior

#### Scenario: Student asks AI from a feed item
- **WHEN** the AI assistant is enabled and the student chooses the AI action from a feed card
- **THEN** the app MUST open AI chat with the item title, catalog path, point identity, and summary context
- **AND** the AI action MUST NOT change the active root tab identity as a side effect

#### Scenario: Feed avoids entertainment chrome
- **WHEN** the home feed is rendered
- **THEN** the feed MUST NOT require likes, comments, creator channels, follower counts, or generic social engagement controls to complete the learning flow
- **AND** visible actions SHOULD prioritize point detail, AI explanation, search, and learning continuation


## MODIFIED Requirements

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

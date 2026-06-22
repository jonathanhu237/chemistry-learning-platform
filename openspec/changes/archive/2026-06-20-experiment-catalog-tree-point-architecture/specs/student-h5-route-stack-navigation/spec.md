## MODIFIED Requirements

### Requirement: P0 second-level detail pages
The authenticated student H5 app SHALL provide P0 second-level detail pages for chapter learning, catalog directory navigation, point/video detail, AI chat, assessment session, assessment report, and feedback.

#### Scenario: Chapter learning detail is opened
- **WHEN** a student opens a chapter from the home root recommendation or the learn root chapter entry
- **THEN** the app MUST render a shared chapter learning detail page
- **AND** the page MUST support chapter context and top-level catalog entries for the selected profile.

#### Scenario: Catalog directory detail is opened
- **WHEN** a student opens a directory node from a chapter or another directory
- **THEN** the app MUST render a shared catalog directory detail page
- **AND** the page MUST fetch durable data from the route node id rather than prior in-memory tree state.

#### Scenario: Point detail is opened
- **WHEN** a student opens a point from chapter learning, catalog navigation, search, recent learning, or related links
- **THEN** the app MUST render a shared point/video detail page
- **AND** the page MUST show the available video, point content, chapter/catalog context, and learning completion affordances.

#### Scenario: AI chat detail is opened
- **WHEN** a student opens AI from the home root, learn root, AI root, point detail, or assessment report
- **THEN** the app MUST render the shared AI chat detail page
- **AND** the page MUST accept optional context from the opening source without changing root tab identity.

#### Scenario: Assessment session detail is opened
- **WHEN** a student starts a post-learning or assessment-center test
- **THEN** the app MUST render a shared assessment session detail page
- **AND** answering the test MUST NOT switch the visible root tab.

#### Scenario: Assessment report detail is opened
- **WHEN** a student submits a test or opens a previous report
- **THEN** the app MUST render a shared assessment report detail page
- **AND** the page MUST support AI summary and mistake explanation behavior where available.

#### Scenario: Feedback detail is opened
- **WHEN** a student opens feedback from profile or support entry points
- **THEN** the app MUST render a feedback detail page
- **AND** the page MUST support the existing authenticated feedback form and optional screenshot attachment behavior.

### Requirement: Shared detail pages preserve source-aware return
Shared second-level pages SHALL preserve source-aware return behavior when opened from different first-level roots or catalog paths.

#### Scenario: Same detail page is opened from different roots
- **WHEN** the same chapter, catalog node, AI chat, report, or point detail page is opened from different root pages
- **THEN** the page component MAY be shared
- **AND** returning MUST go back to the route that opened it rather than switching to a fixed root destination.

#### Scenario: Point is opened through shortcut
- **WHEN** a point detail page is opened through a shortcut node
- **THEN** the route context MUST preserve the shortcut source node or path
- **AND** back navigation MUST return to the shortcut's catalog location.

#### Scenario: Page-local action opens shared detail
- **WHEN** a page-local action such as contextual AI, chapter recommendation, assessment start, feedback, related point, or search result opens a shared detail page
- **THEN** the app MUST push a detail route
- **AND** it MUST NOT directly change the active root tab.

## ADDED Requirements

### Requirement: Durable catalog node routes
The student H5 route stack SHALL support durable routes for catalog directories and point nodes.

#### Scenario: Direct catalog URL is opened
- **WHEN** a student opens a valid catalog directory URL directly
- **THEN** the app MUST fetch the directory node by route id
- **AND** it MUST render the directory page without requiring prior chapter-page state.

#### Scenario: Direct point URL is opened
- **WHEN** a student opens a valid point node URL directly
- **THEN** the app MUST fetch point detail by stable node id
- **AND** it MUST render the point detail without requiring legacy experiment id or point key search parameters.

#### Scenario: Invalid node URL is opened
- **WHEN** a node id is missing, unpublished, archived, or unavailable to the student
- **THEN** the app MUST render a controlled unavailable state or redirect according to route policy
- **AND** it MUST NOT crash the authenticated shell.

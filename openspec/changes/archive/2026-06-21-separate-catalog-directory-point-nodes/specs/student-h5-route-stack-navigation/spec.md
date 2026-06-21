## MODIFIED Requirements

### Requirement: Shared detail pages preserve source-aware return
Shared second-level pages SHALL preserve source-aware return behavior when opened from different first-level roots or catalog paths.

#### Scenario: Same detail page is opened from different roots
- **WHEN** the same chapter, catalog directory, AI chat, report, or point detail page is opened from different root pages
- **THEN** the page component MAY be shared
- **AND** returning MUST go back to the route that opened it rather than switching to a fixed root destination.

#### Scenario: Point is opened through a directory path
- **WHEN** a point detail page is opened from a chapter page, nested directory page, search result, related link, or recent-learning entry
- **THEN** the route context MUST preserve enough source path or search context to support route-appropriate return
- **AND** back navigation MUST NOT depend on shortcut node semantics.

#### Scenario: Page-local action opens shared detail
- **WHEN** a page-local action such as contextual AI, chapter recommendation, assessment start, feedback, related point, or search result opens a shared detail page
- **THEN** the app MUST push a detail route
- **AND** it MUST NOT directly change the active root tab.

### Requirement: Durable catalog node routes
The student H5 route stack SHALL support durable routes for catalog directories and point nodes.

#### Scenario: Direct catalog URL is opened
- **WHEN** a student opens a valid catalog directory URL directly
- **THEN** the app MUST fetch the directory node by route id
- **AND** it MUST render the directory page without requiring prior chapter-page state.

#### Scenario: Direct point URL is opened
- **WHEN** a student opens a valid point node URL directly
- **THEN** the app MUST fetch point detail by stable node id
- **AND** it MUST render the point detail without requiring legacy experiment id, point key, hybrid behavior, or shortcut source parameters.

#### Scenario: Wrong route type is opened
- **WHEN** a student opens a directory id on a point route or a point id on a directory route
- **THEN** the app MUST render a controlled unavailable state or redirect to the correct route according to route policy
- **AND** it MUST NOT crash the authenticated shell.

#### Scenario: Invalid node URL is opened
- **WHEN** a node id is missing, unpublished, archived, unsupported, or unavailable to the student
- **THEN** the app MUST render a controlled unavailable state or redirect according to route policy
- **AND** it MUST NOT crash the authenticated shell.

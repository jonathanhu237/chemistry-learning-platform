## ADDED Requirements

### Requirement: Catalog tree domain services are split by ownership
The backend SHALL split catalog tree behavior into focused domain modules instead of extending a single mixed-concern tree service.

#### Scenario: Developer changes node structure behavior
- **WHEN** a developer updates catalog node lookup, create, update, move, reorder, status, parent validation, or cycle validation
- **THEN** the change MUST be localized to the catalog node structure service and its tests
- **AND** it MUST NOT require editing point content, media binding, related link, student read-model, or search-document modules unless the behavior crosses those explicit boundaries.

#### Scenario: Developer changes point learning behavior
- **WHEN** a developer updates point title, teacher note, point knowledge, point publication validation, point card presentation, or student point detail shaping
- **THEN** the change MUST be localized to point-owned service modules and tests
- **AND** it MUST NOT live in a generic tree catch-all module.

#### Scenario: Developer changes directory card behavior
- **WHEN** a developer updates directory student descriptions, teacher notes, card images, card icons, card accent metadata, or directory publication validation
- **THEN** the change MUST be localized to directory-owned service modules and tests
- **AND** directory code MUST NOT import point-only media binding or point knowledge write paths for normal directory editing.

### Requirement: Catalog routers remain thin
The backend SHALL keep admin and student catalog routers as request/response adapters that delegate stateful behavior to catalog domain services.

#### Scenario: Admin catalog endpoint is added
- **WHEN** a new admin catalog endpoint is introduced for directory, point, media binding, related link, publication, search preview, or tree drag movement
- **THEN** the router MUST perform auth/dependency/schema adaptation and call a domain service
- **AND** SQL-heavy behavior MUST live outside the router.

#### Scenario: Student catalog endpoint is added
- **WHEN** a new student catalog endpoint is introduced for chapter catalog, directory page, point detail, media stream, or thumbnail stream
- **THEN** the router MUST call student read-model or file-resolution services
- **AND** it MUST NOT duplicate admin catalog write logic.

### Requirement: Catalog tree architecture validation prevents regression
The repository SHALL include validation that prevents the catalog tree service from becoming a new monolith.

#### Scenario: Architecture validation runs
- **WHEN** backend architecture validation or production readiness validation runs
- **THEN** it MUST check that retired hybrid/shortcut live paths and catalog upload-and-bind live paths are absent
- **AND** it MUST check that catalog tree domain responsibilities are split across named service modules.

#### Scenario: Large catch-all tree module is reintroduced
- **WHEN** a developer reintroduces a large catalog tree module that owns node CRUD, directory cards, point content, media binding, related links, student read models, and search documents together
- **THEN** architecture validation MUST fail or tests MUST identify the ownership regression.

### Requirement: Catalog tree tests follow service ownership
Catalog tree backend tests SHALL cover each service boundary rather than only end-to-end route behavior.

#### Scenario: Directory service is tested
- **WHEN** directory metadata, card presentation, or directory publication rules change
- **THEN** directory-focused tests MUST assert directories cannot own point content, media bindings, related links, or ES document identity.

#### Scenario: Point service is tested
- **WHEN** point content, media bindings, related links, or point publication rules change
- **THEN** point-focused tests MUST assert point node identity remains stable and point-only student-visible fields drive search/detail behavior.

#### Scenario: Search document service is tested
- **WHEN** search document generation changes
- **THEN** search-focused tests MUST assert directory text contributes only as category/path context to descendant point documents
- **AND** directory nodes MUST NOT become standalone student video-library search documents.

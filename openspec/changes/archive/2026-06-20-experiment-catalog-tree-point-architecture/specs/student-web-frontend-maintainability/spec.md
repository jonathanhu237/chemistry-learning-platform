## MODIFIED Requirements

### Requirement: Student frontend feature module boundaries
The student H5 frontend SHALL organize catalog navigation, point detail, authenticated shell, and onboarding code into feature-oriented modules with explicit ownership boundaries.

#### Scenario: Student app shell owns route orchestration
- **WHEN** the catalog route migration is implemented
- **THEN** app-level route providers, authenticated layout, disabled-route redirect behavior, and finish-learning assessment handoff MUST be owned by app-level modules
- **AND** feature modules MUST NOT each create independent app-level navigation state.

#### Scenario: Feature modules own their own panels
- **WHEN** a developer edits assistant, feedback, assessment, catalog navigation, point detail, periodic-table, learning, auth, or pretest behavior
- **THEN** the primary React components for that behavior MUST live under the corresponding feature module or a clearly shared module
- **AND** `apps/student-web/src/App.tsx` MUST remain a composition/root file rather than the owner of feature internals.

#### Scenario: Shared modules are intentionally limited
- **WHEN** helper logic is shared across feature modules
- **THEN** it MUST live under a shared or app-level module with a clear name
- **AND** feature-private helpers MUST remain inside their feature module to avoid recreating a hidden monolith.

### Requirement: API and domain helper ownership
The student H5 frontend SHALL separate domain helper ownership while adopting the new catalog-node backend contracts.

#### Scenario: Backend contracts move to catalog nodes
- **WHEN** API code is updated for catalog tree and point detail routes
- **THEN** request URLs, request payload shapes, response handling, authentication token behavior, media URL behavior, feedback attachment behavior, and assistant streaming behavior MUST match the new catalog-node contracts
- **AND** legacy experiment group/detail APIs MUST NOT remain as live compatibility exports.

#### Scenario: API modules are split by domain
- **WHEN** API modules are split or reorganized
- **THEN** auth, learning profiles, catalog tree, point detail, assistant, feedback, media, and assessment ownership MUST be clear
- **AND** route pages MUST import through the appropriate domain API surface.

#### Scenario: Formatting helpers move near their domain
- **WHEN** pure formatting helpers are extracted or updated
- **THEN** family/chapter formatting helpers MUST live near learning or periodic-table modules
- **AND** catalog node formatting helpers MUST live near catalog modules
- **AND** assessment answer formatting helpers MUST live near assessment modules.

## ADDED Requirements

### Requirement: Recursive catalog UI ownership
The student H5 frontend SHALL implement recursive catalog pages through reusable catalog feature components rather than hardcoded level-specific pages.

#### Scenario: Directory depth changes
- **WHEN** a chapter catalog has one, two, or more directory levels
- **THEN** the same route/page pattern MUST render each directory level
- **AND** implementation MUST NOT create separate hardcoded pages for third-level, fourth-level, or fifth-level directories.

#### Scenario: Point detail opens from multiple sources
- **WHEN** a point detail opens from chapter catalog, nested catalog, search, related links, or recent learning
- **THEN** the point detail feature MUST reuse the same component path
- **AND** source-aware return behavior MUST be handled by route/search context rather than duplicated component state.

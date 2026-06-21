## MODIFIED Requirements

### Requirement: API and domain helper ownership
The student H5 frontend SHALL separate domain helper ownership while adopting the catalog-node backend contracts.

#### Scenario: Backend contracts move to directory and point nodes
- **WHEN** API code is updated for catalog tree and point detail routes
- **THEN** request URLs, request payload shapes, response handling, authentication token behavior, media URL behavior, feedback attachment behavior, and assistant streaming behavior MUST match the directory/point catalog-node contracts
- **AND** legacy experiment group/detail APIs, hybrid node behavior, and shortcut node behavior MUST NOT remain as live compatibility exports.

#### Scenario: API modules are split by domain
- **WHEN** API modules are split or reorganized
- **THEN** auth, learning profiles, catalog tree, point detail, assistant, feedback, media, and assessment ownership MUST be clear
- **AND** route pages MUST import through the appropriate domain API surface.

#### Scenario: Formatting helpers move near their domain
- **WHEN** pure formatting helpers are extracted or updated
- **THEN** family/chapter formatting helpers MUST live near learning or periodic-table modules
- **AND** catalog node formatting helpers MUST live near catalog modules
- **AND** assessment answer formatting helpers MUST live near assessment modules.

### Requirement: Recursive catalog UI ownership
The student H5 frontend SHALL implement recursive catalog pages through reusable catalog feature components rather than hardcoded level-specific pages.

#### Scenario: Directory depth changes
- **WHEN** a chapter catalog has one, two, or more directory levels
- **THEN** the same route/page pattern MUST render each directory level
- **AND** implementation MUST NOT create separate hardcoded pages for third-level, fourth-level, or fifth-level directories.

#### Scenario: Point detail opens from multiple sources
- **WHEN** a point detail opens from chapter catalog, nested catalog, search, related links, or recent learning
- **THEN** the point detail feature MUST reuse the same component path
- **AND** source-aware return behavior MUST be handled by route/search context rather than duplicated component state or shortcut-specific state.

#### Scenario: Directory and point cards share a list
- **WHEN** a catalog page contains both directory cards and point cards
- **THEN** reusable catalog components MUST render the two card types with clear visual distinction
- **AND** the implementation MUST NOT infer point behavior from child count, media count, or unknown node kind values.

## ADDED Requirements

### Requirement: Student catalog node type assumptions are centralized
The student frontend SHALL centralize catalog node type helpers and remove hybrid/shortcut assumptions from live routes and components.

#### Scenario: Node kind helpers are updated
- **WHEN** student catalog API types or card helpers are updated
- **THEN** they MUST accept only `directory` and `point` as live node kinds
- **AND** repository search MUST show no live student catalog route or component depending on `hybrid`, `shortcut`, or `shortcut_target_node_id`.

#### Scenario: Unknown node kind is received
- **WHEN** a stale server response includes an unknown node kind
- **THEN** the student UI MUST render a controlled unavailable state or ignore the unsupported item
- **AND** it MUST NOT treat the item as a playable point.

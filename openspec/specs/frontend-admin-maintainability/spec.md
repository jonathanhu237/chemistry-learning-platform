# frontend-admin-maintainability Specification

## Purpose
TBD - created by archiving change production-quality-iteration-four. Update Purpose after archive.
## Requirements
### Requirement: Frontend feature modules are decomposed incrementally
The admin frontend SHALL reduce large feature-page modules through behavior-preserving extraction of pure helpers, local components, or local hooks.

#### Scenario: A large feature slice is extracted
- **WHEN** a feature-page slice is moved into a new module
- **THEN** existing route paths, API calls, query keys, mutation behavior, and visible workflows MUST remain compatible

### Requirement: App shell avoids feature-heavy eager imports
The admin app shell SHALL keep feature-only dependencies behind lazy route boundaries.

#### Scenario: Heavy feature dependencies remain route-owned
- **WHEN** the production build is run
- **THEN** charts, markdown/math rendering, upload/tus utilities, and assistant/video/question-bank feature code MUST NOT be newly imported eagerly by the top-level app shell

### Requirement: Build warnings remain owned and actionable
Large production chunks SHALL be named, associated with an owner, and documented as intentional or targeted for later splitting.

#### Scenario: A vendor chunk exceeds the warning threshold
- **WHEN** Vite reports a chunk larger than the warning threshold
- **THEN** the build report MUST identify the chunk owner, and the pass MUST document whether it is accepted or a follow-up target

### Requirement: CI trigger posture remains unchanged
The production readiness workflow SHALL remain manually triggered during this pass.

#### Scenario: Fourth-pass changes are pushed
- **WHEN** commits are pushed to `codex/productionize-admin-platform`
- **THEN** no workflow change in this pass MUST cause production readiness to run solely because of that push

### Requirement: Catalog editor feature boundary
The admin frontend SHALL implement the teacher catalog editor as a feature-owned module with clear submodule boundaries.

#### Scenario: Developer edits tree behavior
- **WHEN** a developer changes tree search, selection, expansion, drag-move, reorder, or node actions
- **THEN** the code MUST be localized to catalog tree modules
- **AND** it MUST NOT require editing an unrelated admin shell or monolithic `App.tsx`.

#### Scenario: Developer edits node editor behavior
- **WHEN** a developer changes basics, point content, videos, related links, publication, validation, or search preview
- **THEN** the code MUST be localized to selected-node editor modules
- **AND** shared formatting or mapping helpers MUST have explicit module ownership.

### Requirement: Catalog domain API client boundary
The admin frontend SHALL use domain-specific catalog API clients instead of a monolithic API module.

#### Scenario: Catalog APIs are added
- **WHEN** admin catalog tree, node content, media binding, related link, publication, or search diagnostics APIs are introduced
- **THEN** they MUST live in feature-appropriate domain API client modules
- **AND** imports MUST respect the admin import boundary validation.

#### Scenario: Legacy experiment API client is removed
- **WHEN** the catalog-node APIs replace experiment video-point APIs
- **THEN** admin feature code MUST stop importing removed legacy experiment point functions
- **AND** boundary validation MUST fail if old APIs are accidentally reintroduced as a compatibility layer.

### Requirement: Large editor surfaces remain split
The admin catalog workspace SHALL avoid becoming another large all-in-one experiments page.

#### Scenario: Catalog workspace grows
- **WHEN** tree editing, node forms, video panels, related-link editors, search preview, and validation panels are implemented
- **THEN** each major surface MUST be split into route-local components, hooks, and pure mappers
- **AND** the route page MUST remain an orchestration layer rather than the owner of all behavior.

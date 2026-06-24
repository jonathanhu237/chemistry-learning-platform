# application-engineering-structure Specification

## Purpose
TBD - created by archiving change standardize-application-engineering-structure. Update Purpose after archive.
## Requirements
### Requirement: Application surfaces have explicit owners
The repository SHALL define `web-student`, `web-teacher`, `web-admin`, backend, and production validation as separate engineering surfaces with explicit ownership boundaries.

#### Scenario: A new product workflow touches multiple surfaces
- **WHEN** a change modifies student H5 behavior, teacher-console authoring, platform operations, backend persistence, or derived search/read models together
- **THEN** the OpenSpec change MUST name each touched surface
- **AND** it MUST describe which surface owns user interaction, admin editing, canonical facts, derived projections, and validation.

#### Scenario: A module is added without a clear owner
- **WHEN** implementation adds a new frontend or backend module
- **THEN** the module path MUST make its owner clear according to the surface owner map
- **AND** it MUST NOT be placed in a generic location solely because multiple callers need it.

### Requirement: Cross-surface contracts are preferred over shared hidden coupling
The application SHALL communicate across surfaces through typed API contracts, derived read models, queues, or validation scripts rather than private helper imports across ownership boundaries.

#### Scenario: Frontend needs new backend data
- **WHEN** the `web-student`, `web-teacher`, or `web-admin` frontend needs new backend data
- **THEN** the backend API and frontend client/schema owner MUST expose a typed contract
- **AND** frontend code MUST NOT duplicate backend projection rules that belong to a backend domain.

#### Scenario: Backend derived model depends on authoring data
- **WHEN** a backend derived model such as the student video-library search index depends on admin-authored data
- **THEN** the canonical database remains the source of truth
- **AND** the derived model owner MUST document how updates are enqueued, rebuilt, and validated.

### Requirement: Destructive structure cleanup is allowed with validation
The application SHALL prefer explicit destructive refactors over compatibility wrappers when the spec and validation gates protect behavior.

#### Scenario: Old internal paths are removed
- **WHEN** a refactor deletes old internal module paths or endpoint aliases
- **THEN** rollback MUST use git or deployment rollback
- **AND** new compatibility wrappers MUST NOT be added unless the spec explicitly makes them canonical.

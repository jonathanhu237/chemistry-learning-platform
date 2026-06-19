## ADDED Requirements

### Requirement: Structural refactors declare their validation gate
Every structural refactor SHALL declare which validation stages are required before commit.

#### Scenario: A change affects only backend ownership
- **WHEN** a structural change is limited to backend package ownership
- **THEN** backend architecture validation, backend tests, route inventory checks, and relevant resource/search validators MUST run
- **AND** Compose smoke MUST run when service entrypoints, Dockerfiles, workers, migrations, or required services change.

#### Scenario: A change affects frontend shell or routing
- **WHEN** a structural change affects admin shell/routing or student H5 route-stack/shell
- **THEN** the corresponding frontend typecheck, tests, build, and e2e/mobile QA MUST run
- **AND** failures caused by UI warnings or auth setup gaps MUST be fixed or explicitly documented before commit.

#### Scenario: A change affects two or more application surfaces
- **WHEN** a structural change touches backend plus either frontend, or both frontends
- **THEN** the full production readiness chain SHOULD run with e2e enabled
- **AND** the result MUST be summarized before commit.

### Requirement: Compose required services are part of the application contract
The production engineering workflow SHALL treat required Compose services as part of the application, not optional local conveniences.

#### Scenario: Search-backed student video library behavior changes
- **WHEN** student video-library search, point search projection, Elasticsearch settings, or IK analyzer behavior changes
- **THEN** Elasticsearch/IK MUST be included in validation
- **AND** local fallback MUST NOT hide production search failures unless the spec explicitly declares a development-only mode.

#### Scenario: Media processing behavior changes
- **WHEN** media upload, binding, derivative generation, processing queue, or worker entrypoint behavior changes
- **THEN** backend and video-worker service startup MUST be validated
- **AND** generic teacher media assets MUST remain separate from student point-centered video-library search documents.

### Requirement: OpenSpec records engineering decisions before large rewrites
Large structure changes SHALL be captured in OpenSpec before implementation begins.

#### Scenario: A future cleanup proposes moving many files
- **WHEN** a cleanup proposes destructive movement across student H5, admin web, backend, scripts, or Docker/Compose
- **THEN** the OpenSpec proposal/design MUST include the current owner map, target owner map, validation plan, and rollback posture
- **AND** implementation tasks MUST be granular enough to verify each surface independently.

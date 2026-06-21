## ADDED Requirements

### Requirement: Backend slim architecture validation is a production quality gate
The production engineering quality workflow SHALL include backend architecture validation for slim dependency boundaries.

#### Scenario: Production quality validation includes architecture rules
- **WHEN** the backend slim refactor is complete
- **THEN** the documented backend verification sequence MUST run architecture validation
- **AND** it MUST fail on disallowed imports between runtime, API, domain, infrastructure, worker, and script-support owners.

#### Scenario: Compose smoke remains required after backend slimming
- **WHEN** backend slim refactor changes are validated in a production-like stack
- **THEN** the Compose smoke validation MUST verify PostgreSQL, backend, Elasticsearch/IK, tusd, and video-worker services
- **AND** it MUST verify migrations and video-library search readiness using the canonical backend entrypoints.

#### Scenario: Route inventory is verified
- **WHEN** backend API ownership changes during the slim refactor
- **THEN** route inventory tests MUST prove canonical routes are registered exactly once
- **AND** removed aliases are absent unless explicitly retained as canonical.

### Requirement: Destructive backend refactors use validation instead of compatibility layers
Production engineering quality SHALL rely on git, tests, route inventory, Compose smoke, and e2e validation rather than preserving old backend compatibility wrappers.

#### Scenario: Old import compatibility wrapper is proposed
- **WHEN** implementation introduces a wrapper module solely to preserve a previous backend import path
- **THEN** production quality validation MUST treat that wrapper as a failure unless the spec explicitly lists it as a canonical owner.

#### Scenario: Runtime rollback is needed
- **WHEN** a destructive backend slim refactor fails after deployment validation
- **THEN** rollback MUST use git or deployment version rollback
- **AND** the codebase MUST NOT add new compatibility layers as the rollback mechanism.

## ADDED Requirements

### Requirement: Backend canonical package ownership remains enforced
The backend SHALL keep runtime, API, domain, infrastructure, worker, and script-support ownership explicit.

#### Scenario: Backend runtime changes
- **WHEN** FastAPI app construction, middleware, lifespan behavior, static frontend mounts, or health routes change
- **THEN** the change MUST be owned by `server/app/app_runtime`
- **AND** reusable domain modules MUST NOT import runtime modules.

#### Scenario: Backend API routes change
- **WHEN** auth, admin, or student HTTP routes change
- **THEN** route modules MUST remain under `server/app/api`
- **AND** route modules SHOULD translate domain results and domain errors into HTTP responses without moving domain rules into the API layer.

#### Scenario: Backend domain behavior changes
- **WHEN** business rules, read models, command workflows, derived projections, or external-service adapters change
- **THEN** the change MUST live under a domain owner or a clearly documented infrastructure owner
- **AND** the module MUST respect the enforced import direction.

### Requirement: Backend domains split by sub-responsibility as they grow
Backend domains SHALL avoid recreating the old service monolith pattern inside new domain directories.

#### Scenario: A domain file mixes commands and read models
- **WHEN** a domain file owns write commands, read-model assembly, external adapters, validation, and formatting/projection logic together
- **THEN** the domain SHOULD split those responsibilities into explicit sub-owners
- **AND** tests SHOULD target the sub-owner behavior rather than only the API route.

#### Scenario: A domain file becomes a structural hotspot
- **WHEN** a domain module repeatedly changes for unrelated workflows or grows beyond a locally accepted size threshold
- **THEN** maintainers MUST evaluate whether it needs command/read-model/projection/adapter separation
- **AND** the decision MUST be captured in the relevant OpenSpec design or implementation notes.

### Requirement: Backend legacy wrappers stay deleted
The backend SHALL NOT reintroduce legacy compatibility modules that were deleted by the slim architecture refactor.

#### Scenario: A script or test imports an old backend path
- **WHEN** code attempts to import a deleted backend path such as old `services`, old `routers`, old runtime wrappers, or old media/worker modules
- **THEN** architecture validation MUST fail
- **AND** the caller MUST be migrated to the canonical owner.

### Requirement: Backend workers remain runtime-safe
Backend workers SHALL import only worker-safe domain and infrastructure owners.

#### Scenario: A worker needs domain behavior
- **WHEN** a worker needs media, processing queue, search projection, or other domain behavior
- **THEN** it MUST import worker-safe domain owners
- **AND** it MUST NOT import FastAPI routes, app runtime, or HTTP response translation modules.

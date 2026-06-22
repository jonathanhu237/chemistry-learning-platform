## MODIFIED Requirements

### Requirement: Production Validation Chain

The repository SHALL provide a documented validation chain that proves the production baseline can be built, tested, data-validated, and product-console validated.

#### Scenario: Maintainer validates the baseline
- **GIVEN** a maintainer runs the production-readiness validation command or documented command set
- **WHEN** validation completes
- **THEN** it checks OpenSpec strict validation, protected resource manifests, backend tests, `web-admin` typecheck/build, `web-teacher` typecheck/build, `web-student` typecheck/build, and core data counts
- **AND** it reports failures with enough detail to identify the broken stage.

#### Scenario: Fresh rebuild is verified
- **GIVEN** an empty database and the declared production resources are available
- **WHEN** the documented restore/import path is executed
- **THEN** the platform can recreate the current formal experiments, knowledge framework, question bank, chunks, embeddings, and point evidence bindings
- **AND** the resulting counts match the protected baseline manifest.

#### Scenario: Console role split is verified
- **GIVEN** validation covers authentication-sensitive frontend and backend behavior
- **WHEN** role-split checks run
- **THEN** `web-admin` MUST be verified as config-token-only
- **AND** `web-teacher` MUST be verified as available to teacher-console accounts with complete teacher functionality
- **AND** `web-student` MUST remain available as the student H5 surface.

### Requirement: Production Operations Baseline

Production hardening SHALL document and validate the operational basics needed for maintainable deployment.

#### Scenario: Migration numbering continues
- **GIVEN** a new database migration is added after this productionization work begins
- **WHEN** the migration is named
- **THEN** it follows the next unambiguous migration number
- **AND** duplicate migration numbers are not introduced.

#### Scenario: Deployment configuration is reviewed
- **GIVEN** a maintainer prepares a deployment or local production-like run
- **WHEN** they inspect repository documentation and examples
- **THEN** they can find environment variable examples, Docker service expectations, health checks, backup/restore notes, validation commands, and default ports for `web-admin`, `web-teacher`, and `web-student`.

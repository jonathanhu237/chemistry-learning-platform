## ADDED Requirements

### Requirement: Release governance distinguishes API and frontend origins
Production readiness governance SHALL distinguish backend API origin, student frontend origin, and admin frontend origin.

#### Scenario: Environment variables are configured
- **WHEN** local or production-like validation configures service origins
- **THEN** backend API origin, student frontend origin, and admin frontend origin MUST be configurable independently
- **AND** validation output MUST make clear which origin was tested.

#### Scenario: Full e2e validation runs
- **WHEN** full e2e validation runs after this split
- **THEN** admin e2e MUST use the admin frontend origin
- **AND** student mobile QA MUST use the student frontend origin
- **AND** backend health/API readiness MUST use the backend origin.

### Requirement: Deployment docs describe split service ownership
Production readiness governance SHALL document that backend, student web, and admin web are separate default services.

#### Scenario: Production operations docs are read
- **WHEN** an operator reads the deployment instructions
- **THEN** the docs MUST state that backend no longer serves the frontends
- **AND** the docs MUST explain how to start and validate the separate frontend services.

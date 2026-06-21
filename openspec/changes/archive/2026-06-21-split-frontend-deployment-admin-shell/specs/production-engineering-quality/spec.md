## ADDED Requirements

### Requirement: Production quality validates split frontend services
Production engineering quality SHALL validate frontend services independently from backend API readiness.

#### Scenario: Full production readiness runs
- **WHEN** full production readiness runs after the frontend deployment split
- **THEN** it MUST validate backend API readiness
- **AND** it MUST validate student frontend readiness
- **AND** it MUST validate admin frontend readiness.

#### Scenario: Compose service list is checked
- **WHEN** production quality checks required Compose services
- **THEN** `student-web` and `admin-web` MUST be included in the required service list for full application validation
- **AND** missing frontend services MUST fail the check.

### Requirement: Admin e2e smoke targets the admin frontend origin
Admin e2e smoke SHALL target the teacher/admin frontend service root after the deployment split.

#### Scenario: Admin e2e smoke opens pages
- **WHEN** admin e2e smoke runs
- **THEN** it MUST open canonical root routes such as `/overview`, `/videos`, `/question-banks`, `/analytics`, and `/learning-assistant` on the admin frontend origin
- **AND** it MUST NOT require `/admin` path prefixes.

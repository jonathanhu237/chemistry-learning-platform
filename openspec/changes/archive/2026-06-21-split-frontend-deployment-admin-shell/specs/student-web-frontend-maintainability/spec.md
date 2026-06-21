## ADDED Requirements

### Requirement: Student SPA deployment is owned by the student frontend
Student web maintainability SHALL treat the student H5 SPA as a frontend service rather than a backend static mount.

#### Scenario: Student frontend deployment is inspected
- **WHEN** the production-like deployment is inspected
- **THEN** the student H5 frontend MUST have its own service and SPA fallback
- **AND** the backend service MUST NOT own student SPA route fallback.

#### Scenario: Student mobile QA runs
- **WHEN** student mobile QA runs after the deployment split
- **THEN** it MUST target the student frontend service origin
- **AND** it MUST continue covering root routes, detail routes, and the video library route.

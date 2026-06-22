## ADDED Requirements

### Requirement: Student preview routes have separated backend ownership
Backend routes for teacher student-preview sessions and web-admin preview governance SHALL be owned by the correct product router namespaces.

#### Scenario: Teacher preview session route is registered
- **WHEN** the production FastAPI route table is inspected
- **THEN** teacher-facing preview session creation routes MUST be registered under `/api/admin/student-preview/*`
- **AND** they MUST require teacher-console authorization
- **AND** they MUST NOT be registered under `/api/web-admin/*`.

#### Scenario: Web-admin preview governance routes are registered
- **WHEN** the production FastAPI route table is inspected
- **THEN** preview class/test-student governance routes MUST be registered under `/api/web-admin/*`
- **AND** they MUST require the configured web-admin platform authorization
- **AND** they MUST NOT be mounted from teacher-facing feature routers.

#### Scenario: Student preview bootstrap route is registered
- **WHEN** the production FastAPI route table is inspected
- **THEN** the student preview ticket exchange route MUST be registered under a preview/student namespace separate from teacher and web-admin governance endpoints
- **AND** it MUST accept only valid short-lived preview tickets rather than teacher or web-admin credentials.

#### Scenario: Router implementation is reviewed
- **WHEN** the backend implementation is reviewed
- **THEN** route handlers MUST stay thin and delegate preview class creation, test-student reuse, ticket exchange, policy resolution, and reset behavior to domain services
- **AND** SQL-heavy roster/account behavior MUST NOT accumulate inside route modules.

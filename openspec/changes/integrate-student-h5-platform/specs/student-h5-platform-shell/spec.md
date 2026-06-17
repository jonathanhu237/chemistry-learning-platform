## ADDED Requirements

### Requirement: Student H5 frontend delivery
The system SHALL build and serve the student H5 frontend as a first-class app alongside the admin console.

#### Scenario: Student frontend build exists
- **WHEN** the FastAPI service starts with a built `apps/student-web/dist`
- **THEN** it SHALL serve the student SPA from the site root
- **AND** it SHALL serve student static assets from `/assets`.

#### Scenario: API route is requested
- **WHEN** a request path starts with `/api`
- **THEN** the student SPA fallback SHALL NOT intercept that request.

### Requirement: Admin frontend coexistence
The system SHALL keep the admin console available under `/admin` while adding student H5 root serving.

#### Scenario: Admin route is requested
- **WHEN** a request path starts with `/admin`
- **THEN** the admin SPA or admin static route SHALL handle the request
- **AND** the student SPA fallback SHALL NOT override it.

### Requirement: Student production readiness validation
The production readiness script SHALL validate both admin and student frontend build health.

#### Scenario: Readiness validation is run
- **WHEN** production readiness validation executes
- **THEN** it SHALL run existing backend, protected-resource, OpenSpec, and admin frontend checks
- **AND** it SHALL also run student H5 typecheck and build checks.

## ADDED Requirements

### Requirement: Teacher endpoints have explicit domain owners
The backend SHALL register teacher product endpoints under `/api/teacher/*` from feature-owned routers.

#### Scenario: Production app registers teacher routers
- **WHEN** the production FastAPI route table is inspected
- **THEN** teacher product routes MUST be registered under `/api/teacher/*`
- **AND** teacher product routes MUST be owned by feature or domain routers rather than a mixed monolithic endpoint module.

#### Scenario: Teacher route inventory is inspected
- **WHEN** the canonical backend route inventory is validated
- **THEN** every teacher path and method pair used by `web-teacher` MUST be registered under `/api/teacher/*`
- **AND** no `/api/admin/*` route MUST be required for the teacher frontend.

### Requirement: Legacy admin and web-admin API surfaces are removed
The legacy runtime SHALL not register `/api/admin/*` or `/api/web-admin/*` as browser-facing supported API contracts.

#### Scenario: Backend route table is inspected
- **WHEN** the production FastAPI route table is inspected after this change
- **THEN** `/api/admin/*` teacher-console routes MUST be absent
- **AND** `/api/web-admin/*` token operations routes MUST be absent
- **AND** `/api/teacher/*` and `/api/student/*` routes MUST remain available according to the route inventory.

#### Scenario: Removed route is requested
- **WHEN** a client requests an old `/api/admin/*` or `/api/web-admin/*` path
- **THEN** the legacy runtime MUST NOT handle it as a supported compatibility alias.

### Requirement: Teacher auth helper replaces admin-console auth helper
Backend authorization helpers SHALL expose a teacher-product check that accepts active `teacher` users and rejects students.

#### Scenario: Teacher route is authorized
- **WHEN** a route is intended for the teacher product
- **THEN** it MUST require an active authenticated `teacher`
- **AND** it MUST reject `student`, missing credentials, invalid credentials, and obsolete `admin` or `platform_admin` sessions.

#### Scenario: Token operations auth is inspected
- **WHEN** backend auth helpers and settings are inspected
- **THEN** `WEB_ADMIN_ACCESS_TOKEN` MUST NOT be required for the legacy runtime
- **AND** token-only `web-admin` auth helpers MUST NOT be part of production route authorization.

## REMOVED Requirements

### Requirement: Admin endpoints have explicit domain owners
**Reason**: Teacher product routes are no longer admin routes.
**Migration**: Move teacher product endpoints to `/api/teacher/*` and document teacher route ownership instead.

### Requirement: Existing admin API contracts remain compatible
**Reason**: `/api/admin/*` compatibility is explicitly removed to avoid carrying the old admin identity model.
**Migration**: Update repository-managed clients, route inventory, and tests to use `/api/teacher/*`.

### Requirement: Web-admin endpoints have explicit platform ownership
**Reason**: The standalone token-protected platform operations API is removed from the legacy branch.
**Migration**: Remove `/api/web-admin/*` route registration and replace teacher account setup with bootstrap/script workflows.

### Requirement: Auth helpers distinguish platform and teacher products
**Reason**: There is no platform token product in the legacy branch after the role collapse.
**Migration**: Use teacher-product auth for `/api/teacher/*` and student auth for `/api/student/*`.

### Requirement: Student preview routes have separated backend ownership
**Reason**: Token-based preview governance and current teacher-preview infrastructure are outside the focused legacy teacher/student runtime.
**Migration**: Remove `/api/web-admin/*` preview governance routes; retain only student-facing preview/session behavior that is still used by the legacy products.

## ADDED Requirements

### Requirement: Web-admin endpoints have explicit platform ownership
The backend SHALL register `web-admin` endpoints from a platform-owned router namespace separate from teacher-facing `/api/admin` routers.

#### Scenario: Production app registers web-admin router
- **WHEN** the production FastAPI app route table is inspected
- **THEN** `/api/web-admin/teacher-accounts` routes MUST be registered
- **AND** they MUST be owned by a web-admin or platform-account router module
- **AND** they MUST NOT be mounted from a teacher-facing feature router.

#### Scenario: Web-admin routes require configured token
- **WHEN** any `/api/web-admin/*` route is requested without the configured `WEB_ADMIN_ACCESS_TOKEN` Bearer token
- **THEN** the backend MUST reject the request with an authorization error.

#### Scenario: Teacher admin routes remain teacher-console routes
- **WHEN** existing `/api/admin/*` teacher-console routes are inspected
- **THEN** they MUST remain available to teacher-console users according to their existing route contracts
- **AND** the new platform teacher-account management endpoints MUST NOT be added under `/api/admin/*`.

### Requirement: Auth helpers distinguish platform and teacher products
Backend authorization helpers SHALL expose product-level checks for config-token web-admin routes and teacher-console routes.

#### Scenario: Teacher-console role check is used
- **WHEN** a route is intended for the teacher console
- **THEN** it MUST allow active `admin` users and compatible legacy `teacher` users unless a separate endpoint contract says otherwise
- **AND** it MUST reject students and platform admins.

#### Scenario: Web-admin config-token check is used
- **WHEN** a route is intended for the platform operations console
- **THEN** it MUST allow only requests carrying the configured web-admin token
- **AND** it MUST reject missing, invalid, or unconfigured tokens.

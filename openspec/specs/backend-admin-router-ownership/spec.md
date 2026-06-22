# backend-admin-router-ownership Specification

## Purpose
TBD - created by archiving change remove-monolithic-admin-router. Update Purpose after archive.
## Requirements
### Requirement: Admin endpoints have explicit domain owners
The backend SHALL register admin endpoints from feature-owned routers instead of a mixed-purpose `server.app.admin` endpoint module.

#### Scenario: Production app registers split admin routers
- **WHEN** `server.app.admin_main.app` is imported
- **THEN** the app MUST include domain routers for platform/AI configuration, learning assistant admin, media, feedback, classes/registration/roster, and curriculum/review endpoints
- **AND** `server.app.admin_main` MUST NOT import `server.app.admin` as an endpoint router

#### Scenario: Monolithic endpoint owner is retired
- **WHEN** the refactor is complete
- **THEN** `server/app/admin.py` MUST be deleted or contain no FastAPI endpoint owner used by production app wiring

### Requirement: Existing admin API contracts remain compatible
The backend SHALL preserve only the canonical admin API route inventory accepted for the backend slim architecture. Legacy aliases and compatibility endpoints MAY be removed when the updated route inventory, frontend calls, backend tests, and e2e validation are changed deliberately in the same refactor.

#### Scenario: Canonical path and method pairs remain registered
- **WHEN** the production FastAPI app route table is inspected
- **THEN** every admin path and method pair listed in the updated canonical route inventory MUST be registered
- **AND** each canonical path and method pair MUST be registered exactly once.

#### Scenario: Legacy compatibility aliases are removed
- **WHEN** a path exists only to preserve an older admin route alias, internal module shape, or deprecated deletion/archive behavior
- **THEN** the backend slim refactor MAY remove that alias
- **AND** the removed alias MUST NOT remain registered unless it is explicitly listed as canonical in the updated route inventory
- **AND** clients and tests MUST be updated to use the canonical route.

#### Scenario: Removed route aliases are recorded
- **WHEN** route aliases are removed during the backend slim refactor
- **THEN** the route inventory or implementation notes MUST record the removed aliases and their canonical replacements or deletion rationale.

### Requirement: Routers remain thin at domain boundaries
Admin routers SHALL delegate SQL-heavy or stateful domain behavior to services rather than growing new large mixed-concern route modules.

#### Scenario: Feedback routes are extracted
- **WHEN** feedback summary, listing, detail, or status update routes are moved
- **THEN** database filtering, counting, and update behavior MUST live in a feedback service module or existing feedback service boundary

#### Scenario: Class and roster routes are extracted
- **WHEN** class creation/update, registration settings, roster import, student CRUD, or password reset routes are moved
- **THEN** database-heavy behavior MUST live in a class/roster service module or existing roster service boundary

### Requirement: Refactor does not affect protected production resources or release triggers
The refactor SHALL leave production resource files and release/CI trigger posture unchanged.

#### Scenario: Protected resources are validated
- **WHEN** production readiness validation is run after the refactor
- **THEN** protected seed/resource manifests MUST still validate successfully

#### Scenario: Workflow trigger posture is preserved
- **WHEN** the refactor is pushed to `codex/productionize-admin-platform`
- **THEN** the production readiness workflow MUST NOT gain push or pull-request triggers as part of this change

### Requirement: Final ownership is documented
The backend admin owner map SHALL be documented after the refactor.

#### Scenario: Handoff documentation is updated
- **WHEN** implementation is complete
- **THEN** the change notes or repository documentation MUST identify which router owns each moved admin domain
- **AND** remaining risks or deliberately accepted compatibility layers MUST be listed

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

### Requirement: Backend route ownership excludes frontend SPA fallback
Backend route ownership SHALL be limited to backend-owned API, health, and service routes after the frontend deployment split.

#### Scenario: Admin SPA fallback is removed
- **WHEN** backend routes are registered
- **THEN** `/admin` and `/admin/{full_path:path}` MUST NOT be registered as backend-served SPA routes
- **AND** admin frontend fallback MUST be served by the admin frontend service.

#### Scenario: Student SPA fallback is removed
- **WHEN** backend routes are registered
- **THEN** `/` and `/{full_path:path}` MUST NOT be registered as student SPA fallback routes
- **AND** student frontend fallback MUST be served by the student frontend service.

#### Scenario: Backend static asset mounts are removed
- **WHEN** backend runtime is inspected
- **THEN** it MUST NOT mount admin or student frontend asset directories
- **AND** frontend assets MUST be served by their corresponding frontend services.

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


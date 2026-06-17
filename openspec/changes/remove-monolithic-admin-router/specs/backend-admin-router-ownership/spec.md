## ADDED Requirements

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
The backend SHALL preserve existing admin API path, method, auth, response, and compatibility behavior while moving endpoint ownership.

#### Scenario: Existing path and method pairs remain registered
- **WHEN** the production FastAPI app route table is inspected
- **THEN** every admin path and method pair listed in this change baseline MUST be registered
- **AND** each path and method pair MUST be registered exactly once

#### Scenario: Compatibility aliases remain available
- **WHEN** media binding deletion compatibility paths are inspected
- **THEN** `DELETE /api/admin/media/bindings/{binding_id}`, `POST /api/admin/media/bindings/{binding_id}/delete`, and `POST /api/admin/media/bindings/{binding_id}/archive` MUST remain registered

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

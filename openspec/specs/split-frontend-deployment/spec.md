# split-frontend-deployment Specification

## Purpose
TBD - created by archiving change split-frontend-deployment-admin-shell. Update Purpose after archive.
## Requirements
### Requirement: Frontend applications are independently deployed services
The system SHALL deploy the student H5 frontend, teacher console, and platform operations console as independent frontend services rather than serving their SPA bundles from the backend service.

#### Scenario: Compose starts the full application
- **WHEN** the default production-like Compose application is started
- **THEN** `web-student` MUST be a running service with its own published port
- **AND** `web-teacher` MUST be a running service with its own published port
- **AND** `web-admin` MUST be a running service with its own published port
- **AND** `backend` MUST remain a separate service with its own published API port.

#### Scenario: Frontend service serves deep SPA routes
- **WHEN** a browser requests a deep student, teacher, or platform SPA route from the corresponding frontend service
- **THEN** that frontend service MUST return the correct SPA `index.html`
- **AND** the backend service MUST NOT be responsible for that SPA fallback.

### Requirement: Backend service is API-only
The backend runtime SHALL stop serving built frontend assets or frontend SPA fallback routes.

#### Scenario: Backend image is built
- **WHEN** the backend Docker image is built
- **THEN** it MUST NOT copy `apps/web-admin/dist`
- **AND** it MUST NOT copy `apps/web-teacher/dist`
- **AND** it MUST NOT copy `apps/web-student/dist`.

#### Scenario: Backend route table is inspected
- **WHEN** the canonical backend route inventory is validated
- **THEN** backend-hosted admin SPA routes MUST be absent
- **AND** backend-hosted student SPA fallback routes MUST be absent
- **AND** backend API and health routes MUST remain available.

### Requirement: Frontend services proxy API traffic to backend
Each frontend service SHALL make backend API calls available through the frontend origin.

#### Scenario: Student frontend calls API
- **WHEN** the student frontend issues a request to `/api/*`
- **THEN** the student frontend runtime MUST forward the request to the backend service
- **AND** the browser-facing API contract MUST remain `/api/*`.

#### Scenario: Teacher frontend calls API
- **WHEN** the teacher frontend issues a request to `/api/*`
- **THEN** the teacher frontend runtime MUST forward the request to the backend service
- **AND** the browser-facing API contract MUST remain `/api/*`.

#### Scenario: Platform operations frontend calls API
- **WHEN** the platform operations frontend issues a request to `/api/*`
- **THEN** the platform operations frontend runtime MUST forward the request to the backend service
- **AND** the browser-facing API contract MUST remain `/api/*`.

### Requirement: Compose validation includes frontend services
The Compose smoke validation SHALL treat the student, teacher, and platform frontend services as required application services.

#### Scenario: Compose smoke runs
- **WHEN** Compose smoke validation runs for the full application
- **THEN** it MUST verify `backend`, `web-student`, `web-teacher`, `web-admin`, `postgres`, `elasticsearch`, `tusd`, and `video-worker` are running
- **AND** it MUST verify backend health, frontend reachability, PostgreSQL readiness, Elasticsearch/IK readiness, migrations, and video-library search readiness.

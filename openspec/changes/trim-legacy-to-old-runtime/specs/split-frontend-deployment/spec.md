## MODIFIED Requirements

### Requirement: Frontend applications are independently deployed services
The legacy branch SHALL deploy the old student frontend and old backoffice frontend as independent frontend services rather than serving SPA bundles from the backend service or exposing the newer three-console topology.

#### Scenario: Compose starts the full application
- **WHEN** the default production-like Compose application is started on the legacy branch
- **THEN** `web-student` MUST be a running frontend service with its own published port
- **AND** `web-backoffice` MUST be a running frontend service with its own published port
- **AND** `backend` MUST remain a separate service with its own published API port
- **AND** `web-teacher` and `web-admin` MUST NOT be required or present frontend services in the default legacy branch topology.

#### Scenario: Frontend service serves deep SPA routes
- **WHEN** a browser requests a deep student or backoffice SPA route from the corresponding frontend service
- **THEN** that frontend service MUST return the correct SPA `index.html`
- **AND** the backend service MUST NOT be responsible for that SPA fallback.

### Requirement: Frontend services proxy API traffic to backend
Each legacy branch frontend service SHALL make backend API calls available through the frontend origin.

#### Scenario: Student frontend calls API
- **WHEN** the student frontend issues a request to `/api/*`
- **THEN** the student frontend runtime MUST forward the request to the backend service
- **AND** the browser-facing API contract MUST remain `/api/*`.

#### Scenario: Teacher frontend calls API
- **WHEN** the backoffice frontend issues a request to `/api/*`
- **THEN** the backoffice frontend runtime MUST forward the request to the backend service
- **AND** the browser-facing API contract MUST remain `/api/*`.

#### Scenario: Platform operations frontend calls API
- **WHEN** a standalone platform operations frontend is inspected on the legacy branch
- **THEN** it MUST NOT exist as a default runtime service
- **AND** platform operations API proxy behavior MUST NOT be required for the legacy branch frontend topology.

### Requirement: Compose validation includes frontend services
The Compose smoke validation SHALL treat the old student and backoffice frontend services as the required legacy branch application frontend services.

#### Scenario: Compose smoke runs
- **WHEN** Compose smoke validation runs for the legacy branch application
- **THEN** it MUST verify `backend`, `web-student`, and `web-backoffice` are running
- **AND** it MUST verify backend health and frontend reachability
- **AND** it MUST NOT require `web-teacher`, `web-admin`, current `web-student`, Elasticsearch, tusd, or video-worker services merely to validate the old runtime entrypoints.

### Requirement: Legacy frontend services are independently deployed
The deployment topology SHALL support the old student and old backoffice frontend services as the canonical legacy branch services.

#### Scenario: Full legacy-enabled Compose topology starts
- **WHEN** the default legacy branch Compose application is started
- **THEN** `web-student` MUST be a running frontend service
- **AND** `web-backoffice` MUST be a running frontend service
- **AND** both frontend services MUST proxy browser-facing `/api/*` requests to the backend service
- **AND** `backend` MUST remain a shared service rather than an app-specific backend fork.

#### Scenario: Legacy frontend services serve deep routes
- **WHEN** a browser requests a deep old student or old backoffice SPA route
- **THEN** the corresponding frontend service MUST return its own SPA `index.html`
- **AND** the backend service MUST NOT become responsible for old SPA fallback routing

#### Scenario: Current-only development topology starts
- **WHEN** a maintainer inspects the legacy branch
- **THEN** the newer current-only frontend topology MUST NOT be the default topology for this branch
- **AND** current frontend service definitions MUST NOT be required to run or validate the legacy branch old products.

### Requirement: Legacy frontend service names and ports are stable
The system SHALL assign stable service names and browser ports to the canonical legacy branch frontend products.

#### Scenario: Service topology is inspected
- **WHEN** the local or production-like service topology is inspected on the legacy branch
- **THEN** the student frontend service MUST be named `web-student`
- **AND** the backoffice frontend service MUST be named `web-backoffice`
- **AND** the former old service names `web-student-old` and `web-teacher-old` MUST NOT be present
- **AND** service ports MUST not collide with the backend API port.

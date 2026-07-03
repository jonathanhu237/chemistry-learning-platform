## ADDED Requirements

### Requirement: Legacy frontend applications are independently deployed services
The legacy branch SHALL deploy `web-teacher` and `web-student` as independent frontend services rather than serving their SPA bundles from the backend service.

#### Scenario: Compose starts the legacy application
- **WHEN** the default production-like Compose application is started on the legacy branch
- **THEN** `web-teacher` MUST be a running frontend service with its own published port
- **AND** `web-student` MUST be a running frontend service with its own published port
- **AND** `backend` MUST remain a separate API service with its own published API port
- **AND** `web-admin`, `web-backoffice`, `web-teacher-old`, and `web-student-old` MUST NOT be required services.

#### Scenario: Frontend service serves deep SPA routes
- **WHEN** a browser requests a deep teacher or student SPA route from the corresponding frontend service
- **THEN** that frontend service MUST return the correct SPA `index.html`
- **AND** the backend service MUST NOT be responsible for frontend SPA fallback.

### Requirement: Compose validation covers the two legacy frontend services
The Compose smoke validation SHALL treat `web-teacher`, `web-student`, `backend`, and required infrastructure as the legacy application graph.

#### Scenario: Compose smoke runs
- **WHEN** Compose smoke validation runs for the legacy branch
- **THEN** it MUST verify `web-teacher`, `web-student`, `backend`, and `postgres` are running
- **AND** it MUST verify backend health, frontend reachability, frontend API proxies, PostgreSQL readiness, and migrations.

## REMOVED Requirements

### Requirement: Frontend applications are independently deployed services
**Reason**: The old requirement names three current-product frontend services including `web-admin`.
**Migration**: Use the legacy two-service frontend topology: `web-teacher` and `web-student`.

### Requirement: Compose validation includes frontend services
**Reason**: Compose validation no longer requires `web-admin`, Elasticsearch, tusd, or video-worker for the default legacy runtime.
**Migration**: Validate the smaller legacy graph and add optional services only through future explicit changes.

### Requirement: Legacy frontend services are independently deployed
**Reason**: The old frontend services are no longer optional `*-old` services; they are canonical.
**Migration**: Replace `web-teacher-old` with `web-teacher` and `web-student-old` with `web-student`.

### Requirement: Legacy frontend service names and ports are stable
**Reason**: The stable legacy service names are now `web-teacher` and `web-student`.
**Migration**: Keep legacy ports where useful, but bind them to canonical service names rather than `*-old` names.

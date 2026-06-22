## MODIFIED Requirements

### Requirement: Student H5 nested route SPA fallback
The system SHALL serve the student H5 SPA for authenticated app deep links and nested client routes while continuing to exclude API and admin paths from the student fallback.

#### Scenario: Student opens a root route directly
- **WHEN** a browser or WebView requests a student H5 root route such as `/home`, `/learn`, `/ai`, `/assessment`, or `/profile`
- **THEN** the FastAPI service MUST serve the student SPA entrypoint when the student frontend build exists
- **AND** the client router MUST be able to render the matching route after load.

#### Scenario: Student opens a detail route directly
- **WHEN** a browser or WebView requests a student H5 detail route such as `/chapter/{profileId}`, `/point/{experimentId}`, `/video-library`, `/ai/chat`, `/assessment/session/{sessionId}`, `/assessment/report/{sessionId}`, or `/feedback/new`
- **THEN** the FastAPI service MUST serve the student SPA entrypoint when the student frontend build exists
- **AND** the client router MUST be able to render the matching detail page after load.

#### Scenario: API route is requested
- **WHEN** a request path starts with `/api`
- **THEN** the student SPA fallback MUST NOT intercept that request
- **AND** the request MUST continue to be handled by the API routing layer.

#### Scenario: Admin route is requested
- **WHEN** a request path starts with `/admin`
- **THEN** the student SPA fallback MUST NOT intercept that request
- **AND** the admin SPA or admin static route MUST continue to handle it.

### Requirement: Student frontend validation includes route stack health
The production readiness checks SHALL validate that the route-driven student H5 frontend builds and can serve nested route entrypoints.

#### Scenario: Student frontend checks run
- **WHEN** production readiness validation or student H5 build validation executes
- **THEN** it MUST run student H5 typecheck and build checks
- **AND** it SHOULD include a smoke check or documented manual check for direct load of at least one root route and one detail route, including the video library route when this capability is enabled.

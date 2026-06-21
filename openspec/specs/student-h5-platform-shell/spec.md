# student-h5-platform-shell Specification

## Purpose
TBD - created by archiving change integrate-student-h5-platform. Update Purpose after archive.
## Requirements
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

### Requirement: Authenticated student bottom tab shell
The student H5 authenticated shell SHALL provide app-level bottom tab navigation after the student has completed login and required onboarding gates.

#### Scenario: Authenticated student enters app shell
- **WHEN** an authenticated student reaches the main H5 app
- **THEN** the app MUST render a bottom navigation bar for app-level destinations
- **AND** the bar MUST include student learning, experiments, assessment, and profile destinations
- **AND** the assistant destination MUST be available only when student assistant feature switches allow it.

#### Scenario: Student switches app tabs
- **WHEN** the student taps a bottom navigation item
- **THEN** the app MUST switch to that destination without logging the student out
- **AND** the app SHOULD preserve nested learning state such as selected chapter or point where practical.

#### Scenario: Onboarding surfaces render outside shell
- **WHEN** the app is showing login, password reset, pretest loading, pretest error, or pretest question surfaces
- **THEN** the bottom tab shell MUST NOT obscure those required onboarding actions
- **AND** those surfaces MAY keep the institutional branding used for entry and authentication.

### Requirement: Authenticated shell uses mobile app headers
The authenticated student H5 shell SHALL use compact mobile app headers instead of the large institutional brand rail on primary app tabs.

#### Scenario: Student views authenticated tab
- **WHEN** the student opens `学习`, `实验`, `问答`, `测评`, or `我的`
- **THEN** the top of the page MUST show compact destination or context information
- **AND** it MUST NOT show the large `中山大学化学学院 / 元素实验` brand rail as the primary first-viewport content.

#### Scenario: Student views login or entry gate
- **WHEN** the student is not yet in the authenticated app shell
- **THEN** the app MAY show institutional branding and the product title
- **AND** that branding MUST NOT force the authenticated shell to use the same large header.


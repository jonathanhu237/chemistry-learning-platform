# student-h5-platform-shell Specification

## Purpose
Define student H5 frontend delivery through the independent `web-student` service, authenticated shell behavior, nested-route fallback, mobile app headers, and frontend coexistence boundaries.
## Requirements
### Requirement: Student H5 frontend delivery
The system SHALL build and serve the student H5 frontend as a first-class `web-student` app alongside the `web-teacher` and `web-admin` frontend services.

#### Scenario: Student frontend build exists
- **WHEN** the production-like frontend stack builds `apps/web-student`
- **THEN** the `web-student` frontend service SHALL serve the student SPA from its own origin
- **AND** it SHALL serve student static assets from its own frontend runtime.

#### Scenario: API route is requested
- **WHEN** a student frontend request path starts with `/api`
- **THEN** the `web-student` frontend runtime SHALL proxy the request to the backend API service
- **AND** the student SPA fallback SHALL NOT intercept that request.

#### Scenario: Backend route table is inspected
- **WHEN** the FastAPI backend route inventory is validated
- **THEN** `/` and `/{full_path:path}` MUST NOT be registered as student SPA fallback routes
- **AND** frontend assets MUST NOT be mounted from the backend runtime.

### Requirement: Frontend service coexistence
The system SHALL keep the student, teacher, and platform operations frontends isolated by service instead of sharing backend-hosted SPA paths.

#### Scenario: Frontend services are inspected
- **WHEN** the production-like frontend services are inspected
- **THEN** the student H5 frontend MUST be served by `web-student`
- **AND** the teacher console MUST be served by `web-teacher`
- **AND** the platform operations console MUST be served by `web-admin`
- **AND** the backend service MUST NOT serve any of those SPA fallbacks.

### Requirement: Student production readiness validation
The production readiness script SHALL validate backend API readiness and student frontend build health independently.

#### Scenario: Readiness validation is run
- **WHEN** production readiness validation executes
- **THEN** it SHALL run existing backend, protected-resource, OpenSpec, and frontend service checks
- **AND** it SHALL run student H5 typecheck and build checks against `apps/web-student`.

### Requirement: Student H5 nested route SPA fallback
The `web-student` frontend service SHALL serve the student H5 SPA for authenticated app deep links and nested client routes while continuing to proxy API paths to the backend service.

#### Scenario: Student opens a root route directly
- **WHEN** a browser or WebView requests a student H5 root route such as `/home`, `/learn`, `/ai`, `/assessment`, or `/profile` from the `web-student` origin
- **THEN** the `web-student` frontend service MUST serve the student SPA entrypoint
- **AND** the client router MUST be able to render the matching route after load.

#### Scenario: Student opens a detail route directly
- **WHEN** a browser or WebView requests a student H5 detail route such as `/chapter/{profileId}`, `/point/{nodeId}`, `/video-library`, `/search`, `/ai/chat`, `/assessment/session/{sessionId}`, `/assessment/report/{sessionId}`, or `/feedback/new` from the `web-student` origin
- **THEN** the `web-student` frontend service MUST serve the student SPA entrypoint
- **AND** the client router MUST be able to render the matching detail page after load.

#### Scenario: API route is requested
- **WHEN** a request path starts with `/api`
- **THEN** the `web-student` frontend runtime MUST proxy the request to the backend API service
- **AND** the student SPA fallback MUST NOT intercept that request
- **AND** the request MUST continue to be handled by the API routing layer.

#### Scenario: Backend service is requested for a frontend route
- **WHEN** a browser requests `/home`, `/learn`, `/chapter/{profileId}`, `/point/{nodeId}`, or another student SPA route from the backend service origin
- **THEN** the backend MUST NOT serve the student SPA as a compatibility fallback
- **AND** deployment and QA MUST target the `web-student` frontend origin for student routes.

### Requirement: Student frontend validation includes route stack health
The production readiness checks SHALL validate that the route-driven student H5 frontend builds and can serve nested route entrypoints from the `web-student` service.

#### Scenario: Student frontend checks run
- **WHEN** production readiness validation or student H5 build validation executes
- **THEN** it MUST run student H5 typecheck and build checks against `apps/web-student`
- **AND** it SHOULD include a smoke check or documented manual check for direct load of at least one root route and one detail route, including the video library route when this capability is enabled.

### Requirement: Authenticated student bottom tab shell
The student H5 authenticated shell SHALL provide app-level bottom tab navigation after the student has completed login and required onboarding gates.

#### Scenario: Authenticated student enters app shell
- **WHEN** an authenticated student reaches the main H5 app
- **THEN** the app MUST render a bottom navigation bar for the five root destinations `home`, `learn`, `ai`, `assessment`, and `profile`
- **AND** the visible labels MUST be equivalent to `首页`, `学习`, `AI`, `测评`, and `我的`
- **AND** the `home` root MUST own experiment-video discovery rather than requiring a separate experiments root tab
- **AND** the `ai` destination MUST be available only when student assistant feature switches allow it.

#### Scenario: Student switches app tabs
- **WHEN** the student taps a bottom navigation item
- **THEN** the app MUST navigate to that root destination without logging the student out
- **AND** the active root destination MUST be derived from the route
- **AND** the app SHOULD preserve nested learning state such as selected chapter or point where practical.

#### Scenario: Onboarding surfaces render outside shell
- **WHEN** the app is showing login, password reset, pretest loading, pretest error, or pretest question surfaces
- **THEN** the bottom tab shell MUST NOT obscure those required onboarding actions
- **AND** those surfaces MAY keep the institutional branding used for entry and authentication.

### Requirement: Authenticated shell uses mobile app headers
The authenticated student H5 shell SHALL use compact mobile app headers instead of the large institutional brand rail on primary app tabs.

#### Scenario: Student views authenticated tab
- **WHEN** the student opens `首页`, `学习`, `AI`, `测评`, or `我的`
- **THEN** the top of the page MUST show compact destination or context information
- **AND** it MUST NOT show the large `中山大学化学学院 / 元素实验` brand rail as the primary first-viewport content.

#### Scenario: Student views login or entry gate
- **WHEN** the student is not yet in the authenticated app shell
- **THEN** the app MAY show institutional branding and the product title
- **AND** that branding MUST NOT force the authenticated shell to use the same large header.

### Requirement: Home root header uses quick-return chrome
The authenticated student H5 shell SHALL treat the home root logo/search row and its below-header recommendation rail as one quick-return header unit controlled by root scroll direction.

#### Scenario: Home root opens with full header
- **WHEN** an authenticated student opens the home root
- **THEN** the shell MUST render the full home header unit before the video feed
- **AND** the home header unit MUST include the main home row and any header-attached below content such as the recommendation rail.

#### Scenario: Downward feed scroll compresses home header
- **WHEN** the student scrolls downward in the home video feed past the configured root-scroll threshold
- **THEN** the shell MUST be allowed to enter the same compressed chrome state family used by root navigation quick-return behavior
- **AND** the visible home header unit MUST compress or move away as one unit without changing the active home root tab.

#### Scenario: Reverse scroll restores home header
- **WHEN** the student scrolls upward after the home header has compressed
- **THEN** the shell MUST restore the home header unit through the quick-return state
- **AND** returning near the top of the document MUST leave the home header fully visible.

#### Scenario: Detail routes do not inherit home header compression
- **WHEN** the current route is a second-level route such as video-library search, point video detail, AI chat detail, assessment session, assessment report, feedback, chapter, catalog, or element detail
- **THEN** the home header quick-return behavior MUST NOT be applied
- **AND** detail-route top chrome and bottom-navigation visibility MUST continue to follow route-stack rules.


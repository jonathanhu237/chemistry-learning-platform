## ADDED Requirements

### Requirement: Route level semantics are based on navigation role
The authenticated student H5 app SHALL classify pages by route role rather than by current history-stack depth, directory nesting, or the number of push navigations used to reach the page.

#### Scenario: Developer classifies authenticated student routes
- **WHEN** a route is one of the five bottom-nav roots: home, learn, AI, assessment, or profile
- **THEN** the route MUST be treated as a first-level/root page
- **AND** all other authenticated task, collection, and detail routes MUST be treated as non-tab detail routes unless a future OpenSpec change explicitly promotes one into root navigation.

#### Scenario: Detail route is opened from another detail route
- **WHEN** a student navigates from a non-tab detail route such as `/video-library` to another detail route such as an experiment point/video detail page
- **THEN** the target route MUST remain a non-tab detail route
- **AND** the app, specs, tests, and route organization MUST NOT introduce a separate "third-level page" category only because the runtime history stack became deeper.

#### Scenario: Navigation chrome follows route role
- **WHEN** the current route is any non-tab task, collection, or detail route
- **THEN** the bottom navigation MUST remain hidden
- **AND** the page MUST keep route-stack return behavior back to the opening source.

## MODIFIED Requirements

### Requirement: TanStack route stack for authenticated student H5
The authenticated student H5 app SHALL use a typed route stack backed by `@tanstack/react-router` instead of controlling primary navigation only through component-local tab state.

#### Scenario: Authenticated shell initializes routing
- **WHEN** an authenticated student reaches the main H5 app after required login and onboarding gates
- **THEN** the app MUST mount the authenticated student route tree
- **AND** route matching MUST determine the visible root or detail page
- **AND** app-level page transitions MUST NOT depend on a monolithic `activeTab` plus nested `screen` state inside one shell component.

#### Scenario: Direct detail route is opened
- **WHEN** a student opens a valid detail URL such as a chapter, point, video library, AI chat, assessment session, assessment report, or feedback URL
- **THEN** the route layer MUST render the matching detail page
- **AND** the page MUST fetch durable data from route params or search state rather than requiring prior in-memory tab state.

### Requirement: P0 second-level detail pages
The authenticated student H5 app SHALL provide P0 semantic second-level/detail pages for chapter learning, experiment point/video detail, video library search, AI chat, assessment session, assessment report, and feedback. "Second-level/detail" describes a non-tab route role, not a guarantee that the route is exactly one history entry away from a root page.

#### Scenario: Chapter learning detail is opened
- **WHEN** a student opens a chapter from the home root recommendation or the learn root chapter entry
- **THEN** the app MUST render a shared chapter learning detail page
- **AND** the page MUST support chapter facts/common-property content and experiment-video content for the selected profile.

#### Scenario: Experiment point detail is opened
- **WHEN** a student opens an experiment point or video from chapter learning, a recent-learning entry, or the video library
- **THEN** the app MUST render a shared experiment point/video detail page
- **AND** the page MUST show the available video, point context, experiment context, and learning completion affordances.

#### Scenario: Video library detail is opened
- **WHEN** a student opens the video library from the home video-library entry
- **THEN** the app MUST render a shared video library detail page
- **AND** the page MUST own experiment-video search, browse organization, and result grouping.

#### Scenario: AI chat detail is opened
- **WHEN** a student opens AI from the home root, learn root, AI root, point detail, video library, video-library result, or assessment report
- **THEN** the app MUST render the shared AI chat detail page
- **AND** the page MUST accept optional context from the opening source without changing root tab identity.

#### Scenario: Assessment session detail is opened
- **WHEN** a student starts a post-learning or assessment-center test
- **THEN** the app MUST render a shared assessment session detail page
- **AND** answering the test MUST NOT switch the visible root tab.

#### Scenario: Assessment report detail is opened
- **WHEN** a student submits a test or opens a previous report
- **THEN** the app MUST render a shared assessment report detail page
- **AND** the page MUST support AI summary and mistake explanation behavior where available.

#### Scenario: Feedback detail is opened
- **WHEN** a student opens feedback from profile or support entry points
- **THEN** the app MUST render a feedback detail page
- **AND** the page MUST support the existing authenticated feedback form and optional screenshot attachment behavior.

### Requirement: Detail pages hide bottom navigation
Semantic second-level/detail pages SHALL hide the bottom navigation while preserving route stack return behavior.

#### Scenario: Student enters detail page
- **WHEN** the current route is a chapter learning, experiment point, video library, AI chat, assessment session, assessment report, or feedback detail route
- **THEN** the bottom navigation MUST NOT be visible
- **AND** the page MUST provide a route-appropriate way to go back.

#### Scenario: Student returns to root page
- **WHEN** the student returns from a detail page to a root route using page back, browser back, Android/WebView back, or equivalent history navigation
- **THEN** the app MUST restore the originating root page
- **AND** the bottom navigation MUST reappear quickly when the root route becomes visible.

### Requirement: Shared detail pages preserve source-aware return
Shared non-tab detail pages SHALL preserve source-aware return behavior when opened from different first-level roots or other non-tab task pages. The video library itself is a collection/search detail page opened from the home entry in P0; it MUST NOT become an intermediate destination for learning-page tags that already have direct target routes.

#### Scenario: Same detail page is opened from different roots
- **WHEN** the same chapter, AI chat, report, or point detail page is opened from different root pages
- **THEN** the page component MAY be shared
- **AND** returning MUST go back to the route that opened it rather than switching to a fixed root destination.

#### Scenario: Page-local action opens shared detail
- **WHEN** a page-local action such as contextual AI, chapter recommendation, assessment start, feedback, or video-library result opens a shared detail page
- **THEN** the app MUST push a detail route
- **AND** it MUST NOT directly change the active root tab.

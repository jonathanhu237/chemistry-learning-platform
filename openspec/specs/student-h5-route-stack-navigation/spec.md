# student-h5-route-stack-navigation Specification

## Purpose
TBD - created by archiving change student-h5-router-tab-page-architecture. Update Purpose after archive.
## Requirements
### Requirement: TanStack route stack for authenticated student H5
The authenticated student H5 app SHALL use a typed route stack backed by `@tanstack/react-router` instead of controlling primary navigation only through component-local tab state.

#### Scenario: Authenticated shell initializes routing
- **WHEN** an authenticated student reaches the main H5 app after required login and onboarding gates
- **THEN** the app MUST mount the authenticated student route tree
- **AND** route matching MUST determine the visible root or detail page
- **AND** app-level page transitions MUST NOT depend on a monolithic `activeTab` plus nested `screen` state inside one shell component.

#### Scenario: Direct detail route is opened
- **WHEN** a student opens a valid detail URL such as a chapter, point, AI chat, assessment session, assessment report, or feedback URL
- **THEN** the route layer MUST render the matching detail page
- **AND** the page MUST fetch durable data from route params or search state rather than requiring prior in-memory tab state.

### Requirement: Five first-level root tabs
The authenticated student H5 app SHALL expose five first-level root destinations: `home`, `learn`, `ai`, `assessment`, and `profile`.

#### Scenario: Student views root navigation
- **WHEN** the authenticated student is on a root route
- **THEN** the app MUST make root destinations available as bottom navigation entries labeled for `首页`, `学习`, `AI`, `测评`, and `我的`
- **AND** the `AI` destination MUST be visually centered in the five-item navigation.

#### Scenario: Student taps bottom navigation
- **WHEN** the student taps a bottom navigation entry
- **THEN** the app MUST navigate to that root route
- **AND** the active root destination MUST match the route
- **AND** this user action is the only normal way to change root tab identity.

### Requirement: Root pages own list and center workflows
Each first-level root route SHALL own the browsing, list, center, or account workflow for its destination rather than rendering a detail task as its only content.

#### Scenario: Student opens learning root
- **WHEN** the student opens the `learn` root
- **THEN** the page MUST provide chapter selection, periodic-table entry, search or filtering affordances where available, and learning entry context
- **AND** it MUST NOT render a specific chapter as the only root content unless that chapter is explicitly opened as a detail route.

#### Scenario: Student opens AI root
- **WHEN** the student opens the `ai` root
- **THEN** the page MUST provide an AI center such as new chat entry, chat history, or suggested prompt entry points
- **AND** entering an actual conversation MUST use the shared AI chat detail page.

#### Scenario: Student opens assessment root
- **WHEN** the student opens the `assessment` root
- **THEN** the page MUST provide assessment-center content such as available assessments, reports, or mistake-review entry points
- **AND** answering a test or viewing a report MUST use the matching detail page.

### Requirement: P0 second-level detail pages
The authenticated student H5 app SHALL provide P0 second-level detail pages for chapter learning, experiment point/video detail, AI chat, assessment session, assessment report, and feedback.

#### Scenario: Chapter learning detail is opened
- **WHEN** a student opens a chapter from the home root recommendation or the learn root chapter entry
- **THEN** the app MUST render a shared chapter learning detail page
- **AND** the page MUST support chapter facts/common-property content and experiment-video content for the selected profile.

#### Scenario: Experiment point detail is opened
- **WHEN** a student opens an experiment point or video from chapter learning or a recent-learning entry
- **THEN** the app MUST render a shared experiment point/video detail page
- **AND** the page MUST show the available video, point context, experiment context, and learning completion affordances.

#### Scenario: AI chat detail is opened
- **WHEN** a student opens AI from the home root, learn root, AI root, point detail, or assessment report
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
Second-level detail pages SHALL hide the bottom navigation while preserving route stack return behavior.

#### Scenario: Student enters detail page
- **WHEN** the current route is a chapter learning, experiment point, AI chat, assessment session, assessment report, or feedback detail route
- **THEN** the bottom navigation MUST NOT be visible
- **AND** the page MUST provide a route-appropriate way to go back.

#### Scenario: Student returns to root page
- **WHEN** the student returns from a detail page to a root route using page back, browser back, Android/WebView back, or equivalent history navigation
- **THEN** the app MUST restore the originating root page
- **AND** the bottom navigation MUST reappear quickly when the root route becomes visible.

### Requirement: Root pages may hide navigation during scroll
Root pages SHALL be allowed to temporarily hide or compress the bottom navigation during scroll while preserving the active root route.

#### Scenario: Root page hides navigation for content focus
- **WHEN** the student scrolls a root page in a direction or state configured to maximize content space
- **THEN** the bottom navigation MAY hide or compress
- **AND** the active root route MUST remain unchanged
- **AND** the navigation MUST be restorable through reverse scroll, idle state, or route transition.

#### Scenario: Detail route overrides scroll navigation
- **WHEN** the student is on a detail route
- **THEN** the bottom navigation MUST remain hidden regardless of root-scroll auto-hide settings
- **AND** returning to a root route MUST restore root-route navigation behavior.

### Requirement: Shared detail pages preserve source-aware return
Shared second-level pages SHALL preserve source-aware return behavior when opened from different first-level roots.

#### Scenario: Same detail page is opened from different roots
- **WHEN** the same chapter, AI chat, report, or point detail page is opened from different root pages
- **THEN** the page component MAY be shared
- **AND** returning MUST go back to the route that opened it rather than switching to a fixed root destination.

#### Scenario: Page-local action opens shared detail
- **WHEN** a page-local action such as contextual AI, chapter recommendation, assessment start, or feedback opens a shared detail page
- **THEN** the app MUST push a detail route
- **AND** it MUST NOT directly change the active root tab.

### Requirement: Route-oriented frontend organization
The student H5 frontend SHALL separate route pages from reusable feature components so first-level and second-level pages can be optimized independently.

#### Scenario: Developer updates a root page
- **WHEN** a developer modifies a first-level root page such as home, learn, AI, assessment, or profile
- **THEN** the route page code SHOULD be localized to a root route module and its immediate supporting components
- **AND** shared feature components MUST remain reusable by detail pages where appropriate.

#### Scenario: Developer updates a detail page
- **WHEN** a developer modifies a P0 second-level page such as chapter learning, point detail, AI chat, assessment session, assessment report, or feedback
- **THEN** the route page code SHOULD be localized to a detail route module and its immediate supporting components
- **AND** the change MUST NOT require editing an unrelated root tab implementation except for intentional navigation entry changes.

### Requirement: Legacy state-driven navigation is removed
The student H5 route-stack refactor SHALL remove the current state-driven authenticated navigation implementation rather than preserving it behind the new router.

#### Scenario: Route refactor reaches parity
- **WHEN** the TanStack route tree renders the five root pages and P0 detail pages
- **THEN** the old authenticated navigation owner based on `activeTab`, `learningRoute`, `experimentRoute`, and `assessmentRoute` MUST be removed or decomposed into route-local components
- **AND** the app MUST NOT keep a parallel tab/screen router inside the authenticated shell.

#### Scenario: Developer locates a route page
- **WHEN** a developer needs to update a first-level or P0 second-level page after the refactor
- **THEN** the page owner MUST be discoverable under the route-page structure
- **AND** the developer MUST NOT need to inspect a monolithic shell component to understand normal page ownership.


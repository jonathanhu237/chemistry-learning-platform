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
- **WHEN** a student opens a valid detail URL such as a chapter, point, video library, AI chat, assessment session, assessment report, or feedback URL
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
Each first-level root route SHALL own the browsing, center, account, or entry workflow for its destination rather than rendering a detail task as its only content.

#### Scenario: Student opens learning root
- **WHEN** the student opens the `learn` root
- **THEN** the page MUST provide the periodic-table learning entry and recommendation guidance
- **AND** it MUST NOT render a selected-area chapter list, specific chapter, catalog directory, or point detail as root content unless that target is explicitly opened as a non-tab detail route.

#### Scenario: Student opens AI root
- **WHEN** the student opens the `ai` root
- **THEN** the page MUST provide an AI center such as new chat entry, chat history, or suggested prompt entry points
- **AND** entering an actual conversation MUST use the shared AI chat detail page.

#### Scenario: Student opens assessment root
- **WHEN** the student opens the `assessment` root
- **THEN** the page MUST provide assessment-center content such as available assessments, reports, or mistake-review entry points
- **AND** answering a test or viewing a report MUST use the matching detail page.

### Requirement: P0 second-level detail pages
The authenticated student H5 app SHALL provide P0 second-level detail pages for learning area selection, chapter learning, chapter element detail, catalog directory navigation, experiment point/video detail, AI chat, assessment session, assessment report, and feedback.

#### Scenario: Learning area detail is opened
- **WHEN** a student opens an area from the learn root periodic-table entry
- **THEN** the app MUST render a selected-area detail page
- **AND** the page MUST show the selected area identity and matching chapter entries
- **AND** the page MUST remain source-aware so back navigation restores the learning root.

#### Scenario: Chapter learning detail is opened
- **WHEN** a student opens a chapter from the home root recommendation or a selected-area chapter entry
- **THEN** the app MUST render a shared chapter learning detail page
- **AND** the page MUST show lightweight selected-element context and real experiment card entries for the selected profile
- **AND** the page MUST NOT show the old chapter-local facts/video capsule switch.

#### Scenario: Chapter element detail is opened
- **WHEN** a student opens an element detail from a chapter learning page
- **THEN** the app MUST render a shared element detail page
- **AND** the page MUST show the full atom/model learning content for the selected element
- **AND** the page MUST remain source-aware so back navigation restores the chapter page.

#### Scenario: Catalog directory detail is opened
- **WHEN** a student opens a catalog directory from a chapter or another catalog directory
- **THEN** the app MUST render a shared catalog directory detail page
- **AND** the page MUST show child directory and point entries for the selected node
- **AND** the page MUST remain source-aware so back navigation restores the opening chapter or directory route.

#### Scenario: Experiment point detail is opened
- **WHEN** a student opens an experiment point or video from chapter learning, catalog directory navigation, search, related-point links, or a recent-learning entry
- **THEN** the app MUST render a shared experiment point/video detail page
- **AND** the page MUST show the available video, point context, experiment context, and learning completion affordances.

#### Scenario: AI chat detail is opened
- **WHEN** a student opens AI from the home root, learn root, AI root, point detail, chapter detail, element detail, or assessment report
- **THEN** the app MUST render the shared AI chat detail page
- **AND** the page MUST accept optional context from the opening source without changing root tab identity.

#### Scenario: Assessment session detail is opened
- **WHEN** a student starts an assessment-center or supported learning-context test
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
- **WHEN** the current route is a selected learning area, chapter learning, chapter element detail, catalog directory, experiment point, AI chat, assessment session, assessment report, or feedback detail route
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
Shared non-tab detail pages SHALL preserve source-aware return behavior when opened from different first-level roots or other non-tab task pages. The video library itself is a collection/search detail page opened from the home entry in P0; it MUST NOT become an intermediate destination for learning-page tags that already have direct target routes.

#### Scenario: Same detail page is opened from different roots
- **WHEN** the same chapter, AI chat, report, or point detail page is opened from different root pages
- **THEN** the page component MAY be shared
- **AND** returning MUST go back to the route that opened it rather than switching to a fixed root destination.

#### Scenario: Page-local action opens shared detail
- **WHEN** a page-local action such as contextual AI, chapter recommendation, assessment start, feedback, or video-library result opens a shared detail page
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

### Requirement: Durable catalog node routes
The student H5 route stack SHALL support durable routes for catalog directories and point nodes.

#### Scenario: Direct catalog URL is opened
- **WHEN** a student opens a valid catalog directory URL directly
- **THEN** the app MUST fetch the directory node by route id
- **AND** it MUST render the directory page without requiring prior chapter-page state.

#### Scenario: Direct point URL is opened
- **WHEN** a student opens a valid point node URL directly
- **THEN** the app MUST fetch point detail by stable node id
- **AND** it MUST render the point detail without requiring legacy experiment id, point key, hybrid behavior, or shortcut source parameters.

#### Scenario: Wrong route type is opened
- **WHEN** a student opens a directory id on a point route or a point id on a directory route
- **THEN** the app MUST render a controlled unavailable state or redirect to the correct route according to route policy
- **AND** it MUST NOT crash the authenticated shell.

#### Scenario: Invalid node URL is opened
- **WHEN** a node id is missing, unpublished, archived, unsupported, or unavailable to the student
- **THEN** the app MUST render a controlled unavailable state or redirect according to route policy
- **AND** it MUST NOT crash the authenticated shell.

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

### Requirement: Element detail route for chapter elements
The authenticated student H5 app SHALL provide a dedicated element detail route opened from a chapter detail page.

#### Scenario: Student opens element detail from chapter page
- **WHEN** a student taps the element-detail entry for a selected element on a chapter detail page
- **THEN** the app MUST push an element detail route that identifies the current learning profile and element symbol
- **AND** the page MUST hide the bottom navigation
- **AND** returning MUST restore the chapter detail route that opened it.

#### Scenario: Student opens element detail directly
- **WHEN** a student opens a valid element detail URL directly
- **THEN** the route layer MUST render the element detail page
- **AND** the page MUST resolve durable data from route params rather than depending on prior in-memory chapter-page state.


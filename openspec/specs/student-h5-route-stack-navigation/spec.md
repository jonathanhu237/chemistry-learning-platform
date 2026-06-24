# student-h5-route-stack-navigation Specification

## Purpose
Define authenticated student H5 route roles, root tab ownership, second-level detail page behavior, source-aware return, and durable route contracts.
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
- **THEN** the app MUST make root destinations available as bottom navigation entries labeled for `首页`, `学习`, `Atom`, `测评`, and `我的`
- **AND** the `Atom` assistant destination MUST be visually centered in the five-item navigation.

#### Scenario: Student taps bottom navigation
- **WHEN** the student taps a bottom navigation entry
- **THEN** the app MUST navigate to that root route
- **AND** the active root destination MUST match the route
- **AND** this user action is the only normal way to change root tab identity.

### Requirement: Root pages own list and center workflows
Each first-level root route SHALL own the browsing, center, account, or entry workflow for its destination rather than rendering a detail task as its only content.

#### Scenario: Student opens learning root
- **WHEN** the student opens the `learn` root
- **THEN** the page MUST provide the periodic-table learning entry and a separate smart recommendation card
- **AND** the periodic-table entry MUST remain a selector for learning areas rather than an inline chapter list
- **AND** it MUST NOT render a selected-area chapter list, specific chapter, catalog directory, or point detail as root content unless that target is explicitly opened as a non-tab detail route.

#### Scenario: Student opens AI root
- **WHEN** the student opens the `ai` root
- **THEN** the page MUST provide the default/global AI conversation entry directly rather than an AI menu or duplicated placeholder page
- **AND** the AI root MUST own the visible history entry point for default/global AI conversations
- **AND** the AI root MAY opt out of the normal root-page header chrome so the assistant canvas starts at the top of the page frame
- **AND** this header opt-out MUST NOT change the route's root-tab identity or bottom-navigation behavior
- **AND** `/ai/chat` MUST remain available for contextual AI sessions opened from non-AI pages.

#### Scenario: Student opens assessment root
- **WHEN** the student opens the `assessment` root
- **THEN** the page MUST provide assessment-center content such as available assessments, reports, or mistake-review entry points
- **AND** answering a test or viewing a report MUST use the matching detail page.

### Requirement: P0 second-level detail pages
The authenticated student H5 app SHALL provide P0 second-level detail pages for learning area fallback selection, chapter learning, chapter element detail, catalog directory navigation, point video detail, AI chat, assessment session, assessment report, and feedback.

#### Scenario: Learning area fallback detail is opened
- **WHEN** a student opens a valid selected-area URL directly or returns to one through preserved history
- **THEN** the app MUST render a selected-area fallback detail page
- **AND** the page MUST show the selected area identity and matching chapter entries
- **AND** the page MUST remain source-aware so back navigation restores the learning root where possible.

#### Scenario: Chapter learning detail is opened
- **WHEN** a student opens a chapter from the home root recommendation, learning-root selected-area popover, or selected-area fallback chapter entry
- **THEN** the app MUST render a shared chapter learning detail page
- **AND** the page MUST show lightweight selected-element context and real catalog directory or point entries for the selected profile
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

#### Scenario: Point video detail is opened
- **WHEN** a student opens a point or video from chapter learning, catalog directory navigation, search, related-point links, or a recent-learning entry
- **THEN** the app MUST render a shared point video detail page
- **AND** the page MUST show the available video, point context, catalog/profile context, and learning completion affordances.

#### Scenario: AI chat detail is opened
- **WHEN** a student opens AI from the home root, learn root, point detail, chapter detail, element detail, or assessment report
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
Second-level detail pages SHALL hide the bottom navigation while preserving route stack return behavior. Transient overlays on root routes SHALL NOT be treated as second-level detail pages only because they appear above root content.

#### Scenario: Student enters detail page
- **WHEN** the current route is a selected learning area fallback, chapter learning, chapter element detail, catalog directory, point video, AI chat, assessment session, assessment report, or feedback detail route
- **THEN** the bottom navigation MUST NOT be visible
- **AND** the page MUST provide a route-appropriate way to go back.

#### Scenario: Student opens transient learning popover on root
- **WHEN** the current route remains the learning root and a selected-area chapter popover is open
- **THEN** the route MUST still be treated as a root route
- **AND** bottom navigation visibility MUST follow root-route behavior rather than detail-page hiding rules.

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
- **WHEN** a student navigates from a non-tab detail route such as `/video-library` to another detail route such as a point video detail page
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

### Requirement: Catalog directory route can render with family shell
The student H5 route stack SHALL allow catalog directory routes to render inside the family catalog shell when selected profile context is available.

#### Scenario: Directory route has profile context
- **WHEN** a catalog directory route is opened with a valid `profileId` search parameter
- **THEN** the route MUST resolve the selected learning profile using durable route/search data
- **AND** the page MUST render the family catalog shell with the directory body
- **AND** the bottom navigation MUST remain hidden because the route is still a non-tab detail route.

#### Scenario: Directory route lacks profile context
- **WHEN** a catalog directory route is opened without selected profile context
- **THEN** the route MUST continue to render a durable standalone directory page or controlled unavailable state
- **AND** it MUST NOT depend on prior in-memory chapter state.

#### Scenario: Directory navigation includes selected element context
- **WHEN** a directory is opened from a family catalog shell after the student selected an element
- **THEN** the navigation SHOULD include the selected element symbol in route search state
- **AND** the receiving shell SHOULD restore that selected element when it belongs to the selected profile.

### Requirement: Home feed navigation preserves source context
The student H5 route stack SHALL preserve home source context when students navigate from the home video feed to detail, search, or AI destinations.

#### Scenario: Feed item opens point detail
- **WHEN** a student opens a point video from the home feed
- **THEN** the route MUST include home source context such as `from=home`
- **AND** the point detail page MUST remain a second-level learning destination reachable from multiple sources

#### Scenario: Student returns from point detail
- **WHEN** the student returns from a point detail opened from home feed
- **THEN** the app MUST return to the home root
- **AND** the home root MUST still be the active bottom-tab identity

#### Scenario: Feed item opens AI chat
- **WHEN** a student opens AI chat from a feed item
- **THEN** the route MUST include the feed item's learning context
- **AND** returning from AI chat MUST preserve normal route-stack behavior without switching the active root tab unexpectedly

### Requirement: Detail route back affordances use shared mobile arrow
The authenticated student H5 route stack SHALL render non-tab/detail page back affordances with the shared student mobile back-arrow treatment so route-stack return feels consistent across page types, while playable point-video routes SHALL place that shared arrow inside the custom active player shell only.

#### Scenario: Normal detail route renders shared back affordance
- **WHEN** a student opens a non-tab detail route that uses the shared page header, including selected-area fallback, chapter/family catalog, catalog directory, chapter element detail, video library, AI chat, assessment session, assessment report, and feedback pages
- **THEN** the visible back arrow MUST use the shared student mobile back-arrow geometry
- **AND** the page MUST use the shared detail header/PageBar contract or a documented equivalent that renders the same shared arrow and placement
- **AND** the route MUST preserve the existing source-aware return behavior.

#### Scenario: Search/detail-style route renders shared back affordance
- **WHEN** a student opens a search or collection-style page that behaves as a second-level/detail route
- **THEN** its back control MUST use the same shared arrow geometry and reference-like left spacing as ordinary detail pages
- **AND** it MUST NOT introduce a separate icon size, stroke, or left-margin standard.

#### Scenario: Playable point-video route renders player-owned shared back affordance
- **WHEN** a student opens a point video detail page with a playable published video
- **THEN** the page MUST keep the video-first layout where the video frame owns the top chrome and long video titles are rendered below the frame
- **AND** the player-owned back arrow MUST use the shared student mobile filled-outline back-arrow geometry
- **AND** the player-owned back arrow MUST be part of the custom active player shell
- **AND** the player-owned back arrow MUST NOT be visible or touchable while the playable player shell is inactive
- **AND** the player-owned back arrow MUST preserve route-stack return behavior when tapped
- **AND** tapping the back arrow MUST NOT also toggle playback, activate progress seeking, or leave the custom shell in a stuck active state.

#### Scenario: Current second-level routes keep one back standard
- **WHEN** the authenticated route tree contains P0 second-level pages for learning area fallback, chapter/family catalog, catalog directory, chapter element detail, video library, search, point video detail, AI chat, assessment session, assessment report, and feedback
- **THEN** all ordinary header-based pages MUST render through the shared detail header/PageBar back affordance
- **AND** search MUST render the same shared arrow inside its search-bar back affordance
- **AND** playable point video detail MUST render the same shared arrow inside the custom active player shell
- **AND** point video empty state MUST render the same shared arrow inside the empty-player header
- **AND** no current P0 second-level page MAY introduce a separate arrow icon, copied SVG geometry, bitmap-derived glyph, or alternate left-spacing standard without a future OpenSpec change.

#### Scenario: Point-video empty state remains navigable
- **WHEN** a student opens a point video detail page with no playable published video
- **THEN** the empty-video frame MUST still expose a visible shared back arrow affordance
- **AND** tapping it MUST return using the same route-stack behavior as the playable-video state
- **AND** the empty-video back affordance MUST NOT wait for active playback chrome because no playable chrome exists
- **AND** the empty-video frame MUST NOT render a fake custom playback shell just to reveal a back affordance.

#### Scenario: Detail route back remains source-aware
- **WHEN** the same point video detail page is opened from a chapter catalog, directory page, unified search result, home feed, related experiment link, or recent-learning entry
- **THEN** the custom player-shell back action MUST return according to the same source-aware route-stack policy as the ordinary detail back action
- **AND** moving the back control into the player shell MUST NOT replace source-aware return with a fixed destination.

### Requirement: Detail back affordance changes do not alter route role semantics
Student H5 navigation SHALL treat this arrow refinement as a visual/navigation-control standardization only, without changing which routes are roots or details.

#### Scenario: Bottom navigation remains hidden on detail routes
- **WHEN** the current route is a non-tab/detail route after the arrow refinement
- **THEN** the bottom navigation MUST remain hidden according to existing route-role rules
- **AND** the updated back arrow MUST NOT promote the page into a root tab or add a new intermediate route category.

#### Scenario: Return behavior remains source-aware
- **WHEN** the same detail page is opened from different roots, search results, catalog directory links, related-point links, or recent-learning entries
- **THEN** the updated shared back arrow MUST return to the opening source according to the existing route-stack policy
- **AND** visual placement changes MUST NOT replace source-aware navigation with a fixed destination.

#### Scenario: Browser and WebView back remain compatible
- **WHEN** a student uses browser back, Android/WebView back, or the visible shared back arrow from a detail route
- **THEN** the app MUST continue to restore the correct previous route state
- **AND** the visual arrow standardization MUST NOT introduce duplicate history entries or bypass route-layer navigation.

### Requirement: Compact bottom navigation preserves root route identity
The authenticated student H5 route stack SHALL preserve the existing five root destinations and route ownership while allowing the centered Atom destination to use a visually elevated branded treatment.

#### Scenario: Root order and route targets remain unchanged
- **WHEN** the authenticated student bottom navigation renders after this redesign
- **THEN** it MUST expose root entries in the order `home`, `learn`, `ai`, `assessment`, and `profile`
- **AND** tapping each entry MUST navigate to the same root route as before the redesign
- **AND** the active root destination MUST continue to be derived from the current route.

#### Scenario: Atom is visual emphasis, not a new action route
- **WHEN** the centered Atom control is tapped
- **THEN** it MUST navigate to the existing `ai` root route
- **AND** it MUST NOT create a new publish/action route, overlay-only action, or contextual `/ai/chat` session by default
- **AND** contextual `/ai/chat` sessions opened from other pages MUST keep their existing detail-route behavior.

#### Scenario: Detail route hidden-navigation contract remains unchanged
- **WHEN** the current route is any non-tab task, collection, or detail route
- **THEN** the compact bottom navigation MUST remain hidden
- **AND** visual changes to root navigation MUST NOT promote any detail route into a root tab or introduce a new intermediate route category.

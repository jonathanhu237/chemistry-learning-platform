## MODIFIED Requirements

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

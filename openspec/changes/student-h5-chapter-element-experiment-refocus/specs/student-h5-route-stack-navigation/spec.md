## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: P0 second-level detail pages
The authenticated student H5 app SHALL provide P0 second-level detail pages for chapter learning, chapter element detail, experiment point/video detail, AI chat, assessment session, assessment report, and feedback.

#### Scenario: Chapter learning detail is opened
- **WHEN** a student opens a chapter from the home root recommendation or the learn root chapter entry
- **THEN** the app MUST render a shared chapter learning detail page
- **AND** the page MUST show lightweight selected-element context and real experiment card entries for the selected profile
- **AND** the page MUST NOT show the old chapter-local facts/video capsule switch.

#### Scenario: Chapter element detail is opened
- **WHEN** a student opens an element detail from a chapter learning page
- **THEN** the app MUST render a shared element detail page
- **AND** the page MUST show the full atom/model learning content for the selected element
- **AND** the page MUST remain source-aware so back navigation restores the chapter page.

#### Scenario: Experiment point detail is opened
- **WHEN** a student opens an experiment point or video from chapter learning or a recent-learning entry
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
- **WHEN** the current route is a chapter learning, chapter element detail, experiment point, AI chat, assessment session, assessment report, or feedback detail route
- **THEN** the bottom navigation MUST NOT be visible
- **AND** the page MUST provide a route-appropriate way to go back.

#### Scenario: Student returns to root page
- **WHEN** the student returns from a detail page to a root route using page back, browser back, Android/WebView back, or equivalent history navigation
- **THEN** the app MUST restore the originating root page
- **AND** the bottom navigation MUST reappear quickly when the root route becomes visible.

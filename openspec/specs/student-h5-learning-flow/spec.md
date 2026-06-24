# student-h5-learning-flow Specification

## Purpose
Define student-facing learning APIs and cross-surface handoffs that are not owned by the route stack or catalog browser layout, including catalog profile access, point video access, protected media, assessment handoff, contextual AI, and video-discovery result handoff.
## Requirements
### Requirement: Student learning home
The system SHALL provide a student learning home that exposes the student's available learning profiles, current family/chapter context, and progress context.

#### Scenario: Student opens learning home
- **WHEN** an authenticated student without a password-change requirement requests the learning home
- **THEN** the backend SHALL return student class context, available learning profiles or catalog entry points, and the current recommended family/chapter context
- **AND** it SHALL avoid exposing teacher-only identifiers or draft-only data.

### Requirement: Catalog profile and point access
The system SHALL provide student-facing catalog profile, directory, point, and video-detail APIs scoped to active/published learning resources.

#### Scenario: Student opens a catalog profile
- **WHEN** an authenticated student requests a family/chapter profile
- **THEN** the backend SHALL return the selected profile context, compact element context, and published directory or point entries available in that profile
- **AND** unavailable, archived, or draft-only resources SHALL NOT be exposed as playable student materials.

#### Scenario: Student opens a point detail
- **WHEN** an authenticated student requests an available catalog point detail
- **THEN** the backend SHALL return point metadata, learning content, published video readiness, and resource references for that point.

### Requirement: Protected media delivery
The system SHALL protect student media stream and thumbnail access using authenticated student context or equivalent short-lived authorization.

#### Scenario: Student requests protected media
- **WHEN** an authenticated student requests media that is bound to an available published point
- **THEN** the backend SHALL authorize access before serving the stream or thumbnail
- **AND** unpublished or unready media SHALL remain unavailable.

#### Scenario: Unauthenticated media request
- **WHEN** a request lacks a valid student authorization token
- **THEN** the backend SHALL reject protected media access.

### Requirement: Chapter learning to assessment handoff
The student H5 learning flow SHALL preserve the existing completion-to-assessment path from point detail by opening assessment detail routes instead of switching the assessment root tab.

#### Scenario: Chapter page does not show completion action
- **WHEN** a student opens the current family or chapter detail page
- **THEN** the page MUST NOT show a generic finish-learning or start-assessment action
- **AND** the page MUST focus on compact element summary and catalog directory or point entries.

#### Scenario: Student completes point detail learning
- **WHEN** a student opens a point detail from the current family or chapter page and then completes learning
- **THEN** the H5 app MUST preserve the point, profile, chapter, selected-element, and video context needed for learning events, AI context, feedback context, and the existing assessment handoff
- **AND** the app MUST navigate to a second-level assessment session route with the bottom navigation hidden
- **AND** returning through history MUST restore the previous detail or root route rather than forcing the assessment root.

### Requirement: Chapter-local catalog learning flow
The student H5 learning flow SHALL make the selected family or chapter detail page a lightweight entry surface that shows compact selected-element context and real catalog entries, while moving full element-model learning into a dedicated detail route.

#### Scenario: Student enters chapter from periodic table
- **WHEN** a student selects a family/chapter from the periodic-table learning root
- **THEN** the H5 app MUST open that family/chapter as the current learning detail route
- **AND** it MUST show a compact current-element summary rather than the full atom model
- **AND** it MUST show real catalog directory and point entries for the selected chapter/profile below the element summary
- **AND** it MUST NOT show a local two-mode facts/video capsule switch
- **AND** the bottom navigation MUST remain hidden because the student is on a detail route.

#### Scenario: Student changes selected element on the chapter page
- **WHEN** a student selects another element within the current chapter/family page
- **THEN** the page MUST update the compact selected-element summary
- **AND** the selected chapter/profile MUST remain unchanged
- **AND** the page MUST NOT navigate to another first-level root tab.

#### Scenario: Student opens element detail
- **WHEN** a student taps the element-detail entry from the compact selected-element summary
- **THEN** the app MUST open a dedicated element detail route for the selected profile and element
- **AND** the element detail page MUST render the full element model and detailed atom/fact controls
- **AND** returning MUST restore the chapter detail page.

#### Scenario: Student opens a point from the chapter catalog
- **WHEN** a student selects a real point entry from the chapter detail page
- **THEN** the app MUST open the existing point detail experience as a second-level point detail route with profile, chapter, point, video, and selected element context where available
- **AND** returning from point detail MUST restore the chapter page
- **AND** the app MUST NOT switch to a separate obsolete experiment root tab.

#### Scenario: Student views removed property sections
- **WHEN** a student is on the refocused chapter detail page
- **THEN** the page MUST NOT render whole-family/common-property cards as a separate encyclopedia section
- **AND** detailed element facts MUST remain available through the element detail route instead of expanding the chapter page.

### Requirement: Contextual AI opens shared chat detail
The student H5 learning flow SHALL open contextual AI as the shared AI chat detail page without changing the active root tab.

#### Scenario: Student asks from chapter detail
- **WHEN** a student taps a contextual AI action from a chapter learning detail page
- **THEN** the app MUST open the shared AI chat detail page with chapter context
- **AND** the bottom navigation MUST remain hidden
- **AND** returning MUST restore the chapter learning detail route.

#### Scenario: Student asks from point detail
- **WHEN** a student taps a contextual AI action from a point detail page
- **THEN** the app MUST open the shared AI chat detail page with profile and point context
- **AND** the bottom navigation MUST remain hidden
- **AND** returning MUST restore the point detail route.

### Requirement: Video library results hand off to learning flow
The student H5 learning flow SHALL allow video-library search and browse results to open existing learning detail pages without changing root tab identity. Normal learning-page tags and cards SHALL continue to navigate directly to their matching learning targets rather than opening the video library.

#### Scenario: Learning page tag opens direct target
- **WHEN** a student selects a tag, chapter card, catalog directory, or point card from the learning root or chapter learning page
- **THEN** the app MUST navigate directly to the matching chapter, directory, or point detail route
- **AND** it MUST NOT open the video library as an intermediate page.

#### Scenario: Student opens point result from video library
- **WHEN** a student selects a video point result from the video library
- **THEN** the app MUST open the existing point/video detail route
- **AND** the route MUST include available point, video, profile, chapter, element, property, or knowledge context from the result.

#### Scenario: Student opens chapter result from video library
- **WHEN** a student selects a chapter, element-family, or catalog chapter result from the video library
- **THEN** the app MUST open the related chapter learning detail route
- **AND** the route MUST preserve source context so back navigation can return to the video library search page.

#### Scenario: Student asks AI from a video-library result
- **WHEN** a student opens AI explanation for a video-library result
- **THEN** the app MUST open the shared AI chat detail page with video, phenomenon, reagent, experiment, or knowledge-point context
- **AND** returning MUST restore the video library page or the detail page that opened AI.

#### Scenario: Student returns from a result detail
- **WHEN** a student returns from a point detail, chapter detail, or AI chat opened from the video library
- **THEN** the app MUST restore the video library route where browser history allows
- **AND** it MUST NOT force the assessment root, learning root, or any obsolete experiment root tab.

#### Scenario: Student completes point learning opened from video library
- **WHEN** a student completes learning from a point detail that was opened through the video library
- **THEN** the existing supported completion-to-assessment behavior MAY start an assessment session detail route
- **AND** the completion action MUST NOT change the active root tab identity as a side effect.

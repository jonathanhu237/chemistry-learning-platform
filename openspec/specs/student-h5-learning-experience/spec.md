# student-h5-learning-experience Specification

## Purpose
TBD - created by archiving change student-h5-real-learning-experience. Update Purpose after archive.
## Requirements
### Requirement: Student H5 app configuration
The platform SHALL provide an authenticated student app configuration endpoint that exposes student-visible feature flags without exposing admin-only settings internals.

#### Scenario: Student loads app config
- **WHEN** an authenticated student requests the H5 app configuration
- **THEN** the response MUST include whether the AI assistant entry is visible
- **AND** it MUST include whether the feedback entry is visible
- **AND** it MUST include whether student AI capability is enabled

#### Scenario: Unauthenticated app config is rejected
- **WHEN** a request without a valid student token requests the H5 app configuration
- **THEN** the backend MUST reject the request using the normal student authentication rules

#### Scenario: H5 refreshes feature flags without WebSocket
- **WHEN** the student H5 app starts, regains focus, or changes major learning screens
- **THEN** it MUST refresh or reuse a recently refreshed app configuration
- **AND** it MUST hide AI or feedback entry points when the corresponding flag is disabled

### Requirement: Explicit student learning profile seed
The system SHALL keep display-facing family and element property facts in an explicit maintained seed resource instead of deriving H5 UI fields from RAG chunks at request time.

#### Scenario: Learning profile seed is validated
- **WHEN** production resource validation or test validation runs
- **THEN** every enabled student learning profile MUST include a chapter or family identifier, display title, summary, required property cards, and related property sections
- **AND** required property cards MUST cover atomic number, electron configuration, group, common valence, elemental state, and oxidizing/reducing tendency where applicable

#### Scenario: Backend loads profile facts
- **WHEN** the student learning API builds the H5 learning payload
- **THEN** it MUST read display facts from the explicit seed resource
- **AND** it MUST NOT depend on parsing canonical RAG chunk text to produce display facts

### Requirement: Real student learning page payload
The backend SHALL expose a student learning payload centered on a family or chapter profile, its display facts, and its chapter-level experiment-point video groups.

#### Scenario: Student opens learning page
- **WHEN** an authenticated student opens the H5 learning page
- **THEN** the backend MUST return a recommended, default, or explicitly selected learning profile
- **AND** the payload MUST include the profile's visible family/element facts and common-property content
- **AND** it MUST include experiment-point video groups derived from published formal experiments for the current chapter

#### Scenario: Student opens the experiment-point video view
- **WHEN** a student switches to the experiment-point video view
- **THEN** the H5 app MUST show experiment-point cards grouped by chapter parent experiment and point
- **AND** the cards MUST include experiment/point title, concise reaction or point summary when available, media availability, and question count
- **AND** the view MUST NOT depend on selecting a chemical property section such as oxidizing property or reducing property

#### Scenario: No video exists for a point
- **WHEN** a related experiment point has no published video media
- **THEN** the H5 app MUST still show the point and its learning context
- **AND** it MUST render a graceful empty video state instead of failing navigation

### Requirement: Student H5 mobile-first WebView contract
The student learning surface SHALL be treated as a phone-first H5 / mini-program WebView experience, not as a desktop admin page or a shrunken desktop layout.

#### Scenario: Student opens H5 on a phone viewport
- **WHEN** the student H5 app is viewed at common phone widths from 360px to 430px CSS pixels
- **THEN** primary learning screens MUST fit the viewport without horizontal scrolling
- **AND** headings, cards, segmented chapter switcher, bottom navigation, floating feedback entry, chat entry, and action buttons MUST remain tappable and non-overlapping
- **AND** the layout MUST prioritize the phone flow: current chapter context, A/B facts-or-experiments switching, experiment-point cards, point detail, chat, and feedback

#### Scenario: Student uses touch-only interaction
- **WHEN** a student uses the app without hover, precise mouse input, or desktop keyboard shortcuts
- **THEN** all required learning, A/B switching, chat, feedback, login, password-change, pretest-skip, and logout actions MUST be reachable through touch controls
- **AND** interactive controls SHOULD use phone-appropriate hit areas and spacing

#### Scenario: Desktop browser is used only for development preview
- **WHEN** a developer opens the student H5 app on a wide desktop browser
- **THEN** the app MAY center or constrain the phone layout for preview
- **BUT** it MUST NOT introduce desktop-only navigation, table-first layouts, hover-only affordances, or admin-console density into the student H5 experience

### Requirement: Student experiment point detail
The student H5 app SHALL provide a point detail experience that keeps video learning primary while showing compact explanation context.

#### Scenario: Student opens a point detail
- **WHEN** a student opens a related experiment point
- **THEN** the page MUST show the point title, parent experiment context, available video, observed phenomenon or summary, related reaction or principle when available, and safety/caution notes when available
- **AND** the app MUST preserve student learning event recording for post-learning behavior

#### Scenario: Point detail chat context is created
- **WHEN** a point detail page is open and AI assistant is enabled
- **THEN** the H5 app MUST pass chapter, experiment, point key or point title, and page summary context to student chat requests

### Requirement: Global authenticated H5 feedback
The student H5 app SHALL provide a global feedback entry for authenticated students when the feedback feature is enabled.

#### Scenario: Student submits feedback
- **WHEN** an authenticated student submits feedback from any H5 learning screen
- **THEN** the backend MUST create a feedback record using the authenticated student's identity
- **AND** it MUST capture feedback type, content, page path or screen, and available chapter/experiment/point context
- **AND** the feedback MUST appear in the existing admin feedback management workflow

#### Scenario: Feedback switch is disabled
- **WHEN** the admin feedback switch is disabled
- **THEN** the H5 app MUST hide the feedback entry after configuration refresh
- **AND** the backend MUST reject new student feedback submissions even if a stale client attempts one

#### Scenario: Client cannot spoof student identity
- **WHEN** a student feedback request includes client-supplied student or class identity in metadata
- **THEN** the backend MUST derive the authoritative student and class identity from the authenticated token
- **AND** it MUST NOT trust client-supplied identity fields

### Requirement: Current family chapter composition
The student H5 element learning page SHALL render as the learning page for one current family or chapter selected from the periodic-table learning entry, not as a primary sibling-family browsing surface.

#### Scenario: Student opens a selected family chapter
- **WHEN** a student opens the H5 learning page for a selected profile such as `halogens-17`
- **THEN** the page MUST show the selected family or chapter as the current learning context
- **AND** it MUST NOT present sibling families as the page-level primary navigation
- **AND** it MUST provide a secondary way to return to or switch through the periodic-table learning entry.

#### Scenario: Student opens the default or recommended chapter
- **WHEN** no explicit profile is selected and the system resolves a default or recommended profile
- **THEN** the page MUST still render that profile as the current family or chapter
- **AND** it MUST NOT imply that the student is on a cross-family index page.

### Requirement: Within-family element selection
The student H5 element learning page SHALL let students select an element within the current family and view facts for that selected element without changing the current family or chapter.

#### Scenario: Student selects an element chip
- **WHEN** the current profile contains multiple elements such as `F`, `Cl`, `Br`, `I`, and `At`
- **THEN** the page MUST render touch-friendly element chips for those elements
- **AND** selecting a chip MUST update the selected-element facts area
- **AND** the selected property section and experiment-point groups MUST remain scoped to the same current family or chapter.

#### Scenario: Selected element facts are shown
- **WHEN** a student selects an element inside the current family
- **THEN** the page MUST show available element-specific facts including atomic number, electron configuration, family or group, common valence, elemental state, and oxidizing or reducing tendency where applicable
- **AND** missing optional facts MUST degrade to a clear empty or unavailable state rather than causing the page to fail.

### Requirement: Family-wide common properties
The student H5 element learning page SHALL distinguish family-wide common properties and trends from selected-element facts.

#### Scenario: Student reviews family common properties
- **WHEN** the current profile defines common properties or trend summaries
- **THEN** the page MUST show those properties as family-level learning context
- **AND** the content MUST remain visually separate from selected-element facts
- **AND** it MUST support trend formulas or summaries such as oxidizing strength, reducing strength, salt formation, precipitation, coordination, or disproportionation where defined by seed data.

#### Scenario: Common properties connect to experiment sections
- **WHEN** a family-wide property corresponds to one or more experiment-point sections
- **THEN** the page MUST provide a clear path from the property summary to the related experiment-point group
- **AND** the experiment-point group MUST remain the primary actionable learning content.

### Requirement: Experiment-point primary task area
The student H5 element learning page SHALL keep related experiment points as the primary learning task after the compact chemistry context.

#### Scenario: Student reaches related experiment points
- **WHEN** a selected family or property has related experiment points
- **THEN** the page MUST show point cards grouped by the relevant property or parent experiment
- **AND** each point card MUST include the point title, parent experiment context, concise reaction or point summary when available, media availability, and question count
- **AND** selecting a point card MUST open the point detail learning page.

#### Scenario: Context area would push points too low
- **WHEN** selected-element facts and family common properties contain more content than fits comfortably before the point list on a phone viewport
- **THEN** the page MUST prioritize compact summaries, expandable detail, or equivalent progressive disclosure
- **AND** it MUST keep the experiment-point task area discoverable without requiring excessive scrolling.

### Requirement: Optional licensed reference media
The student H5 element learning page SHALL treat public images, videos, or external reference resources as optional licensed reference media, not as protected experiment-point resources.

#### Scenario: Reference media exists
- **WHEN** the profile seed or media manifest provides reference media for a family, element, or property
- **THEN** the page MAY show the media as contextual illustration
- **AND** the resource metadata MUST include source URL, license, attribution, usage scope, and alt text
- **AND** the page MUST distinguish reference media from protected experiment videos and manually reviewed point evidence.

#### Scenario: Reference media is absent
- **WHEN** no reference media exists or a reference media source is unavailable
- **THEN** the page MUST still render the selected-element facts, family common properties, experiment-point groups, AI entry, feedback entry, and assessment handoff.

### Requirement: Two-tab chapter learning composition
The student H5 chapter learning page SHALL split the selected family/chapter learning experience into two quickly switchable sibling views: a facts/common-property view and an experiment-point video view.

#### Scenario: Student switches from facts to experiments
- **WHEN** a student opens a selected family/chapter page
- **THEN** the H5 app MUST show a visible two-option switcher for facts/common properties and experiment videos
- **AND** selecting the experiment option MUST show the chapter's experiment-point video learning view without changing the selected chapter or selected element

#### Scenario: Student switches from experiments to facts
- **WHEN** a student is viewing experiment-point video content for a chapter
- **THEN** selecting the facts option MUST return to the same chapter's element facts and family common properties
- **AND** the selected family/chapter MUST remain the current learning context

#### Scenario: Facts view contains theory content
- **WHEN** the facts/common-property view is active
- **THEN** the page MUST show selected-element facts, family-wide common properties or trend summaries, and optional licensed reference media when available
- **AND** it MUST NOT require the student to interpret experiment-point navigation through chemical property sections

#### Scenario: Experiments view contains task content
- **WHEN** the experiment-point video view is active
- **THEN** the page MUST show experiment-point learning content grouped by current chapter, parent experiment, and point
- **AND** it MUST keep video availability, point title, parent experiment context, and question count visible on point cards where available

### Requirement: Property sections are facts content
The student H5 learning page SHALL treat property sections as theory/common-property content rather than as the required primary grouping for experiment-point video learning.

#### Scenario: Property sections exist in seed data
- **WHEN** a learning profile includes property sections such as oxidizing property, reducing property, precipitation, coordination, or disproportionation
- **THEN** the H5 app MAY render those sections in the facts/common-property view
- **AND** it MUST NOT require the experiment-point view to group points by those property sections

#### Scenario: Experiment-point grouping is chapter based
- **WHEN** the backend builds the experiment-point payload for a selected profile
- **THEN** it MUST provide or derive groups based on the selected chapter's parent experiments and points
- **AND** it MUST avoid using property section selection as the primary experiment navigation contract

### Requirement: Periodic-table entry distinguishes selection from recommendation
The student H5 periodic-table entry SHALL distinguish area selection, recommended guidance, and chapter navigation entry semantics.

#### Scenario: Recommended chapter is shown as guidance
- **WHEN** the periodic-table entry has a recommended profile
- **THEN** the matching chapter entry MUST show a recommendation label
- **AND** it MUST NOT render as a selected, active, or current chapter before the student opens it

#### Scenario: Student changes selected area
- **WHEN** the student taps an area control or an element cell from a different area
- **THEN** the chapter list MUST filter to that selected area
- **AND** the selected area MUST be visually distinguishable from other areas
- **AND** the recommended area cue MUST remain recommendation guidance rather than forcing the selected area back after the student's tap

#### Scenario: Student opens a chapter entry
- **WHEN** the student taps a chapter entry card
- **THEN** the H5 app MUST navigate into that family or chapter learning page
- **AND** the entry card itself MUST be treated as a navigation row rather than a persistent selected item on the entry page

#### Scenario: Current area shows learnable elements
- **WHEN** the periodic-table entry has learning profiles for the selected area
- **THEN** element cells in the selected area whose symbols appear in those profiles MUST show the element symbol
- **AND** element cells outside the selected area MUST NOT show profile-driven element symbols
- **AND** selected-area element cells without a matching profile symbol MAY remain unlabeled color cells

#### Scenario: Hydrogen and noble gases are a student learning area
- **WHEN** the student uses the periodic-table entry
- **THEN** hydrogen and group 18 noble gas cells MUST map to a dedicated `氢和稀有气体` learning area
- **AND** the area MUST filter the chapter list to matching learning profiles such as the hydrogen and noble gases chapter
- **AND** the student entry MUST NOT expose a `通识资源` area
- **AND** f-block layout coordinates MUST NOT cause lanthanide or actinide cells such as Lu or Lr to map to the `氢和稀有气体` learning area

### Requirement: H5 feedback supports screenshot attachments
The student H5 feedback capability SHALL support one optional image screenshot attachment from the authenticated mobile feedback entry while preserving feature-flag and identity controls.

#### Scenario: Student submits feedback with screenshot
- **WHEN** an authenticated student submits H5 feedback with a png, jpg, jpeg, or webp screenshot no larger than 5 MB
- **THEN** the backend MUST create the feedback record using the authenticated student's identity
- **AND** it MUST store attachment metadata linked to that feedback record
- **AND** the response MUST indicate that one attachment was accepted
- **AND** the feedback MUST remain visible in the existing admin feedback workflow.

#### Scenario: Student submits feedback without screenshot
- **WHEN** an authenticated student submits H5 feedback without an attachment
- **THEN** the backend MUST create the feedback record through the same authoritative student feedback endpoint
- **AND** the response MUST indicate zero attachments.

#### Scenario: Student submits unsupported attachment
- **WHEN** a student submits feedback with an empty file, a file over 5 MB, or a file that is not png, jpg, jpeg, or webp
- **THEN** the backend MUST reject the request
- **AND** it MUST NOT create an orphaned attachment record.

#### Scenario: Feedback metadata includes spoofed identity
- **WHEN** a feedback request includes client-supplied student id, class id, or student snapshot data in metadata
- **THEN** the backend MUST derive authoritative student and class identity from the authenticated token
- **AND** it MUST remove or quarantine the client-supplied identity fields before storing metadata.

### Requirement: Single student feedback route ownership
The platform SHALL expose only one authoritative student feedback submission behavior for `POST /api/student/feedback`.

#### Scenario: Student feedback endpoint is registered
- **WHEN** backend routes are loaded
- **THEN** there MUST NOT be competing route handlers with different authentication, feature-flag, or payload semantics for `POST /api/student/feedback`
- **AND** the route MUST enforce the student feedback feature switch before creating feedback.

#### Scenario: Feedback switch is disabled
- **WHEN** the student feedback feature switch is disabled and a stale client submits feedback
- **THEN** the authoritative endpoint MUST reject the submission
- **AND** it MUST NOT create a feedback record or attachment.

### Requirement: Element detail atom model stage remains stable
The student H5 element detail page SHALL render the selected element's atom model in a stable, readable stage whose size is independent of adjacent fact content.

#### Scenario: Student opens element detail on a phone viewport
- **WHEN** a student opens an element detail route such as `/chapter/halogens-17/element/Cl` at a common phone viewport width from 360px to 430px CSS pixels
- **THEN** the atom model stage MUST be visible, nonblank, centered within its card, and controlled by readable touch controls
- **AND** selected-element fact content MUST appear without overlapping or stretching the atom model stage

#### Scenario: Developer previews element detail on a wide browser
- **WHEN** a developer opens the same element detail route in a wide desktop browser preview
- **THEN** the page MUST preserve the phone-first H5 composition for the atom model card
- **AND** fact chips, teaching cues, or other detail content MUST NOT stretch the atom viewer canvas into an abnormally tall rectangle
- **AND** the atom model MUST remain visible near the intended visual center of the stage without requiring excessive scrolling inside the model card

#### Scenario: External console errors are present
- **WHEN** unrelated browser extension CORS errors or backend auth errors appear in the developer console while the already-rendered element detail page is visible
- **THEN** those errors MUST NOT be treated as the rendering cause unless they prevent the atom data or component from loading
- **AND** layout geometry MUST remain the primary regression signal for this atom-stage failure mode

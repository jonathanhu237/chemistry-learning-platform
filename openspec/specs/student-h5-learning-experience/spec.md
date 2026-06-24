# student-h5-learning-experience Specification

## Purpose
Define general student H5 learning content behavior, including app configuration, learning payloads, point detail, element facts, feedback, chemistry notation, and home-vs-learning product boundaries. Catalog-browser navigation rules live in student-h5-learning-catalog.
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
The backend SHALL expose a student learning payload centered on a selected family or chapter profile and its chapter-scoped catalog tree, with catalog card display derived from authoritative catalog and point content.

#### Scenario: Student opens learning page
- **WHEN** an authenticated student opens the H5 learning page
- **THEN** the backend MUST return a recommended, default, or explicitly selected learning profile
- **AND** the payload MUST include the profile's visible family/element facts and common-property content where available
- **AND** it MUST include the top-level published catalog directory and point nodes for the current chapter.

#### Scenario: Student opens the catalog learning view
- **WHEN** a student enters the experiment learning area for a chapter
- **THEN** the H5 app MUST show catalog nodes according to the authored directory tree
- **AND** directory node cards MUST derive visible display from directory title, hierarchy, child availability, and stable frontend defaults
- **AND** point node cards MUST derive visible display from point title, point learning summary where available, binary video presence, and bound video thumbnail where available
- **AND** the view MUST NOT depend on a fixed parent grouping level or on teacher-authored card-presentation override fields.

#### Scenario: No video exists for a point
- **WHEN** a published point node has no published video media
- **THEN** the H5 app MUST still show the point and its learning context
- **AND** it MUST render a graceful empty video state instead of failing navigation.

### Requirement: Student H5 mobile-first WebView contract
The student learning surface SHALL be treated as a phone-first H5 / mini-program WebView experience, not as a desktop admin page or a shrunken desktop layout.

#### Scenario: Student opens H5 on a phone viewport
- **WHEN** the student H5 app is viewed at common phone widths from 360px to 430px CSS pixels
- **THEN** primary learning screens MUST fit the viewport without horizontal scrolling
- **AND** headings, cards, chapter catalog controls, bottom navigation, chat page, profile feedback, video controls, and action buttons MUST remain tappable and non-overlapping
- **AND** the layout MUST prioritize the phone flow: app-level tabs, home video discovery, current chapter context, catalog browser navigation, point video detail, chat, feedback, and assessment.

#### Scenario: Student uses touch-only interaction
- **WHEN** a student uses the app without hover, precise mouse input, or desktop keyboard shortcuts
- **THEN** all required learning, catalog navigation, video playback, chat, feedback, login, password-change, pretest-skip, and logout actions MUST be reachable through touch controls
- **AND** interactive controls SHOULD use phone-appropriate hit areas and spacing.

#### Scenario: Desktop browser is used only for development preview
- **WHEN** a developer opens the student H5 app on a wide desktop browser
- **THEN** the app MAY center or constrain the phone layout for preview
- **BUT** it MUST NOT introduce desktop-only navigation, table-first layouts, hover-only affordances, or admin-console density into the student H5 experience.

### Requirement: Student point detail
The student H5 app SHALL provide a point detail experience keyed by stable catalog point node identity.

#### Scenario: Student opens a point detail
- **WHEN** a student opens a point node
- **THEN** the page MUST show the point title, chapter/catalog path context, available video, principle equation or text, phenomenon explanation, safety/caution notes, and related experiment links when available
- **AND** the app MUST preserve student learning event recording for post-learning behavior.
- **AND** the page MUST NOT render teacher-only notes.

#### Scenario: Point detail chat context is created
- **WHEN** a point detail page is open and AI assistant is enabled
- **THEN** the H5 app MUST pass chapter, point node id, optional source path, and page summary context to student chat requests
- **AND** it MUST NOT rely on legacy `experiment_id` plus `point_key` as the primary context.

#### Scenario: Directory is opened as point detail
- **WHEN** a student route or stale client attempts to open a directory node as a point detail
- **THEN** the app MUST render a controlled unavailable state or redirect to the directory page
- **AND** it MUST NOT request video, point knowledge, or assessment context for the directory.

### Requirement: Global authenticated H5 feedback
The student H5 app SHALL provide authenticated feedback from the `我的` profile destination when the feedback feature is enabled.

#### Scenario: Student submits feedback from profile
- **WHEN** an authenticated student submits feedback from `我的`
- **THEN** the backend MUST create a feedback record using the authenticated student's identity
- **AND** it MUST capture feedback type, content, page path or screen, optional screenshot attachment, and any available route or learning context metadata
- **AND** the feedback MUST appear in the existing admin feedback management workflow.

#### Scenario: Student reports a page problem
- **WHEN** a student encounters a problem on a learning, experiment, assistant, or assessment page
- **THEN** the app MUST allow the student to report it through `我的` with a written description and optional screenshot
- **AND** the app MUST NOT require a current-page floating feedback widget to submit the report.

#### Scenario: Feedback switch is disabled
- **WHEN** the admin feedback switch is disabled
- **THEN** the H5 app MUST hide or disable the profile feedback entry after configuration refresh
- **AND** the backend MUST reject new student feedback submissions even if a stale client attempts one.

#### Scenario: Client cannot spoof student identity
- **WHEN** a student feedback request includes client-supplied student or class identity in metadata
- **THEN** the backend MUST derive the authoritative student and class identity from the authenticated token
- **AND** it MUST NOT trust client-supplied identity fields.

### Requirement: Within-family element selection
The student H5 element learning page SHALL let students select an element within the current family and view a model-led selected-element facts area for that element without changing the current family or chapter.

#### Scenario: Student selects an element chip
- **WHEN** the current profile contains multiple elements such as `F`, `Cl`, `Br`, `I`, and `At`
- **THEN** the page MUST render touch-friendly element chips for those elements
- **AND** selecting a chip MUST update the selected-element atom model card and compact facts area
- **AND** the selected property section and experiment-point groups MUST remain scoped to the same current family or chapter.

#### Scenario: Selected element compact context is shown
- **WHEN** a student selects an element inside the current family
- **THEN** the chapter page MUST show compact element-specific context such as atomic number, symbol, English name, focus copy, experiment relevance, and compact tags where available
- **AND** the compact context MUST preserve the selected element tile identity with atomic number, symbol, and English element name
- **AND** the full atom visualization and detailed physical facts MUST be opened through the element detail route
- **AND** missing optional facts or unavailable model data MUST degrade to a clear empty or unavailable state rather than causing the page to fail.

#### Scenario: Selected element facts remain compact before tasks
- **WHEN** selected-element physical facts, teaching notes, family common properties, and property summaries would make the chapter context long on a phone viewport
- **THEN** the selected-element card MUST use compact summaries, strips, chips, or progressive disclosure
- **AND** it MUST keep family common properties and experiment-point learning entry discoverable without excessive scrolling

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

### Requirement: RSC-backed selected-element physical facts
The student H5 learning experience SHALL support curated physical fact fields for selected elements using RSC Periodic Table fact boxes as the primary reference.

#### Scenario: Student sees RSC-style physical facts
- **WHEN** the selected element has curated physical facts
- **THEN** the element detail route MUST be able to show relative atomic mass, group, period, block, 20°C state, density, and electron configuration in a compact mobile layout
- **AND** those fields MUST be maintained in profile or profile-adjacent seed data rather than fetched from RSC at runtime

#### Scenario: Student sees teaching facts separately
- **WHEN** the selected element also has common valence, redox tendency, or profile-specific teaching note
- **THEN** the compact chapter context or element detail route MUST keep those teaching facts visible as learning cues
- **AND** it MUST distinguish them from source-attributed physical facts where attribution is shown

### Requirement: Experiment-focused selected element card
The student H5 chapter learning page SHALL present the selected element as a compact experiment-learning card rather than as a generated sentence or full detail summary.

#### Scenario: Selected element card renders curated focus copy
- **WHEN** a student selects an element within the current family or chapter
- **THEN** the compact selected-element card MUST keep the periodic-table element tile visible with atomic number, symbol, and English element label
- **AND** it MUST show a curated focus-property line for the selected element
- **AND** it MUST show a curated experiment-relevance line explaining why that element matters to the current chapter's experiments or observation tasks
- **AND** it MUST show compact supporting tags such as group, period/block, state, or common valence where available

#### Scenario: Selected element card avoids generated prose
- **WHEN** the H5 app renders the compact selected-element card
- **THEN** it MUST NOT generate the primary title or body by concatenating the selected element name with the family name
- **AND** it MUST NOT use family-wide trend text as the selected element card body
- **AND** it MUST NOT prefix a family trend sentence with the selected element name to make it appear element-specific

#### Scenario: Detailed facts remain outside compact card
- **WHEN** the selected element has detailed facts such as electron configuration, atomic mass, density, full redox tendency, reference URL, or longer notes
- **THEN** those details MUST remain available in the element detail route or equivalent detail area
- **AND** the compact selected-element card MUST only surface the short focus property, experiment relevance, and compact tags

#### Scenario: Element switching updates compact card
- **WHEN** the student taps another element chip in the same family or chapter
- **THEN** the compact card MUST update its tile, focus property, experiment relevance, and tags for the newly selected element
- **AND** the current family or chapter context, catalog browser state, and point entries MUST remain scoped to the same learning profile

### Requirement: Explicit element focus card seed copy
The platform SHALL store selected-element card copy as explicit maintained student learning seed data instead of deriving the compact card's teaching copy from RAG chunks, family trend summaries, or front-end string composition.

#### Scenario: Learning profile seed includes card copy
- **WHEN** production resource validation or test validation runs for enabled student learning profiles
- **THEN** each enabled element MUST include card-level focus copy, experiment relevance copy, and compact card tags before the profile is treated as complete for the redesigned card experience
- **AND** missing card-level copy MUST be reported as validation feedback before the profile is considered complete for the redesigned card experience

#### Scenario: Backend exposes card copy
- **WHEN** the student learning API builds the H5 learning payload for a selected family or chapter
- **THEN** each element badge MUST expose the card-level focus property, experiment relevance, and card tags when seed data provides them
- **AND** existing detailed element facts MUST remain available for the element detail experience

#### Scenario: Card copy is temporarily missing
- **WHEN** an element is missing redesigned card copy during migration
- **THEN** the H5 app MUST render a graceful compact fallback using stable factual tags where available
- **AND** the fallback MUST NOT recreate the old generated `<element>在<family>中的位置` pattern or use a family trend sentence as the element card body

### Requirement: Bottom-tab student app information architecture
The student H5 learning experience SHALL organize authenticated student workflows around bottom app tabs rather than a single learning page with floating global entries.

#### Scenario: Student views bottom-tab destinations
- **WHEN** a student is in the authenticated app shell with all features enabled
- **THEN** the app MUST provide destinations for `首页`, `学习`, `AI`, `测评`, and `我的`
- **AND** each destination MUST represent app-level navigation, not a chapter-local view switch.

#### Scenario: Student opens learning tab
- **WHEN** the student opens `学习`
- **THEN** the app MUST provide the periodic-table chapter entry, current or recommended chapter access, selected-area navigation, family/chapter catalog navigation, and point detail navigation
- **AND** chapter-local catalog controls MUST remain inside learning detail pages rather than becoming app-level tabs.

#### Scenario: Student opens home tab
- **WHEN** the student opens `首页`
- **THEN** the app MUST provide experiment-video discovery through the home video feed
- **AND** it MUST route known experiments into point detail, video library, chapter, catalog, or AI contexts rather than creating a separate experiments root tab.

#### Scenario: Student opens assessment tab
- **WHEN** the student opens `测评`
- **THEN** the app MUST provide student assessment status, post-learning assessment entry when available, and report access where data exists
- **AND** assessment actions MUST remain reachable above the bottom navigation.

#### Scenario: Student opens profile tab
- **WHEN** the student opens `我的`
- **THEN** the app MUST provide student identity, feedback, account, and logout-oriented actions
- **AND** global support actions such as feedback MUST live here instead of as floating page controls.

### Requirement: Student equation principles display inline annotations
The student H5 point detail SHALL display inline annotation text attached to its reaction equation when a published point uses annotated equation-mode principles.

#### Scenario: Student opens a point with annotated reaction principles
- **WHEN** a student opens a published catalog point whose normalized reaction rows include annotation text
- **THEN** the point detail MUST show the rendered equation and its annotation together
- **AND** the annotation MUST be readable as explanatory text for that reaction rather than as another equation.

#### Scenario: Point has multiple annotated reactions
- **WHEN** a point contains multiple reaction rows and some rows have inline annotations
- **THEN** each annotation MUST appear only with its corresponding reaction row
- **AND** unannotated reaction rows MUST continue to render without annotation chrome.

#### Scenario: Student-facing payload is assembled
- **WHEN** the backend builds the student point detail payload for equation-mode principles
- **THEN** it MUST include annotation text for each annotated reaction row
- **AND** it MUST keep annotation formulae and condition tags separate from core reactants and products in any structured fields exposed to the frontend.

### Requirement: Student preview mode does not change normal student behavior
The student H5 code used for teacher preview SHALL preserve normal authenticated student behavior outside preview routes.

#### Scenario: Student opens normal H5 app
- **WHEN** an authenticated student opens the normal learning, catalog, or point routes
- **THEN** the app MUST continue to use student authentication, student endpoints, and student progress behavior
- **AND** teacher preview authorization MUST NOT be accepted as a normal student session.

#### Scenario: Teacher preview renders H5 component
- **WHEN** the teacher preview shell renders student point/detail content
- **THEN** preview-only disabled actions MUST NOT affect normal student routes
- **AND** the normal point route MUST still support learning completion, assessment handoff, AI chat, and related-point navigation according to existing student rules.

### Requirement: Related experiment links use real experiment titles
The student H5 point detail page SHALL render related experiment links from canonical target experiment titles rather than teacher-authored short display names.

#### Scenario: Student views related experiments
- **WHEN** a point detail payload includes related experiments
- **THEN** each related experiment link MUST display the resolved target experiment title
- **AND** it MUST NOT display a teacher-authored short name, display label, or stale related-link label override.

#### Scenario: Teacher preview views related experiments
- **WHEN** the teacher preview shell renders the student point detail page
- **THEN** related experiment links MUST match the same title behavior as normal student H5
- **AND** preview mode MUST NOT expose teacher-only related-link labels or raw related-link configuration fields.

### Requirement: Student point videos use active ready bindings
The student H5 learning experience SHALL render catalog point videos from the point's single active ready media binding rather than a separate binding publication state.

#### Scenario: Published point has active ready video
- **WHEN** a student opens a visible catalog point that has an active non-archived binding to a ready video asset
- **THEN** the H5 point detail page MUST render that video as the point video
- **AND** it MUST NOT require the binding row to carry a separate `published` status.

#### Scenario: Point has no active ready video
- **WHEN** a student opens a visible catalog point with no active ready video binding
- **THEN** the H5 point detail page MUST show the existing graceful no-video state
- **AND** it MUST not fail or expose teacher-only binding diagnostics.

#### Scenario: Point has archived or unready bindings
- **WHEN** a point has only archived bindings or bindings to unready video assets
- **THEN** the H5 point detail page MUST treat the point as having no playable video
- **AND** it MUST not expose archived or processing-only media URLs to students.

### Requirement: Teacher preview follows the same video visibility rule
Teacher preview SHALL render the same student-facing video behavior as normal H5 point detail while remaining read-only.

#### Scenario: Teacher previews a point with active ready video
- **WHEN** a teacher opens the learning-card preview for a point with an active ready video binding
- **THEN** the preview MUST render that video through preview-scoped media access
- **AND** it MUST match the normal student rule that binding publication state is not required.

#### Scenario: Teacher previews a point without active ready video
- **WHEN** a teacher previews a point with no active ready video
- **THEN** the preview MUST show the same no-video state as normal H5
- **AND** it MUST not expose binding status internals or teacher-only diagnostics.

### Requirement: Point detail uses edge-to-edge player header chrome
The student H5 point video detail page SHALL render the playable video as the page header, SHALL make that player span the full available mobile width, and SHALL avoid using the standard detail page title bar for point video pages.

#### Scenario: Student opens a point with a long title
- **WHEN** a student opens a visible catalog point whose title is longer than one normal mobile header line
- **THEN** the point detail page MUST keep the video player as the top page header
- **AND** the player MUST touch the top of the detail viewport without route padding above it
- **AND** the player MUST span the full width of the phone content area without side gutters, outer border, radius, shadow, or card background
- **AND** the page MUST render the catalog path and full point title below the player
- **AND** the title MUST be allowed to wrap without increasing or pushing down the player stage

#### Scenario: Playable player defaults to quiet video-first chrome
- **WHEN** a student opens a catalog point that has a playable video
- **THEN** the video frame or poster MUST be the dominant visible content in the player header
- **AND** the playable player MUST NOT render a persistent page-style back arrow while playback controls are inactive
- **AND** the playable player MUST NOT render a persistent full toolbar while playback controls are inactive
- **AND** the playable player MUST render only a subtle bottom mini progress indicator as persistent inactive chrome when progress data is available.

#### Scenario: Player controls reveal return action
- **WHEN** a student taps or otherwise activates the point video player controls
- **THEN** the return action MUST appear as part of the active player control chrome
- **AND** activating that return action MUST call the same source-aware route back behavior as the existing point detail back action
- **AND** the point detail page MUST NOT render a separate always-visible standard `PageBar` title above the player
- **AND** the return action MUST hide again when the playable player control chrome becomes inactive according to the player inactivity behavior.

#### Scenario: Active player controls use mobile video composition
- **WHEN** a playable point video's controls are active on a phone-width viewport
- **THEN** the player header MUST reveal the primary playback affordance inside the video footprint
- **AND** it MUST expose interactive progress inside the player footprint
- **AND** it MUST expose time feedback where duration/current-time data is available
- **AND** it MUST expose fullscreen or equivalent player affordances where the runtime supports them
- **AND** those controls MUST remain part of the player header rather than moving into the catalog title/content sections below.

#### Scenario: Page separates video header from learning content
- **WHEN** the point detail page is rendered
- **THEN** the page MUST NOT use the experiment grid-paper background behind the detail content
- **AND** the player and title area MUST NOT be presented as stacked floating cards
- **AND** the page MUST use flat sections and dividers below the video header for title, principle, explanation, safety, related links, AI handoff, and assessment handoff

#### Scenario: Point has no playable video
- **WHEN** a student opens a visible catalog point with no active ready video binding
- **THEN** the point detail page MUST keep the same edge-to-edge top video-header footprint
- **AND** it MUST show the existing graceful no-video state in that footprint
- **AND** the no-video state MUST keep a visible shared return affordance because there is no playback toolbar to reveal it
- **AND** the catalog path, title, learning content, related links, AI handoff, and assessment handoff MUST remain available

#### Scenario: Teacher previews point detail
- **WHEN** the teacher preview shell renders a student point detail page
- **THEN** the preview MUST use the same player-first layout and title-below-player composition
- **AND** playable-video return chrome MUST follow the same active/inactive player behavior as normal student H5
- **AND** preview media URLs MUST continue to resolve through preview-scoped media access

### Requirement: Point principle equations render as chemistry notation
The student H5 point detail page SHALL render equation-mode experiment principles as chemical equations from the same normalized reaction-equation semantics used by the teacher catalog preview.

#### Scenario: Student opens a point with normalized reaction equations
- **WHEN** a point detail payload contains `reaction_equations` with `canonical_mhchem`
- **THEN** the experiment principle section MUST render each equation through the shared reaction-equation rendering core
- **AND** it MUST keep each row's supplemental `annotation_text` as a readable explanation below its rendered equation
- **AND** it MUST NOT rely on a single plain-text paragraph that shows the backend raw equation string as the primary student-facing equation display

#### Scenario: Student opens a point with long normalized reaction equations
- **WHEN** a normalized reaction equation is wider than the phone content width at 360px, 390px, or 430px CSS-pixel widths
- **THEN** the student H5 equation presentation MUST use body-copy scale rather than large display-math scale
- **AND** it MUST allow the equation to wrap naturally across lines where the renderer permits
- **AND** it MUST keep horizontal scrolling as an overflow fallback only, not as the expected reading path
- **AND** it MUST NOT render KaTeX display blocks as the default student mobile equation treatment

#### Scenario: Teacher preview and student display share equation semantics
- **WHEN** the teacher catalog preview and the student H5 point detail render the same normalized reaction row
- **THEN** both surfaces MUST use the same priority order for renderable source and fallback text
- **AND** both surfaces MUST treat `canonical_mhchem` as the trusted renderable chemistry source
- **AND** both surfaces MUST preserve the same supplemental `annotation_text`
- **AND** any difference between the teacher and student output MUST be limited to the named presentation profile, not duplicated business parsing logic

#### Scenario: Student opens a legacy equation-only point
- **WHEN** a point detail payload has `principle_mode` set to `equation` but has no valid normalized `reaction_equations`
- **THEN** the experiment principle section MUST show each non-empty line of `principle_equation` through the shared fallback path
- **AND** it MUST NOT invent a chemistry parse for unconfirmed raw legacy text
- **AND** invalid or unrenderable chemistry syntax MUST fall back gracefully to the original text without breaking the page

### Requirement: Home is experiment-video discovery while learning remains catalog map
The student H5 learning experience SHALL separate home discovery from catalog learning: home is the experiment video discovery stream, while the learning tab remains the textbook/catalog map.

#### Scenario: Student opens home
- **WHEN** an authenticated student opens the home root
- **THEN** the page MUST prioritize experiment video discovery through the home video feed
- **AND** it MUST NOT use the old generic recommended-learning hero and multi-action grid as the primary home experience

#### Scenario: Student wants to locate a known experiment
- **WHEN** the student wants to browse by chapter, element, family, or catalog directory
- **THEN** the app MUST keep that behavior under the learning/catalog surfaces
- **AND** the home feed MUST route into those learning contexts through point detail or explicit search/navigation actions rather than replacing the catalog map

#### Scenario: Assessment recommends weak content later
- **WHEN** assessment logic identifies weak chapters or point nodes
- **THEN** recommendation MAY influence home feed ranking or reasons
- **AND** the catalog tree itself MUST remain a neutral classification model rather than being rewritten as a fixed guided-learning path

### Requirement: Point detail body uses watch-page learning hierarchy
The student H5 point video detail page SHALL organize required learning text below the fixed point video player as a flat mobile watch-page body.

#### Scenario: Student opens a point with complete learning content
- **WHEN** a student opens a visible experiment point that has a title, catalog path, phenomenon explanation, principle content, safety note, and related experiments
- **THEN** the scrollable body below the fixed player MUST show the catalog path and full point title first
- **AND** it MUST show the phenomenon explanation before the experiment principle
- **AND** it MUST show the safety note after the principle
- **AND** it MUST show related experiment links after the required explanatory sections.

#### Scenario: Student scans the body after watching the video
- **WHEN** the point detail body is rendered on a phone viewport
- **THEN** the content MUST use compact section headings, body-copy scale text, and flat dividers between major sections
- **AND** it MUST NOT present title, phenomenon, principle, safety, or related links as nested cards inside another card
- **AND** it MUST NOT use large decorative colored panels for long explanatory text.

#### Scenario: Required content is missing
- **WHEN** a point detail payload omits phenomenon explanation, principle content, safety note, or related experiments
- **THEN** the corresponding section MUST render a controlled empty state or be omitted according to existing student rules
- **AND** the remaining required sections MUST retain their relative learning order without collapsing into an undifferentiated paragraph.

### Requirement: Point principle text is structured as readable learning notes
The student H5 point video detail page SHALL treat principle content as structured learning notes rather than as a single heavy plain-text block.

#### Scenario: Equation-mode principle contains reaction rows
- **WHEN** a point detail payload has `principle_mode` set to `equation` and includes normalized `reaction_equations`
- **THEN** the principle section MUST render each valid reaction as its own readable row
- **AND** each row MUST visually associate the rendered equation with its annotation text when annotation text exists
- **AND** the section MUST preserve the shared chemistry renderer and fallback behavior defined by existing point-equation requirements.

#### Scenario: Reaction rows include annotations
- **WHEN** one or more rendered reaction rows include supplemental annotation text
- **THEN** each annotation MUST read as explanatory body text attached to its reaction
- **AND** repeated labels such as `补充说明：` MUST NOT be the dominant visual text for every row
- **AND** annotation text MUST wrap within the phone content width without overlapping the equation, neighboring rows, or fixed controls.

#### Scenario: Text-mode principle is available
- **WHEN** a point detail payload has text-mode principle content
- **THEN** the principle section MUST render the text as readable body copy with preserved intentional line breaks
- **AND** it MUST use the same watch-page section rhythm as phenomenon and safety sections.

### Requirement: Phenomenon and safety sections remain concise and scannable
The student H5 point video detail page SHALL make phenomenon and safety content easy to scan while preserving the authored text.

#### Scenario: Phenomenon explanation is shown
- **WHEN** a point detail payload includes a phenomenon explanation
- **THEN** the phenomenon section MUST appear immediately after the title area
- **AND** it MUST present the explanation as primary body copy that answers what the student observed in the video
- **AND** it MUST NOT be visually subordinated to equation annotations or action buttons.

#### Scenario: Safety note is shown
- **WHEN** a point detail payload includes a safety note
- **THEN** the safety section MUST include a clear caution heading or icon treatment
- **AND** it MUST keep the note compact and readable
- **AND** it MUST avoid a treatment that visually overpowers the phenomenon and principle sections unless future hazard severity metadata explicitly requires stronger warning levels.

### Requirement: Related experiments render as video-style recommendations
The student H5 point video detail page SHALL present related experiment links as a YouTube-like vertical list of related experiment video rows.

#### Scenario: Related experiments are available
- **WHEN** a point detail payload includes one or more related experiments
- **THEN** each related item MUST render as a single tappable row with a 16:10 visual area, the resolved related experiment title, and a secondary relation label or generic related-experiment label
- **AND** the visual area MUST use a stable placeholder when no student-visible thumbnail is available
- **AND** selecting the row MUST preserve the existing related-point navigation behavior.

#### Scenario: Related experiment title is long
- **WHEN** a related experiment title is longer than the available row copy width
- **THEN** the title MUST wrap or clamp cleanly without overlapping the visual area, relation label, neighboring rows, bottom controls, or viewport edge.

#### Scenario: Teacher preview renders related experiments
- **WHEN** the teacher preview shell renders the student point detail page
- **THEN** related experiment rows MUST use the same student-facing title and row presentation
- **AND** disabled preview actions MUST remain disabled without exposing teacher-only related-link labels or raw configuration.

### Requirement: Point detail actions stay separate from required learning content
The student H5 point video detail page SHALL keep AI, practice, completion, and assessment handoff controls visually separate from the required learning content hierarchy.

#### Scenario: Action controls are available
- **WHEN** AI, practice, completion, or assessment handoff controls are enabled for a point detail page
- **THEN** those controls MUST appear as action affordances outside the title, phenomenon, principle, safety, and related experiment content hierarchy
- **AND** they MUST NOT interrupt the required learning section order.

#### Scenario: Fixed or floating action controls are present
- **WHEN** a completion or practice action is fixed or floating near the bottom of the viewport
- **THEN** the scrollable content MUST include enough bottom spacing for related experiment rows and final content to remain reachable
- **AND** fixed or floating actions MUST NOT permanently cover required content.

### Requirement: Point detail text layout remains mobile-safe
The student H5 point video detail text layout SHALL remain usable on common phone preview widths.

#### Scenario: Phone viewport renders long text
- **WHEN** the point detail page is viewed at 360px, 390px, or 430px CSS-pixel widths
- **THEN** long titles, catalog paths, equations, annotations, phenomenon text, safety text, and related titles MUST remain within the phone content area
- **AND** the page MUST avoid horizontal body scrolling caused by the learning text layout.

#### Scenario: Fixed player and scroll body coexist
- **WHEN** the student scrolls the point detail body
- **THEN** the fixed player MUST remain at the top of the viewport
- **AND** the scroll body MUST start below the player footprint rather than sliding underneath it
- **AND** section headings and body text MUST not be hidden behind the player.

### Requirement: Point detail uses custom video shell
The student H5 point detail experience SHALL render playable point videos through an ArtPlayer-backed media engine with a student-owned custom mobile shell, while keeping point title, catalog path, learning text, equations, safety, related experiments, AI handoff, and assessment handoff below the video header.

#### Scenario: Playable point video uses ArtPlayer as engine
- **WHEN** a student opens a visible catalog point with a playable published video
- **THEN** the point detail page MUST create the video header through the ArtPlayer-backed point video player
- **AND** ArtPlayer MUST remain responsible for media source loading, poster, autoplay policy, inline playback, playback state, current time, duration, seek, and cleanup
- **AND** the visible student playback UI MUST come from the custom mobile shell rather than ArtPlayer's default chrome
- **AND** the page MUST NOT render browser native video controls.

#### Scenario: Point detail keeps learning content below player
- **WHEN** the playable point detail page renders
- **THEN** the video header MUST remain stable at the top of the detail viewport
- **AND** the catalog path and full point title MUST render below the player rather than inside a generic page bar above the player
- **AND** long titles MUST wrap below the player without changing the video header height
- **AND** learning content below the player MUST continue to show available principle equation or text, phenomenon explanation, safety/caution notes, related experiment links, and learning/assessment actions according to the existing point-detail contract.

#### Scenario: Autoplay recovery uses custom shell
- **WHEN** playable video autoplay is attempted and the browser or WebView rejects playback
- **THEN** the point detail page MUST keep the video header usable
- **AND** the custom shell MUST expose a visible play affordance when active
- **AND** the student MUST be able to start playback through the custom shell without needing ArtPlayer's default toolbar or browser native controls.

#### Scenario: Custom shell events stay synchronized
- **WHEN** the video emits playback lifecycle events such as loaded metadata, duration change, time update, play, pause, waiting, playing, seek, error, fullscreen, or destroy
- **THEN** the custom shell MUST update its visible state from the ArtPlayer/media source of truth
- **AND** time feedback MUST use the current media time and duration
- **AND** the shell MUST not keep stale playing, seeking, or duration state after the source changes or the player unmounts.

#### Scenario: No playable video keeps graceful empty header
- **WHEN** a student opens a visible catalog point with no active ready video binding
- **THEN** the point detail page MUST keep the same edge-to-edge video-header footprint
- **AND** it MUST show the graceful no-video placeholder instead of initializing a fake playable shell
- **AND** the no-video placeholder MUST keep an immediately visible shared route-return affordance
- **AND** the page MUST still show the point's learning content below the placeholder when available.

#### Scenario: Related point navigation preserves player model
- **WHEN** the student opens a related experiment point from a point detail page
- **THEN** the target point detail page MUST apply the same playable custom-shell or no-video placeholder rules according to that target point's video availability
- **AND** returning MUST preserve normal source-aware route-stack behavior.


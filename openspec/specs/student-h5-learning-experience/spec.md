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
- **AND** the view MUST NOT depend on a fixed parent experiment group level or on teacher-authored card-presentation override fields.

#### Scenario: No video exists for a point
- **WHEN** a published point node has no published video media
- **THEN** the H5 app MUST still show the point and its learning context
- **AND** it MUST render a graceful empty video state instead of failing navigation.

### Requirement: Student H5 mobile-first WebView contract
The student learning surface SHALL be treated as a phone-first H5 / mini-program WebView experience, not as a desktop admin page or a shrunken desktop layout.

#### Scenario: Student opens H5 on a phone viewport
- **WHEN** the student H5 app is viewed at common phone widths from 360px to 430px CSS pixels
- **THEN** primary learning screens MUST fit the viewport without horizontal scrolling
- **AND** headings, cards, segmented chapter switcher, bottom navigation, chat page, profile feedback, and action buttons MUST remain tappable and non-overlapping
- **AND** the layout MUST prioritize the phone flow: app-level tabs, current chapter context, A/B facts-or-experiments switching, experiment-point cards, point detail, chat, feedback, and assessment.

#### Scenario: Student uses touch-only interaction
- **WHEN** a student uses the app without hover, precise mouse input, or desktop keyboard shortcuts
- **THEN** all required learning, A/B switching, chat, feedback, login, password-change, pretest-skip, and logout actions MUST be reachable through touch controls
- **AND** interactive controls SHOULD use phone-appropriate hit areas and spacing.

#### Scenario: Desktop browser is used only for development preview
- **WHEN** a developer opens the student H5 app on a wide desktop browser
- **THEN** the app MAY center or constrain the phone layout for preview
- **BUT** it MUST NOT introduce desktop-only navigation, table-first layouts, hover-only affordances, or admin-console density into the student H5 experience.

### Requirement: Student experiment point detail
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
The student H5 element learning page SHALL let students select an element within the current family and view a model-led selected-element facts area for that element without changing the current family or chapter.

#### Scenario: Student selects an element chip
- **WHEN** the current profile contains multiple elements such as `F`, `Cl`, `Br`, `I`, and `At`
- **THEN** the page MUST render touch-friendly element chips for those elements
- **AND** selecting a chip MUST update the selected-element atom model card and compact facts area
- **AND** the selected property section and experiment-point groups MUST remain scoped to the same current family or chapter.

#### Scenario: Selected element model and facts are shown
- **WHEN** a student selects an element inside the current family
- **THEN** the page MUST show available element-specific facts including atomic number, electron configuration, family or group, common valence, elemental state, and oxidizing or reducing tendency where applicable
- **AND** the page MUST present those facts through a selected-element atom model card rather than a primary 2x3 static fact-card grid
- **AND** the card MUST preserve the selected element tile identity with atomic number, symbol, and English element name
- **AND** the card MUST show the atom visualization when electron configuration or fallback model data is available
- **AND** missing optional facts or unavailable model data MUST degrade to a clear empty or unavailable state rather than causing the page to fail.

#### Scenario: Selected element facts remain compact before tasks
- **WHEN** selected-element physical facts, teaching notes, family common properties, and property summaries would make the facts view long on a phone viewport
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

### Requirement: Experiment-point primary task area
The student H5 element learning page SHALL keep catalog point navigation as the primary learning task after compact chemistry context.

#### Scenario: Student reaches catalog points
- **WHEN** a selected family or chapter has published catalog nodes
- **THEN** the page MUST show top-level directory and point entries for that chapter
- **AND** selecting a directory MUST open the next catalog level
- **AND** selecting a point MUST open the point detail learning page.

#### Scenario: Directory card appears in task area
- **WHEN** a directory node is shown in the catalog task area
- **THEN** it MUST render as a navigation category card using derived directory card presentation
- **AND** it MUST NOT appear as a playable video point
- **AND** it MUST NOT require manual directory description, card image, icon, accent, or layout fields.

#### Scenario: Context area would push catalog too low
- **WHEN** selected-element facts and family common properties contain more content than fits comfortably before the catalog entry area on a phone viewport
- **THEN** the page MUST prioritize compact summaries, expandable detail, or equivalent progressive disclosure
- **AND** it MUST keep the catalog task area discoverable without requiring excessive scrolling.

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
The student H5 chapter learning page SHALL support the prototype's selected-chapter flow and MUST NOT require a fixed facts-vs-experiments two-tab contract when the authored catalog is the primary navigation.

#### Scenario: Student opens a selected chapter
- **WHEN** a student opens a selected family or chapter page from the periodic-table entry
- **THEN** the page MUST show the selected chapter context and a clear entry into its catalog tree
- **AND** the catalog tree MUST be available without assuming a fixed experiment group tab.

#### Scenario: Student navigates catalog depth
- **WHEN** a student opens a catalog directory from the chapter page
- **THEN** the app MUST render a catalog page for that node with breadcrumbs or equivalent source context
- **AND** returning MUST restore the previous chapter or directory page.

#### Scenario: Facts content remains available
- **WHEN** the profile has facts, common properties, or element context
- **THEN** the page MAY show them as compact chapter context
- **AND** these facts MUST NOT replace the catalog as the path to point video/detail learning.

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
The student H5 periodic-table entry SHALL distinguish area selection, recommended guidance, selected-area route navigation, and chapter navigation entry semantics.

#### Scenario: Recommended chapter is shown as guidance
- **WHEN** the periodic-table entry has a recommended profile
- **THEN** the matching area or element cue MUST show recommendation guidance
- **AND** it MUST NOT render as a selected, active, current chapter, or inline chapter list before the student opens a detail route.

#### Scenario: Student opens a selected area
- **WHEN** the student taps an area control or an element cell from the periodic-table learning root
- **THEN** the H5 app MUST navigate to a selected-area second-level route for that area
- **AND** the learning root MUST NOT render the selected area's chapter list inline
- **AND** the selected area MUST be visually distinguishable on the root as navigation feedback or recommendation guidance without turning the root into a list page.

#### Scenario: Student views selected-area chapter list
- **WHEN** the selected-area route is open
- **THEN** the page MUST show the selected area identity and chapter list filtered to that area
- **AND** the recommended area or chapter cue MUST remain recommendation guidance rather than forcing a different route after the student's tap
- **AND** the bottom navigation MUST remain hidden because the selected-area route is a detail route.

#### Scenario: Student opens a chapter entry
- **WHEN** the student taps a chapter entry card from the selected-area route
- **THEN** the H5 app MUST navigate into that family or chapter learning page
- **AND** the entry card itself MUST be treated as a navigation row rather than a persistent selected item on the entry page.

#### Scenario: Current area shows learnable elements
- **WHEN** the periodic-table entry or selected-area page has learning profiles for the relevant area
- **THEN** element cells in that area whose symbols appear in those profiles MUST show the element symbol where the table is rendered
- **AND** element cells outside the relevant area MUST NOT show profile-driven element symbols
- **AND** selected-area element cells without a matching profile symbol MAY remain unlabeled color cells.

#### Scenario: Hydrogen and noble gases are a student learning area
- **WHEN** the student uses the periodic-table entry
- **THEN** hydrogen and group 18 noble gas cells MUST map to a dedicated `氢和稀有气体` learning area route
- **AND** the selected-area page MUST filter the chapter list to matching learning profiles such as the hydrogen and noble gases chapter
- **AND** the student entry MUST NOT expose a `通识资源` area
- **AND** f-block layout coordinates MUST NOT cause lanthanide or actinide cells such as Lu or Lr to map to the `氢和稀有气体` learning area.

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

### Requirement: Prototype-aligned multi-level catalog flow
The student H5 app SHALL implement the prototype flow from periodic-table entry to selected area to chapter to catalog directories to point video/detail.

#### Scenario: Student enters from periodic table
- **WHEN** a student taps an area control or element cell from the periodic-table learning entry
- **THEN** the app MUST navigate to that area's standalone selected-area page
- **AND** the selected-area page MUST make the area identity clear before showing chapter entries.

#### Scenario: Student enters chapter from selected area
- **WHEN** a student taps a chapter/family entry from the selected-area page
- **THEN** the app MUST navigate to that chapter's standalone page
- **AND** the page MUST make the chapter identity clear before showing catalog entries.

#### Scenario: Student opens nested directory
- **WHEN** a student taps a directory catalog node
- **THEN** the app MUST open a second-level route for that directory
- **AND** the page MUST show child directory and point entries according to the authored order.

#### Scenario: Student opens concrete point video
- **WHEN** a student taps a point catalog node
- **THEN** the app MUST open the point video/detail page
- **AND** the page MUST show manually authored principle, phenomenon explanation, safety note, related links, and the fixed test handoff
- **AND** teacher-only remarks MUST remain hidden from this page.

#### Scenario: Directory search context leads to points
- **WHEN** a student search result is matched through directory/category text
- **THEN** the result list MUST show concrete descendant point entries
- **AND** selecting a result MUST open point detail rather than a directory-only search result page.

### Requirement: RSC-backed selected-element physical facts
The student H5 learning experience SHALL support curated physical fact fields for selected elements using RSC Periodic Table fact boxes as the primary reference.

#### Scenario: Student sees RSC-style physical facts
- **WHEN** the selected element has curated physical facts
- **THEN** the facts view MUST be able to show relative atomic mass, group, period, block, 20°C state, density, and electron configuration in a compact mobile layout
- **AND** those fields MUST be maintained in profile or profile-adjacent seed data rather than fetched from RSC at runtime

#### Scenario: Student sees teaching facts separately
- **WHEN** the selected element also has common valence, redox tendency, or profile-specific teaching note
- **THEN** the facts view MUST keep those teaching facts visible as learning cues
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
- **THEN** those details MUST remain available in the facts view, element detail route, or equivalent detail area
- **AND** the compact selected-element card MUST only surface the short focus property, experiment relevance, and compact tags

#### Scenario: Element switching updates compact card
- **WHEN** the student taps another element chip in the same family or chapter
- **THEN** the compact card MUST update its tile, focus property, experiment relevance, and tags for the newly selected element
- **AND** the current family or chapter context, facts/experiments switcher state, and experiment-point groups MUST remain scoped to the same learning profile

### Requirement: Explicit element focus card seed copy
The platform SHALL store selected-element card copy as explicit maintained student learning seed data instead of deriving the compact card's teaching copy from RAG chunks, family trend summaries, or front-end string composition.

#### Scenario: Learning profile seed includes card copy
- **WHEN** production resource validation or test validation runs for enabled student learning profiles
- **THEN** each enabled element MUST include card-level focus copy, experiment relevance copy, and compact card tags before the profile is treated as complete for the redesigned card experience
- **AND** missing card-level copy MUST be reported as validation feedback before the profile is considered complete for the redesigned card experience

#### Scenario: Backend exposes card copy
- **WHEN** the student learning API builds the H5 learning payload for a selected family or chapter
- **THEN** each element badge MUST expose the card-level focus property, experiment relevance, and card tags when seed data provides them
- **AND** existing detailed element facts MUST remain available for the facts view and element detail experience

#### Scenario: Card copy is temporarily missing
- **WHEN** an element is missing redesigned card copy during migration
- **THEN** the H5 app MUST render a graceful compact fallback using stable factual tags where available
- **AND** the fallback MUST NOT recreate the old generated `<element>在<family>中的位置` pattern or use a family trend sentence as the element card body

### Requirement: Bottom-tab student app information architecture
The student H5 learning experience SHALL organize authenticated student workflows around bottom app tabs rather than a single learning page with floating global entries.

#### Scenario: Student views bottom-tab destinations
- **WHEN** a student is in the authenticated app shell with all features enabled
- **THEN** the app MUST provide destinations for `学习`, `实验`, `问答`, `测评`, and `我的`
- **AND** each destination MUST represent app-level navigation, not a chapter-local view switch.

#### Scenario: Student opens learning tab
- **WHEN** the student opens `学习`
- **THEN** the app MUST provide the periodic-table chapter entry, current or recommended chapter access, selected chapter facts, selected chapter experiment videos, and point detail navigation
- **AND** chapter-local controls such as `性质通识` and `实验视频` MUST remain inside the learning tab.

#### Scenario: Student opens experiments tab
- **WHEN** the student opens `实验`
- **THEN** the app MUST provide an experiment-resource or point-resource overview using existing student-visible experiment data
- **AND** it MUST avoid showing generic placeholder marketing content.

#### Scenario: Student opens assessment tab
- **WHEN** the student opens `测评`
- **THEN** the app MUST provide student assessment status, post-learning assessment entry when available, and report access where data exists
- **AND** assessment actions MUST remain reachable above the bottom navigation.

#### Scenario: Student opens profile tab
- **WHEN** the student opens `我的`
- **THEN** the app MUST provide student identity, feedback, account, and logout-oriented actions
- **AND** global support actions such as feedback MUST live here instead of as floating page controls.

### Requirement: Student equation principles display inline annotations
The student H5 experiment point detail SHALL display inline annotation text attached to its reaction equation when a published point uses annotated equation-mode principles.

#### Scenario: Student opens a point with annotated reaction principles
- **WHEN** a student opens a published experiment point whose normalized reaction rows include annotation text
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

### Requirement: Student catalog cards ignore removed card overrides
The student H5 catalog SHALL render directory and point cards without relying on removed manual card-presentation fields.

#### Scenario: Removed fields are absent from API payload
- **WHEN** a student catalog response omits `student_description`, `card_image_asset_id`, `card_icon_key`, `card_accent`, `card_layout`, `card_presentation`, and `point_card_presentation`
- **THEN** the student H5 catalog MUST still render directory and point cards successfully
- **AND** no runtime error or blank card MUST occur because those fields are absent.

#### Scenario: Point learning summary is available
- **WHEN** a point has learning content such as principle, phenomenon explanation, or safety note
- **THEN** the point card MAY show a concise derived summary from that content
- **AND** the summary MUST be treated as a display projection rather than an editable card override.

#### Scenario: Point learning summary is missing
- **WHEN** a point has no available learning summary yet
- **THEN** the point card MUST still show the point title and stable point/video affordance
- **AND** it MUST not require teacher-authored short card description.

#### Scenario: Bound video thumbnail is available
- **WHEN** a point has a bound video thumbnail available to students
- **THEN** the point card MAY use that thumbnail as the visual cue
- **AND** it MUST fall back to a stable default if no thumbnail is available.

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


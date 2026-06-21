## MODIFIED Requirements

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

## ADDED Requirements

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

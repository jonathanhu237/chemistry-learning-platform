## MODIFIED Requirements

### Requirement: Real student learning page payload
The backend SHALL expose a student learning payload centered on a selected family or chapter profile and its chapter-scoped catalog tree.

#### Scenario: Student opens learning page
- **WHEN** an authenticated student opens the H5 learning page
- **THEN** the backend MUST return a recommended, default, or explicitly selected learning profile
- **AND** the payload MUST include the profile's visible family/element facts and common-property content where available
- **AND** it MUST include the top-level published catalog directory and point nodes for the current chapter.

#### Scenario: Student opens the catalog learning view
- **WHEN** a student enters the experiment learning area for a chapter
- **THEN** the H5 app MUST show catalog nodes according to the authored directory tree
- **AND** directory node cards MUST include student-visible title, description, and card presentation metadata
- **AND** point node cards MUST include point/video learning entry metadata such as title, summary, media availability, and question count where available
- **AND** the view MUST NOT depend on a fixed parent experiment group level.

#### Scenario: No video exists for a point
- **WHEN** a published point node has no published video media
- **THEN** the H5 app MUST still show the point and its learning context
- **AND** it MUST render a graceful empty video state instead of failing navigation.

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

### Requirement: Experiment-point primary task area
The student H5 element learning page SHALL keep catalog point navigation as the primary learning task after compact chemistry context.

#### Scenario: Student reaches catalog points
- **WHEN** a selected family or chapter has published catalog nodes
- **THEN** the page MUST show top-level directory and point entries for that chapter
- **AND** selecting a directory MUST open the next catalog level
- **AND** selecting a point MUST open the point detail learning page.

#### Scenario: Directory card appears in task area
- **WHEN** a directory node is shown in the catalog task area
- **THEN** it MUST render as a navigation category card using directory card presentation
- **AND** it MUST NOT appear as a playable video point.

#### Scenario: Context area would push catalog too low
- **WHEN** selected-element facts and family common properties contain more content than fits comfortably before the catalog entry area on a phone viewport
- **THEN** the page MUST prioritize compact summaries, expandable detail, or equivalent progressive disclosure
- **AND** it MUST keep the catalog task area discoverable without requiring excessive scrolling.

### Requirement: Prototype-aligned multi-level catalog flow
The student H5 app SHALL implement the new prototype flow from periodic-table entry to chapter to catalog directories to point video/detail.

#### Scenario: Student enters from periodic table
- **WHEN** a student taps a chapter/family entry from the periodic-table learning entry
- **THEN** the app MUST navigate to that chapter's standalone page
- **AND** the page MUST make the chapter identity clear before showing catalog entries.

#### Scenario: Student opens nested directory
- **WHEN** a student taps a directory catalog node
- **THEN** the app MUST open a second-level route for that directory
- **AND** the page MUST show child directory and point entries according to the authored order.

#### Scenario: Student opens concrete point video
- **WHEN** a student taps a point catalog node
- **THEN** the app MUST open the point video/detail page
- **AND** the page MUST show manually authored principle, phenomenon explanation, safety note, related links, and the fixed test handoff.
- **AND** teacher-only remarks MUST remain hidden from this page.

#### Scenario: Directory search context leads to points
- **WHEN** a student search result is matched through directory/category text
- **THEN** the result list MUST show concrete descendant point entries
- **AND** selecting a result MUST open point detail rather than a directory-only search result page.

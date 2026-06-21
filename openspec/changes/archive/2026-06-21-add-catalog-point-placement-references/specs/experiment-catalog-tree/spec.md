## MODIFIED Requirements

### Requirement: Stable point node identity
The system SHALL distinguish stable catalog placement identity from stable canonical experiment point identity.

#### Scenario: Placement is moved
- **WHEN** a teacher moves a point placement to a different parent directory
- **THEN** the placement node id MUST remain unchanged
- **AND** the canonical experiment point id targeted by the placement MUST remain unchanged.

#### Scenario: Canonical experiment content is edited
- **WHEN** a teacher edits shared experiment content, videos, evidence state, question bindings, assessment metadata, analytics identity, or feedback identity from any placement
- **THEN** those resources MUST resolve to the canonical experiment point id
- **AND** every placement targeting that canonical experiment point MUST continue to show the updated shared learning identity.

#### Scenario: Placement is renamed or display-overridden
- **WHEN** a teacher changes a placement-local display field that is explicitly supported by the API
- **THEN** the placement's searchable path or card text MUST update for that placement
- **AND** the canonical experiment point id used by stored shared bindings and historical records MUST NOT change.

#### Scenario: Legacy point key exists
- **WHEN** migrated data has a legacy `(experiment_id, point_key)` identity or old catalog point node identity
- **THEN** the system MUST map it to a canonical experiment point id and a source placement id where available
- **AND** new shared-content write paths MUST use the canonical experiment point id instead of the legacy pair or placement id alone.

### Requirement: Catalog node kinds
The system SHALL support exactly directory and point node kinds, with point nodes acting as catalog placements for canonical experiment points.

#### Scenario: Directory node is opened
- **WHEN** a directory node is opened
- **THEN** the system MUST return its child nodes, breadcrumbs, directory description, card presentation metadata, and navigation metadata
- **AND** it MUST NOT require or expose point learning content, video bindings, related point links, assessment identity, or ES result identity for the directory itself.

#### Scenario: Point placement node is opened
- **WHEN** a point placement node is opened
- **THEN** the system MUST return placement context and resolve shared point detail content, video bindings, related links, and assessment context from the targeted canonical experiment point
- **AND** it MUST NOT return child catalog nodes for the point placement.

#### Scenario: Point placement node is used as parent
- **WHEN** a client attempts to create or move another catalog node under a point placement node
- **THEN** the system MUST reject the operation
- **AND** the placement id, canonical point id, and existing bindings MUST remain unchanged.

#### Scenario: Hybrid or shortcut node kind is submitted
- **WHEN** a client attempts to create or update a catalog node with kind `hybrid`, `shortcut`, `reference`, or another unsupported kind
- **THEN** the system MUST reject the request
- **AND** reuse MUST be represented by point placements targeting canonical experiment points, not by live shortcut node behavior.

### Requirement: Point learning content belongs to point-capable nodes
The system SHALL attach manually authored point learning content to canonical experiment points and expose that content through point placements.

#### Scenario: Teacher saves the point authoring model
- **WHEN** a teacher edits a point placement
- **THEN** the system MUST resolve the targeted canonical experiment point and support manually maintained point title, teacher-only note, point knowledge, related point links, and video bindings on that canonical point
- **AND** point knowledge MUST include principle mode with either equation or text, phenomenon explanation, and safety note.

#### Scenario: Teacher saves equation principle content
- **WHEN** a teacher saves canonical point content with principle mode `equation`
- **THEN** the system MUST require at least one valid chemical equation value
- **AND** it MUST store phenomenon explanation and safety note as teacher-authored canonical point text.

#### Scenario: Teacher saves text principle content
- **WHEN** a teacher saves canonical point content with principle mode `text`
- **THEN** the system MUST require a principle text value
- **AND** it MUST NOT require a chemical equation.

#### Scenario: Point has no video
- **WHEN** a canonical experiment point has learning content but no published video
- **THEN** the system MUST still allow published placements targeting that canonical point to appear in the catalog and search
- **AND** the student detail page MUST render a graceful no-video state.

#### Scenario: Teacher-only note is stored
- **WHEN** a teacher saves a teacher-only note for a canonical experiment point
- **THEN** the system MUST persist the note for admin authoring context
- **AND** student APIs, student search documents, student snippets, and student page payloads MUST NOT expose or index the note.

#### Scenario: Directory receives point content
- **WHEN** a client attempts to save point learning content, video bindings, related point links, or point publication state on a directory node
- **THEN** the system MUST reject the operation
- **AND** the directory MUST remain a navigation/category node.

### Requirement: Related point links use node identities
The system SHALL represent related experiment links between canonical experiment points while resolving placement routes for display.

#### Scenario: Default related links are generated
- **WHEN** a point has sibling, adjacent, or otherwise relevant published point placements in the catalog neighborhood
- **THEN** the system MUST generate default related links using canonical target point ids
- **AND** it MUST resolve a suitable published target placement for the current student chapter/path when rendering the link.

#### Scenario: Teacher edits related links
- **WHEN** a teacher manually edits related point links from any placement
- **THEN** the system MUST persist the chosen canonical target point ids, labels, order, and hidden overrides on the source canonical point
- **AND** it MUST allow links to canonical points that are displayed outside the current directory when selected intentionally.

#### Scenario: Target canonical point has no available placement
- **WHEN** a related canonical target point has no published placement available to the student
- **THEN** the system MUST hide or disable the related link in student responses
- **AND** it MUST NOT expose an unavailable canonical point through a stale placement route.

### Requirement: Published point-node search documents
The system SHALL build student video-library search documents from published point placements and their shared canonical experiment resources.

#### Scenario: Published point placement is indexed
- **WHEN** a point placement is published or its searchable placement context changes
- **THEN** the system MUST queue an ES document upsert keyed by placement node id
- **AND** the document MUST include canonical experiment point id, chapter path, ancestor directory category/path text, canonical point title, principle, phenomenon explanation, safety note, student-facing related link text, extracted formulae, aliases, reaction features, and published video metadata where available.
- **AND** the document MUST NOT include teacher-only notes, raw AI source chunks, `experiment_video_point_evidence` payloads, or standalone directory-only documents.

#### Scenario: Canonical point content changes
- **WHEN** canonical point title, principle, phenomenon explanation, safety note, videos, or related links change
- **THEN** the system MUST queue search upserts for every active published placement targeting that canonical experiment point
- **AND** archived or unpublished placements MUST NOT be indexed as active student search results.

#### Scenario: Point placement is unpublished or archived
- **WHEN** a point placement becomes unpublished, archived, or unavailable through its ancestor path
- **THEN** the system MUST queue deletion or disabling of that placement's student search document
- **AND** it MUST NOT delete search documents for other active placements targeting the same canonical experiment point.

#### Scenario: Directory text matches a search query
- **WHEN** a student searches for text that appears only in a published ancestor directory title or description
- **THEN** the search backend MUST return matching descendant published point placement documents
- **AND** it MUST NOT return the directory as an independent video-library result.

#### Scenario: Raw media asset exists
- **WHEN** a teacher uploads a media asset that is not bound to a canonical experiment point through a published point placement context
- **THEN** the media asset MUST NOT appear in student video-library search.

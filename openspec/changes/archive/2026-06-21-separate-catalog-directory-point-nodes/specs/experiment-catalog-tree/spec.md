## MODIFIED Requirements

### Requirement: Chapter-scoped recursive catalog tree
The system SHALL model experiment learning structure as a chapter-scoped recursive catalog tree rather than a fixed chapter -> experiment -> point hierarchy.

#### Scenario: Chapter catalog is requested
- **WHEN** a chapter catalog is requested by an authorized user
- **THEN** the system MUST return root catalog nodes for that chapter ordered by display order
- **AND** each node MUST expose enough metadata to render either directory navigation/card behavior or point learning behavior.

#### Scenario: Catalog depth differs by chapter
- **WHEN** two chapters have different directory depths
- **THEN** the system MUST support both without requiring placeholder experiment levels
- **AND** the student and teacher APIs MUST NOT assume a fixed third, fourth, or fifth level.

#### Scenario: Directory has no point children
- **WHEN** a directory node currently has no published child point nodes
- **THEN** the system MUST keep the directory editable for teachers
- **AND** the student API MUST either hide it or render an intentional empty state according to publication settings.

### Requirement: Stable point node identity
The system SHALL use stable catalog point node identity as the authoritative identity for point learning content.

#### Scenario: Point is moved
- **WHEN** a teacher moves a point node to a different parent directory
- **THEN** the point node id MUST remain unchanged
- **AND** video bindings, point content, question bindings, assessment metadata, analytics, feedback context, and search index state MUST continue to resolve to the same point.

#### Scenario: Point is renamed
- **WHEN** a teacher renames a point node
- **THEN** the title and searchable text MUST update
- **AND** the identity used by stored bindings and historical records MUST NOT change.

#### Scenario: Legacy point key exists
- **WHEN** migrated data has a legacy `(experiment_id, point_key)` identity
- **THEN** the system MUST map it to a stable point node id
- **AND** new write paths MUST use the stable point node id instead of the legacy pair.

### Requirement: Catalog node kinds
The system SHALL support exactly directory and point node kinds with explicit behavior.

#### Scenario: Directory node is opened
- **WHEN** a directory node is opened
- **THEN** the system MUST return its child nodes, breadcrumbs, directory description, card presentation metadata, and navigation metadata
- **AND** it MUST NOT require or expose point learning content, video bindings, related point links, assessment context, or ES result identity for the directory itself.

#### Scenario: Point node is opened
- **WHEN** a point node is opened
- **THEN** the system MUST return point detail content, video bindings, related links, assessment context, and source path context where available
- **AND** it MUST NOT return child catalog nodes for the point.

#### Scenario: Point node is used as parent
- **WHEN** a client attempts to create or move another catalog node under a point node
- **THEN** the system MUST reject the operation
- **AND** the point node id and existing bindings MUST remain unchanged.

#### Scenario: Hybrid or shortcut node kind is submitted
- **WHEN** a client attempts to create or update a catalog node with kind `hybrid` or `shortcut`
- **THEN** the system MUST reject the request
- **AND** no live compatibility path MUST preserve hybrid or shortcut behavior.

### Requirement: Point learning content belongs to point-capable nodes
The system SHALL attach manually authored point learning content only to point nodes.

#### Scenario: Teacher saves the point authoring model
- **WHEN** a teacher edits a point node
- **THEN** the system MUST support manually maintained point title, teacher-only note, point knowledge, related point links, and video bindings
- **AND** point knowledge MUST include principle mode with either equation or text, phenomenon explanation, and safety note.

#### Scenario: Teacher saves equation principle content
- **WHEN** a teacher saves point content with principle mode `equation`
- **THEN** the system MUST require a chemical equation value
- **AND** it MUST store phenomenon explanation and safety note as teacher-authored text.

#### Scenario: Teacher saves text principle content
- **WHEN** a teacher saves point content with principle mode `text`
- **THEN** the system MUST require a principle text value
- **AND** it MUST NOT require a chemical equation.

#### Scenario: Point has no video
- **WHEN** a point node has learning content but no published video
- **THEN** the system MUST still allow the point to appear in the catalog and search when published
- **AND** the student detail page MUST render a graceful no-video state.

#### Scenario: Teacher-only note is stored
- **WHEN** a teacher saves a teacher-only note for a point node
- **THEN** the system MUST persist the note for admin authoring context
- **AND** student APIs, student search documents, student snippets, and student page payloads MUST NOT expose or index the note.

#### Scenario: Directory receives point content
- **WHEN** a client attempts to save point learning content, video bindings, related point links, or point publication state on a directory node
- **THEN** the system MUST reject the operation
- **AND** the directory MUST remain a navigation/category node.

### Requirement: Published point-node search documents
The system SHALL build student video-library search documents from published point nodes and their bound learning resources.

#### Scenario: Published point is indexed
- **WHEN** a point node is published or its searchable content changes
- **THEN** the system MUST queue an ES document upsert keyed by point node id
- **AND** the document MUST include chapter path, ancestor directory category/path text, point title, principle, phenomenon explanation, safety note, student-facing related link text, extracted formulae, aliases, reaction features, and published video metadata where available.
- **AND** the document MUST NOT include teacher-only notes, raw AI source chunks, `experiment_video_point_evidence` payloads, or standalone directory-only documents.

#### Scenario: Point is unpublished or archived
- **WHEN** a point node becomes unpublished or archived
- **THEN** the system MUST queue deletion or disabling of its student search document.

#### Scenario: Directory text matches a search query
- **WHEN** a student searches for text that appears only in a published ancestor directory title or description
- **THEN** the search backend MUST return matching descendant published point documents
- **AND** it MUST NOT return the directory as an independent video-library result.

#### Scenario: Raw media asset exists
- **WHEN** a teacher uploads a media asset that is not bound to a published point node
- **THEN** the media asset MUST NOT appear in student video-library search.

## ADDED Requirements

### Requirement: Directory card presentation
The system SHALL let directory nodes maintain structured student-facing card presentation metadata.

#### Scenario: Teacher edits directory card fields
- **WHEN** a teacher edits a directory node
- **THEN** the system MUST allow title, teacher-only note, student-visible description, optional card image reference, optional icon key, optional accent/theme token, and optional layout variant to be saved
- **AND** it MUST store the teacher-only note separately from student-visible directory fields.

#### Scenario: Student catalog renders directory card
- **WHEN** a published directory node is returned to the student catalog
- **THEN** the payload MUST include student-visible card presentation fields needed to render a navigation card
- **AND** it MUST NOT include teacher-only notes.

### Requirement: Point card presentation stays constrained
The system SHALL allow limited point card presentation overrides without weakening point identity or list consistency.

#### Scenario: Teacher edits point card overrides
- **WHEN** a teacher edits a point node card presentation
- **THEN** the system MAY allow an explicit cover image reference, short student-facing display description, icon key, accent/theme token, or emphasis flag
- **AND** it MUST keep point title, point node id, and point learning content as the authoritative point identity and detail source.

#### Scenario: Student catalog renders point card
- **WHEN** a published point node is returned inside a chapter or directory catalog
- **THEN** the payload MUST render as a point/video learning entry rather than as a directory category
- **AND** the card MUST remain visually distinguishable from directory cards.

### Requirement: Hybrid and shortcut live semantics are removed
The system SHALL remove live hybrid and shortcut semantics from catalog tree behavior.

#### Scenario: Existing hybrid data is migrated
- **WHEN** a migration encounters an existing hybrid node
- **THEN** it MUST normalize the record to directory and/or point semantics using deterministic rules
- **AND** it MUST preserve migration metadata for audit or data repair.

#### Scenario: Existing shortcut data is migrated
- **WHEN** a migration encounters an existing shortcut node
- **THEN** it MUST remove shortcut behavior from live student and teacher APIs
- **AND** it MUST either materialize an allowed directory/point placement or archive the shortcut with audit metadata.

#### Scenario: Shortcut route is requested
- **WHEN** a client attempts to use shortcut target behavior after this change
- **THEN** the system MUST return a controlled rejection or unavailable response
- **AND** it MUST NOT resolve point detail through a shortcut node.

# experiment-catalog-tree Specification

## Purpose
TBD - created by archiving change experiment-catalog-tree-point-architecture. Update Purpose after archive.
## Requirements
### Requirement: Chapter-scoped recursive catalog tree
The system SHALL model experiment learning structure as a chapter-scoped recursive catalog tree rather than a fixed chapter -> experiment -> point hierarchy.

#### Scenario: Chapter catalog is requested
- **WHEN** a chapter catalog is requested by an authorized user
- **THEN** the system MUST return root catalog nodes for that chapter ordered by display order
- **AND** each node MUST expose enough metadata to render directory, point, hybrid, or shortcut behavior.

#### Scenario: Catalog depth differs by chapter
- **WHEN** two chapters have different directory depths
- **THEN** the system MUST support both without requiring placeholder experiment levels
- **AND** the student and teacher APIs MUST NOT assume a fixed third, fourth, or fifth level.

#### Scenario: Directory has no point children
- **WHEN** a directory node currently has no published child point nodes
- **THEN** the system MUST keep the directory editable for teachers
- **AND** the student API MUST either hide it or render an intentional empty state according to publication settings.

### Requirement: Stable point node identity
The system SHALL use stable catalog node identity as the authoritative identity for point-capable learning content.

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
The system SHALL support directory, point, hybrid, and shortcut node kinds with explicit behavior.

#### Scenario: Directory node is opened
- **WHEN** a directory node is opened
- **THEN** the system MUST return its child nodes and navigation metadata
- **AND** it MUST NOT require point learning content.

#### Scenario: Point node is opened
- **WHEN** a point node is opened
- **THEN** the system MUST return point detail content, video bindings, related links, assessment context, and source path context where available.

#### Scenario: Hybrid node is opened
- **WHEN** a hybrid node is opened
- **THEN** the system MUST expose both child-node navigation and point detail capability
- **AND** clients MUST receive explicit actions so they do not infer behavior from child count alone.

#### Scenario: Shortcut node is opened
- **WHEN** a shortcut node references a canonical point node
- **THEN** the system MUST resolve detail content from the target point node
- **AND** it MUST preserve the opening shortcut path as navigation context.

### Requirement: Point learning content belongs to point-capable nodes
The system SHALL attach manually authored point learning content to point-capable catalog nodes.

#### Scenario: Teacher saves the point authoring model
- **WHEN** a teacher edits a point-capable node
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
- **WHEN** a point-capable node has learning content but no published video
- **THEN** the system MUST still allow the point to appear in the catalog and search when published
- **AND** the student detail page MUST render a graceful no-video state.

#### Scenario: Teacher-only note is stored
- **WHEN** a teacher saves a teacher-only note for a point-capable node
- **THEN** the system MUST persist the note for admin authoring context
- **AND** student APIs, student search documents, student snippets, and student page payloads MUST NOT expose or index the note.

### Requirement: Related point links use node identities
The system SHALL represent related experiment links between stable point nodes.

#### Scenario: Default related links are generated
- **WHEN** a point has sibling or adjacent point nodes in the same catalog neighborhood
- **THEN** the system MAY generate default related links from nearby published points
- **AND** generated defaults MUST reference target point node ids.

#### Scenario: Teacher edits related links
- **WHEN** a teacher manually edits related point links
- **THEN** the system MUST persist the chosen target point node ids, labels, order, and hidden overrides
- **AND** it MUST allow links to points outside the current directory when selected intentionally.

### Requirement: Published point-node search documents
The system SHALL build student video-library search documents from published point nodes and their bound learning resources.

#### Scenario: Published point is indexed
- **WHEN** a point-capable node is published or its searchable content changes
- **THEN** the system MUST queue an ES document upsert keyed by point node id
- **AND** the document MUST include chapter path, node path, point title, principle, phenomenon explanation, safety note, student-facing related link text, extracted formulae, aliases, reaction features, and published video metadata where available.
- **AND** the document MUST NOT include teacher-only notes, raw AI source chunks, or `experiment_video_point_evidence` payloads.

#### Scenario: Point is unpublished or archived
- **WHEN** a point-capable node becomes unpublished or archived
- **THEN** the system MUST queue deletion or disabling of its student search document.

#### Scenario: Raw media asset exists
- **WHEN** a teacher uploads a media asset that is not bound to a published point node
- **THEN** the media asset MUST NOT appear in student video-library search.

### Requirement: Chemistry ES analyzer dictionaries
The system SHALL provide a production-ready ES/IK analyzer stack for student video-library search.

#### Scenario: ES index is created
- **WHEN** the student video-library ES index is created or recreated
- **THEN** the index MUST use an IK-based chemistry analyzer for Chinese text fields
- **AND** the analyzer stack MUST include the IK tokenizer, Harbin Institute of Technology stopwords, project chemistry stopwords, a chemistry custom dictionary, and a chemistry synonym dictionary.

#### Scenario: Dictionary assets are deployed
- **WHEN** the Docker Compose application stack starts ES/IK
- **THEN** the required stopword, custom dictionary, and synonym files MUST be available to the ES/IK container
- **AND** production readiness validation MUST fail if the analyzer assets or IK analyzer are missing.

#### Scenario: Chemistry synonym is searched
- **WHEN** a student searches by a formula, Chinese reagent name, English reagent name, ion notation, or common alias covered by the synonym dictionary
- **THEN** the search backend MUST match published point-node documents containing the equivalent student-facing point knowledge
- **AND** matching MUST NOT depend on teacher-only notes or AI evidence chunks.

### Requirement: Destructive legacy model replacement
The system SHALL retire legacy experiment-parent write paths after migration to the catalog tree.

#### Scenario: Legacy admin point API is called
- **WHEN** a client calls the old experiment video-point write API after the migration
- **THEN** the system MUST not process the write as an authoritative path
- **AND** tests MUST verify application code uses catalog-node APIs.

#### Scenario: Legacy experiment data is migrated
- **WHEN** the migration runs against existing formal experiments and experiment video points
- **THEN** useful titles, summaries, chapter bindings, video candidates, point content, related links, videos, questions, and search state MUST be migrated into catalog-tree records
- **AND** the migration MUST record old-to-new identity mapping for audit and data repair.


## MODIFIED Requirements

### Requirement: In-context tree editing
The teacher catalog tree SHALL support fast in-context creation, reuse, movement, ordering, and cleanup of directory nodes and point placements.

#### Scenario: Teacher adds a child directory
- **WHEN** a teacher adds a child directory under a selected directory node
- **THEN** the system MUST create the directory under that parent with server-controlled identity
- **AND** the directory MUST NOT target a canonical experiment point.

#### Scenario: Teacher creates a new experiment placement
- **WHEN** a teacher creates a new experiment point under a selected directory node
- **THEN** the system MUST create a canonical experiment point and a point placement under that parent
- **AND** the teacher MUST be able to edit the shared canonical point content from the new placement.

#### Scenario: Teacher reuses an existing experiment
- **WHEN** a teacher adds an existing experiment to a selected directory
- **THEN** the system MUST create a new point placement targeting the selected canonical experiment point
- **AND** it MUST NOT duplicate videos, content, AI evidence, question bindings, assessment identity, analytics, or feedback identity.

#### Scenario: Teacher attempts to add under a point placement
- **WHEN** a teacher attempts to add a child under a point placement
- **THEN** the editor MUST prevent or reject the operation
- **AND** the UI MUST make clear that point placements are learning leaves.

#### Scenario: Teacher reorders nodes
- **WHEN** a teacher drags a directory or point placement within the same parent or uses an accessible fallback reorder action
- **THEN** the system MUST persist display order
- **AND** sibling order MUST remain stable after refresh.

#### Scenario: Teacher moves a placement
- **WHEN** a teacher moves a point placement to another directory parent
- **THEN** the system MUST validate that the move does not create a cycle and does not place children under a point placement
- **AND** the placement id and targeted canonical experiment point id MUST remain stable.

#### Scenario: Teacher archives a placement
- **WHEN** a teacher archives a point placement
- **THEN** the system MUST hide that placement from normal student catalog responses
- **AND** it MUST preserve the canonical experiment point unless final-placement archival is explicitly confirmed.

### Requirement: Node editor tabs follow node capability
The right editor SHALL show editing panels based on whether the selected node is a directory or a point placement.

#### Scenario: Directory node is selected
- **WHEN** a directory node is selected
- **THEN** the editor MUST show basics, teacher-only note, student card copy, card presentation, child ordering, publication, and validation
- **AND** it MUST NOT show shared point principle, video binding, related point links, assessment, or search-document panels as editable directory-owned fields.

#### Scenario: Point placement is selected
- **WHEN** a point placement is selected
- **THEN** the editor MUST show placement context, shared canonical point content, teacher-only point note, limited placement/card presentation, video bindings, related links, search preview, assessment context, publication, and validation
- **AND** the editor MUST indicate the canonical experiment point id or equivalent teacher-readable shared identity where appropriate.

#### Scenario: Shared experiment has multiple placements
- **WHEN** the selected placement targets a canonical experiment point with more than one active placement
- **THEN** the editor MUST show a reuse indicator and the list or count of other placements
- **AND** it MUST warn that shared content and video edits affect every placement.

#### Scenario: Removed node type is selected
- **WHEN** stale data or a stale client references a hybrid, shortcut, reference, or otherwise unsupported node kind
- **THEN** the editor MUST render a controlled migration/unavailable state or normalized directory/point-placement editor
- **AND** it MUST NOT expose hybrid, shortcut, or reference-node editing controls.

### Requirement: Teacher-authored point content form
The editor SHALL let teachers maintain canonical point content without AI generation while making shared-edit scope clear.

#### Scenario: Teacher edits point content
- **WHEN** a teacher edits point content from a point placement
- **THEN** the form MUST provide fields for point title, teacher-only note, principle mode, principle equation or text, phenomenon explanation, safety note, related point links, bound videos, and publication state.
- **AND** the save MUST apply to the targeted canonical experiment point rather than only the selected placement.

#### Scenario: Teacher edits teacher-only note
- **WHEN** a teacher enters remarks, non-experiment knowledge, operational comments, or authoring hints in the canonical point teacher-only note field
- **THEN** the editor MUST save the note for teacher/admin reuse across all placements of that canonical experiment point
- **AND** the editor MUST indicate that this note is not shown to students and is not part of student video-library search.

#### Scenario: Teacher edits placement note or placement override
- **WHEN** the editor exposes a placement-local note, card override, or path-specific display field
- **THEN** it MUST label that field as applying only to the selected catalog location
- **AND** saving it MUST NOT alter shared canonical point content.

#### Scenario: Teacher saves draft content
- **WHEN** required publish fields are incomplete
- **THEN** the system MUST allow draft save on the canonical point
- **AND** it MUST show validation messages explaining what is missing before any placement can expose student-visible point detail.

#### Scenario: Teacher publishes point content
- **WHEN** a teacher publishes canonical point content or a placement that targets it
- **THEN** the system MUST validate required shared fields and placement availability
- **AND** queued search indexing MUST use student-facing canonical point knowledge plus placement path context rather than teacher-only notes.

### Requirement: Video binding inside node editor
The editor SHALL bind existing videos to canonical experiment points from within the selected placement workspace.

#### Scenario: Teacher binds existing video
- **WHEN** a teacher selects an existing media asset for a point placement
- **THEN** the system MUST create or update a media binding on the targeted canonical experiment point
- **AND** the asset MUST become eligible for student display through every published placement targeting that canonical point according to publication rules.

#### Scenario: Teacher needs to upload a new video
- **WHEN** a teacher needs media that is not yet in the media library
- **THEN** the catalog editor MUST direct the teacher to the media/video upload page or workflow
- **AND** it MUST NOT include local file upload controls or create new media assets inside the catalog editor.

#### Scenario: Teacher manages an existing binding
- **WHEN** a teacher publishes, unpublishes, previews, or removes a canonical point media binding
- **THEN** the editor MUST update only the binding state for the canonical experiment point
- **AND** it MUST NOT alter the underlying media asset upload lifecycle.

#### Scenario: Reused experiment has bound videos
- **WHEN** a point placement targets a canonical experiment point with published video bindings
- **THEN** every published placement of that canonical point MUST show the same eligible videos
- **AND** the editor MUST not create duplicate video bindings merely because the experiment appears in another directory.

### Requirement: Publication and validation are explicit
The teacher catalog editor SHALL separate canonical experiment publication readiness from placement visibility.

#### Scenario: Teacher reviews validation
- **WHEN** a teacher selects a directory, placement, or subtree
- **THEN** the editor MUST show validation status for required title, directory card fields, canonical point content, placement availability, video binding status where relevant, related links, and search-index readiness
- **AND** validation MUST identify whether an issue belongs to the selected placement or the shared canonical experiment point.

#### Scenario: Teacher publishes a subtree
- **WHEN** a teacher publishes a directory subtree
- **THEN** the system MUST publish eligible child directory and point placement nodes according to explicit teacher action
- **AND** it MUST report any placements skipped because their canonical experiment point content is incomplete or unavailable.

#### Scenario: Teacher removes the last placement
- **WHEN** a teacher removes or archives the last active placement for a canonical experiment point
- **THEN** the editor MUST require an explicit final-placement decision before archiving the canonical point
- **AND** it MUST explain that shared content, videos, evidence, questions, assessment identity, analytics, and feedback references are affected.

## ADDED Requirements

### Requirement: Experiment reuse management
The teacher catalog editor SHALL provide a reuse workflow for adding the same experiment to multiple catalog directories.

#### Scenario: Teacher searches for an experiment to reuse
- **WHEN** a teacher starts adding an existing experiment to a directory
- **THEN** the editor MUST allow searching canonical experiment points by title, reagent, formula, chapter path, or existing placement context
- **AND** results MUST show enough context to avoid choosing the wrong experiment.

#### Scenario: Teacher confirms reuse
- **WHEN** a teacher selects an existing experiment and confirms reuse
- **THEN** the editor MUST create a new placement in the selected directory
- **AND** it MUST show that the placement is synchronized with the selected experiment.

#### Scenario: Teacher wants an independent copy
- **WHEN** a teacher needs an independent experiment based on an existing one
- **THEN** the UI MUST require an explicit independent-copy or fork action separate from normal reuse
- **AND** the action MUST create a new canonical experiment point rather than another placement targeting the original canonical point.

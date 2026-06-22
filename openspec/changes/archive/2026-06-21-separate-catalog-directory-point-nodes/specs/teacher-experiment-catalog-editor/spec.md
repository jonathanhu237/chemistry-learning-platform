## MODIFIED Requirements

### Requirement: In-context tree editing
The teacher catalog tree SHALL support fast in-context creation, movement, ordering, and cleanup of directory and point nodes.

#### Scenario: Teacher adds a child node
- **WHEN** a teacher adds a child under a selected directory node
- **THEN** the system MUST create the node under that parent with server-controlled identity
- **AND** the teacher MUST be able to choose whether the new child is a directory or point.

#### Scenario: Teacher attempts to add under a point
- **WHEN** a teacher attempts to add a child under a point node
- **THEN** the editor MUST prevent or reject the operation
- **AND** the UI MUST make clear that point nodes are learning leaves.

#### Scenario: Teacher reorders nodes
- **WHEN** a teacher drags a node within the same parent or uses an accessible fallback reorder action
- **THEN** the system MUST persist display order
- **AND** sibling order MUST remain stable after refresh.

#### Scenario: Teacher moves a node
- **WHEN** a teacher moves a node to another directory parent
- **THEN** the system MUST validate that the move does not create a cycle and does not place children under a point
- **AND** all point identities and bindings under the moved subtree MUST remain stable.

#### Scenario: Teacher archives a node
- **WHEN** a teacher archives a node
- **THEN** the system MUST hide it from normal student catalog responses
- **AND** it MUST preserve historical data and allow teacher-side recovery or audit according to admin rules.

### Requirement: Node editor tabs follow node capability
The right editor SHALL show editing panels based on whether the selected node is a directory or point.

#### Scenario: Directory node is selected
- **WHEN** a directory node is selected
- **THEN** the editor MUST show basics, teacher-only note, student card copy, card presentation, child ordering, publication, and validation
- **AND** it MUST NOT show point principle, video binding, related point links, assessment, or search-document panels as editable directory-owned fields.

#### Scenario: Point node is selected
- **WHEN** a point node is selected
- **THEN** the editor MUST show point learning content, teacher-only note, limited point card presentation, video bindings, related links, search preview, assessment context, publication, and validation.

#### Scenario: Removed node type is selected
- **WHEN** stale data or a stale client references a hybrid or shortcut node
- **THEN** the editor MUST render a controlled migration/unavailable state or normalized directory/point editor
- **AND** it MUST NOT expose hybrid or shortcut editing controls.

### Requirement: Teacher-authored point content form
The editor SHALL let teachers maintain point content without AI generation.

#### Scenario: Teacher edits point content
- **WHEN** a teacher edits a point node
- **THEN** the form MUST provide fields for point title, teacher-only note, principle mode, principle equation or text, phenomenon explanation, safety note, related point links, bound videos, and publication state.
- **AND** the teacher-only note MUST be visually and technically separated from student-facing point knowledge.

#### Scenario: Teacher edits teacher-only note
- **WHEN** a teacher enters remarks, non-experiment knowledge, operational comments, or authoring hints in the teacher-only note field
- **THEN** the editor MUST save the note for teacher/admin reuse
- **AND** the editor MUST indicate that this note is not shown to students and is not part of student video-library search.

#### Scenario: Teacher saves draft content
- **WHEN** required publish fields are incomplete
- **THEN** the system MUST allow draft save
- **AND** it MUST show validation messages explaining what is missing before publication.

#### Scenario: Teacher publishes point content
- **WHEN** a teacher publishes point content
- **THEN** the system MUST validate required fields, update student visibility, and queue search indexing.
- **AND** queued search indexing MUST use student-facing point title and point knowledge rather than the teacher-only note.

### Requirement: Video binding inside node editor
The editor SHALL bind existing videos to point nodes from within the selected node workspace.

#### Scenario: Teacher binds existing video
- **WHEN** a teacher selects an existing media asset for a point node
- **THEN** the system MUST create a point-node media binding
- **AND** the asset MUST become eligible for student display only through that point binding and publication rules.

#### Scenario: Teacher needs to upload a new video
- **WHEN** a teacher needs media that is not yet in the media library
- **THEN** the catalog editor MUST direct the teacher to the media/video upload page or workflow
- **AND** it MUST NOT include local file upload controls or create new media assets inside the catalog editor.

#### Scenario: Teacher manages an existing binding
- **WHEN** a teacher publishes, unpublishes, previews, or removes a point-node media binding
- **THEN** the editor MUST update only the binding state
- **AND** it MUST NOT alter the underlying media asset upload lifecycle.

### Requirement: Publication and validation are explicit
The teacher catalog editor SHALL separate draft editing from student-visible publication.

#### Scenario: Teacher reviews validation
- **WHEN** a teacher selects a node or subtree
- **THEN** the editor MUST show validation status for required title, directory card fields, point content, video binding status where relevant, related links, and search-index readiness.

#### Scenario: Teacher publishes a subtree
- **WHEN** a teacher publishes a directory subtree
- **THEN** the system MUST publish eligible child directory and point nodes according to explicit teacher action
- **AND** it MUST report any nodes skipped because they are incomplete.

## ADDED Requirements

### Requirement: Professional draggable tree interaction
The teacher catalog tree SHALL use a polished draggable tree interaction instead of always-visible up/down row controls.

#### Scenario: Teacher reorders by dragging
- **WHEN** a teacher drags a directory or point row to a valid sibling or directory drop target
- **THEN** the UI MUST show a clear drop indicator and persist the new parent/order after drop
- **AND** the selected node and expanded ancestor context SHOULD remain stable after refresh.

#### Scenario: Invalid drop is attempted
- **WHEN** a teacher drags a node onto a point, across a disallowed chapter boundary, or into its own descendant
- **THEN** the UI MUST prevent the drop or show a controlled validation error
- **AND** no partial move MUST be persisted.

#### Scenario: Row actions are needed
- **WHEN** a teacher hovers, focuses, or selects a tree row
- **THEN** add, archive, duplicate-if-supported, and more actions MAY appear contextually
- **AND** rows MUST NOT show large always-visible move-up and move-down buttons for every node.

### Requirement: Directory card editor
The editor SHALL provide directory-specific card presentation controls.

#### Scenario: Teacher edits directory card
- **WHEN** a teacher selects a directory node
- **THEN** the editor MUST allow student-visible title/description and structured card presentation fields such as image, icon, accent, and layout variant
- **AND** it MUST preview how the directory card will appear in the student catalog where practical.

#### Scenario: Directory teacher note is edited
- **WHEN** a teacher edits the directory teacher note
- **THEN** the editor MUST save it for teacher/admin authoring context
- **AND** it MUST indicate that the note is not visible to students and is not indexed for student search.

### Requirement: Point card editor remains constrained
The editor SHALL allow limited point card presentation overrides while preserving consistent point-list design.

#### Scenario: Teacher edits point card
- **WHEN** a teacher selects a point node
- **THEN** the editor MAY allow cover image, short description, icon, accent, or emphasis override fields
- **AND** it MUST NOT allow arbitrary point card layout changes that make points indistinguishable from directories.

#### Scenario: Point card defaults exist
- **WHEN** no point card override is configured
- **THEN** the student point card MUST use stable defaults derived from point title, point knowledge summary, and bound video thumbnail where available.

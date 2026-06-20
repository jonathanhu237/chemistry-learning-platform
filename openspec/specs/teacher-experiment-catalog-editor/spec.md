# teacher-experiment-catalog-editor Specification

## Purpose
TBD - created by archiving change experiment-catalog-tree-point-architecture. Update Purpose after archive.
## Requirements
### Requirement: Left tree and right editor workspace
The teacher admin console SHALL provide a catalog authoring workspace with a navigable tree on the left and the selected node editor on the right.

#### Scenario: Teacher opens catalog management
- **WHEN** a teacher opens experiment catalog management
- **THEN** the page MUST show chapter selection and a tree of catalog nodes for the selected chapter
- **AND** selecting a node MUST open its editor without leaving the workspace.

#### Scenario: Teacher searches the tree
- **WHEN** a teacher searches by node title, alias, reagent, point text, or legacy code
- **THEN** the tree MUST surface matching nodes and enough ancestors to preserve context
- **AND** selecting a result MUST focus the matching node in the editor.

### Requirement: In-context tree editing
The teacher catalog tree SHALL support fast in-context creation, movement, ordering, and cleanup of nodes.

#### Scenario: Teacher adds a child node
- **WHEN** a teacher adds a child under a selected node
- **THEN** the system MUST create the node under that parent with server-controlled identity
- **AND** the teacher MUST be able to choose or later change whether it is a directory, point, hybrid, or shortcut.

#### Scenario: Teacher reorders nodes
- **WHEN** a teacher drags a node within the same parent or uses reorder controls
- **THEN** the system MUST persist display order
- **AND** sibling order MUST remain stable after refresh.

#### Scenario: Teacher moves a node
- **WHEN** a teacher moves a node to another parent
- **THEN** the system MUST validate that the move does not create a cycle
- **AND** all point identities and bindings under the moved subtree MUST remain stable.

#### Scenario: Teacher archives a node
- **WHEN** a teacher archives a node
- **THEN** the system MUST hide it from normal student catalog responses
- **AND** it MUST preserve historical data and allow teacher-side recovery or audit according to admin rules.

### Requirement: Node editor tabs follow node capability
The right editor SHALL show editing panels based on the selected node's capabilities.

#### Scenario: Directory node is selected
- **WHEN** a directory-only node is selected
- **THEN** the editor MUST show basics, student card copy, child ordering, publication, and validation
- **AND** it MUST NOT require point principle, video, or assessment fields.

#### Scenario: Point-capable node is selected
- **WHEN** a point or hybrid node is selected
- **THEN** the editor MUST show point learning content, teacher-only note, video bindings, related links, search preview, assessment context, publication, and validation.

#### Scenario: Shortcut node is selected
- **WHEN** a shortcut node is selected
- **THEN** the editor MUST show shortcut target selection and local display override fields
- **AND** it MUST make clear that canonical point content lives on the target node.

### Requirement: Teacher-authored point content form
The editor SHALL let teachers maintain point content without AI generation.

#### Scenario: Teacher edits point content
- **WHEN** a teacher edits a point-capable node
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
The editor SHALL bind videos to point nodes from within the selected node workspace.

#### Scenario: Teacher binds existing video
- **WHEN** a teacher selects an existing media asset for a point node
- **THEN** the system MUST create a point-node media binding
- **AND** the asset MUST become eligible for student display only through that point binding and publication rules.

#### Scenario: Teacher uploads video for point
- **WHEN** a teacher uploads a video from the point editor
- **THEN** the system MUST create the media asset and bind it to the selected point node
- **AND** processing, ready, failed, draft, and published states MUST be visible inside the editor.

### Requirement: Publication and validation are explicit
The teacher catalog editor SHALL separate draft editing from student-visible publication.

#### Scenario: Teacher reviews validation
- **WHEN** a teacher selects a node or subtree
- **THEN** the editor MUST show validation status for required title, structure, point content, video binding status where relevant, related links, and search-index readiness.

#### Scenario: Teacher publishes a subtree
- **WHEN** a teacher publishes a directory subtree
- **THEN** the system MUST publish eligible child nodes according to explicit teacher action
- **AND** it MUST report any nodes skipped because they are incomplete.

### Requirement: Engineering boundaries for catalog editor
The teacher catalog editor SHALL follow the established admin frontend architecture.

#### Scenario: Developer updates catalog editor
- **WHEN** a developer changes the catalog tree, node editor, point content form, video binding panel, or search preview
- **THEN** the code MUST live in feature-scoped modules under the catalog/experiments feature
- **AND** shared API calls MUST be owned by domain API client modules rather than a monolithic API barrel.


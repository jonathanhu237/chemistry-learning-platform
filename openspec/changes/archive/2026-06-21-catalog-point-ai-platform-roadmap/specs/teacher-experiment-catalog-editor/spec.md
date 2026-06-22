## ADDED Requirements

### Requirement: Chapter switching lives in the workspace title area
The teacher catalog editor SHALL avoid duplicate chapter selectors and use the current chapter title area as the primary chapter-switching control.

#### Scenario: Teacher changes chapter
- **WHEN** a teacher opens the catalog workspace and wants to switch chapters
- **THEN** the current chapter title area MUST provide a clear chapter switching interaction
- **AND** the editor MUST NOT show a redundant left-sidebar chapter dropdown that repeats the same title.

#### Scenario: Chapter changes
- **WHEN** the teacher selects a different chapter
- **THEN** the tree, selection, validation summary, and right workspace MUST refresh to that chapter's catalog context
- **AND** stale node details from the previous chapter MUST NOT remain actionable.

### Requirement: Right workspace uses a contextual title card and tab surface
The selected node workspace SHALL present node identity, status, and work panels as one coherent surface.

#### Scenario: Directory node is selected
- **WHEN** a teacher selects a directory node
- **THEN** the workspace MUST show a title card with directory identity, publication/status summary, child point counts, and actionable checks
- **AND** it MUST avoid repeating the same title as both labels and content tags.

#### Scenario: Point node is selected
- **WHEN** a teacher selects a point node
- **THEN** the workspace MUST show a title card with point title, catalog path context, video/content/evidence/status indicators, and publish/archive actions
- **AND** the edit panels MUST sit in a tabbed workbench below the title card.

#### Scenario: No node is selected
- **WHEN** no catalog node is selected
- **THEN** the workspace MUST render a visually consistent empty state aligned with the surrounding editor shell
- **AND** it MUST invite selecting or creating a node without looking like a detached blank card.

### Requirement: Modern tree drag-and-drop behavior
The catalog tree SHALL behave like a modern online file tree during move and reorder operations.

#### Scenario: Teacher drags a node
- **WHEN** a teacher starts dragging a catalog node
- **THEN** the tree MUST show a visible drag preview or drag overlay
- **AND** potential drop targets MUST provide clear hover/drop feedback.

#### Scenario: Teacher hovers over a collapsed directory
- **WHEN** a dragged node hovers over a collapsed directory long enough to indicate intent
- **THEN** the directory MUST auto-expand or expose an intentional expand affordance
- **AND** the drop target MUST remain understandable after expansion.

#### Scenario: Move succeeds
- **WHEN** a node move or reorder operation succeeds
- **THEN** the tree MUST refresh or update local state immediately
- **AND** the moved node MUST remain visible and selected in its new location when possible.

#### Scenario: Move fails
- **WHEN** a move is rejected by validation or network failure
- **THEN** the tree MUST restore the previous layout
- **AND** it MUST show a teacher-readable error without leaving a phantom row or stale target highlight.

### Requirement: Tree connector geometry is consistent across depths
The catalog tree SHALL draw indentation and branch connectors without overlapping expand controls or node icons.

#### Scenario: First-level directory is rendered
- **WHEN** a first-level directory row is displayed
- **THEN** its horizontal connector MUST extend only far enough to indicate hierarchy
- **AND** it MUST NOT overlap the child expand/collapse control.

#### Scenario: Deeper rows are rendered
- **WHEN** second-level or deeper directory and point rows are displayed
- **THEN** each row MUST show the same short horizontal connector convention as first-level rows
- **AND** vertical guide lines MUST align with the correct ancestor depth.

### Requirement: Teaching note is the only teacher-only note field
The catalog editor SHALL use one teacher-only note concept named teaching note.

#### Scenario: Teacher edits point notes
- **WHEN** a teacher edits point content
- **THEN** the form MUST expose a single teacher-only teaching note field
- **AND** it MUST NOT separately expose overlapping labels such as management summary and teacher note for the same semantic purpose.

#### Scenario: New point is created
- **WHEN** a teacher creates a new point or directory
- **THEN** default authoring fields MUST use teaching note wording wherever teacher-only remarks are collected
- **AND** student-facing descriptions MUST remain separate from teaching notes.

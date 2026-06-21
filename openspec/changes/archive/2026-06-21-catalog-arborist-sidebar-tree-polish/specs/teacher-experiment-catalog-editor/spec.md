## MODIFIED Requirements

### Requirement: Node editor tabs follow node capability
The right editor SHALL show editing panels based on the selected node's capabilities and SHALL hide point-only panels for directory nodes.

#### Scenario: Directory node is selected
- **WHEN** a directory node is selected
- **THEN** the editor MUST show only directory-relevant tabs: content, student card, publish checks, and advanced
- **AND** it MUST NOT show video binding or related experiment tabs
- **AND** it MUST NOT run point-only media asset or related-point search queries for that directory selection.

#### Scenario: Directory node replaces a point selection while a point-only tab is active
- **WHEN** the active tab is video or related experiments and the teacher selects a directory node
- **THEN** the editor MUST switch the active tab back to content
- **AND** no video binding or related-link form MUST remain visible for the directory node.

#### Scenario: Point node is selected
- **WHEN** a point node is selected
- **THEN** the editor MUST show point-relevant tabs: content, video, related experiments, student card, publish checks, and advanced
- **AND** the video and related experiment panels MUST operate on the selected stable point node id.

## ADDED Requirements

### Requirement: Arborist sidebar navigation tree
The teacher catalog editor SHALL render the chapter catalog tree through an Arborist-backed sidebar navigation tree inspired by the shared Dribbble sidebar navigation reference and `react-arborist` Gmail/sidebar demo.

#### Scenario: Teacher views the catalog tree
- **WHEN** a teacher opens a chapter catalog
- **THEN** the tree MUST render as a single coherent sidebar row system rather than an Ant Design Tree wrapper containing a separate custom row
- **AND** the tree MUST NOT expose Ant Design Tree switcher/indent/content-wrapper visuals as part of the visible row language.

#### Scenario: Directory row renders
- **WHEN** a directory row is visible
- **THEN** a disclosure chevron MUST appear immediately before the directory icon
- **AND** the directory icon MUST use a sidebar-appropriate folder icon
- **AND** the row MUST be able to display trailing metadata such as status or child count without overlapping the title.

#### Scenario: Point row renders
- **WHEN** a point row is visible
- **THEN** it MUST reserve the same disclosure width as directory rows so titles align
- **AND** it MUST use experiment-specific iconography such as a flask or test-tube icon rather than a generic document/file icon
- **AND** video availability MUST appear as trailing metadata, not as the primary node-kind icon.

#### Scenario: Teacher selects a row
- **WHEN** a teacher selects a directory or point row
- **THEN** the selected state MUST be a full-row rounded sidebar highlight
- **AND** it MUST NOT look like a bordered card embedded inside the tree.

#### Scenario: Teacher scans nested directories
- **WHEN** the catalog contains at least three nested levels
- **THEN** the tree MUST render soft nested guide lines or an equivalent stable hierarchy affordance
- **AND** indentation, chevrons, icons, labels, trailing metadata, and actions MUST remain aligned at common admin desktop widths.

### Requirement: Sidebar tree actions remain available without visual clutter
The teacher catalog tree SHALL keep add, drag, status, and secondary actions available while preserving the clean sidebar tree appearance.

#### Scenario: Teacher hovers or focuses a directory row
- **WHEN** a directory row is hovered, focused, or selected
- **THEN** a child-add action MUST be available for creating a child directory or child point
- **AND** the action MUST NOT be permanently visible on every unselected row.

#### Scenario: Teacher hovers or focuses any row
- **WHEN** a row is hovered, focused, or selected
- **THEN** a more-actions menu MUST provide secondary actions such as copy id, archive or restore, publish or unpublish, and fallback movement
- **AND** these controls MUST NOT shift title, icon, or trailing metadata layout when they appear.

#### Scenario: Teacher sees drag affordance
- **WHEN** dragging is available for a row
- **THEN** the implementation MUST provide a visually subtle drag affordance through the row itself or a hover-only handle
- **AND** the UI MUST NOT show always-visible six-dot drag grips on every row.

#### Scenario: Teacher adds a top-level node
- **WHEN** a teacher adds a node at the selected chapter root
- **THEN** the UI MUST use teacher-facing wording such as "add to chapter"
- **AND** it MUST NOT expose implementation wording such as "root node" as the primary visible label.

### Requirement: Arborist drag movement preserves catalog semantics
The teacher catalog tree SHALL map Arborist drag and move events to existing catalog move and reorder semantics without changing backend APIs.

#### Scenario: Teacher drags within the same parent
- **WHEN** a teacher drags a directory or point row to a valid sibling position under the same parent
- **THEN** the UI MUST show a clear Arborist drop cursor
- **AND** the system MUST persist the new sibling order through the existing reorder API.

#### Scenario: Teacher drags into a directory
- **WHEN** a teacher drags a directory or point row into a valid directory parent
- **THEN** the UI MUST show that the directory can receive the drop
- **AND** the system MUST persist the new parent id and display order through the existing move API.

#### Scenario: Teacher attempts an invalid drop
- **WHEN** a teacher attempts to drop a node into a point node, into its own descendant, or across an unsupported chapter boundary
- **THEN** the UI MUST prevent the drop or show a controlled validation warning
- **AND** no partial move or reorder MUST be persisted.

#### Scenario: Teacher cannot use drag precisely
- **WHEN** a teacher uses a row menu or keyboard-accessible command instead of drag
- **THEN** the editor MUST provide fallback movement commands
- **AND** those commands MUST apply the same directory, cycle, and chapter validation as drag.

### Requirement: Arborist lazy loading preserves directory affordances
The teacher catalog tree SHALL bridge server-loaded catalog children into Arborist without losing directory disclosure or drop behavior.

#### Scenario: Directory has children that are not loaded yet
- **WHEN** a directory node reports child availability but its children have not yet been fetched
- **THEN** the tree MUST still render the node as expandable and directory-like
- **AND** opening the node MUST fetch its children and merge them into the tree without clearing the selected node.

#### Scenario: Directory is currently empty
- **WHEN** a directory has no child nodes
- **THEN** the tree MUST still render it as a directory that can receive newly created child nodes where allowed
- **AND** it MUST NOT render as a point-like leaf.

#### Scenario: Search or creation selects a nested node
- **WHEN** search results or a newly created node select a nested node
- **THEN** the tree MUST open known ancestors and scroll the selected node into view where the client has enough loaded context
- **AND** it MUST preserve the selected stable node id.

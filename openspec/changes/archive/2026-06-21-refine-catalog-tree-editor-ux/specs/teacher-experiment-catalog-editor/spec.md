## ADDED Requirements

### Requirement: Polished source-list catalog tree
The teacher catalog editor SHALL render the chapter catalog as a polished source-list/file-tree surface with a coherent visual language for hierarchy, node kind, selection, and status.

#### Scenario: Teacher views a mixed directory and point tree
- **WHEN** a teacher opens a chapter catalog containing expandable directories, collapsed directories, and point leaves
- **THEN** expandable directories MUST show a consistent disclosure affordance
- **AND** point leaves MUST reserve equivalent disclosure space so titles align with directory titles
- **AND** directory and point icons MUST use the same optical size, stroke weight, and color system.

#### Scenario: Teacher selects a point row
- **WHEN** a teacher selects a point row in the tree
- **THEN** the row MUST use a full-row selected state that stays aligned with the tree hierarchy
- **AND** it MUST NOT render as a large bordered card inside the tree.

#### Scenario: Teacher scans a deep catalog
- **WHEN** the tree contains at least three nested levels and long chemistry node titles
- **THEN** indentation, guide lines, title truncation, status display, and row actions MUST remain visually stable
- **AND** node text, status, disclosure controls, drag handles, and action controls MUST NOT overlap at common admin desktop widths.

#### Scenario: Row actions are available
- **WHEN** a teacher hovers, focuses, or selects a row
- **THEN** contextual actions such as add child, archive or restore, publish action where supported, copy id, and more actions MAY appear
- **AND** every row MUST NOT show large always-visible move-up or move-down controls.

### Requirement: Mature drag movement with accessible fallback
The teacher catalog tree SHALL support reorder and move through a mature draggable tree interaction with a non-mouse fallback.

#### Scenario: Teacher drags a node to a valid position
- **WHEN** a teacher drags a directory or point row to a valid sibling position or valid directory parent
- **THEN** the UI MUST show a clear drop indicator before persistence
- **AND** the saved tree MUST preserve the moved node id, child subtree where relevant, and sibling order after refresh.

#### Scenario: Teacher drags to an invalid target
- **WHEN** a teacher attempts to drop a node onto a point, into its own descendant, or across a disallowed chapter boundary
- **THEN** the UI MUST prevent the drop or show a controlled validation error
- **AND** no partial move or reorder MUST be persisted.

#### Scenario: Teacher cannot use drag precisely
- **WHEN** a teacher uses keyboard navigation, focus actions, or a row menu instead of drag
- **THEN** the editor MUST provide a fallback way to move or reorder the selected node where movement is allowed
- **AND** the fallback MUST apply the same directory/point and cycle validation as drag.

### Requirement: Focused selected-node editor information architecture
The right editor SHALL present selected-node editing as a focused workspace with primary authoring fields first and operational/debug fields separated into task-specific panels.

#### Scenario: Point node default editor opens
- **WHEN** a teacher selects a point node
- **THEN** the default editor view MUST prioritize point title, teacher-only note, principle mode and principle content, phenomenon explanation, safety note, and primary publish actions
- **AND** raw node id, parent id, display order, search-index diagnostics, validation internals, and related-link sort internals MUST NOT appear in the default point content view.

#### Scenario: Directory node default editor opens
- **WHEN** a teacher selects a directory node
- **THEN** the default editor view MUST prioritize directory title, teacher-only note, student-visible description, and directory card presentation entry points
- **AND** it MUST NOT show point principle, video binding, related experiment links, assessment, or search-document controls as directory-owned fields.

#### Scenario: Teacher needs less-common metadata
- **WHEN** a teacher opens publish checks, student card, related experiments, video binding, or advanced/debug panels
- **THEN** the editor MAY show the fields specific to that task
- **AND** those panels MUST be visually secondary to the main content authoring view.

#### Scenario: Selected node header renders
- **WHEN** any catalog node is selected
- **THEN** the editor MUST show a stable selected-node header with status, node kind, title, breadcrumb path, and primary actions
- **AND** point nodes with bound videos MUST show compact video count/status in the header or video panel.

### Requirement: Point title is a single visible authoring concept
The teacher editor SHALL avoid exposing duplicate primary title concepts for point nodes.

#### Scenario: Teacher edits a point title
- **WHEN** a teacher edits the primary title field for a point node
- **THEN** the UI MUST treat it as the point name shown in the tree and point detail editor
- **AND** the save flow MUST keep node title and point title synchronized unless an explicit advanced override is later introduced.

#### Scenario: Backend data contains divergent titles
- **WHEN** loaded point data contains a node title and point title that differ
- **THEN** the default editor MUST choose one teacher-facing primary title according to documented mapping rules
- **AND** any mismatch diagnostics MUST appear only in advanced/debug context.

### Requirement: Catalog video panel remains binding-only
The selected-node editor SHALL keep video upload separate from catalog authoring and only manage existing media bindings for point nodes.

#### Scenario: Teacher opens the point video panel
- **WHEN** a teacher opens video management for a point node
- **THEN** the panel MUST allow selecting existing media assets, binding, previewing, publishing, unpublishing, or removing point media bindings
- **AND** it MUST NOT render a local file input, tus upload control, or upload-and-bind action.

#### Scenario: Teacher needs a new video asset
- **WHEN** the needed video asset is not available in the existing media selector
- **THEN** the catalog editor MUST provide a clear navigation hint or link to the media/video upload workflow
- **AND** the upload lifecycle MUST remain owned by the media/video feature.

### Requirement: Catalog workspace visual acceptance is verified
The teacher catalog editor SHALL include visual and interaction acceptance checks for the tree and selected-node editor.

#### Scenario: Tree visual QA runs
- **WHEN** implementation validates the catalog tree UI
- **THEN** QA MUST cover expanded directory, collapsed directory, selected point, long title, hover or focus row action, and drag/drop indicator states
- **AND** QA MUST inspect at least one narrow laptop-width admin viewport where row actions are likely to collide.

#### Scenario: Editor visual QA runs
- **WHEN** implementation validates the selected-node editor UI
- **THEN** QA MUST cover directory default editor, point default editor, video panel, related experiments panel, publish checks, and advanced/debug fields
- **AND** QA MUST verify that default point content editing is not visually dominated by debug/search/order metadata.

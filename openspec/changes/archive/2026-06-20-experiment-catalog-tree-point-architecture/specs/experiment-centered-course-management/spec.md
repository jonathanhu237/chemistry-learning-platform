## MODIFIED Requirements

### Requirement: Theory chapter to experiment binding
The system SHALL keep theory chapters visible and bind each chapter to an experiment catalog tree instead of fixed experiment units.

#### Scenario: Teacher views chapter structure
- **GIVEN** the textbook theory chapters are available
- **WHEN** a teacher opens course structure management
- **THEN** the teacher SHALL see chapters as grouping/navigation roots
- **AND** each chapter SHALL show its experiment catalog tree as learning resources under that chapter.

#### Scenario: Learning content appears in multiple chapter contexts
- **GIVEN** a point is relevant to more than one chapter or conceptual path
- **WHEN** the point is reused
- **THEN** the system SHALL use a shortcut/reference or explicit chapter-node placement
- **AND** it SHALL NOT require duplicating the canonical point content.

#### Scenario: Chapter has no catalog content
- **GIVEN** a chapter such as lanthanides/actinides has no authored catalog nodes
- **WHEN** the chapter is displayed
- **THEN** the system SHALL show that no catalog content is currently bound
- **AND** it SHALL NOT fabricate an experiment to fill the gap.

### Requirement: Student H5 published experiment exposure
Student H5 learning APIs SHALL expose only active and published catalog nodes and point resources.

#### Scenario: Published point node is requested
- **WHEN** a student requests a published point node available to their class
- **THEN** the backend SHALL return student-facing point metadata, learning content, related links, assessment context, and playable resources.
- **AND** it SHALL exclude teacher-only notes and draft-only authoring metadata.

#### Scenario: Draft or archived node is requested
- **WHEN** a student requests a draft, archived, hidden, or otherwise unavailable node
- **THEN** the backend SHALL hide unavailable playable resources and teacher-only draft data
- **AND** it SHALL return a controlled not-found or unavailable response.

## ADDED Requirements

### Requirement: Chapter catalog course management
The admin course management capability SHALL treat the chapter catalog tree as the authoritative learning resource structure.

#### Scenario: Teacher creates catalog root content
- **WHEN** a teacher creates top-level learning content for a chapter
- **THEN** the backend SHALL create catalog nodes with server-controlled ids
- **AND** the teacher SHALL NOT need to enter database ids, legacy experiment ids, or point keys.

#### Scenario: Teacher manages chapter catalog status
- **WHEN** a teacher publishes, unpublishes, or archives catalog nodes
- **THEN** student APIs, video library search, and point detail visibility SHALL reflect the node status.

### Requirement: Official catalog seed migration
The system SHALL migrate existing official experiment units and their points into the catalog tree as seed content.

#### Scenario: Official experiments are migrated
- **GIVEN** the existing seeded formal experiments and video points are present
- **WHEN** the catalog migration runs
- **THEN** the system SHALL create chapter catalog nodes preserving useful titles, display order, summaries, video candidates, point content, and bindings
- **AND** it SHALL record legacy identity mapping for audit.

#### Scenario: Teacher edits migrated content
- **WHEN** a teacher edits migrated catalog nodes
- **THEN** the new catalog tables SHALL become authoritative
- **AND** the system SHALL NOT write changes back to the retired experiment-parent model.

## REMOVED Requirements

### Requirement: Experiment-first admin management
**Reason**: The new catalog is not experiment-first; experiments are no longer the fixed parent of point learning content.
**Migration**: Replace experiment list/detail management with the chapter catalog tree editor.

#### Scenario: Legacy experiment list is replaced
- **WHEN** implementation is complete
- **THEN** teachers SHALL manage catalog nodes from the tree editor
- **AND** the old experiment-first page SHALL NOT remain the authoritative editing path.

### Requirement: Seeded extensible experiment catalog
**Reason**: Seeded experiment units become migrated catalog nodes rather than first-class parent units.
**Migration**: Backfill official experiments into chapter catalog roots and point nodes, then use catalog-node creation for future content.

#### Scenario: Teacher creates additional learning content
- **WHEN** a teacher adds new content after migration
- **THEN** they SHALL create catalog nodes rather than formal experiment units.

### Requirement: Experiment resource binding
**Reason**: Video resources bind to point nodes, not experiment units.
**Migration**: Move experiment media bindings to point-node media bindings using the legacy identity map and teacher review where needed.

#### Scenario: Teacher binds a video after migration
- **WHEN** a teacher binds a video to learning content
- **THEN** the binding SHALL target a point-capable catalog node
- **AND** it SHALL NOT target a formal experiment as the student-visible resource.

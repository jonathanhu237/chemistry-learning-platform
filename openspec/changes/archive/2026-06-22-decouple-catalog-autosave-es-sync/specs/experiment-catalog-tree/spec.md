## ADDED Requirements

### Requirement: Published catalog edits preserve visibility
The catalog tree SHALL keep publication visibility separate from routine teacher edits to published catalog content.

#### Scenario: Teacher edits an already published point
- **WHEN** a teacher changes point title, principle, reaction equations, phenomenon explanation, safety note, related links, or video binding on a point whose placement and shared content are already published
- **THEN** the point and content MUST remain published unless the teacher explicitly unpublishes, archives, hides, or deletes it
- **AND** student-facing read models MUST read the latest saved authoritative content according to current publication and path visibility rules.

#### Scenario: Teacher edits a published point into an incomplete state
- **WHEN** a teacher clears or invalidates a required field on an already published point
- **THEN** the node status model MUST report the missing or invalid field as content completeness state
- **AND** it MUST NOT silently convert the point or content publication state to draft solely because the field was edited.

#### Scenario: Teacher edits a published directory title
- **WHEN** a teacher changes a published directory title or moves a published directory in a way that affects descendant paths
- **THEN** descendant point placements MUST keep their own publication state
- **AND** downstream search/evidence state MUST be marked stale or pending for affected placements rather than treating the directory edit as an unpublish action.

#### Scenario: Teacher-only note changes
- **WHEN** a teacher edits a directory or point teaching note that is not exposed to students or student search
- **THEN** the system MUST persist the note for teacher/admin use
- **AND** it MUST NOT change publication visibility or student-searchable content by itself.

### Requirement: Publication actions are explicit visibility transitions
The catalog tree SHALL reserve publication-state changes for explicit visibility actions, not autosave side effects.

#### Scenario: Teacher explicitly publishes an unpublished point
- **WHEN** a teacher explicitly publishes a valid unpublished point
- **THEN** the system MUST update the point/content publication state to published
- **AND** downstream ES/RAG sync MUST be triggered according to the hard-change policy.

#### Scenario: Teacher explicitly removes visibility
- **WHEN** a teacher explicitly unpublishes, archives, hides, deletes, or moves a point under an unpublished path
- **THEN** the system MUST remove or disable student visibility according to catalog rules
- **AND** downstream ES delete or disable work MUST be triggered immediately.

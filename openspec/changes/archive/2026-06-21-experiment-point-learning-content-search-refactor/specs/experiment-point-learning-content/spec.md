## ADDED Requirements

### Requirement: Stable experiment video point identity
The system SHALL store experiment video points as first-class records keyed by stable `(experiment_id, point_key)` identities.

#### Scenario: Existing candidate point is migrated
- **WHEN** the migration processes a `formal_experiments.metadata.video_candidates` entry
- **THEN** it MUST create or preserve an `experiment_video_points` row for that experiment and point
- **AND** it MUST use the current candidate key algorithm so existing routes, question metadata, evidence bindings, and media bindings continue to resolve.

#### Scenario: Existing media binding has point metadata
- **WHEN** a media binding contains `point_key` or `point_title` metadata for an experiment
- **THEN** the system MUST ensure that point exists in `experiment_video_points`
- **AND** it MUST not require the point to appear in `metadata.video_candidates` before it can be managed.

#### Scenario: Point title is edited
- **WHEN** a teacher changes a point display title
- **THEN** the point key MUST remain unchanged
- **AND** existing media bindings, question point references, assistant evidence bindings, analytics, and search route targets MUST continue to resolve.

#### Scenario: Point is archived
- **WHEN** a teacher archives a point
- **THEN** the point MUST be hidden from active student-facing point lists and search
- **AND** historical media bindings, question attempts, assistant evidence references, and analytics MUST remain auditable.

### Requirement: Human-authored point learning content
The system SHALL store point learning content as teacher-authored data linked to a stable experiment video point.

#### Scenario: Teacher saves equation-mode principle
- **WHEN** a teacher edits point content and selects `equation` as the experiment principle mode
- **THEN** the backend MUST require a chemical equation value
- **AND** it MUST treat text principle content as absent or secondary rather than as the primary principle.

#### Scenario: Teacher saves text-mode principle
- **WHEN** a teacher edits point content and selects `text` as the experiment principle mode
- **THEN** the backend MUST require a text principle value
- **AND** it MUST treat equation content as absent or secondary rather than as the primary principle.

#### Scenario: Teacher publishes point content
- **WHEN** a teacher publishes point learning content
- **THEN** the backend MUST require a valid principle, phenomenon explanation, and safety note
- **AND** it MUST record publication status, publication time, and publisher identity.

#### Scenario: Draft content exists
- **WHEN** point content is saved as draft
- **THEN** it MUST remain editable in the admin console
- **AND** it MUST NOT appear in student point detail content or video-library search results as published content.

#### Scenario: AI evidence exists for the same point
- **WHEN** manual-reviewed point evidence or source chunks exist for the same `(experiment_id, point_key)`
- **THEN** the point learning content MUST still come from the teacher-authored content table
- **AND** the backend MUST NOT auto-populate student page body copy from AI-generated chunk bindings.

### Requirement: Point media binding remains separate from point copy
The system SHALL keep video media assets and point learning content as separate but related resources.

#### Scenario: Teacher binds a video to a point
- **WHEN** a teacher binds an existing or newly uploaded video to a point
- **THEN** the media binding MUST reference the stable point key
- **AND** the point learning content MUST remain unchanged unless the teacher explicitly edits it.

#### Scenario: Video is replaced
- **WHEN** a point's video resource is replaced or removed
- **THEN** the point title, principle, phenomenon explanation, safety note, related links, and publication audit MUST remain intact.

#### Scenario: Point has no published video
- **WHEN** a point has published learning content but no published playable video
- **THEN** the student point detail API MUST represent video availability explicitly
- **AND** the frontend MUST render a controlled no-video state rather than failing.

### Requirement: Editable related experiment links
The system SHALL support related point links with same-experiment nearby points as defaults and manual edits for curated links.

#### Scenario: No manual related links exist
- **WHEN** a student opens a point with no manual related link configuration
- **THEN** the backend MUST provide default related links from nearby points in the same parent experiment where available
- **AND** it MUST only include active student-visible target points.

#### Scenario: Teacher adds a manual related link
- **WHEN** a teacher adds another experiment point as a related link
- **THEN** the backend MUST validate that the target experiment and target point resolve
- **AND** the student point detail page MUST include the curated link when both source and target are student-visible.

#### Scenario: Teacher hides or reorders a default link
- **WHEN** a teacher hides or reorders a default related link
- **THEN** the student point detail response MUST respect the manual override
- **AND** it MUST not reintroduce the hidden default link ahead of the curated order.

### Requirement: Student point detail content API
The backend SHALL expose published point learning content to the student H5 point detail page without using the search index as the display source.

#### Scenario: Published point content is requested
- **WHEN** an authenticated student requests a published experiment point detail
- **THEN** the response MUST include point identity, experiment context, playable video resources where available, principle, phenomenon explanation, safety note, related point links, question count, and assessment context
- **AND** the response MUST derive display body content from PostgreSQL point learning content, not from Elasticsearch.

#### Scenario: Point content is unpublished
- **WHEN** an authenticated student requests a point whose learning content is draft, archived, or missing
- **THEN** the backend MUST avoid exposing draft teacher-authored fields
- **AND** it MUST return a controlled unavailable or partial-content state that the frontend can render safely.

#### Scenario: Hidden experiment is requested
- **WHEN** the parent experiment is draft, archived, unavailable, or outside the student-visible scope
- **THEN** the backend MUST not expose the point content, videos, related links, or search target data.

### Requirement: Point content validation and audit
The system SHALL validate point content before publication and preserve edit and publication audit data.

#### Scenario: Required content is missing
- **WHEN** a teacher attempts to publish point content without a principle, phenomenon explanation, or safety note
- **THEN** the backend MUST reject publication with field-level validation errors
- **AND** the admin UI MUST show which fields block publication.

#### Scenario: Content is updated after publication
- **WHEN** a teacher edits already published point content
- **THEN** the system MUST preserve updated audit fields
- **AND** the search projection MUST be updated or queued for update after the edit is saved.

#### Scenario: Production resource validation runs
- **WHEN** production validation checks point learning content resources
- **THEN** it MUST validate point key resolution, publication consistency, and absence of unresolved related links
- **AND** it MUST not require AI evidence rows to exist before teacher-authored content can be published.

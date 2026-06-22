## ADDED Requirements

### Requirement: Catalog point bindings respond to archived media assets
The catalog tree service SHALL archive point video bindings that reference an archived media asset without deleting point content.

#### Scenario: Archived asset has active point bindings
- **WHEN** the catalog domain handles a `media_asset_archived` lifecycle event for a media asset with active point video bindings
- **THEN** it MUST archive every non-archived `experiment_catalog_point_media_bindings` row for that asset
- **AND** it MUST record archive reason metadata including the media asset id and lifecycle event id.

#### Scenario: Binding cleanup affects published points
- **WHEN** archived bindings belonged to published point placements
- **THEN** the affected points MUST remain published if their point content is still published
- **AND** their video readiness MUST be recomputed as missing unless another active ready video binding exists.

#### Scenario: Binding cleanup completes
- **WHEN** catalog point bindings are archived due to media asset archive
- **THEN** the service MUST queue or update derived search/evidence jobs for affected active point placements
- **AND** student detail reads MUST no longer expose the archived media asset for playback.

#### Scenario: Asset archive event is repeated
- **WHEN** the same media asset archive event is handled more than once
- **THEN** binding cleanup MUST be idempotent
- **AND** it MUST NOT create duplicate jobs or corrupt archived binding metadata.

## MODIFIED Requirements

### Requirement: Published point-node search documents
The system SHALL build student video-library search documents from published point nodes and their student-facing point knowledge.

#### Scenario: Published point is indexed
- **WHEN** a point node is published or its searchable content changes
- **THEN** the system MUST queue an ES document upsert keyed by point node id
- **AND** the document MUST include chapter path, ancestor directory category/path text, point title, principle, phenomenon explanation, safety note, student-facing related link text, extracted formulae, aliases, reaction features, and video readiness signals where available.
- **AND** the document MUST NOT include teacher-only notes, raw AI source chunks, `experiment_video_point_evidence` payloads, standalone directory-only documents, video resource titles, original file names, media asset ids, thumbnail paths, stream paths, or other video resource metadata.

#### Scenario: Point is unpublished or archived
- **WHEN** a point node becomes unpublished or archived
- **THEN** the system MUST queue deletion or disabling of its student search document.

#### Scenario: Directory text matches a search query
- **WHEN** a student searches for text that appears only in a published ancestor directory title or description
- **THEN** the search backend MUST return matching descendant published point documents
- **AND** it MUST NOT return the directory as an independent video-library result.

#### Scenario: Raw media asset exists
- **WHEN** a teacher uploads a media asset that is not bound to a published point node
- **THEN** the media asset MUST NOT appear in student video-library search.

#### Scenario: Bound video has a teacher-only title
- **WHEN** a published point has an active ready video binding whose media asset title or file name contains text absent from point content
- **THEN** that text MUST NOT be added to the student search document or searchable text
- **AND** search recall MUST depend on the point's authored learning content and catalog context instead.

### Requirement: Catalog card display is derived from authoritative content
The system SHALL treat student catalog card display as a read-model projection rather than teacher-authored card configuration.

#### Scenario: Directory card projection is needed
- **WHEN** a student catalog response needs to render a directory card
- **THEN** the read model MUST provide enough remaining metadata for title, hierarchy, child availability, and stable default visual treatment
- **AND** it MUST NOT depend on stored directory student-card copy, image, icon, accent, or layout fields.

#### Scenario: Point card projection is needed
- **WHEN** a student catalog response needs to render a point card
- **THEN** the read model MUST derive title from point/catalog title, derive optional summary from point learning content when available, and MAY derive visual media from the active ready bound video thumbnail
- **AND** it MUST NOT depend on stored point-card override fields.

#### Scenario: Search documents are built
- **WHEN** student search or video-library documents are built
- **THEN** searchable student-facing text MUST come from directory titles/path, point title, point learning content, and related experiment titles
- **AND** searchable text MUST NOT include removed manual student-card description, presentation fields, video resource titles, original file names, media asset titles, or other teacher-only video labels.

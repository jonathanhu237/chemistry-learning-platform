## ADDED Requirements

### Requirement: Media asset archive queues affected point jobs
Catalog point indexing SHALL respond to media asset archive events through controlled point jobs.

#### Scenario: Archived asset removes active bindings
- **WHEN** a media asset archive event archives active catalog point video bindings
- **THEN** ES sync jobs MUST be queued or updated for every affected active point placement
- **AND** each job MUST rebuild or delete the document according to the point's current publication and visibility state.

#### Scenario: Archived asset changes video readiness
- **WHEN** a published point loses its only active ready video because a media asset was archived
- **THEN** the point readiness model MUST show missing video
- **AND** ES/RAG diagnostics MUST treat the change as downstream consumption work rather than upload processing work.

#### Scenario: Archive event is retried
- **WHEN** a media asset archive event is retried after partial failure
- **THEN** point jobs MUST remain idempotent for equivalent placement/action payloads
- **AND** retry MUST NOT create duplicate active bindings or duplicate live ES documents.

### Requirement: ES rebuild can be destructive
Catalog point ES synchronization SHALL support destructive rebuild when index semantics or mapping purity changes.

#### Scenario: ES purity migration is applied
- **WHEN** the implementation removes video resource semantic fields from the ES mapping and document builders
- **THEN** operators MUST be able to delete and recreate the student video-library ES index
- **AND** rebuilt documents MUST come from PostgreSQL point facts rather than old ES sources.

#### Scenario: Rebuild fails for some documents
- **WHEN** a destructive ES rebuild cannot index all eligible point placement documents
- **THEN** failed rows MUST be recorded in index-state diagnostics
- **AND** stale video-resource semantic fields MUST NOT be accepted as a synced state.

## MODIFIED Requirements

### Requirement: RAG evidence refresh is asynchronous
The system SHALL refresh catalog-node evidence bindings through asynchronous jobs rather than blocking teacher saves.

#### Scenario: Point context changes
- **WHEN** point title, catalog path, normalized equations, phenomenon explanation, safety note, video readiness, or related point context changes
- **THEN** the system MUST mark catalog-node evidence as stale or enqueue a refresh according to configured trigger policy
- **AND** teacher save/publish actions MUST not wait for high-precision BGE rerank completion.
- **AND** evidence refresh queries MUST NOT use teacher-only video resource titles, media file names, or media asset metadata as point semantics.

#### Scenario: Evidence refresh runs
- **WHEN** a RAG evidence refresh job runs
- **THEN** it MUST generate retrieval queries from catalog node context
- **AND** it MUST use the configured RAG/BGE pipeline to select candidate source chunks
- **AND** output bindings MUST target catalog node id or stable catalog seed key, not legacy `(experiment_id, point_key)`.

#### Scenario: BGE service is unavailable
- **WHEN** the BGE service is disabled, unreachable, or too slow during evidence refresh
- **THEN** the job MUST fail or defer with a diagnostic reason
- **AND** the point MUST remain editable and dynamically RAG-consumable when runtime RAG later becomes healthy.

### Requirement: ES sync fans out by point placement
Catalog point ES synchronization SHALL enqueue and process work for each active point placement affected by canonical point content, placement state, directory context, video readiness, or related-point changes.

#### Scenario: Canonical point content changes
- **WHEN** student-searchable content changes for a canonical point
- **THEN** ES sync jobs MUST be queued for all active placements of that canonical point
- **AND** each job MUST build or delete the placement document according to publication and visibility state.

#### Scenario: Directory path changes
- **WHEN** a directory title, parent, order, chapter, or visibility state changes in a way that affects descendant catalog paths
- **THEN** ES sync jobs MUST be queued for affected descendant point placements
- **AND** the rebuilt documents MUST reflect the new catalog path and directory-derived recall context.

#### Scenario: Video readiness or related-point title changes
- **WHEN** video readiness, active binding presence, or related point titles change for a point placement
- **THEN** ES sync jobs MUST be queued for affected point placement documents
- **AND** the resulting search document MUST reflect current point readiness and related-text metadata without indexing video resource titles or video file metadata.

## ADDED Requirements

### Requirement: Media asset lifecycle events preserve domain boundaries
The backend SHALL connect media asset archive events to catalog binding cleanup without merging media upload ownership with catalog point ownership.

#### Scenario: Media asset archive is requested
- **WHEN** the media asset domain archives an asset
- **THEN** it MUST persist media lifecycle state and publish or enqueue a lifecycle event
- **AND** it MUST NOT directly contain catalog point binding business rules in upload, processing, file helper, or worker-safe modules.

#### Scenario: Catalog consumes archive event
- **WHEN** the catalog domain handles a media asset archived event
- **THEN** it MUST archive affected point video bindings and queue point projection work
- **AND** it MUST remain the owner of catalog binding semantics.

#### Scenario: Architecture validation runs
- **WHEN** backend architecture validation scans media upload and processing modules
- **THEN** imports from catalog point binding services into worker-safe media modules MUST fail or be explicitly rejected by tests
- **AND** event/outbox interfaces MAY be shared only through a narrow domain-safe boundary.

## MODIFIED Requirements

### Requirement: Media domain is split by responsibility
The backend SHALL split media behavior into separate owners for assets, asset lifecycle, bindings, processing queues, lifecycle cleanup, file helpers, and visibility rules.

#### Scenario: Video worker depends on processing-safe media modules
- **WHEN** the video worker imports media functionality
- **THEN** it MUST import only file helper, processing queue, asset persistence, or infrastructure modules needed for video processing
- **AND** it MUST NOT import media binding publication, experiment point content, student search projection, catalog point binding cleanup, or FastAPI router modules.

#### Scenario: Media binding changes publish domain events
- **WHEN** a media binding is created, published, unpublished, deleted, or archived for an experiment point
- **THEN** the owning binding domain MUST emit or call an explicit point search projection event
- **AND** it MUST NOT route the change through the video worker.

#### Scenario: Media asset lifecycle changes publish domain events
- **WHEN** a media asset is archived or restored
- **THEN** the media asset lifecycle owner MUST emit an explicit lifecycle event or outbox record
- **AND** downstream point binding cleanup MUST be handled by the catalog domain rather than upload or processing code.

#### Scenario: Teacher asset library stays separate from student search
- **WHEN** a media asset is uploaded but not attached to published point content through a student-visible binding
- **THEN** the asset MUST remain part of the teacher asset library only
- **AND** it MUST NOT appear as a student video-library search document.

### Requirement: Experiment point, student detail, and video-library projection are separate domains
The backend SHALL separate canonical experiment point facts, student point detail read models, media playback authorization, and video-library search projection documents.

#### Scenario: Student detail reads canonical PostgreSQL facts
- **WHEN** a student opens an experiment point detail page
- **THEN** the response MUST be built from PostgreSQL point facts and student-visible media resources
- **AND** it MUST NOT render body content from Elasticsearch hit sources or AI evidence chunks.

#### Scenario: Video-library search documents are projection records
- **WHEN** the video-library search index is rebuilt or synchronized
- **THEN** the document builder MUST use published point learning content, catalog path, related point text, chemistry fields, and non-semantic video readiness state as inputs
- **AND** it MUST treat Elasticsearch as a derived read model that can be rebuilt from PostgreSQL.
- **AND** it MUST NOT copy video resource titles, file names, media ids, stream paths, thumbnails, or upload metadata into searchable document fields or ES source.

#### Scenario: AI evidence remains assistant-owned
- **WHEN** assistant or question diagnostics consume `experiment_video_point_evidence` or `source_chunks`
- **THEN** those evidence flows MUST remain separate from student point display body content and video-library searchable body copy.

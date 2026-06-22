# backend-slim-domain-architecture Specification

## Purpose
TBD - created by archiving change backend-slim-domain-architecture. Update Purpose after archive.
## Requirements
### Requirement: Catalog preview routes preserve backend architecture gates
The backend SHALL keep catalog preview behavior compatible with the slim domain architecture and canonical route inventory.

#### Scenario: Preview domain creates a teacher-scoped token
- **WHEN** the teacher API asks the catalog preview domain to create a point preview token
- **THEN** the domain MUST receive only runtime-neutral teacher identity fields
- **AND** the domain MUST NOT import `server.app.auth`, FastAPI, API routers, or runtime app wiring.

#### Scenario: Preview routes are registered
- **WHEN** the FastAPI route inventory validation runs
- **THEN** teacher preview token, preview point detail, preview media stream, preview media thumbnail, admin thumbnail-stream, and video-library search diagnostics routes MUST appear in the canonical route inventory
- **AND** route inventory validation MUST report no untracked registered routes.

### Requirement: Backend has explicit slim layer ownership
The backend SHALL be organized into explicit runtime, API, domain, infrastructure, projection, worker, and script-support ownership boundaries.

#### Scenario: Backend package layout exposes ownership
- **WHEN** the backend slim refactor is complete
- **THEN** runtime app wiring MUST live in a dedicated runtime owner
- **AND** HTTP routers MUST live under API owners grouped by admin, student, auth, or equivalent public surface
- **AND** reusable business logic MUST live under domain owners
- **AND** database, file, settings, and external-service clients MUST live under infrastructure owners
- **AND** worker entrypoints MUST live under worker owners.

#### Scenario: Mixed top-level modules are retired
- **WHEN** the backend slim refactor is complete
- **THEN** mixed-purpose top-level modules that combine API, domain, worker, and projection responsibilities MUST be deleted or moved into a single explicit owner
- **AND** no deleted top-level module MAY remain as a compatibility wrapper.

### Requirement: Domain modules are FastAPI-free
Reusable backend domain modules SHALL NOT import FastAPI, Starlette response classes, routers, or HTTP exception classes.

#### Scenario: Domain module import validation runs
- **WHEN** architecture validation scans reusable domain modules
- **THEN** imports from `fastapi`, `starlette.responses`, `server.app.api`, `server.app.routers`, and runtime app wiring MUST fail validation.

#### Scenario: Routers translate domain errors
- **WHEN** a domain operation fails because of validation, missing resources, authorization state, or conflict state
- **THEN** the domain module MUST return a domain result or raise a domain exception
- **AND** the API router MUST translate that outcome into the HTTP status and response payload.

### Requirement: Worker and CLI imports are web-runtime safe
Worker and CLI entrypoints SHALL depend only on infrastructure, domain, and explicit script-support modules that are safe outside the FastAPI runtime.

#### Scenario: Worker imports are validated
- **WHEN** architecture validation scans backend worker entrypoints
- **THEN** worker modules MUST NOT import FastAPI, API routers, runtime app wiring, or broad web-only services.

#### Scenario: CLI imports are validated
- **WHEN** maintenance scripts import backend code for migrations, validation, search rebuilds, media cleanup, or diagnostics
- **THEN** those imports MUST resolve through infrastructure, domain, or script-support modules
- **AND** they MUST NOT initialize the FastAPI application as an import side effect.

### Requirement: Destructive compatibility cleanup is intentional
The backend slim refactor SHALL remove old compatibility modules, compatibility barrels, and route aliases that exist only to preserve prior internal structure.

#### Scenario: Legacy import path is removed
- **WHEN** a backend module is moved into its final slim owner
- **THEN** the previous module path MUST NOT remain as a wrapper that re-exports the new implementation
- **AND** all canonical imports in backend code, scripts, and tests MUST be updated to the new owner.

#### Scenario: Removed compatibility is documented
- **WHEN** a compatibility route, module, or import path is removed
- **THEN** the implementation notes or route inventory MUST record what was removed and which canonical owner replaces it.

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

### Requirement: Backend route inventory is canonical
The backend SHALL maintain a canonical route inventory for admin, student, auth, and runtime endpoints after destructive route cleanup.

#### Scenario: Route table matches inventory
- **WHEN** the FastAPI app route table is inspected in tests
- **THEN** every canonical path and method pair in the route inventory MUST be registered exactly once
- **AND** removed legacy aliases MUST NOT be registered.

#### Scenario: Frontend calls use canonical routes
- **WHEN** admin and student frontend API calls are inspected or exercised by e2e tests
- **THEN** they MUST call canonical backend routes from the updated route inventory
- **AND** they MUST NOT depend on removed backend aliases.

### Requirement: Architecture validation is committed
The repository SHALL include committed architecture validation that enforces backend slim dependency direction.

#### Scenario: Validation fails on disallowed import
- **WHEN** a module under a domain owner imports API routers, FastAPI, runtime app wiring, or worker entrypoints
- **THEN** the architecture validation command MUST fail and identify the violating file and import.

#### Scenario: Validation is part of backend quality gates
- **WHEN** the backend slim implementation is complete
- **THEN** the architecture validation command MUST be documented
- **AND** it MUST run as part of the backend verification sequence for this change.

### Requirement: Backend slim documentation is updated
The backend SHALL document final module ownership, route ownership, entrypoints, import rules, and removed compatibility layers.

#### Scenario: Backend ownership map is available
- **WHEN** the refactor is complete
- **THEN** repository documentation MUST identify the owner for each backend domain, API surface, worker, and script-support module.

#### Scenario: Removed compatibility is discoverable
- **WHEN** a developer needs to update old code after the refactor
- **THEN** documentation MUST list removed compatibility paths and their canonical replacements or deletion rationale.

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

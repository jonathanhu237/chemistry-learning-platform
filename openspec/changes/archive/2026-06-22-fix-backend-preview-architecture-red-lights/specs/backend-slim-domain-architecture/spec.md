## ADDED Requirements

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

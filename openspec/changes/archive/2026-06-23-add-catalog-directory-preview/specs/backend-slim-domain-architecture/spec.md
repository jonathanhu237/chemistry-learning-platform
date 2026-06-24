## MODIFIED Requirements

### Requirement: Catalog preview routes preserve backend architecture gates
The backend SHALL keep catalog preview behavior compatible with the slim domain architecture and canonical route inventory.

#### Scenario: Preview domain creates a teacher-scoped token
- **WHEN** the teacher API asks the catalog preview domain to create a catalog node preview token
- **THEN** the domain MUST receive only runtime-neutral teacher identity fields
- **AND** the domain MUST verify that the selected node is a supported preview node kind
- **AND** the token MUST be scoped to the selected point or selected directory subtree
- **AND** the domain MUST NOT import `server.app.auth`, FastAPI, API routers, or runtime app wiring.

#### Scenario: Directory preview read is scoped to subtree
- **WHEN** a preview request uses a directory-scoped token
- **THEN** the backend MUST allow reads for the selected directory and its descendant nodes only
- **AND** it MUST reject sibling nodes, unrelated nodes, and non-preview endpoints
- **AND** it MUST keep normal student authorization unchanged for normal student APIs.

#### Scenario: Point preview read is scoped to point
- **WHEN** a preview request uses a point-scoped token
- **THEN** the backend MUST allow reads for that selected point detail and its previewable media only
- **AND** it MUST reject any other catalog node or media outside that point scope.

#### Scenario: Preview routes are registered
- **WHEN** the FastAPI route inventory validation runs
- **THEN** teacher catalog node preview token, preview catalog node read, preview point detail compatibility, preview media stream, preview media thumbnail, admin thumbnail-stream, and video-library search diagnostics routes MUST appear in the canonical route inventory
- **AND** route inventory validation MUST report no untracked registered routes.

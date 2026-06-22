## MODIFIED Requirements

### Requirement: Protected Core Resource Manifest

The platform SHALL define a versioned manifest for every current core resource required to rebuild or validate the production baseline.

#### Scenario: Current resources are registered
- **GIVEN** the production-readiness manifest is generated or checked
- **WHEN** it lists protected core resources
- **THEN** it includes formal experiments, stable experiment video points, published point learning content resources when present, point related-link resources when present, the knowledge framework, the current point inventory, the current point-aware question bank, the question-bank schema, canonical chunks, canonical embeddings, manually reviewed point evidence, and current import reports
- **AND** each entry records semantic role, path or source location, required status, item count where applicable, byte size, and SHA256 where applicable.

#### Scenario: Evidence file is under a historical path
- **GIVEN** a protected resource lives under an artifact path with `video` or review wording in the directory name
- **WHEN** cleanup classification runs
- **THEN** the final manually reviewed point evidence file remains classified as protected core data
- **AND** it is not deleted or overwritten by legacy artifact cleanup.

#### Scenario: Point content and point evidence both exist
- **GIVEN** protected teacher-authored point learning content and protected manual-reviewed point evidence resources both exist
- **WHEN** production validation classifies resources
- **THEN** it MUST classify them as separate protected resources with different semantic roles
- **AND** it MUST NOT treat one as a replacement for the other.

### Requirement: Production Operations Baseline

Production hardening SHALL document and validate the operational basics needed for maintainable deployment.

#### Scenario: Migration numbering continues
- **GIVEN** a new database migration is added after this productionization work begins
- **WHEN** the migration is named
- **THEN** it follows the next unambiguous migration number
- **AND** duplicate migration numbers are not introduced.

#### Scenario: Deployment configuration is reviewed
- **GIVEN** a maintainer prepares a deployment or local production-like run
- **WHEN** they inspect repository documentation and examples
- **THEN** they can find environment variable examples, Docker service expectations, health checks, backup/restore notes, and validation commands.

#### Scenario: Search service configuration is reviewed
- **GIVEN** a maintainer prepares a deployment or local production-like run that includes student video-library search
- **WHEN** they inspect repository documentation and examples
- **THEN** they MUST find the Elasticsearch/IK service expectation, index bootstrap process, analyzer requirements, environment variables, health checks, and rebuild command
- **AND** production readiness validation MUST fail if the required ES/IK search service is missing or unhealthy.

### Requirement: Production-like application stack deployment contract

The platform SHALL treat the Docker Compose application as one production-like multi-service stack rather than as independently optional frontend, backend, database, and search processes.

#### Scenario: Standard Compose stack starts
- **GIVEN** a maintainer has built the admin and student frontend assets and prepared `.env`
- **WHEN** they run the standard production-like Compose startup command
- **THEN** the stack MUST start the required default services `postgres`, `elasticsearch`, `backend`, `tusd`, and `video-worker` under the same Compose project
- **AND** `backend` MUST depend on healthy PostgreSQL and Elasticsearch/IK services before it is considered ready
- **AND** student and admin production-style pages MUST be served by the backend at `/` and `/admin` rather than by Vite development servers.

#### Scenario: Required service image is not buildable or pullable
- **GIVEN** a required default Compose service uses a Docker image or Dockerfile
- **WHEN** the standard Compose stack is built or started
- **THEN** every required service image MUST be buildable or pullable from its declared source
- **AND** an Elasticsearch replacement image MUST prove IK analyzer support, including the `ik_max_word` tokenizer, before the stack can pass readiness.

#### Scenario: Host Postgres port is fixed for the Compose stack
- **GIVEN** a developer machine may already use the common local Postgres host port `5432`
- **WHEN** the production-like Compose stack starts
- **THEN** container-to-container service discovery MUST still use stable Compose network names such as `postgres:5432` and `elasticsearch:9200`
- **AND** the PostgreSQL host binding MUST default to `127.0.0.1:15432`
- **AND** local deployment scripts and host-side validation defaults MUST connect to Postgres on `127.0.0.1:15432`.

#### Scenario: Compose stack smoke validation runs
- **WHEN** production readiness validation is asked to validate the real Compose application stack
- **THEN** it MUST start or verify the required Compose services, verify backend health, verify PostgreSQL reachability, verify Elasticsearch cluster health, and verify IK analyzer behavior through an Elasticsearch analyzer request
- **AND** it MUST apply migrations and rebuild or validate the student video-library search index with production fallback disabled
- **AND** it MUST fail if any required default service is missing, unhealthy, misconfigured, or silently replaced by deterministic local search fallback.

#### Scenario: Local development rebuilds are service scoped
- **GIVEN** a developer changes code or configuration owned by one Compose service
- **WHEN** they update the local Docker Compose runtime during ordinary development
- **THEN** documentation and examples MUST direct them to rebuild and recreate only the affected service or services, such as `docker compose up -d --build backend`, `docker compose up -d --build web-teacher`, `docker compose up -d --build web-student`, `docker compose up -d --build web-admin`, `docker compose up -d --build video-worker`, or `docker compose --profile rag up -d --build bge-rag`
- **AND** full-stack image rebuilds MUST be reserved for initial setup, shared base-image or Compose-topology changes, multi-service dependency changes, release smoke checks, or explicitly requested full validation
- **AND** Docker build cache deletion commands, no-cache rebuilds, and system-wide prune commands MUST NOT be part of routine development startup; they may be used only as documented recovery steps for cache corruption or disk pressure after service-scoped restart or rebuild has been tried.

#### Scenario: Development servers are used
- **WHEN** a developer runs Vite development servers for local UI work
- **THEN** `5173` MUST remain the student H5 development server and `5174` MUST remain the admin development server
- **AND** this development split MUST NOT be treated as a substitute for the production-like Compose stack validation.

#### Scenario: Optional RAG profile is enabled
- **WHEN** the `rag` Compose profile is enabled
- **THEN** the BGE/RAG service MUST be treated as an additional runtime dependency for RAG-backed workflows
- **AND** the default application stack and video-library search readiness MUST remain independently valid without confusing optional RAG health with required ES/IK search health.

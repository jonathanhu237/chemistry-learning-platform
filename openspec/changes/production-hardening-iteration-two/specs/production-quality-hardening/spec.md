## ADDED Requirements

### Requirement: Frontend Build Output Is Classified And Budgeted
The admin frontend SHALL classify heavyweight production build output into named route or vendor chunks, and MUST keep large chunks intentional, documented, and verifiable.

#### Scenario: Build output uses named chunks
- **WHEN** the frontend production build is run
- **THEN** heavyweight dependencies such as React, Ant Design, charts, markdown/math rendering, upload/tus utilities, and feature-only pages are emitted as named route or vendor chunks rather than being hidden inside an oversized anonymous main bundle

#### Scenario: Build warnings are actionable
- **WHEN** Vite reports a chunk-size warning
- **THEN** the warning corresponds to a documented named vendor or route chunk with a known owner, or the build configuration/tasks fail the hardening acceptance check until the chunk is split or justified

#### Scenario: Lazy-loaded features keep behavior
- **WHEN** an admin navigates to a lazy-loaded page such as learning assistant, question bank, analytics, videos, or upload workflows
- **THEN** the route loads the same feature behavior and data as before, with only an acceptable loading state added at the route boundary

### Requirement: FastAPI Apps Use Lifespan Startup
The backend FastAPI applications SHALL use lifespan startup/shutdown hooks instead of deprecated `on_event` handlers while preserving existing startup behavior.

#### Scenario: Admin service startup behavior is preserved
- **WHEN** the admin service starts
- **THEN** it performs the configured database startup check, ensures the media root exists, registers the same routers/static admin routes, and returns the same `/health` response as before

#### Scenario: BGE service warmup behavior is preserved
- **WHEN** the BGE service starts with warmup enabled
- **THEN** it triggers the same background warmup flow and exposes equivalent warmup status through `/health` and `/metrics`

#### Scenario: Deprecation warnings are removed
- **WHEN** backend tests or import smoke checks exercise the FastAPI app modules
- **THEN** FastAPI `on_event` deprecation warnings are not emitted by project startup code

### Requirement: Media Cleanup Preserves Database And UI Consistency
The system SHALL manage local media cleanup as a database/file lifecycle operation and MUST NOT delete media files independently from related media records and bindings.

#### Scenario: Cleanup dry run reports dependencies
- **WHEN** a media cleanup dry run is executed
- **THEN** it reports candidate files, matching `media_assets`, related `media_bindings`, derived files, processing rows, review rows, byte impact, and the action that would be taken

#### Scenario: Destructive cleanup refuses unsafe state
- **WHEN** destructive media cleanup is requested for files that still have active database references without an archive or tombstone plan
- **THEN** the cleanup command refuses to delete those files and explains the blocking records

#### Scenario: Archived media has intentional admin behavior
- **WHEN** a media asset is archived, removed, or otherwise made unavailable by the lifecycle flow
- **THEN** admin APIs and UI surfaces expose an intentional archived/missing state rather than returning broken playback or thumbnail paths as if the file still existed

### Requirement: Production Validation Is CI Ready
The repository SHALL provide a CI-ready validation chain that matches local production-readiness checks.

#### Scenario: Local validation targets the active hardening change
- **WHEN** the production-readiness validation script is run without an explicit change override during this pass
- **THEN** it validates the current hardening OpenSpec change, protected resource manifest, backend import smoke, backend tests, frontend typecheck, frontend tests, and frontend build

#### Scenario: CI runs the same quality gates
- **WHEN** a remote branch or pull request runs CI
- **THEN** CI executes the same required quality gates or invokes the same validation script with documented skip/install options for environment-specific steps

#### Scenario: Validation failures stop the pipeline
- **WHEN** any required validation stage fails
- **THEN** the script or CI job exits non-zero and reports the failing stage clearly

### Requirement: Assistant Runtime Refactor Preserves Semantics
The learning-assistant backend SHALL split the remaining large assistant runtime module by stable responsibility while preserving existing request/response contracts and evidence semantics.

#### Scenario: Assistant module responsibilities are separated
- **WHEN** `server/app/agent.py` is refactored
- **THEN** runtime orchestration, RAG retrieval/reranking, prompt/context construction, output normalization, and evidence/citation shaping are moved into focused modules or services with clear ownership

#### Scenario: Existing assistant behavior remains equivalent
- **WHEN** existing assistant tests and smoke scenarios run after the refactor
- **THEN** response shapes, guardrails, retrieved evidence semantics, and debug/runtime metadata remain equivalent for the same inputs

#### Scenario: Refactor does not change public API contracts
- **WHEN** clients call existing learning-assistant endpoints after the refactor
- **THEN** endpoint paths, authentication/authorization behavior, request fields, and response fields remain compatible with the pre-refactor implementation

### Requirement: Migration Discipline Continues From Current History
Database migration work in this pass SHALL preserve historical migration files and MUST continue numbering from the next unused migration identifier.

#### Scenario: New migrations do not rewrite history
- **WHEN** this hardening pass needs a database change
- **THEN** it adds a new migration starting from `014_...` or later and does not rename, edit, remove, or reorder existing applied migration files

#### Scenario: Migration policy is documented
- **WHEN** production operations documentation is updated
- **THEN** it states that the duplicate historical `010_...` migration names are retained for compatibility and that future migrations continue from `014_...`

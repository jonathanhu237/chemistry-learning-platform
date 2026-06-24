# production-readiness-governance Specification

## Purpose
TBD - created by archiving change productionize-admin-platform. Update Purpose after archive.
## Requirements
### Requirement: Protected Core Resource Manifest

The platform SHALL define a versioned manifest for every current core resource required to rebuild or validate the production baseline.

#### Scenario: Current resources are registered
- **GIVEN** the production-readiness manifest is generated or checked
- **WHEN** it lists protected core resources after the catalog outline seed replacement
- **THEN** it MUST include the canonical structured experiment catalog seed, the 30 mapped point-content example seed, the knowledge framework, canonical chunks, canonical embeddings, ES analyzer dictionaries, and current import/validation reports
- **AND** each entry MUST record semantic role, path or source location, required status, item count where applicable, byte size, and SHA256 where applicable.

#### Scenario: Retired resources are encountered
- **GIVEN** old point inventory files, old point-aware question-bank seed files, old manually reviewed point evidence files, or old video-point evidence artifacts remain under historical paths
- **WHEN** cleanup classification or production validation runs
- **THEN** those retired resources MUST NOT be classified as protected current core data
- **AND** they MAY be archived or removed according to cleanup policy after the new protected resources validate.

#### Scenario: Canonical retrieval corpus is encountered
- **GIVEN** canonical chunks and chunk embeddings remain under current production resource paths
- **WHEN** cleanup classification or production validation runs
- **THEN** those corpus resources MUST remain classified as protected current core data
- **AND** they MUST NOT be deleted merely because old point evidence bindings are retired.

### Requirement: Destructive Cleanup Guard

Cleanup tooling SHALL refuse to delete or move historical artifacts when protected current resources cannot be validated.

#### Scenario: Protected resource is missing
- **GIVEN** a cleanup command is requested
- **WHEN** any required protected resource is missing, has an unexpected count, or has a mismatched checksum
- **THEN** the cleanup command fails before deleting files
- **AND** the failure output identifies the invalid resource

#### Scenario: Legacy artifacts are removable
- **GIVEN** protected resources pass validation
- **WHEN** cleanup runs in apply mode
- **THEN** it may remove or archive historical audit packets, obsolete generated packages, temporary video/rerank outputs, screenshots, caches, frontend builds, dependency directories, and logs
- **AND** it preserves every manifest-listed protected resource

#### Scenario: Media files are removed
- **GIVEN** `data/media` cleanup is requested
- **WHEN** the database still contains media asset records that point to those files
- **THEN** cleanup requires an explicit database/UI consistency plan
- **AND** it does not leave the admin UI with records for missing local files

### Requirement: Stable Resource Defaults

Import and validation scripts SHALL use stable production resource paths by default instead of relying on deep historical artifact paths.

#### Scenario: Import script runs without overrides
- **GIVEN** a maintainer runs a current import or validation script with default options
- **WHEN** the script resolves core resource inputs
- **THEN** it reads from the stable production seed/resource locations or the manifest-declared external resource locations
- **AND** it does not require knowledge of historical review packet paths

#### Scenario: Maintenance override is needed
- **GIVEN** a maintainer needs to inspect or compare an old artifact
- **WHEN** the script is run with an explicit override path
- **THEN** the override is accepted for that run
- **AND** the protected production defaults remain unchanged

### Requirement: Behavior-Preserving Refactor Stages

Frontend and backend modularization SHALL preserve current behavior unless a separate feature spec changes it.

#### Scenario: Frontend console modules are split
- **GIVEN** `App.tsx` and shared styles are split into routes, features, components, API clients, and scoped styles
- **WHEN** the `web-teacher` or `web-admin` frontend is built and tested
- **THEN** existing routes, visible workflows, permissions, data loading behavior, and user-facing states remain equivalent
- **AND** heavy optional modules are lazy-loaded where page boundaries allow

#### Scenario: Backend admin routers are split
- **GIVEN** `experiment_admin.py` is split into routers and services
- **WHEN** existing admin endpoints are exercised
- **THEN** endpoint paths, request schemas, response schemas, permissions, and database effects remain equivalent
- **AND** any intentional contract change is deferred to a separate OpenSpec change

### Requirement: Production Validation Chain

The repository SHALL provide a documented validation chain that proves the production baseline can be built, tested, and data-validated.

#### Scenario: Maintainer validates the baseline
- **GIVEN** a maintainer runs the production-readiness validation command or documented command set
- **WHEN** validation completes after the catalog outline seed replacement
- **THEN** it MUST check OpenSpec strict validation, protected resource manifests, catalog seed counts, 30-example content mapping, backend tests, frontend typecheck, frontend tests, frontend build, and core data counts
- **AND** it MUST report failures with enough detail to identify the broken stage.

#### Scenario: Fresh rebuild is verified
- **GIVEN** an empty database and the declared production resources are available
- **WHEN** the documented restore/import path is executed
- **THEN** the platform MUST recreate the current chapter-scoped experiment catalog tree from the structured seed
- **AND** it MUST recreate the 30 mapped point-content examples
- **AND** it MUST preserve or import canonical chunks and embeddings
- **AND** it MUST leave the retired experiment question bank and retired point evidence bindings empty or absent.

#### Scenario: Legacy protected counts are checked
- **GIVEN** validation code still contains old expected counts for 300 video points, 77 question banks, 2,310 questions, or 300 point evidence bindings
- **WHEN** the production-readiness validation command runs
- **THEN** validation MUST fail until those old protected counts are removed or replaced by catalog-outline seed expectations
- **AND** the failure MUST identify the outdated baseline expectation.

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
- **THEN** they can find environment variable examples, Docker service expectations, health checks, backup/restore notes, validation commands, and default ports for `web-admin`, `web-teacher`, and `web-student`.

### Requirement: Retired seed documentation
Production operations documentation SHALL explain the intentional retirement of legacy experiment seed resources.

#### Scenario: Maintainer reads production seed documentation
- **WHEN** a maintainer reads the seed or production operations documentation after this change
- **THEN** the documentation MUST state that old question-bank seeds, old video point inventory, old video references, and old point evidence bindings are invalid for the current catalog baseline
- **AND** it MUST state that canonical chunks and embeddings remain valid retrieval corpus resources.

#### Scenario: Maintainer looks for question-bank regeneration instructions
- **WHEN** a maintainer searches the documentation for the new question-bank baseline
- **THEN** the documentation MUST state that the current bank is empty until fresh catalog-node evidence and a future generation workflow create a replacement
- **AND** it MUST NOT instruct maintainers to import the retired 2,310-question bank as a current baseline.

### Requirement: Release governance distinguishes API and frontend origins
Production readiness governance SHALL distinguish backend API origin, student frontend origin, teacher frontend origin, and platform operations frontend origin.

#### Scenario: Environment variables are configured
- **WHEN** local or production-like validation configures service origins
- **THEN** backend API origin, student frontend origin, teacher frontend origin, and platform operations frontend origin MUST be configurable independently
- **AND** validation output MUST make clear which origin was tested.

#### Scenario: Full e2e validation runs
- **WHEN** full e2e validation runs after this split
- **THEN** teacher-console and platform-console e2e MUST use their configured frontend origins
- **AND** student mobile QA MUST use the student frontend origin
- **AND** backend health/API readiness MUST use the backend origin.

### Requirement: Deployment docs describe split service ownership
Production readiness governance SHALL document that backend, `web-student`, `web-teacher`, and `web-admin` are separate default services.

#### Scenario: Production operations docs are read
- **WHEN** an operator reads the deployment instructions
- **THEN** the docs MUST state that backend no longer serves the frontends
- **AND** the docs MUST explain how to start and validate the separate frontend services.

### Requirement: Production validation enforces ES point-content purity
Production readiness validation SHALL verify that the student video-library Elasticsearch index contains only published point semantics and allowed readiness signals.

#### Scenario: ES purity validation runs
- **WHEN** the production-readiness validation command or video-library search validator runs after this change
- **THEN** it MUST inspect generated or indexed student video-library documents for forbidden video resource fields
- **AND** validation MUST fail if documents contain video resource titles, original file names, media asset ids, stream paths, thumbnail paths, upload status, processing status, duplicate-candidate data, or media metadata in searchable text or ES source.

#### Scenario: Bound video title appears only in media tables
- **WHEN** a media asset title or binding title exists in PostgreSQL but is absent from point content
- **THEN** validation MUST confirm that title does not appear in ES `search_text`, student search snippets, or local fallback searchable text
- **AND** matching only that title MUST NOT recall the point in search validation.

#### Scenario: Video readiness signals are present
- **WHEN** an indexed published point has an active ready video binding
- **THEN** validation MAY accept `has_video` and `video_count`
- **AND** `video_count` MUST be either `0` or `1`
- **AND** those fields MUST NOT contain media labels, ids, file names, or paths.

### Requirement: Destructive ES rebuild is part of the migration gate
Production readiness governance SHALL require a controlled ES rebuild when index semantics or mapping purity changes.

#### Scenario: Mapping purity changes
- **WHEN** this change is applied in a production-like environment
- **THEN** the documented migration path MUST recreate or fully rebuild the student video-library ES index
- **AND** local fallback MUST NOT hide stale production ES documents that still contain forbidden video resource data.

#### Scenario: Rebuild command completes
- **WHEN** the rebuild command finishes
- **THEN** validation MUST compare eligible published placement counts, indexed document counts, and sync-state rows
- **AND** any failed or pending rows MUST be reported before the change is considered production-ready.

#### Scenario: Rollback is needed
- **WHEN** operators roll back after a destructive ES rebuild
- **THEN** the rollback plan MUST describe rebuilding ES from PostgreSQL again
- **AND** it MUST not rely on old ES `_source` documents as authoritative backups.

### Requirement: Media archive migration is database-consistency aware
Production readiness governance SHALL treat media asset archive state as part of database/UI consistency for local media cleanup.

#### Scenario: Media cleanup deletes DB-backed files
- **WHEN** cleanup is asked to delete DB-backed media asset files
- **THEN** cleanup MUST require an archived or tombstoned asset state
- **AND** it MUST refuse to delete files for active media assets.

#### Scenario: Archive migration is applied destructively
- **WHEN** a destructive database rebuild or migration is used to introduce media lifecycle state
- **THEN** validation MUST document which media records, bindings, lifecycle events, and derived ES states were reset or rebuilt
- **AND** protected seed resources, users, roles, analyzer dictionaries, and canonical retrieval corpus resources MUST remain protected.

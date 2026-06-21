## ADDED Requirements

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

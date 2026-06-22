## ADDED Requirements

### Requirement: Media assets have an explicit lifecycle
The system SHALL track media asset lifecycle separately from upload and processing status.

#### Scenario: Existing media asset is read
- **WHEN** a media asset has no explicit lifecycle value after migration
- **THEN** the system MUST treat it as active
- **AND** its existing `upload_status` MUST continue to represent only upload or processing state.

#### Scenario: Media asset is archived
- **WHEN** an authorized teacher or operator archives a media asset
- **THEN** the system MUST mark the asset lifecycle as archived
- **AND** it MUST record actor, timestamp, reason, and archive metadata without changing point content records.

#### Scenario: Archived asset is listed
- **WHEN** the default teacher asset library or catalog video picker lists media assets
- **THEN** archived assets MUST be hidden by default
- **AND** an audit or maintenance view MAY expose archived assets only as unavailable records.

### Requirement: Media asset archive has an impact plan
The system SHALL provide an archive impact plan before a teacher can archive a media asset from the video resource library.

#### Scenario: Asset has catalog point bindings
- **WHEN** the archive plan is requested for an asset with active catalog point video bindings
- **THEN** the response MUST include the affected binding count, placement node ids, canonical point ids, point titles, catalog paths, and publication/readiness state
- **AND** it MUST state that point content remains but video bindings will be removed.

#### Scenario: Asset has no active bindings
- **WHEN** the archive plan is requested for an asset with no active catalog point video bindings
- **THEN** the response MUST say the asset can be archived without changing point video bindings
- **AND** it MUST still report processing jobs, renditions, duplicate candidates, and file-state summary for audit.

#### Scenario: Legacy generic media bindings exist
- **WHEN** the archive plan sees generic `media_bindings` rows for the asset
- **THEN** the response MUST report them separately from catalog point video bindings
- **AND** generic binding counts MUST NOT be used as the only source of catalog point impact.

### Requirement: Media asset archive emits lifecycle events
The system SHALL record a media asset lifecycle event whenever an asset is archived.

#### Scenario: Archive command succeeds
- **WHEN** a media asset archive command is committed
- **THEN** the system MUST create an auditable `media_asset_archived` event or equivalent outbox record
- **AND** the event MUST include media asset id, actor, reason, previous lifecycle state, and affected binding summary.

#### Scenario: Event handler is retryable
- **WHEN** a lifecycle event cannot be fully consumed by downstream domains
- **THEN** the system MUST leave enough event or job state to retry catalog binding cleanup
- **AND** diagnostics MUST expose the failure without reactivating the media asset.

#### Scenario: Video worker imports media modules
- **WHEN** the video worker imports media functionality
- **THEN** archive event handling MUST NOT require importing catalog point binding services into worker-safe upload or processing modules.

### Requirement: Archived media is unavailable to student playback
Archived media assets SHALL be treated as unavailable for student and preview playback.

#### Scenario: Student requests archived media
- **WHEN** a student media stream or thumbnail request targets an archived media asset
- **THEN** the backend MUST reject the request as unavailable or not found
- **AND** it MUST NOT serve the archived file even if the local file still exists.

#### Scenario: Teacher previews archived media
- **WHEN** a teacher opens an archived media asset from an audit view
- **THEN** the UI MUST make the archived state explicit
- **AND** it MUST NOT imply the asset can still be selected for a point.

### Requirement: Physical file deletion follows archive policy
The system SHALL keep physical media file deletion separate from teacher asset archive.

#### Scenario: Teacher archives an asset
- **WHEN** archive confirmation succeeds
- **THEN** the system MUST NOT synchronously delete source, playback, thumbnail, rendition, or fingerprint files
- **AND** the asset record MUST retain enough paths for later maintenance cleanup or audit.

#### Scenario: Maintenance cleanup deletes files
- **WHEN** a maintenance command deletes files for archived assets
- **THEN** it MUST verify the asset is archived or otherwise tombstoned
- **AND** it MUST avoid deleting active DB-backed media files.

### Requirement: Destructive lifecycle rebuild is allowed
The system SHALL allow a controlled destructive database rebuild for media lifecycle structures when this change is applied.

#### Scenario: Fresh database is built
- **WHEN** migrations run on a fresh database
- **THEN** media asset lifecycle fields and lifecycle event storage MUST exist in the baseline schema
- **AND** existing upload, processing, rendition, fingerprint, and duplicate-candidate tables MUST remain consistent.

#### Scenario: Existing database is upgraded destructively
- **WHEN** operators choose the destructive rebuild path for this change
- **THEN** the migration or maintenance sequence MAY reset derived lifecycle/index state
- **AND** it MUST preserve or explicitly document the handling of `media_assets`, local media files, users, roles, and protected seed resources.

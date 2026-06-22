## ADDED Requirements

### Requirement: Catalog point video binding is a single active reference
The catalog tree service SHALL model a point's experiment video as at most one active media binding per canonical point.

#### Scenario: Teacher binds a video to a point
- **WHEN** a teacher binds an eligible media asset to a catalog point
- **THEN** the service MUST make that media asset the only active non-archived video binding for the point's canonical point identity
- **AND** any previous active video bindings for that canonical point MUST be archived or otherwise made inactive in the same transaction.

#### Scenario: Teacher replaces a point video
- **WHEN** a teacher selects a different media asset for a point that already has an active video binding
- **THEN** the new media asset MUST replace the previous active binding
- **AND** subsequent point detail reads MUST return only the replacement video as the current point video.

#### Scenario: Teacher binds the existing current video again
- **WHEN** a teacher binds the same media asset that is already active for the point
- **THEN** the service MUST keep a single active binding
- **AND** it MUST update safe binding metadata without creating duplicate active rows.

#### Scenario: Existing data contains multiple active bindings
- **WHEN** the migration for this change runs on data with multiple non-archived video bindings for one canonical point
- **THEN** the migration MUST keep one deterministic active binding per canonical point
- **AND** it MUST archive all other active bindings for that canonical point.

### Requirement: Catalog point video binding has no teacher-facing publish state
The catalog tree service SHALL stop treating point video bindings as independently published authoring objects.

#### Scenario: New video binding is created
- **WHEN** a teacher binds a media asset to a point
- **THEN** the request MUST NOT require a binding-level `draft` or `published` choice
- **AND** the resulting binding MUST be active unless it is explicitly removed.

#### Scenario: Stale client sends binding status
- **WHEN** a stale client sends `status`, `binding_status`, `published_by`, or `published_at` for a catalog point video binding
- **THEN** the service MUST ignore, strip, or reject those values according to the API compatibility policy
- **AND** stale status values MUST NOT create a hidden draft binding that prevents a ready video from appearing to students.

#### Scenario: Teacher removes a video binding
- **WHEN** a teacher removes the current point video
- **THEN** the service MUST archive or delete the active binding
- **AND** subsequent point detail reads MUST show no current video for that point.

#### Scenario: Video asset is not ready
- **WHEN** the active binding points at a media asset whose upload or processing status is not ready
- **THEN** teacher detail MAY show the binding with a processing/unready state
- **AND** student-facing reads MUST NOT expose a playable video until the asset is ready.

### Requirement: Video readiness counts reflect active ready bindings
Catalog tree node summaries SHALL report video readiness from active non-archived bindings and ready media assets rather than binding publication state.

#### Scenario: Point has an active ready video
- **WHEN** a catalog point has one active non-archived binding to a ready media asset
- **THEN** node summaries and validation MUST count the point as having a student-visible video
- **AND** they MUST NOT require `binding_status = published`.

#### Scenario: Point has only archived or unready videos
- **WHEN** a catalog point has no active binding to a ready media asset
- **THEN** node summaries and validation MUST count the point as missing a student-visible video
- **AND** status labels MUST remain accurate for teacher repair workflows.

## ADDED Requirements

### Requirement: Teacher can archive stored video resources
The teacher video resource library SHALL provide an explicit archive/delete action for stored media assets without changing the upload workflow.

#### Scenario: Teacher sees resource actions
- **WHEN** a teacher views an uploaded media asset in the video resource library
- **THEN** the asset actions MUST include preview, retry when failed, and archive/delete when allowed
- **AND** archive/delete MUST be visually distinct from removing a file from the pending upload queue.

#### Scenario: Asset is still processing
- **WHEN** a teacher attempts to archive a processing asset
- **THEN** the UI MUST either block the action with a clear reason or require confirmation that processing output will be abandoned
- **AND** the backend MUST keep media processing state consistent.

#### Scenario: Asset is already archived
- **WHEN** the teacher opens an archived asset through an audit filter
- **THEN** the UI MUST show it as unavailable
- **AND** it MUST NOT show the normal archive/delete action as if the asset were active.

### Requirement: Archive confirmation explains binding impact
The teacher video resource library SHALL require impact-aware confirmation before archiving a media asset.

#### Scenario: Asset is bound to points
- **WHEN** the archive impact plan reports active catalog point bindings
- **THEN** the confirmation UI MUST show the affected point count and representative point titles or catalog paths
- **AND** it MUST say that those point video bindings will be removed while point content remains.

#### Scenario: Asset affects published student content
- **WHEN** at least one affected point is currently student-visible
- **THEN** the confirmation UI MUST warn that students will no longer play this video from those points
- **AND** it MUST avoid saying that the experiment point itself will be deleted.

#### Scenario: Asset has no active bindings
- **WHEN** the archive impact plan reports no active point bindings
- **THEN** the confirmation UI MAY use a lighter confirmation
- **AND** it MUST still identify the media asset being archived.

### Requirement: Video resource archive stays separate from upload
The teacher video resource library SHALL keep archive/delete behavior separate from upload, resumable upload, duplicate detection, and processing controls.

#### Scenario: Teacher uploads videos
- **WHEN** a teacher is selecting local files or managing pending upload queue items
- **THEN** queue removal MUST affect only the pending upload list
- **AND** it MUST NOT call stored media asset archive endpoints.

#### Scenario: Teacher archives stored asset
- **WHEN** a teacher confirms archive/delete for a stored media asset
- **THEN** the frontend MUST call the media asset lifecycle archive API
- **AND** it MUST NOT call catalog point binding APIs directly.

#### Scenario: Archive succeeds
- **WHEN** the archive API returns success
- **THEN** the resource library MUST refresh asset lists, counts, duplicate hints, and processing states
- **AND** it MUST show archived assets only in audit or maintenance filters.

### Requirement: Archive result is auditable to teachers
The teacher video resource library SHALL show enough result feedback after archive to explain what changed.

#### Scenario: Bindings were removed
- **WHEN** archiving a video asset causes catalog point bindings to be archived
- **THEN** the success result MUST include the number of bindings removed
- **AND** the UI SHOULD provide a route or hint for reviewing affected points.

#### Scenario: Downstream cleanup is pending
- **WHEN** ES or RAG refresh jobs are queued because bindings changed
- **THEN** the archive result or diagnostics MUST indicate that search and AI context may update asynchronously
- **AND** the UI MUST NOT imply that upload processing is responsible for the delay.

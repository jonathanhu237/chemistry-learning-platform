## ADDED Requirements

### Requirement: Video tab shows a single current video slot
The teacher catalog editor SHALL present the point video tab as one current-video slot, because each catalog point can bind at most one video.

#### Scenario: Point has no bound video
- **WHEN** a teacher opens the video tab for a point with no active video binding
- **THEN** the tab MUST show an empty video slot or dashed placeholder inviting the teacher to choose a video
- **AND** it MUST NOT show a multi-select dropdown, batch bind button, or binding table.

#### Scenario: Point has a bound video
- **WHEN** a teacher opens the video tab for a point with an active video binding
- **THEN** the tab MUST show exactly one selected-video card or row with thumbnail, title, file name, upload/processing readiness, and preview access
- **AND** it MUST expose only visually secondary replace and remove actions.

#### Scenario: Bound video is processing or not ready
- **WHEN** the active binding's media asset is not ready
- **THEN** the selected-video slot MUST show the processing/unready state clearly
- **AND** it MUST avoid implying the video is already playable for students.

### Requirement: Teacher selects videos from a media picker
The teacher catalog editor SHALL use a media-library style picker for choosing or replacing a point video.

#### Scenario: Teacher chooses a video
- **WHEN** a teacher clicks the empty video slot or replace action
- **THEN** the editor MUST open a modal or equivalent picker listing existing video assets
- **AND** each selectable item MUST include a thumbnail or video placeholder, title, file name, upload/processing state, and preview affordance where available.

#### Scenario: Teacher searches videos
- **WHEN** a teacher types in the picker search field
- **THEN** the picker MUST filter or query video assets by title or file name
- **AND** it MUST keep metadata and thumbnail context visible in results.

#### Scenario: Teacher selects an eligible video
- **WHEN** a teacher selects a ready eligible video from the picker
- **THEN** the editor MUST immediately persist that video as the point's current video
- **AND** it MUST close the picker and keep the teacher on the video tab after detail refresh.

#### Scenario: Teacher inspects an unready video
- **WHEN** a video asset is still processing, failed, or otherwise not ready
- **THEN** the picker MAY show it for context
- **AND** it MUST disable or clearly prevent selecting it as a student-playable video until it is ready.

### Requirement: Video binding edits auto-save without binding publication controls
The teacher catalog editor SHALL make video selection, replacement, and removal direct persisted actions.

#### Scenario: Teacher replaces a video
- **WHEN** a teacher chooses a new video for a point that already has a current video
- **THEN** the editor MUST persist the replacement immediately
- **AND** it MUST show the replacement as the only current video after refresh.

#### Scenario: Teacher removes a video
- **WHEN** a teacher confirms removal of the current video
- **THEN** the editor MUST persist the removal immediately
- **AND** it MUST return the video tab to the empty slot state after refresh.

#### Scenario: Teacher edits video binding
- **WHEN** the video tab renders
- **THEN** it MUST NOT show binding-level `发布`, `取消发布`, `draft`, or `published` controls as authoring actions
- **AND** it MUST NOT require a separate save button after choosing or removing a video.

#### Scenario: Teacher needs to upload a new video
- **WHEN** a teacher needs a video that is not yet in the asset library
- **THEN** the video tab MAY provide a shortcut to the video resource page
- **AND** upload and processing MUST remain owned by the video resource workflow rather than embedded as the primary point binding action.

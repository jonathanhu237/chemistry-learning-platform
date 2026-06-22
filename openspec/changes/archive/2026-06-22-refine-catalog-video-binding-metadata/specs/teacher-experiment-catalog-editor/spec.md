## ADDED Requirements

### Requirement: Current video card shows left-aligned playback metadata
The teacher catalog editor SHALL present the current bound-video card like a mature video product: playable thumbnail first, then left-aligned title and student playback metadata beside it.

#### Scenario: Point has a bound ready video
- **WHEN** a teacher opens the video tab for a point with an active ready video binding
- **THEN** the current-video card MUST show the playable thumbnail on the left
- **AND** it MUST show exactly one prominent title block to the right of the thumbnail
- **AND** the title block MUST be left-aligned rather than horizontally centered in the empty right side
- **AND** the metadata under the title MUST include student playback file size when available
- **AND** the metadata MUST include upload time formatted to seconds, such as `2026-06-22 14:31:09`.

#### Scenario: Detailed playback facts are available
- **WHEN** the current binding payload includes bitrate, frame rate, codec, mime type, duration, or source-size comparison fields
- **THEN** the current-video card SHOULD show those facts as a compact one-property-per-line details list
- **AND** those facts MUST remain visually subordinate to the video title
- **AND** they MUST NOT duplicate the title or present the original file name as a second title.

#### Scenario: Playback resolution is available
- **WHEN** the current binding payload includes playback width and height
- **THEN** the current-video metadata MUST include the student playback resolution
- **AND** it MUST display the resolution as a compact fact near the playback size and upload time.

#### Scenario: Playback metadata is incomplete
- **WHEN** the current binding payload lacks playback size or resolution
- **THEN** the current-video card MUST omit only the missing fact or show a neutral pending-size message
- **AND** it MUST NOT show the original file name as a duplicate title line
- **AND** it MUST NOT imply that source size is the student playback size.

#### Scenario: Teacher manages the current binding
- **WHEN** the teacher needs to replace or remove the bound video
- **THEN** replace and remove actions MUST remain visually secondary
- **AND** the actions MUST stay anchored to the lower-right of the current-video information area without disturbing the title and metadata layout.

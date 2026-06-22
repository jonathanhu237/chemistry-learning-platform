## ADDED Requirements

### Requirement: Catalog point media bindings expose student playback metadata
The catalog tree service SHALL include student playback metadata in teacher point-detail media binding responses.

#### Scenario: Ready learning rendition exists
- **WHEN** a teacher opens a point with an active video binding whose media asset has a ready learning rendition
- **THEN** the media binding payload MUST include the learning rendition file size as `playback_file_size_bytes`
- **AND** it MUST include the learning rendition width and height as `playback_width` and `playback_height` when available
- **AND** it MUST include the learning rendition duration as `playback_duration_seconds` when available
- **AND** it MUST include available playback frame rate, bitrate, video codec, and audio codec metadata for that rendition
- **AND** it MUST keep the media asset `created_at` timestamp available for upload-time display.

#### Scenario: No ready learning rendition exists
- **WHEN** a teacher opens a point with an active video binding whose media asset has no ready learning rendition
- **THEN** the media binding payload MUST prefer another ready rendition when available
- **AND** if no ready rendition is available, it MUST fall back to the asset playback/source metadata without failing the point-detail response
- **AND** it MUST NOT label the uploaded source file size as a processed student playback rendition.

#### Scenario: Binding is inactive or asset is archived
- **WHEN** a media binding is archived or the media asset lifecycle is no longer active
- **THEN** the point-detail media binding response MUST continue excluding that binding
- **AND** playback metadata MUST NOT make inactive bindings appear current.

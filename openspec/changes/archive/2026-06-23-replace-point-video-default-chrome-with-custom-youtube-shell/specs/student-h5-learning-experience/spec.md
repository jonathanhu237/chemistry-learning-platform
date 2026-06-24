## ADDED Requirements

### Requirement: Point detail uses custom video shell
The student H5 point detail experience SHALL render playable point videos through an ArtPlayer-backed media engine with a student-owned custom mobile shell, while keeping point title, catalog path, learning text, equations, safety, related experiments, AI handoff, and assessment handoff below the video header.

#### Scenario: Playable point video uses ArtPlayer as engine
- **WHEN** a student opens a visible catalog point with a playable published video
- **THEN** the point detail page MUST create the video header through the ArtPlayer-backed point video player
- **AND** ArtPlayer MUST remain responsible for media source loading, poster, autoplay policy, inline playback, playback state, current time, duration, seek, and cleanup
- **AND** the visible student playback UI MUST come from the custom mobile shell rather than ArtPlayer's default chrome
- **AND** the page MUST NOT render browser native video controls.

#### Scenario: Point detail keeps learning content below player
- **WHEN** the playable point detail page renders
- **THEN** the video header MUST remain stable at the top of the detail viewport
- **AND** the catalog path and full point title MUST render below the player rather than inside a generic page bar above the player
- **AND** long titles MUST wrap below the player without changing the video header height
- **AND** learning content below the player MUST continue to show available principle equation or text, phenomenon explanation, safety/caution notes, related experiment links, and learning/assessment actions according to the existing point-detail contract.

#### Scenario: Autoplay recovery uses custom shell
- **WHEN** playable video autoplay is attempted and the browser or WebView rejects playback
- **THEN** the point detail page MUST keep the video header usable
- **AND** the custom shell MUST expose a visible play affordance when active
- **AND** the student MUST be able to start playback through the custom shell without needing ArtPlayer's default toolbar or browser native controls.

#### Scenario: Custom shell events stay synchronized
- **WHEN** the video emits playback lifecycle events such as loaded metadata, duration change, time update, play, pause, waiting, playing, seek, error, fullscreen, or destroy
- **THEN** the custom shell MUST update its visible state from the ArtPlayer/media source of truth
- **AND** time feedback MUST use the current media time and duration
- **AND** the shell MUST not keep stale playing, seeking, or duration state after the source changes or the player unmounts.

#### Scenario: No playable video keeps graceful empty header
- **WHEN** a student opens a visible catalog point with no active ready video binding
- **THEN** the point detail page MUST keep the same edge-to-edge video-header footprint
- **AND** it MUST show the graceful no-video placeholder instead of initializing a fake playable shell
- **AND** the no-video placeholder MUST keep an immediately visible shared route-return affordance
- **AND** the page MUST still show the point's learning content below the placeholder when available.

#### Scenario: Related point navigation preserves player model
- **WHEN** the student opens a related experiment point from a point detail page
- **THEN** the target point detail page MUST apply the same playable custom-shell or no-video placeholder rules according to that target point's video availability
- **AND** returning MUST preserve normal source-aware route-stack behavior.

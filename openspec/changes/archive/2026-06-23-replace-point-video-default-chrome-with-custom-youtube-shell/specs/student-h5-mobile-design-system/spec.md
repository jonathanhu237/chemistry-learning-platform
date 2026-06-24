## MODIFIED Requirements

### Requirement: Branded edge-to-edge point video player controls
The student H5 mobile design system SHALL support a branded, touch-safe, edge-to-edge point video player control layer for point video detail pages, and playable point videos SHALL use a single custom mobile shell rather than ArtPlayer's default visible chrome.

#### Scenario: Player controls are inactive
- **WHEN** the point detail video player is visible, playable, and its custom shell is inactive
- **THEN** the player MUST prioritize the video frame or poster
- **AND** the player MUST appear as the page header rather than as a card inside a card-like content stack
- **AND** browser native video controls MUST NOT be visible
- **AND** ArtPlayer's default bottom toolbar, default progress control, default time display, default play control, default settings control, default fullscreen control, and default mask/state chrome MUST NOT be visible as the student-facing product UI
- **AND** the playable player-owned return arrow MUST NOT be visible or touchable
- **AND** the inactive shell MUST expose no persistent toolbar except a faint bottom progress indicator when progress data is available.

#### Scenario: Student activates player controls
- **WHEN** the student taps or otherwise activates the playable video player on a touch viewport
- **THEN** the player MUST reveal the custom active shell inside the player footprint
- **AND** the active shell MUST include a touch-reachable route return action, a central play/pause control, time feedback where duration is available, an interactive progress/seek control, and a fullscreen or equivalent player affordance where supported
- **AND** those controls MUST hide or de-emphasize again according to normal player inactivity behavior
- **AND** those controls MUST remain inside the player footprint rather than using the generic detail-page header
- **AND** the player-owned return action MUST become visible and touchable only while the custom shell is active
- **AND** the player-owned return action MUST render the same shared filled-outline back-arrow path as ordinary second-level page headers.

#### Scenario: Custom shell owns visible playback actions
- **WHEN** a playable point video renders visible playback controls
- **THEN** every visible custom playback control MUST call a real playback, seek, fullscreen, mute, settings, or route action
- **AND** display-only playback controls MUST NOT be rendered as if they control playback
- **AND** the custom shell MUST use ArtPlayer or the underlying `HTMLVideoElement` as the playback source of truth for current time, duration, playing state, buffering/loading state, error state, and fullscreen state
- **AND** the shell MUST clean up timers and event listeners when the ArtPlayer instance is destroyed or the source changes.

#### Scenario: Progress is custom and touch safe
- **WHEN** playable point-video progress is shown in the custom shell
- **THEN** the inactive progress indicator MUST be a quiet bottom-pinned line without a draggable thumb or full toolbar
- **AND** the active progress control MUST provide a phone-safe hit target larger than the visible line
- **AND** the active progress control MUST use a colored branded played track and a small circular SYSU progress thumb
- **AND** the inactive progress indicator MUST NOT show the SYSU thumb or colored active seek treatment
- **AND** dragging or tapping the active progress control MUST seek the ArtPlayer media to the corresponding playback time
- **AND** seeking MUST NOT accidentally trigger route back or simple tap-to-toggle behavior.

#### Scenario: SYSU progress branding is restrained
- **WHEN** a playable point video renders custom progress branding
- **THEN** any SYSU logo or SYSU-logo-derived progress treatment MUST be scoped to the point video player
- **AND** the SYSU progress thumb MUST appear only with the active progress/seek control
- **AND** the branding MUST NOT make the inactive state visually noisy
- **AND** the branding MUST NOT obscure the progress hit target, central play/pause control, time capsule, or player-owned return action
- **AND** unrelated student controls MUST NOT be restyled by the player branding.

#### Scenario: Empty video state keeps visible route return
- **WHEN** the point video header renders the no-playable-video placeholder
- **THEN** the placeholder MUST keep a visible shared return affordance immediately available
- **AND** the placeholder return affordance MUST use the same shared filled-outline back-arrow geometry as playable player chrome
- **AND** the placeholder MUST NOT show fake play, progress, time, fullscreen, or settings controls
- **AND** the placeholder MUST remain visually distinct from an inactive playable video, because inactive playable videos can still reveal controls by tapping the player.

#### Scenario: Phone viewport layout is verified
- **WHEN** the point video detail page is viewed at 360px, 390px, or 430px CSS-pixel widths
- **THEN** the player, custom shell, flat title section, learning content sections, and finish-learning action MUST avoid horizontal scrolling and incoherent overlap
- **AND** the player controls MUST remain reachable by touch without relying on hover or desktop keyboard shortcuts
- **AND** playable-video inactive state MUST show no persistent toolbar except the faint bottom progress indicator
- **AND** playable-video active state MUST keep the back arrow, centered playback control, time feedback, progress, and supported fullscreen/settings controls inside the player footprint
- **AND** chemistry equations inside learning content MUST render at body-copy scale and wrap within the phone content area whenever the rendering engine permits
- **AND** large display-math equation styling MUST NOT be the default student mobile treatment.

#### Scenario: Detail page opts out of card-grid styling
- **WHEN** a point video detail route is displayed in the student H5 shell or teacher student-preview phone frame
- **THEN** the detail content MUST remove the paper grid background used by other experiment learning views
- **AND** the player MUST have square outer corners at the page edge
- **AND** the title and learning sections MUST be separated by full-width bands or dividers rather than nested cards
- **AND** the custom player shell MUST clip to the video header footprint and MUST NOT create page-level overlays outside the player frame.

#### Scenario: Student preview matches real H5 player interaction
- **WHEN** the point video detail route is rendered inside the teacher student-preview phone frame
- **THEN** tapping the playable video MUST reveal the same custom active player shell as normal student H5
- **AND** inactive-player shell hiding MUST match the normal student H5 behavior
- **AND** progress tapping or dragging in student preview MUST seek through the same shell logic as real H5
- **AND** no preview-only player controls or preview-only event paths MAY replace the student shell behavior.

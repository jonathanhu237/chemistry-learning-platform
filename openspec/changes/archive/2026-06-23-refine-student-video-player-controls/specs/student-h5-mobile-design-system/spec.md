## MODIFIED Requirements

### Requirement: Branded edge-to-edge point video player controls
The student H5 mobile design system SHALL support a branded, touch-safe, edge-to-edge point video player control layer for point video detail pages.

#### Scenario: Player controls are inactive
- **WHEN** the point detail video player is visible but its controls are inactive
- **THEN** the player MUST prioritize the video frame or poster
- **AND** the player MUST appear as the page header rather than as a card inside a card-like content stack
- **AND** return, full progress, time capsule, fullscreen, settings, and other player toolbar chrome MUST NOT permanently occupy the page header area above the player
- **AND** playable videos MUST hide the player-owned return arrow while inactive
- **AND** playable videos MUST expose only a faint bottom mini progress indicator as persistent inactive chrome when progress data is available
- **AND** the mini progress indicator MUST be visually quieter than the active interactive progress control.

#### Scenario: Student activates player controls
- **WHEN** the student taps the video player on a touch viewport
- **THEN** the player MUST reveal a touch-reachable return action, play/pause control, progress control, time feedback where available, and fullscreen affordance where supported
- **AND** the controls MUST hide or de-emphasize again according to normal player inactivity behavior
- **AND** those controls MUST remain inside the player footprint rather than using the generic detail-page header
- **AND** the player-owned return action MUST become visible and touchable only while the player chrome is active
- **AND** the player-owned return action MUST render the same shared filled-outline back-arrow path as ordinary second-level page headers.

#### Scenario: Active controls use YouTube-like mobile composition
- **WHEN** playable point video controls are active on a phone-width viewport
- **THEN** the primary play/pause affordance MUST be visually centered in the video area or use the player library's equivalent centered playback state
- **AND** the progress control MUST remain pinned near the bottom edge of the player footprint
- **AND** current-time and duration feedback MUST render as compact bottom-left toolbar feedback or a capsule-like control when duration is known
- **AND** secondary controls such as fullscreen, settings, or playback options MUST remain subordinate to playback, return, progress, and time feedback
- **AND** controls MUST NOT overlap the shared return arrow, video content center control, or progress hit area on 360px, 390px, or 430px CSS-pixel widths.

#### Scenario: Artplayer native control model is preferred
- **WHEN** the point player needs inactive mini progress, active progress, time feedback, layers, or toolbar controls
- **THEN** the implementation MUST use Artplayer's native `miniProgressBar`, `controls`, `layers`, CSS variables, and player events where practical
- **AND** custom React/CSS overlays MUST NOT duplicate Artplayer progress, seek, duration, or control visibility state unless a documented QA failure requires it
- **AND** any custom Artplayer control MUST clean up event listeners when the Artplayer instance is destroyed.

#### Scenario: SYSU progress branding is rendered
- **WHEN** a playable point video is rendered through the student H5 point player
- **THEN** the progress control MUST use SYSU-aligned branding
- **AND** the active interactive progress thumb MUST use the existing SYSU logo or another SYSU-logo-derived visual treatment when a custom progress thumb is shown
- **AND** the inactive mini progress indicator MUST remain subtle and MUST NOT use an oversized decorative thumb
- **AND** the branding MUST be scoped to the point video player so unrelated student controls are not restyled.

#### Scenario: Empty video state keeps visible route return
- **WHEN** the point video header renders the no-playable-video placeholder
- **THEN** the placeholder MUST keep a visible shared back affordance without waiting for playback chrome
- **AND** the placeholder return affordance MUST use the same shared filled-outline back-arrow geometry as playable player chrome
- **AND** the placeholder MUST remain visually distinct from an inactive playable video, because inactive playable videos can still reveal controls by tapping the player.

#### Scenario: Phone viewport layout is verified
- **WHEN** the point video detail page is viewed at 360px, 390px, or 430px CSS-pixel widths
- **THEN** the player, control layer, flat title section, learning content sections, and finish-learning action MUST avoid horizontal scrolling and incoherent overlap
- **AND** the player controls MUST remain reachable by touch without relying on hover or desktop keyboard shortcuts
- **AND** playable-video inactive state MUST show no persistent toolbar except the faint mini progress indicator
- **AND** playable-video active state MUST keep the back arrow, centered playback control, time feedback, progress, and supported fullscreen/settings controls inside the player footprint
- **AND** chemistry equations inside learning content MUST render at body-copy scale and wrap within the phone content area whenever the rendering engine permits
- **AND** large display-math equation styling MUST NOT be the default student mobile treatment.

#### Scenario: Student preview matches real H5 player interaction
- **WHEN** the point video detail route is rendered inside the teacher student-preview phone frame
- **THEN** tapping the playable video MUST reveal the same active player chrome as normal student H5
- **AND** inactive-player chrome hiding MUST match the normal student H5 behavior
- **AND** progress seeking and toolbar hit targets MUST continue to work through the preview iframe/touch-emulation layer.

#### Scenario: Detail page opts out of card-grid styling
- **WHEN** a point video detail route is displayed in the student H5 shell or teacher student-preview phone frame
- **THEN** the detail content MUST remove the paper grid background used by other experiment learning views
- **AND** the player MUST have square outer corners at the page edge
- **AND** the title and learning sections MUST be separated by full-width bands or dividers rather than nested cards.

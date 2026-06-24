## ADDED Requirements

### Requirement: Branded edge-to-edge point video player controls
The student H5 mobile design system SHALL support a branded, touch-safe, edge-to-edge point video player control layer for experiment point detail pages.

#### Scenario: Player controls are inactive
- **WHEN** the point detail video player is visible but its controls are inactive
- **THEN** the player MUST prioritize the video frame or poster
- **AND** the player MUST appear as the page header rather than as a card inside a card-like content stack
- **AND** return, progress, and other player chrome MUST NOT permanently occupy the page header area above the player

#### Scenario: Student activates player controls
- **WHEN** the student taps the video player on a touch viewport
- **THEN** the player MUST reveal a touch-reachable return action, play/pause control, progress control, time feedback where available, and fullscreen affordance where supported
- **AND** the controls MUST hide or de-emphasize again according to normal player inactivity behavior
- **AND** those controls MUST remain inside the player footprint rather than using the generic detail-page header

#### Scenario: SYSU progress branding is rendered
- **WHEN** a playable point video is rendered through the student H5 point player
- **THEN** the progress control MUST use SYSU-aligned branding
- **AND** the progress thumb MUST use a SYSU logo or SYSU-logo-derived visual treatment
- **AND** the branding MUST be scoped to the point video player so unrelated student controls are not restyled

#### Scenario: Phone viewport layout is verified
- **WHEN** the point video detail page is viewed at 360px, 390px, or 430px CSS-pixel widths
- **THEN** the player, control layer, flat title section, learning content sections, and finish-learning action MUST avoid horizontal scrolling and incoherent overlap
- **AND** the player controls MUST remain reachable by touch without relying on hover or desktop keyboard shortcuts
- **AND** chemistry equations inside learning content MUST render at body-copy scale and wrap within the phone content area whenever the rendering engine permits
- **AND** large display-math equation styling MUST NOT be the default student mobile treatment

#### Scenario: Detail page opts out of card-grid styling
- **WHEN** a point video detail route is displayed in the student H5 shell or teacher student-preview phone frame
- **THEN** the detail content MUST remove the paper grid background used by other experiment learning views
- **AND** the player MUST have square outer corners at the page edge
- **AND** the title and learning sections MUST be separated by full-width bands or dividers rather than nested cards

## ADDED Requirements

### Requirement: Fullscreen assistant canvas layout
The student H5 mobile design system SHALL support root-level fullscreen assistant canvases that are not visually framed as cards.

#### Scenario: Assistant root uses full-bleed canvas
- **WHEN** the authenticated student opens the `AI` root on a 360px, 390px, or 430px CSS-pixel-wide viewport
- **THEN** the assistant root MUST avoid a bordered floating panel/card appearance
- **AND** it MUST avoid nested cards inside the first-screen assistant canvas
- **AND** it MUST avoid horizontal page overflow.

#### Scenario: Composer and bottom navigation coexist
- **WHEN** the root assistant composer and bottom navigation are both visible
- **THEN** the composer bottom edge MUST sit above the bottom navigation top edge
- **AND** the send action MUST remain reachable by touch
- **AND** the bottom navigation MUST NOT cover the active input, send button, starter prompt, or visible chat messages.

#### Scenario: Root and detail assistant variants remain distinct
- **WHEN** the root assistant route and contextual assistant detail route are rendered
- **THEN** root styling MUST be scoped to the root variant
- **AND** detail styling MUST preserve route-stack pagebar/back behavior and hidden bottom navigation
- **AND** root-only actions such as history MUST NOT leak into contextual detail routes.

### Requirement: Mobile chat empty-state rhythm
The student H5 mobile design system SHALL support sparse AI chat empty states with large breathing room before the first turn.

#### Scenario: Empty chat uses low prompt placement
- **WHEN** a root AI chat has no messages
- **THEN** the first-screen prompt or starter copy MUST sit closer to the composer than to the top identity area
- **AND** the middle of the screen MUST remain visually calm and uncluttered
- **AND** the UI MUST NOT fill the empty state with multiple stacked cards or dense prompt grids.

#### Scenario: Empty chat keeps course atmosphere
- **WHEN** the sparse AI root empty state renders
- **THEN** the visual treatment MAY use the existing chemistry green, subtle grid, and paper-like surface
- **AND** those treatments MUST behave as background/canvas treatments rather than card borders around the whole assistant.

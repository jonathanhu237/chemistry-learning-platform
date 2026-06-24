## ADDED Requirements

### Requirement: Collapsing family headers preserve mobile content space
The student H5 mobile design system SHALL allow a family context header to collapse into a compact sticky header without harming catalog readability.

#### Scenario: Detail page chrome is compact
- **WHEN** a student opens a second-level detail page
- **THEN** the page bar MUST use a plain left arrow and a left-aligned title
- **AND** the page bar MUST NOT reserve a decorative square button background or mirrored right spacer only for centering
- **AND** the vertical padding MUST stay compact enough to preserve room for the content below.

#### Scenario: Expanded family header renders on phone
- **WHEN** a family catalog shell is rendered at common phone widths from 360px to 430px
- **THEN** the expanded header MUST use stable dimensions, line clamping, and horizontal overflow where needed
- **AND** text, element tiles, buttons, and catalog cards MUST not overlap
- **AND** the header MUST avoid decorative height that prevents catalog discovery.

#### Scenario: Compact family header sticks during scroll
- **WHEN** the family context collapses while the student scrolls catalog content
- **THEN** the compact header MUST remain readable and tappable
- **AND** it MUST keep touch targets usable without growing taller than the intended compact row
- **AND** it MUST contrast with catalog content without hiding list rows behind translucent artifacts.

#### Scenario: Motion is used for collapse
- **WHEN** the expanded header transitions into the compact header
- **THEN** the animation MUST be short, natural, and responsive to scroll
- **AND** it MUST NOT use delayed follower behavior, idle timers, or continuous expensive re-rendering.

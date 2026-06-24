## ADDED Requirements

### Requirement: Compact Atom-centered bottom navigation
The student H5 mobile design system SHALL provide a compact root bottom navigation bar that reserves less vertical space than the previous icon-plus-label bar while keeping fixed-control safe-area protection.

#### Scenario: Compact bottom bar uses shared layout token
- **WHEN** a root route renders the authenticated student bottom navigation
- **THEN** the visible bar height MUST be controlled by the shared mobile bottom-navigation height token
- **AND** the compact token value MUST be shorter than the previous `68px` bar height before safe-area inset is added
- **AND** route-content bottom spacing and root page height formulas MUST continue to derive from that token rather than hardcoded per-page nav heights.

#### Scenario: Ordinary destinations are text-forward
- **WHEN** the bottom navigation renders the non-Atom root destinations
- **THEN** `home`, `learn`, `assessment`, and `profile` MUST render as compact text-forward controls
- **AND** their selected state MUST use a quiet active text treatment without a large filled active background block
- **AND** their labels MUST remain readable and non-overlapping on supported phone widths from `360px` to `430px`.

#### Scenario: Atom destination is the centered branded control
- **WHEN** the bottom navigation renders the `ai` root destination
- **THEN** the Atom destination MUST remain visually centered among the five root entries
- **AND** it MUST render as a rounded rectangular or squircle control containing an Atom icon
- **AND** its inactive state MUST be visually distinct from its active state
- **AND** only the active `ai` root state MUST use the solid product-green control with a white Atom icon
- **AND** the Atom control MUST stay within the bottom navigation bar instead of protruding as a floating action button.

#### Scenario: Compact navigation remains touch and safe-area usable
- **WHEN** the compact bottom navigation is shown in a mobile browser or WebView
- **THEN** every root navigation entry MUST remain reachable by touch
- **AND** the bar MUST account for `env(safe-area-inset-bottom)`
- **AND** focus-visible styling MUST remain available without showing default browser focus boxes during normal pointer use.

#### Scenario: Keyboard and detail-route rules continue to win
- **WHEN** the root Atom composer enters keyboard-active layout
- **THEN** the bottom navigation MUST continue to hide so it does not compete with the composer workbench
- **AND** when any non-tab/detail route is open the bottom navigation MUST remain hidden according to route-stack semantics.

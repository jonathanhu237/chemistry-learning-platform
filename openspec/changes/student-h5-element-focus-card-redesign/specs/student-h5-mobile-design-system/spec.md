## ADDED Requirements

### Requirement: Compact element focus card layout
The student H5 mobile layout SHALL render the selected-element focus card as a compact phone-first learning component that preserves the periodic-table tile while keeping experiment tasks discoverable.

#### Scenario: Element tile remains the visual anchor
- **WHEN** the selected-element focus card is shown on a 360px to 430px CSS-pixel-wide phone viewport
- **THEN** the card MUST keep the element square visible near the leading edge of the card
- **AND** the square MUST show atomic number, element symbol, and English label without clipping
- **AND** the surrounding card content MUST align with the square rather than replacing it with plain text-only identity

#### Scenario: Focus and relevance text fit the card
- **WHEN** the selected element has focus-property and experiment-relevance copy
- **THEN** the focus-property line MUST be visually more prominent than supporting tags
- **AND** the experiment-relevance line MUST wrap within the card without horizontal overflow
- **AND** long labels MUST be clamped, wrapped, or otherwise constrained so they do not overlap the tile, tags, action, or following content

#### Scenario: Card stays compact before experiment tasks
- **WHEN** the chapter page contains the selected-element focus card above family facts or experiment-point content
- **THEN** the card MUST use a compact layout that avoids pushing the experiment-point task area below excessive introductory content
- **AND** long detailed facts MUST be placed in the facts/detail area instead of expanding the compact card by default

#### Scenario: Detail action is touch reachable
- **WHEN** the focus card includes an action to view element details
- **THEN** the action MUST be reachable by touch without hover or desktop-only interaction
- **AND** it MUST NOT visually compete with the facts/experiments segmented switcher, experiment-point card actions, AI entry, feedback entry, or completion action

#### Scenario: Mobile viewport QA covers redesigned card
- **WHEN** implementation verification runs for the redesigned selected-element card
- **THEN** QA MUST cover 360x780, 390x844, and 430x932 CSS-pixel viewports
- **AND** it MUST check element switching, long Chinese focus/relevance copy, tag wrapping, detail action reachability, and the first visible experiment-point task area

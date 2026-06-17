## ADDED Requirements

### Requirement: Mobile current-chapter composition
The student H5 mobile layout SHALL present the element learning page as a current family or chapter page optimized for phone WebView reading and tapping.

#### Scenario: Student views the current chapter page on a phone
- **WHEN** the current family or chapter page is rendered at common phone widths from 360px to 430px CSS pixels
- **THEN** the layout MUST show current chapter identity, within-family element chips, selected-element facts, family common properties, property-driven experiment-point groups, floating AI or feedback entries when enabled, and completion actions without horizontal scrolling
- **AND** sibling-family browsing controls MUST NOT consume the page's primary top navigation area.

#### Scenario: Student needs to switch chapter
- **WHEN** a student wants to choose a different family or chapter
- **THEN** the page MUST expose a touch-friendly secondary navigation affordance to return to the periodic-table learning entry or switch chapter
- **AND** that affordance MUST NOT obscure the main experiment-point task area.

### Requirement: Touch-first chemistry learning controls
The student H5 mobile layout SHALL make within-family element selection and experiment-point learning controls reachable by touch without desktop-only interaction patterns.

#### Scenario: Student switches selected element
- **WHEN** element chips are displayed for the current family
- **THEN** each chip MUST use a phone-appropriate hit area
- **AND** the active element state MUST be visually clear without relying on hover.

#### Scenario: Student opens an experiment point
- **WHEN** experiment-point cards are displayed below the chemistry context
- **THEN** each card MUST be tappable without hover or precise pointer input
- **AND** floating AI or feedback controls MUST NOT block the point card, back action, completion action, or assessment entry.

### Requirement: Compact context before primary tasks
The student H5 mobile layout SHALL keep chemistry context compact enough that the experiment-point task area remains discoverable on phone viewports.

#### Scenario: Chemistry facts are lengthy
- **WHEN** selected-element facts, family common properties, trend formulas, or reference media would make the top context area long
- **THEN** the layout MUST use compact summaries, carousels, accordions, tabs, or equivalent progressive disclosure
- **AND** it MUST avoid making experiment-point learning feel secondary to an encyclopedia-style fact page.

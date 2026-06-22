## ADDED Requirements

### Requirement: Embedded atom model mobile layout
The student H5 mobile design system SHALL support an embedded atom model card inside the chapter facts view without breaking phone viewport layout.

#### Scenario: Atom model card fits phone widths
- **WHEN** the atom model card is rendered at 360px, 390px, or 430px CSS-pixel viewport widths
- **THEN** the card MUST fit without page-level horizontal scrolling
- **AND** its element tile, title, mode controls, compact facts, and canvas MUST not overlap each other
- **AND** long facts such as electron configuration and density MUST wrap or truncate in a readable mobile-safe way

#### Scenario: Atom model card does not hide primary tasks
- **WHEN** the facts view contains the atom model card, family common properties, property summaries, and experiment handoff content
- **THEN** the card MUST remain compact enough that the rest of the learning content is discoverable on a phone
- **AND** it MUST not reintroduce an encyclopedia-style stack of large fact cards before the experiment-point learning task area

#### Scenario: Atom model coexists with app shell controls
- **WHEN** the app bottom navigation, local facts/experiments switcher, assistant handoff, feedback/profile flow, or finish-learning action is present
- **THEN** the atom model card MUST not be obscured by those controls
- **AND** it MUST not obscure those controls

### Requirement: Touch-safe atom canvas interaction
The student H5 mobile design system SHALL make atom canvas interaction touch-friendly without interfering with page scrolling.

#### Scenario: Student rotates the atom by touch
- **WHEN** the student drags inside the atom canvas
- **THEN** the atom model MAY capture the pointer to rotate the model
- **AND** the drag behavior MUST remain limited to the canvas interaction region
- **AND** vertical page scrolling outside the canvas MUST remain usable

#### Scenario: Student uses mode and playback controls
- **WHEN** the atom model card exposes mode, reset, play, pause, or orbital option controls
- **THEN** every exposed control MUST have a phone-appropriate hit area
- **AND** active states MUST be visually clear without hover
- **AND** labels MUST remain readable on the smallest supported viewport

### Requirement: Mobile animation governance for atom viewer
The student H5 mobile design system SHALL govern embedded atom animation so it remains responsive and battery-conscious on phones.

#### Scenario: Atom animation is hidden or paused
- **WHEN** the page becomes hidden, the card unmounts, or the student pauses the model
- **THEN** the viewer MUST stop unnecessary animation frames
- **AND** it MUST clean up observers and pointer handlers when unmounted

#### Scenario: Atom model resizes
- **WHEN** the phone viewport changes size, browser chrome changes available space, or the student switches tabs/routes and returns
- **THEN** the atom canvas MUST recalculate its size
- **AND** it MUST render a nonzero visible model region rather than a collapsed or blank panel

### Requirement: Atom model mobile QA evidence
The student H5 mobile QA suite SHALL cover the atom model card as part of the authenticated learning flow.

#### Scenario: Mobile QA covers atom model
- **WHEN** mobile viewport QA runs after this change
- **THEN** it MUST cover navigating to a selected chapter facts view
- **AND** it MUST verify the atom model card is visible
- **AND** it MUST verify element chip switching still works
- **AND** it MUST verify the local facts/experiments switcher remains reachable
- **AND** it MUST verify no horizontal overflow occurs at 360x780, 390x844, and 430x932 CSS-pixel viewports

#### Scenario: Canvas QA has practical fallback
- **WHEN** automated QA cannot reliably inspect rendered canvas pixels in the local environment
- **THEN** QA MUST at least verify the canvas exists, has nonzero dimensions, and survives element/mode switching
- **AND** final verification MUST record any remaining manual phone/WebView visual check performed for canvas rendering

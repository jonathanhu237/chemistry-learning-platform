## ADDED Requirements

### Requirement: Assistant point starter mobile layout
The student H5 mobile design system SHALL support a point-aware assistant starter layout that remains readable and reachable on supported phone viewports.

#### Scenario: Point starter renders on narrow phones
- **WHEN** the student opens experiment/video-point starter mode on a 360px to 430px CSS-pixel-wide viewport
- **THEN** experiment group, experiment, point, template, preview, composer, and launch controls MUST remain within the viewport width
- **AND** the page MUST avoid horizontal scrolling caused by long Chinese experiment or point labels.

#### Scenario: Point starter uses progressive disclosure
- **WHEN** the point starter contains multiple experiment groups, experiments, or video points
- **THEN** the UI MUST present them through stacked sections, segmented controls, accordions, sheets, or equivalent phone-first disclosure
- **AND** it MUST NOT require a desktop three-column grid to use the starter.

#### Scenario: Long point labels are rendered
- **WHEN** experiment titles, point titles, candidate labels, template descriptions, or preview questions are longer than one short phrase
- **THEN** the UI MUST wrap, clamp, or otherwise constrain text so controls remain usable
- **AND** selected states MUST remain visually clear without relying on hover.

### Requirement: Assistant point starter touch and safe-area behavior
The student H5 mobile design system SHALL keep assistant point starter actions reachable around the fixed bottom navigation, safe areas, and the chat composer.

#### Scenario: Starter and bottom navigation coexist
- **WHEN** point starter controls, composer, starter launch action, and bottom tab navigation are all visible
- **THEN** the composer and launch action MUST remain reachable by touch
- **AND** bottom navigation MUST NOT cover the active input, selected controls, send button, or launch action.

#### Scenario: Student scrolls point starter
- **WHEN** the point starter content is taller than the available chat panel space
- **THEN** the starter content MUST scroll inside the assistant panel or otherwise remain reachable
- **AND** the page MUST NOT create nested scrolling that traps the composer or bottom navigation offscreen.

#### Scenario: Student focuses the composer in point mode
- **WHEN** the student focuses the assistant composer while point starter mode is active
- **THEN** the input and submit action MUST remain usable when the mobile keyboard is expected to appear
- **AND** point starter controls MUST not overlap the focused input.

### Requirement: Assistant point starter loading and empty states
The student H5 mobile design system SHALL present point starter loading, empty, and error states without blocking global course asking.

#### Scenario: Point starter is loading data
- **WHEN** the app is loading experiment groups, experiments, or point detail for the point starter
- **THEN** it MUST show compact mobile-readable loading feedback in the relevant point-starter section
- **AND** it MUST keep the global course starter or free-form composer usable whenever possible.

#### Scenario: No point choices are available
- **WHEN** the selected group or experiment has no visible point choices
- **THEN** the UI MUST show a compact empty state that explains the point choices are unavailable
- **AND** it MUST provide a way to choose another group/experiment or ask a global/free-form question.

#### Scenario: Point starter request fails
- **WHEN** an optional point starter data request fails
- **THEN** the UI MUST show a student-readable error or retry affordance
- **AND** it MUST NOT break the rest of the assistant tab.

### Requirement: Assistant point starter mobile QA coverage
The student H5 mobile QA workflow SHALL verify the point-aware assistant starter across supported phone viewports.

#### Scenario: Mobile viewport QA covers point starter
- **WHEN** mobile viewport QA runs for student-web
- **THEN** it MUST cover point starter mode at 360x780, 390x844, and 430x932 CSS-pixel viewports
- **AND** it MUST check that there is no horizontal overflow, no blocked composer, no blocked launch action, and no bottom-navigation overlap.

#### Scenario: Mobile QA covers point starter launch
- **WHEN** mobile viewport QA exercises the assistant point starter
- **THEN** it MUST select a student-visible group, experiment or point option, and question template
- **AND** it MUST verify that the generated point starter request transitions into normal chat.

#### Scenario: Mobile QA confirms bottom status removal
- **WHEN** mobile viewport QA sends an assistant message
- **THEN** it MUST verify that per-turn assistant status remains visible
- **AND** it MUST verify that the redundant bottom status row below the composer is not rendered.

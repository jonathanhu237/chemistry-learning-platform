## ADDED Requirements

### Requirement: Viewport-contained anchored learning popover
The student H5 mobile design system SHALL support anchored learning-selection popovers that remain inside the visible phone viewport and do not affect root page layout.

#### Scenario: Popover opens from a periodic-table trigger
- **WHEN** a student taps a periodic-table area control or element cell on a supported phone viewport
- **THEN** the popover MUST appear visually related to the tapped trigger
- **AND** it MUST render above the page as a fixed or portaled overlay rather than inline content
- **AND** opening it MUST NOT change the document flow, stretch the periodic-table card, or increase the root page's layout height.

#### Scenario: Popover avoids viewport clipping
- **WHEN** the tapped trigger is near the top, bottom, left, or right edge of the visible viewport
- **THEN** the popover MUST flip, shift, or otherwise reposition so its actionable rows remain visible
- **AND** it MUST respect viewport padding and mobile safe-area constraints
- **AND** it MUST NOT be clipped behind the bottom navigation, browser chrome, or rounded phone preview frame in the supported QA viewports.

#### Scenario: Area chapter list fits normal phone viewports
- **WHEN** an area chapter list such as the p-area list is opened at 360x780, 390x844, or 430x932 CSS pixels
- **THEN** the popover SHOULD show the complete list without internal scrolling
- **AND** if the visual viewport is unusually short, the popover MUST clamp its max height and keep rows reachable through internal scrolling rather than expanding the page.

#### Scenario: Popover rows are touch safe
- **WHEN** chapter rows are shown inside the popover
- **THEN** each row MUST have a phone-appropriate touch target
- **AND** row titles, element symbol summaries, and trailing navigation icons MUST fit without horizontal overflow
- **AND** the selected row action MUST be reachable without hover, long press, or desktop keyboard shortcuts.

#### Scenario: Popover dismissal is predictable
- **WHEN** the popover is open
- **THEN** outside tap, Escape, route transition, and row selection MUST dismiss it
- **AND** dismissal MUST restore interaction to the periodic-table root without visual overlap or stuck focus state.

## MODIFIED Requirements

### Requirement: Floating overlay governance
The student frontend SHALL coordinate bottom navigation, fixed controls, dialogs, sheets, anchored popovers, and any remaining overlays through a shared mobile layering rule.

#### Scenario: Fixed and overlay controls do not overlap
- **WHEN** dialogs, sheets, anchored popovers, chat pages, feedback forms, assessment actions, or other fixed controls are shown
- **THEN** conflicting controls MUST be hidden, disabled, or repositioned so they do not overlap the active interaction
- **AND** the active interaction MUST stay within the visible phone viewport width.

#### Scenario: Bottom actions remain reachable
- **WHEN** a page contains the bottom tab bar and also contains an in-content primary action or anchored learning-selection popover
- **THEN** the page MUST provide enough bottom spacing or overlay collision handling for the action to remain reachable
- **AND** the tab bar MUST NOT block completion, submit, back, logout, chat composer, feedback, video actions, or learning-selection popover rows.

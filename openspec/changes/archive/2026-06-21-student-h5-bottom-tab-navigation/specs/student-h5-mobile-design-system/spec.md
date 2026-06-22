## ADDED Requirements

### Requirement: Bottom tab navigation primitive
The student H5 mobile design system SHALL provide a bottom tab navigation primitive for authenticated app-level destinations.

#### Scenario: Bottom tab bar renders on phone viewport
- **WHEN** an authenticated student page is rendered at 360px, 390px, or 430px CSS-pixel width
- **THEN** the bottom tab bar MUST fit without horizontal scrolling
- **AND** each visible item MUST have a phone-appropriate touch target, readable label, and clear active state.

#### Scenario: Safe area protects bottom navigation
- **WHEN** the H5 app runs in a mobile browser or WebView with bottom browser chrome or safe-area insets
- **THEN** the bottom navigation MUST account for the bottom safe area
- **AND** page content MUST reserve enough bottom padding so primary actions, inputs, cards, and video controls can scroll clear of the bar.

#### Scenario: Tab labels are localized and stable
- **WHEN** all student features are enabled
- **THEN** the bottom navigation MUST use concise app-level labels such as `学习`, `实验`, `问答`, `测评`, and `我的`
- **AND** it MUST NOT use chapter-local labels such as `性质通识` or `实验视频` as app-level tabs.

### Requirement: Profile feedback attachment controls
The student H5 mobile design system SHALL support feedback screenshot attachment controls inside the `我的` profile destination rather than inside a global floating feedback overlay.

#### Scenario: Student opens profile feedback
- **WHEN** the student opens the feedback area from `我的`
- **THEN** the form MUST provide touch-friendly screenshot add, change, and remove controls
- **AND** selected filename or attachment state MUST fit within phone viewport width without horizontal overflow.

#### Scenario: Feedback form uses mobile keyboard
- **WHEN** the student focuses the feedback text input on a phone viewport
- **THEN** the input and submit action MUST remain usable with the mobile keyboard expected
- **AND** the bottom navigation MUST NOT cover the submit action.

## MODIFIED Requirements

### Requirement: Floating overlay governance
The student frontend SHALL coordinate bottom navigation, fixed controls, dialogs, sheets, and any remaining overlays through a shared mobile layering rule.

#### Scenario: Fixed and overlay controls do not overlap
- **WHEN** dialogs, sheets, chat pages, feedback forms, assessment actions, or other fixed controls are shown
- **THEN** conflicting controls MUST be hidden, disabled, or repositioned so they do not overlap the active interaction
- **AND** the active interaction MUST stay within the visible phone viewport width.

#### Scenario: Bottom actions remain reachable
- **WHEN** a page contains the bottom tab bar and also contains an in-content primary action
- **THEN** the page MUST provide enough bottom spacing for the in-content action to scroll clear of the tab bar
- **AND** the tab bar MUST NOT block completion, submit, back, logout, chat composer, feedback, or video actions.

### Requirement: Mobile current-chapter composition
The student H5 mobile layout SHALL present the element learning page as a current family or chapter page optimized for phone WebView reading and tapping.

#### Scenario: Student views the current chapter page on a phone
- **WHEN** the current family or chapter page is rendered at common phone widths from 360px to 430px CSS pixels
- **THEN** the layout MUST show current chapter identity, within-family element chips, selected-element facts, family common properties, property-driven experiment-point groups, bottom navigation when in the authenticated shell, and completion actions without horizontal scrolling
- **AND** sibling-family browsing controls MUST NOT consume the page's primary top navigation area.

#### Scenario: Student needs to switch chapter
- **WHEN** a student wants to choose a different family or chapter
- **THEN** the page MUST expose a touch-friendly secondary navigation affordance to return to the periodic-table learning entry or switch chapter
- **AND** that affordance MUST NOT obscure the main experiment-point task area or the bottom tab bar.

### Requirement: Touch-first chemistry learning controls
The student H5 mobile layout SHALL make within-family element selection and experiment-point learning controls reachable by touch without desktop-only interaction patterns.

#### Scenario: Student switches selected element
- **WHEN** element chips are displayed for the current family
- **THEN** each chip MUST use a phone-appropriate hit area
- **AND** the active element state MUST be visually clear without relying on hover.

#### Scenario: Student opens an experiment point
- **WHEN** experiment-point cards are displayed below the chemistry context
- **THEN** each card MUST be tappable without hover or precise pointer input
- **AND** the bottom navigation, assistant tab, profile feedback form, or completion action MUST NOT block the point card, back action, completion action, or assessment entry.

### Requirement: Segmented switcher overlay governance
The segmented switcher SHALL coexist with the authenticated app shell, safe areas, and bottom actions without visual or interaction overlap.

#### Scenario: Bottom navigation is visible
- **WHEN** the student is on a chapter page with the bottom tab bar available
- **THEN** the segmented switcher MUST remain a local chapter control above the content
- **AND** it MUST NOT be placed in or visually merge with the bottom app navigation.

#### Scenario: Safe-area and browser chrome are present
- **WHEN** the H5 app runs in a mobile browser or WebView with safe-area insets or browser chrome
- **THEN** the segmented switcher and its sticky offset MUST account for the app's safe-area and compact header layout
- **AND** it MUST avoid clipped labels, clipped active indicators, and horizontal overflow.

#### Scenario: Mobile QA covers A/B switching
- **WHEN** mobile viewport QA runs for this change
- **THEN** it MUST cover facts-to-experiments switching, experiments-to-facts switching, element switching, experiment point list, point detail, assistant tab entry, profile feedback entry, and assessment handoff
- **AND** it MUST check 360x780, 390x844, and 430x932 CSS-pixel viewports.

### Requirement: Mobile QA covers feedback attachments
The student frontend SHALL cover feedback screenshot attachment behavior from the `我的` profile destination in repeatable mobile QA.

#### Scenario: Feedback attachment QA runs
- **WHEN** mobile QA is run for 360x780, 390x844, and 430x932 CSS-pixel viewports
- **THEN** it MUST cover opening `我的`, opening feedback, selecting or simulating a screenshot attachment, removing an attachment, submitting feedback, and returning to another tab
- **AND** it MUST verify that the feedback form and bottom navigation do not block each other.

## REMOVED Requirements

### Requirement: Feedback attachment controls follow mobile overlay governance
**Reason**: Feedback is moving out of the global floating overlay model and into the `我的` profile destination.
**Migration**: Reuse the screenshot validation and submission behavior inside `StudentFeedbackForm` or an equivalent profile feedback component, and remove authenticated floating feedback positioning from the shell.

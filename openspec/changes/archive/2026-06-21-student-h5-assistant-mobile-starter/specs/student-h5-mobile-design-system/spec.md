## ADDED Requirements

### Requirement: Assistant starter mobile layout
The student H5 mobile design system SHALL support an assistant starter layout that fits phone viewports without horizontal overflow, clipped text, or blocked actions.

#### Scenario: Starter renders on narrow phones
- **WHEN** the student opens the `问答` tab on a 360px to 430px CSS-pixel-wide viewport
- **THEN** the assistant starter surface MUST keep all primary starter controls within the viewport width
- **AND** starter intent labels, context title, preview text, and launch action MUST not overlap each other.

#### Scenario: Long Chinese starter labels render
- **WHEN** starter labels, prompt text, or context titles are longer than a single short phrase
- **THEN** the UI MUST wrap, clamp, or otherwise constrain text so it remains readable
- **AND** it MUST NOT rely on horizontal scrolling for the primary first-screen starter intent choices.

#### Scenario: Starter and bottom navigation coexist
- **WHEN** the starter surface, composer, and bottom tab navigation are all visible
- **THEN** the composer and starter launch action MUST remain reachable by touch
- **AND** bottom navigation MUST NOT cover the active input, send button, or launch action.

#### Scenario: Assistant panel uses available mobile height
- **WHEN** the student opens the `问答` tab between the sticky app header and fixed bottom navigation
- **THEN** the primary assistant panel SHOULD occupy the available vertical space with only necessary top and bottom breathing room
- **AND** it MUST NOT use a short fixed maximum height that leaves a large empty background area before the bottom navigation.

### Requirement: Assistant composer mobile ergonomics
The student H5 assistant composer SHALL remain usable with mobile keyboards and student-length chemistry questions.

#### Scenario: Student focuses the composer
- **WHEN** a student focuses the assistant input on a phone viewport
- **THEN** the input and submit action MUST remain usable when the mobile keyboard is expected to appear
- **AND** the layout MUST avoid desktop-only fixed heights that hide the focused input behind browser chrome or bottom navigation.

#### Scenario: Student enters a longer question
- **WHEN** the student types a multi-clause chemistry question or edits a starter preview into a custom question
- **THEN** the composer MUST allow enough visible text for comfortable editing
- **AND** the send action MUST remain visually associated with the input.

### Requirement: Assistant viewport QA coverage
The student H5 mobile QA workflow SHALL verify the assistant starter and chat interaction across supported phone viewports.

#### Scenario: Mobile viewport QA runs for assistant starter
- **WHEN** mobile viewport QA runs for student-web
- **THEN** it MUST cover the global assistant starter at 360x780, 390x844, and 430x932 CSS-pixel viewports
- **AND** it MUST check that there is no horizontal page overflow.

#### Scenario: Mobile viewport QA covers context handoff
- **WHEN** mobile viewport QA runs for student-web
- **THEN** it MUST cover at least one assistant launch from a learning chapter or experiment point context
- **AND** it MUST verify that the merged context cue, starter intents, composer, and bottom navigation remain reachable.

#### Scenario: Feature-disabled assistant remains covered
- **WHEN** assistant feature flags are disabled
- **THEN** student-web tests or QA MUST verify that the assistant tab remains hidden, disabled, or redirected according to the current app-config behavior.

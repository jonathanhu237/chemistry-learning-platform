## ADDED Requirements

### Requirement: Mobile composer workbench supports stable action anchoring
The student H5 mobile design system SHALL support a composer workbench layout whose action controls stay fixed while the input zone grows or scrolls.

#### Scenario: Workbench has stable touch targets
- **WHEN** the Atom composer renders on supported phone widths from 360px to 430px CSS pixels
- **THEN** the `+` action and send action MUST each remain reachable by touch inside the composer workbench
- **AND** their hit targets MUST NOT shrink because the textarea content grows
- **AND** the controls MUST maintain clear visual separation from typed text.

#### Scenario: Composer shape transitions without action drift
- **WHEN** the composer changes from compact one-line mode to expanded multi-line mode
- **THEN** the outer composer shape MUST transition from a race-track capsule to a rounded rectangle
- **AND** the `+` action and send action MUST remain visually aligned to the workbench row rather than following the text baseline.

#### Scenario: Compact width owns the expansion boundary
- **WHEN** typed text sits near the one-line boundary
- **THEN** the decision to stay compact or expand MUST use the compact race-track text lane width as the canonical line-capacity measurement
- **AND** changing into the wider expanded layout MUST NOT immediately reclassify that same text as compact.

#### Scenario: Compact measurement mirrors one-row input
- **WHEN** the design system measures compact composer line capacity with a hidden textarea
- **THEN** that measurement element MUST use the same one-row baseline as the visible compact composer input
- **AND** a one-character input MUST NOT make the composer leave compact mode.

#### Scenario: Compact composer text is centered and readable
- **WHEN** the compact Atom composer displays placeholder text or one-line typed text
- **THEN** the text MUST be vertically centered in the race-track lane
- **AND** the text size MUST visually match the left `+` action scale closely enough that both read as one row of the same control surface
- **AND** the same root composer text size MUST continue to be used after expansion or internal scrolling.

#### Scenario: Text area growth is bounded above the workbench
- **WHEN** the composer input zone grows for multi-line text
- **THEN** the growth MUST occur upward from the fixed workbench row
- **AND** the growth MUST preserve the existing effective-panel-height budget for the full root Atom composer
- **AND** once the growth budget is exceeded, only the input zone MUST scroll internally.

#### Scenario: Composer outer height respects the growth budget
- **WHEN** the root Atom composer is expanded or scrollable during normal or keyboard-active layout
- **THEN** the full composer surface, including padding and the fixed workbench row, MUST NOT exceed the configured `61.8%` effective-panel-height budget
- **AND** the input zone MUST receive the remaining height after the workbench row and composer padding are reserved.

### Requirement: Composer workbench coexists with keyboard-aware layout
The student H5 mobile design system SHALL keep the composer workbench usable during soft-keyboard and visible-viewport changes.

#### Scenario: Keyboard-active root composer preserves workbench gap
- **WHEN** the root Atom composer is keyboard-active
- **THEN** the composer bottom edge MUST retain the established breathing gap above the expected keyboard edge
- **AND** the workbench actions MUST remain visible above the keyboard
- **AND** the page MUST NOT expose unrelated raw background bands between the composer and the keyboard area.

#### Scenario: Bottom navigation does not conflict with workbench
- **WHEN** the root Atom composer and bottom navigation are both visible
- **THEN** the composer workbench MUST remain above the bottom navigation top edge
- **AND** the bottom navigation MUST NOT cover the `+` action, send action, or textarea input zone.

#### Scenario: Detail route chrome remains independent
- **WHEN** the contextual Atom chat detail route is open
- **THEN** detail-route chrome and hidden-bottom-navigation behavior MUST remain governed by route-stack rules
- **AND** composer workbench styling MUST NOT force root-route spacing or root-route actions into the detail route.

### Requirement: Composer workbench visual semantics are course-specific
The student H5 mobile design system SHALL present the composer workbench as a course-learning control surface rather than a generic consumer chat toolbar.

#### Scenario: Plus action uses course context semantics
- **WHEN** the workbench displays the `+` action
- **THEN** its accessible label and any visible supporting UI MUST describe injecting or using learning background context
- **AND** it MUST NOT use attachment, upload, media, microphone, or model-selection language.

#### Scenario: Unsupported controls remain absent
- **WHEN** the workbench renders in compact, expanded, scrollable, or loading states
- **THEN** it MUST NOT display unsupported upload, attachment, model-picker, microphone, voice-waveform, image-generation, or external-service controls
- **AND** visual space reserved for possible future controls MUST NOT imply those unsupported actions are currently available.

#### Scenario: Workbench remains visually quiet
- **WHEN** the composer is empty or contains short text
- **THEN** the workbench MUST preserve the calm bottom-weighted Atom root composition
- **AND** the composer MUST NOT become a dense toolbar that competes with the welcome group, history action, new-chat action, or generated follow-up chips.

### Requirement: Chat body text uses one mobile reading scale
The student H5 mobile design system SHALL treat chat body reading and writing text as one typography role.

#### Scenario: Body text scale is shared across chat surfaces
- **WHEN** root composer text, user message body text, assistant message body text, or Markdown paragraph/list body text is displayed
- **THEN** those surfaces MUST use the same mobile chat body font family, size, line-height, weight, and letter spacing
- **AND** the size SHOULD use the existing mobile large text token rather than introducing a one-off midpoint size.

#### Scenario: Non-body text remains separate
- **WHEN** chat headers, welcome text, metadata, badges, progress states, quick prompts, or code snippets render
- **THEN** those elements MUST remain allowed to use distinct typography appropriate to their function.

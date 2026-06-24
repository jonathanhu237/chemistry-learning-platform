## ADDED Requirements

### Requirement: Root Atom assistant handles mobile keyboard focus
The student H5 `/ai` root assistant SHALL enter a keyboard-aware layout when the root composer is focused on a phone viewport.

#### Scenario: Root composer focus hides app navigation
- **WHEN** an authenticated student focuses the `/ai` root assistant composer on a phone viewport
- **THEN** the app MUST hide the bottom Atom navigation while the composer remains focused
- **AND** the hidden navigation MUST NOT receive pointer events
- **AND** the focused composer and send action MUST remain visible and reachable above the expected soft keyboard area.

#### Scenario: Root composer uses visible viewport
- **WHEN** the `/ai` root assistant is keyboard-active and the browser exposes a reduced visual viewport
- **THEN** the root assistant surface MUST size itself against the visible viewport rather than the old full `100dvh` page height
- **AND** the root assistant MUST NOT reserve the bottom navigation height while the bottom navigation is hidden
- **AND** the area between the composer and the keyboard edge MUST NOT reveal an unrelated raw page background band.

#### Scenario: Root empty welcome remains visible above keyboard
- **WHEN** the `/ai` root assistant has no messages and the root composer is keyboard-active
- **THEN** the Atom welcome pictogram and welcome phrase MUST remain visible in the chat content area above the composer
- **AND** the welcome group MUST shift upward from its normal empty-state placement so it is not obscured by the composer or expected soft keyboard area
- **AND** the welcome group MUST remain part of the chat stream rather than a fixed overlay that could cover future messages or controls.

#### Scenario: Root welcome yields to actual text entry
- **WHEN** the `/ai` root assistant has no messages and the root composer is focused but empty
- **THEN** the Atom welcome pictogram and welcome phrase MAY remain visible as the empty chat prompt
- **WHEN** the student enters non-whitespace text into the root composer
- **THEN** the textarea placeholder MUST naturally disappear
- **AND** the Atom welcome group MUST disappear until the composer is cleared or a new empty root chat is started.

#### Scenario: Root composer grows before becoming scrollable
- **WHEN** the student enters multi-line text in the `/ai` root composer
- **THEN** the composer SHOULD grow upward with the content while the textarea's natural content height does not exceed approximately `61.8%` of the effective chat panel height
- **AND** the send action MUST remain inside the composer and reachable at the bottom-right of the input capsule
- **WHEN** the textarea's natural content height would exceed approximately `61.8%` of the effective chat panel height
- **THEN** the composer MUST stop growing
- **AND** the textarea content MUST become vertically scrollable inside the composer instead of expanding the page or pushing the composer behind the soft keyboard.

#### Scenario: Root keyboard state restores normal chrome
- **WHEN** focus leaves the `/ai` root composer or the soft keyboard is dismissed
- **THEN** the bottom Atom navigation MUST become visible again on the `/ai` root
- **AND** the root assistant surface MUST return to the normal bottom-navigation-aware layout
- **AND** existing chat messages, local history identity, current input text, history action, and new-chat action MUST remain intact.

#### Scenario: Contextual Atom chat is not affected
- **WHEN** a student opens contextual `/ai/chat` from another page and focuses its composer
- **THEN** the contextual chat route MUST continue to hide bottom navigation according to detail-route rules
- **AND** it MUST NOT show root-only history or new-chat actions
- **AND** it MUST NOT depend on the `/ai` root keyboard-active state to remain usable.

#### Scenario: System keyboard chrome is outside app control
- **WHEN** the mobile input method shows its own toolbar, emoji row, microphone row, or language controls
- **THEN** the student H5 app MUST NOT attempt to control or hide those operating-system keyboard controls
- **AND** the app MUST only adjust its own bottom navigation, route content height, and assistant composer placement.

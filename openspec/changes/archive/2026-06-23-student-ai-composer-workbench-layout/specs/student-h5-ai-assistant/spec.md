## ADDED Requirements

### Requirement: Root composer has a fixed workbench zone
The student H5 Atom root composer SHALL separate text entry from a fixed composer workbench for supported chat actions.

#### Scenario: Compact composer renders before multi-line input
- **WHEN** the `/ai` root assistant renders with no composer text or with text that fits in one visual line
- **THEN** the composer MUST retain a compact race-track capsule appearance
- **AND** the composer MUST show a left-side background-knowledge `+` action and a right-side send action inside the same composer surface
- **AND** the text entry lane MUST remain usable between those actions
- **AND** placeholder or typed text MUST be vertically centered on the same visual row as those actions.

#### Scenario: Composer expands for multi-line input
- **WHEN** the student enters text that no longer fits in the compact one-line lane
- **THEN** the composer MUST transition to an expanded rounded-rectangle state
- **AND** the textarea MUST occupy an upper input zone
- **AND** the `+` action and send action MUST occupy a lower workbench zone inside the composer.

#### Scenario: Expansion threshold uses compact lane width
- **WHEN** the student enters boundary-length text that wraps in the compact race-track text lane
- **THEN** the composer MUST remain expanded even if the same text would fit on one line in the wider expanded textarea zone
- **AND** the composer MUST NOT oscillate between compact and expanded modes because the current rendered textarea width changed.

#### Scenario: Single-character input remains compact
- **WHEN** the student enters a single visible character into the root Atom composer
- **THEN** the composer MUST remain in the compact race-track state
- **AND** any hidden compact measurement textarea MUST mirror the visible compact textarea's one-row configuration rather than using the browser's multi-row default.

#### Scenario: Text cannot occupy the workbench
- **WHEN** the composer is expanded or internally scrollable
- **THEN** typed text MUST NOT overlap, push, resize, or visually occupy the workbench zone
- **AND** the workbench zone MUST remain reserved for composer actions.

### Requirement: Composer workbench controls remain position-invariant
The student H5 Atom composer SHALL keep workbench actions visually anchored across composer states.

#### Scenario: Workbench action positions are stable
- **WHEN** the composer changes between compact, expanded, scrollable, keyboard-active, and loading states
- **THEN** the left-side `+` action MUST remain visually anchored to the left side of the workbench
- **AND** the send action MUST remain visually anchored to the right side of the workbench
- **AND** neither action MUST jump vertically because the textarea content grows.

#### Scenario: Loading preserves workbench geometry
- **WHEN** the student submits a question and the assistant turn is loading or streaming
- **THEN** the send action MAY show a loading or disabled state
- **AND** the workbench layout MUST NOT move, collapse, or change the `+` action position.

#### Scenario: Long text scrolls above the workbench
- **WHEN** the textarea's natural content height would make the outer composer exceed the configured root composer growth budget
- **THEN** the textarea MUST become internally scrollable in the upper input zone
- **AND** the lower workbench actions MUST remain visible and reachable without scrolling the composer actions away.

#### Scenario: Growth budget applies to the outer composer
- **WHEN** the root composer is expanded or scrollable
- **THEN** the combined outer composer height, including input zone, composer padding, and workbench row, MUST stay within the configured `61.8%` effective panel-height budget
- **AND** the textarea height MUST be calculated from the remaining budget after the fixed workbench row and composer padding are reserved.

### Requirement: Plus action injects background knowledge
The student H5 Atom composer SHALL treat the `+` action as a course-background knowledge affordance rather than an unsupported attachment affordance.

#### Scenario: Student activates plus with available context
- **WHEN** the student activates the composer `+` action and the current assistant context has available learning background such as video-point, catalog-point, experiment, assessment-report, or page context
- **THEN** the app MUST expose or apply that background knowledge as context for the next assistant turn
- **AND** the interaction MUST communicate that the action is about learning context or background knowledge.

#### Scenario: Plus does not imply uploads
- **WHEN** the root composer renders the `+` action
- **THEN** the app MUST NOT present the action as file upload, attachment selection, image selection, model selection, microphone input, or voice input
- **AND** the action MUST NOT introduce unsupported upload or attachment controls.

#### Scenario: No background context is available
- **WHEN** the student activates the `+` action and no usable background knowledge is available
- **THEN** the app MUST keep the composer usable for free-form text input
- **AND** the app MUST NOT block sending a manually typed question.

### Requirement: Composer workbench preserves existing Atom chat states
The student H5 Atom composer workbench SHALL preserve the existing root and contextual chat behavior while changing the composer internals.

#### Scenario: Empty welcome behavior remains
- **WHEN** the root assistant has no messages and no non-whitespace composer text
- **THEN** the Atom welcome group MAY remain visible according to the existing empty-state rules
- **AND** introducing the workbench MUST NOT force the welcome group to disappear before the student enters text.

#### Scenario: Typed text still clears root welcome
- **WHEN** the student enters non-whitespace text into the root composer
- **THEN** the root welcome group MUST disappear according to the existing text-entry rule
- **AND** the composer workbench MUST remain visible.

#### Scenario: Contextual chat remains distinct
- **WHEN** a student opens contextual `/ai/chat` from another page
- **THEN** the contextual route MUST preserve its detail-route navigation and context behavior
- **AND** root-only history or new-chat affordances MUST NOT appear because of the composer workbench change
- **AND** any reused workbench layout MUST NOT erase the distinction between root and contextual chat.

#### Scenario: Follow-up prompt chips remain outside composer workbench
- **WHEN** model-generated follow-up prompt chips are displayed after a successful assistant turn
- **THEN** those chips MUST remain post-turn prompt suggestions outside the pre-send composer workbench
- **AND** they MUST NOT move into, resize, or replace the `+` and send workbench actions.

### Requirement: Conversational body typography is consistent
The student H5 Atom chat SHALL use one shared body typography treatment for the primary reading and writing surfaces.

#### Scenario: Root text entry matches message body
- **WHEN** the root Atom composer renders placeholder text or typed student text
- **THEN** that root textarea body text MUST use the same font family, font size, line-height, font weight, and letter spacing as chat message body text.

#### Scenario: Markdown body matches message body
- **WHEN** assistant Markdown paragraphs or list items render inside a message bubble
- **THEN** those paragraph and list body lines MUST use the same font family, font size, line-height, font weight, and letter spacing as plain message body text.

#### Scenario: Supporting labels keep their hierarchy
- **WHEN** titles, status badges, metadata labels, quick prompt chips, history labels, or inline code render
- **THEN** they MAY use their existing specialized typography
- **AND** the body typography unification MUST NOT flatten those supporting hierarchy levels.

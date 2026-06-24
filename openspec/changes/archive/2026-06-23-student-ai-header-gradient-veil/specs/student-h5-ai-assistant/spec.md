## ADDED Requirements

### Requirement: Root assistant header uses an integrated gradient veil
The student H5 Atom root assistant SHALL render its title row as a root-only translucent overlay whose own background veil fades from a more protective top edge to a transparent lower edge.

#### Scenario: Empty root assistant shows translucent title chrome
- **WHEN** an authenticated student opens the `/ai` root with no visible chat turns
- **THEN** the top title row MUST render `Atom 学习助手` as fully opaque foreground text
- **AND** the title row MUST use a transparent gradient veil as its background layer
- **AND** the veil MUST be part of the header itself rather than a separate extra region below the header
- **AND** the veil MUST fade to transparent at the lower edge so the root assistant canvas remains visually continuous.

#### Scenario: Content exists behind the root header
- **WHEN** root assistant messages, restored history, or the empty welcome group occupy the root chat stream
- **THEN** the stream content MUST be able to visually pass behind the root header overlay during scroll or layout
- **AND** the header veil MUST soften the underlying content near the title row instead of blocking it with a hard opaque header background
- **AND** the header title and root action controls MUST remain readable above that underlying content.

#### Scenario: Header veil does not duplicate the page background
- **WHEN** the root assistant header renders over the root assistant canvas
- **THEN** the header MUST NOT copy the root panel's radial-gradient glow background or any full page background stack into the header
- **AND** the root assistant's warm paper, pale yellow-green, and sage-green canvas background MUST continue to be painted by the root assistant canvas as the single source of background truth
- **AND** the header veil MUST be a simple semi-transparent tint or gradient layer that has no independent glow alignment requirement.

#### Scenario: Header foreground remains fully opaque
- **WHEN** the root assistant header renders its title and actions
- **THEN** the implementation MUST NOT use whole-header opacity that fades the title, icons, hit targets, or action capsule
- **AND** any veil, pseudo-element, mask, or similar background layer MUST be layered behind the title and actions.

#### Scenario: Header veil uses alpha gradient rather than blur
- **WHEN** the root assistant header overlays scrollable chat content
- **THEN** the veil MUST make underlying content progressively less visible toward the top through translucent gradient opacity stops
- **AND** the primary translucency effect MUST NOT rely on `backdrop-filter`, blur, or whole-header opacity
- **AND** the foreground title and action capsule MUST remain sharp and fully opaque.

### Requirement: Root assistant actions use one protected capsule
The student H5 Atom root assistant SHALL protect its root-only history and new-chat actions with one compact capsule while keeping the actions visually lightweight.

#### Scenario: Root actions render in one capsule
- **WHEN** the `/ai` root assistant header renders
- **THEN** the history action and new-chat action MUST sit inside a single rounded capsule with a real local background
- **AND** each action MUST occupy one half of the capsule's visual width
- **AND** the capsule MUST align with the title row rather than appearing as two separate cards.

#### Scenario: Action capsule preserves existing behavior
- **WHEN** the student activates the history half of the capsule
- **THEN** the app MUST open the existing root chat history UI without leaving the AI root route
- **WHEN** the student activates the new-chat half of the capsule
- **THEN** the app MUST preserve the existing new root chat behavior
- **AND** the visual capsule change MUST NOT alter local history storage, restored conversation turns, or assistant request payloads.

#### Scenario: Contextual chat does not inherit root capsule
- **WHEN** a student opens the contextual `/ai/chat` detail route from another page
- **THEN** the contextual chat page MUST NOT render the root history/new-chat capsule
- **AND** contextual detail header/navigation behavior MUST remain distinct from the root assistant overlay.

### Requirement: Root header veil preserves established Atom chat states
The student H5 Atom root header veil SHALL coexist with the established root welcome, composer, keyboard-aware layout, and conversation states without changing their state machines.

#### Scenario: Root welcome remains governed by input state
- **WHEN** the root assistant has no messages and no non-whitespace composer text
- **THEN** the Atom welcome group MUST remain governed by the existing empty-state rule
- **AND** adding the header veil MUST NOT force the welcome group to disappear
- **WHEN** the student enters non-whitespace composer text
- **THEN** the welcome group MUST still disappear according to the existing text-entry rule.

#### Scenario: Composer geometry is unchanged by header veil
- **WHEN** the root composer changes between compact, expanded, scrollable, loading, and keyboard-active states
- **THEN** the header veil change MUST NOT alter compact lane measurement, compact-to-expanded threshold, `61.8%` composer growth budgeting, workbench action placement, or internal textarea scrolling behavior.

#### Scenario: Keyboard-active layout remains stable
- **WHEN** the root composer is focused and the mobile keyboard is expected to be open
- **THEN** the bottom navigation hiding behavior, visual-viewport sizing, composer bottom breathing gap, and keyboard-active welcome positioning MUST continue to follow the existing keyboard-aware layout contract
- **AND** the header veil MUST NOT create a new top gap, bottom gap, or exposed raw page background band.

#### Scenario: Root header layout states are explicit
- **WHEN** the `/ai` root assistant renders
- **THEN** the implementation MUST distinguish empty-welcome, no-message draft, and conversation/restored-message layout states with explicit classes, data attributes, or equivalently specific selectors
- **AND** the implementation MUST NOT use one shared root stream padding rule to represent all root states
- **AND** keyboard-active styling MAY add its own modifier, but it MUST preserve the empty/draft/conversation state distinction.

#### Scenario: Empty root welcome does not inherit message scroll spacing
- **WHEN** the root assistant has no messages and no non-whitespace composer text
- **THEN** the Atom welcome group MUST keep the established empty-state placement
- **AND** the root stream MUST NOT receive conversation-only header top padding or scroll-padding
- **AND** the header overlay MUST NOT create a scrollbar, bottom compression, or downward shift in the empty welcome state
- **AND** the composer and bottom navigation MUST keep their existing anchored positions.

#### Scenario: No-message draft state hides welcome without becoming conversation layout
- **WHEN** the root assistant has no messages
- **AND** the student enters non-whitespace composer text
- **THEN** the welcome group MUST disappear according to the existing input-state rule
- **AND** the root panel MUST still reserve or protect the title/header area without adding conversation-only message scroll padding
- **AND** the composer geometry MUST remain governed by the established compact, expanded, scrollable, and keyboard-active state machine.

#### Scenario: Conversation root applies header-safe scroll spacing only to messages
- **WHEN** root assistant messages, restored history, or a running assistant turn are present
- **THEN** the root stream MUST use the conversation layout that allows content to visually pass behind the header veil
- **AND** only this conversation/restored-message state MUST add header-safe top padding, scroll-padding, or equivalent first-content spacing
- **AND** quick prompts and the root composer MUST remain in their existing bottom rows without being pushed by empty-state header spacing.

#### Scenario: Conversation root scrolls without visible desktop scrollbar chrome
- **WHEN** root assistant conversation or restored-message content exceeds the visible stream height
- **THEN** the root chat stream MUST remain internally scrollable
- **AND** desktop, iframe, or teacher-preview environments MUST NOT render a persistent visible scrollbar over the phone canvas
- **AND** hiding scrollbar chrome MUST NOT disable touch, pointer, wheel, keyboard, or programmatic scrolling
- **AND** empty-welcome and no-message draft states MUST keep their established overflow behavior.

#### Scenario: Header overlay selector wins the CSS cascade
- **WHEN** root header overlay styles override generic root layering styles
- **THEN** the root header overlay selector MUST be at least as specific as any generic root header selector that sets `position`, `z-index`, or pointer interaction
- **AND** generic root foreground-layer rules MUST NOT accidentally force `.ai-chat-head.root` back to non-overlay positioning
- **AND** regression tests MUST verify the effective scoped selector/cascade contract, not only the presence of lower-specificity declarations.

#### Scenario: Mobile viewport QA covers the header veil
- **WHEN** root assistant visual QA runs for 360px, 390px, and 430px CSS-pixel-wide phone viewports
- **THEN** the QA MUST check the empty state, at least one message state, restored-history or scroll-near-top state, and keyboard-active focused state
- **AND** each checked state MUST avoid clipped title text, unreadable actions, horizontal overflow, and hard opaque header blocking.

### Requirement: Root assistant successful replies use a flat canvas turn
The student H5 Atom root assistant SHALL render successful assistant replies as flat text turns on the root chat canvas instead of white card-style bubbles.

#### Scenario: Successful root assistant reply is not a card
- **WHEN** an authenticated student asks a question on the `/ai` root route
- **AND** Atom completes a successful assistant response
- **THEN** the assistant reply MUST render as a full-width flat content turn on the root assistant canvas
- **AND** the successful assistant reply MUST NOT use the previous white card background, bordered card shell, or card-like shadow as its primary surface
- **AND** the root canvas background MUST remain visible around the reply text
- **AND** the reply text MUST keep the established Atom chat body font family, font size, line height, font weight, and zero letter spacing.

#### Scenario: User question remains a right-aligned bubble
- **WHEN** the root conversation contains both a user question and a successful Atom reply
- **THEN** the user question MUST remain visually distinct as a right-aligned green bubble
- **AND** removing the assistant reply card MUST NOT make user messages full-width
- **AND** long user messages MUST remain constrained enough to read as user-authored bubbles.

#### Scenario: Flat reply supports long educational Markdown
- **WHEN** a successful root assistant reply contains paragraphs, headings, lists, strong text, inline code, formulas, or markdown fallback text
- **THEN** the flat reply MUST preserve readable vertical rhythm and wrapping
- **AND** the content MUST avoid horizontal overflow on common phone widths
- **AND** the reply MUST use the available text width better than the previous card layout without colliding with the phone frame, composer, or header overlay.

### Requirement: Root assistant turn actions delimit successful replies
The student H5 Atom root assistant SHALL use a lightweight action row below each successful root assistant reply as the primary turn delimiter.

#### Scenario: Successful root assistant reply shows an action row
- **WHEN** a root assistant reply reaches a successful final state
- **THEN** the reply MUST show an action row below the answer body
- **AND** the action row MUST visually separate that assistant turn from following content without reintroducing a full card shell
- **AND** the action row MUST be lower contrast than the answer text.

#### Scenario: Action row exposes behavior-backed controls
- **WHEN** the successful root assistant action row renders
- **THEN** the left side SHOULD include icon controls for positive feedback, negative feedback, and copying the assistant answer text
- **AND** every visible action control MUST have an accessible name and a phone-appropriate hit target
- **AND** controls that do not yet have behavior SHOULD be hidden or placed behind a future menu rather than rendered as misleading inactive affordances.

#### Scenario: Feedback controls are local unless backend feedback is specified
- **WHEN** the student taps positive or negative feedback for a root assistant reply
- **THEN** the first implementation MAY store that selection as local UI state only
- **AND** selecting positive feedback MUST clear negative feedback for that turn
- **AND** selecting negative feedback MUST clear positive feedback for that turn
- **AND** the implementation MUST NOT require a new backend endpoint or durable feedback schema unless a later spec explicitly defines it.

#### Scenario: Copy action copies only assistant answer text
- **WHEN** the student activates the copy action for a successful root assistant reply
- **THEN** the app MUST attempt to copy the assistant answer content
- **AND** it MUST NOT include hidden metadata, raw sources, RAG traces, system prompts, guardrail decisions, or dynamic follow-up chip text in the copied answer
- **AND** the UI SHOULD provide lightweight confirmation that copying succeeded when practical.

### Requirement: Root assistant citations stay student-safe in the action row
The student H5 Atom root assistant SHALL move successful-reply citation disclosure to the action row while preserving student-safe source privacy.

#### Scenario: Citation count appears on the action row right side
- **WHEN** a successful root assistant reply has `source_count` greater than zero or sanitized `sources` metadata with at least one item
- **THEN** the action row MUST show a right-aligned citation affordance with the safe citation count
- **AND** the citation affordance MUST remain visually secondary to the answer body
- **AND** it MUST align with the action row rather than occupying a separate card section.

#### Scenario: Raw source fields are not exposed
- **WHEN** root assistant metadata includes `sources`, raw RAG traces, chunk identifiers, source titles, source sections, scores, tool calls, or guardrail details
- **THEN** the root reply action row MUST NOT expose raw source titles, sections, scores, chunk IDs, RAG trace details, tool-call internals, teacher-only metadata, or guardrail internals
- **AND** existing student role-boundary protections MUST continue to reject direct rendering of raw source fields in the student assistant panel.

#### Scenario: Citation affordance is hidden when no sources exist
- **WHEN** a successful root assistant reply has no positive safe citation count
- **THEN** the action row MUST omit the citation affordance
- **AND** omitting citations MUST NOT disturb the left-side action cluster alignment.

### Requirement: Root assistant dynamic chips remain latest-successful next-turn suggestions
The student H5 Atom root assistant SHALL preserve dynamic follow-up chip behavior while adapting their placement to the flat reply surface.

#### Scenario: Chips appear after the latest successful assistant turn
- **WHEN** the latest root assistant response completes successfully with sanitized `suggested_prompts`
- **THEN** the dynamic chips MUST render after that reply's action row and before the composer
- **AND** the chips MUST be visually understood as next-turn suggestions rather than metadata inside the answer body.

#### Scenario: Older suggestions are ignored
- **WHEN** the conversation contains multiple prior successful root assistant replies with suggested prompts
- **THEN** only the latest successful assistant reply's sanitized suggestions MUST be considered for visible chips
- **AND** older assistant suggestions MUST NOT remain visible once a newer successful assistant reply has completed.

#### Scenario: Chips remain hidden during loading and error states
- **WHEN** Atom is streaming a root assistant reply
- **THEN** dynamic chips MUST be hidden or disabled according to the established loading behavior
- **WHEN** the latest root assistant turn fails
- **THEN** dynamic chips MUST remain hidden
- **AND** a failed turn MUST NOT reuse the previous successful reply's suggestions.

### Requirement: Root flat replies preserve assistant state semantics
The student H5 Atom root assistant SHALL keep running and failed assistant states clear while successful replies use the flat turn model.

#### Scenario: Running root assistant turn has lightweight status
- **WHEN** Atom is generating a root assistant response
- **THEN** the active assistant turn MAY show a lightweight generating indicator and streaming text or skeleton
- **AND** the running indicator MUST not become a persistent success header after final completion
- **AND** streaming text MUST remain readable on the root canvas.

#### Scenario: Failed root assistant turn remains visibly bounded
- **WHEN** the latest root assistant turn fails
- **THEN** the error message MAY remain in a distinct error block or bounded error treatment
- **AND** the failed turn MUST not render the successful-reply action row
- **AND** the failed turn MUST not render dynamic follow-up chips.

#### Scenario: Contextual assistant route keeps its distinct surface
- **WHEN** a student opens the contextual `/ai/chat` detail route
- **THEN** the contextual chat page MUST NOT inherit the root-only flat successful reply styling unless explicitly scoped
- **AND** contextual detail header, contextual reset behavior, and detail-route message boundaries MUST remain distinct from the root Atom assistant page.

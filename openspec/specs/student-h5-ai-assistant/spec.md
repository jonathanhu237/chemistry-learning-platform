# student-h5-ai-assistant Specification

## Purpose
Define the student H5 AI chat surfaces, including direct composer-first root chat, contextual detail chat, optional starter behavior, unsupported-control boundaries, and local conversation history.
## Requirements
### Requirement: Mobile assistant starter surface
The student H5 AI root SHALL prioritize a direct mobile chat composer before any structured starter surface; starter prompts, if present, SHALL be secondary and MUST NOT block free-form asking.

#### Scenario: Student opens global assistant with no prior messages
- **WHEN** an authenticated student opens the `/ai` root with the default `learning_home` context and no chat turns
- **THEN** the app MUST render a mobile chat shell with a visible free-form composer
- **AND** the page MUST NOT require the student to choose a starter prompt, point, or intent before asking.

#### Scenario: Optional starter appears without occupying the primary flow
- **WHEN** optional starter prompts or question directions are shown before the first turn
- **THEN** they MUST remain visually secondary to the free-form composer
- **AND** they MUST NOT reoccupy the entire chat area after the first sent question.

#### Scenario: Starter copy stays student-facing
- **WHEN** optional starter copy renders labels, descriptions, status, or preview text
- **THEN** the copy MUST use student-facing learning language
- **AND** it MUST NOT expose teacher/admin diagnostics, policy codes, raw retrieval traces, or implementation jargon.

### Requirement: Starter intent choices
When the student H5 assistant exposes compact learning-intent choices inspired by the teacher learning assistant, those choices SHALL remain optional secondary controls that preserve direct free-form asking.

#### Scenario: Optional structured starter intents are exposed
- **WHEN** the implementation exposes optional starter intents for `learning_profile`, `catalog_profile`, `catalog_point`, or `learning_point` contexts
- **THEN** the starter surface MUST offer student-readable choices such as observation, phenomenon explanation, principle explanation, or mistake review
- **AND** it MUST include experiment design or comparison intents only when the context contains experiment or point information.

#### Scenario: Intent choice is selected
- **WHEN** the student taps an optional starter intent
- **THEN** the app MUST mark that intent as selected
- **AND** it MUST make the text that will be sent unambiguous before submission.

#### Scenario: Student chooses custom asking
- **WHEN** the student selects a custom asking intent
- **THEN** the app MUST preserve the active assistant context
- **AND** it MUST guide the student to type their own question rather than sending an empty or generic prompt.

### Requirement: Starter question preview and launch
The student H5 assistant SHALL only show starter previews when an optional structured starter is active, and the preview MUST NOT replace the direct composer as the default first-screen action.

#### Scenario: Preview is available for selected optional intent
- **WHEN** the active context and selected optional intent can produce a starter question
- **THEN** the app MUST display a student-readable preview region
- **AND** the preview MUST include the relevant context title or point title when available.

#### Scenario: Student launches optional starter question
- **WHEN** the student activates the optional starter launch action
- **THEN** the app MUST submit the previewed question through the existing student assistant stream endpoint
- **AND** the request MUST include the active `AssistantContext` fields already used by the student assistant.

#### Scenario: Preview and composer both contain text
- **WHEN** a starter preview exists and the student has also typed free-form input
- **THEN** the app MUST make the sent text unambiguous
- **AND** it MUST either send the typed input with the active context or clearly label separate actions for sending the preview versus the typed input.

### Requirement: Active context header
The student H5 assistant SHALL make active contextual chat understandable and dismissible without duplicating separate "current content" cards on the first screen.

#### Scenario: Global context is active
- **WHEN** the assistant context is the default `learning_home`
- **THEN** the root chat shell MUST identify the assistant as a global course Q&A entry
- **AND** it MUST avoid implying that a chapter, experiment, or point is bound.

#### Scenario: Learning or catalog context is active
- **WHEN** the assistant context is provided by a chapter, catalog profile, catalog point, point handoff, video result, or assessment report
- **THEN** the contextual chat shell MUST show the context title and a concise context type cue
- **AND** the subsequent assistant request MUST include available `chapter_id`, `experiment_id`, `point_key`, and `context_summary` values.

#### Scenario: Student clears context
- **WHEN** the student activates the context clear action
- **THEN** the app MUST return to the default `learning_home` assistant context
- **AND** the UI MUST make clear whether existing chat turns were preserved or a new global chat state was started.

### Requirement: Optional experiment starter data
The student H5 assistant SHALL remain useful without loading optional experiment starter data in the global AI root.

#### Scenario: Experiment starter data is not loaded
- **WHEN** the global AI root opens before experiment starter data is available or if an experiment request fails
- **THEN** the direct chat composer MUST remain usable
- **AND** student asking MUST NOT be blocked on experiment data loading.

#### Scenario: Experiment module starter is exposed later
- **WHEN** a later implementation exposes an optional experiment-question path using student-visible modules
- **THEN** the starter MUST load those modules through existing student APIs
- **AND** it MUST NOT introduce a new backend starter-suggestion contract unless a later change explicitly adds one.

### Requirement: Grok-like root assistant visual target
The student H5 `AI` root SHALL learn the provided Grok-style mobile chat target's layout grammar and sizing rhythm while remaining a bright static chemistry-course interface.

#### Scenario: Root assistant fills available phone space
- **WHEN** the `AI` root renders at 360px to 430px CSS-pixel phone widths
- **THEN** the assistant surface MUST occupy the available route width and height without appearing as a floating card
- **AND** the `/ai` root MUST NOT render the normal fixed root-page `StudentAppHeader` above the assistant surface
- **AND** the route content and root assistant panel MUST begin at the top of the student page frame while still respecting safe-area and bottom-navigation constraints
- **AND** the chat composer MUST remain above the bottom navigation with visible separation.

#### Scenario: Root layout follows Grok vertical rhythm
- **WHEN** the root assistant first screen renders with no messages
- **THEN** the screen MUST use a light top bar, a large calm middle space, and bottom-weighted interaction area
- **AND** the empty first screen SHOULD show the Atom AI identity pictogram centered above the welcome line `从一个实验开始吧！`
- **AND** the welcome group MUST NOT include a card frame, subtitle, or explanatory copy
- **AND** the middle of the screen MUST remain mostly open rather than filled with cards, grids, explanations, or prompt stacks
- **AND** root chat shortcuts, if introduced later, MUST use compact low-position chips rather than large centered cards.

#### Scenario: Root assistant top identity is lightweight
- **WHEN** the root assistant first screen renders
- **THEN** the top identity area MUST render as a minimal chat-app title bar centered on `Atom 学习助手`
- **AND** the history and new-chat actions MUST appear as compact icon-only actions near the top-right of the chat surface and inline with the title row
- **AND** those actions MUST blend into the assistant background rather than appearing as framed cards
- **AND** the title row SHOULD stay close to a 52px to 56px visual height on common phone widths
- **AND** the root top identity MUST NOT show the previous `课程 AI` label, duplicated context title, global-course description, or explanatory summary block
- **AND** the identity area MUST NOT become a framed intro card.

#### Scenario: Static learning-page background is used
- **WHEN** the root assistant idle surface renders
- **THEN** it SHOULD use a near-white paper-like static background inspired by the student learning pages
- **AND** the background glow SHOULD reuse the student learning pages' warm paper, pale yellow-green, and light sage-green language rather than introducing a cold Tiffany or blue-mint wash
- **AND** the root assistant MUST NOT render animated star, particle, meteor, or canvas background effects
- **AND** the static background MUST sit behind all interactive content and not block scrolling, typing, sending, history, new-chat, or bottom navigation controls.

#### Scenario: Context description is not duplicated on root
- **WHEN** the root assistant first screen renders with no messages
- **THEN** the page MUST NOT show a separate fixed header or descriptive intro section above the empty chat surface
- **AND** the root assistant MAY show the Atom AI identity pictogram above the single centered welcome line `从一个实验开始吧！`
- **AND** the root assistant MUST NOT show a first-screen starter prompt card or explanatory copy block above the composer.

#### Scenario: Student starts a new root chat
- **WHEN** the student activates the root top-bar new-chat action
- **THEN** the root chat shell MUST clear the visible conversation turns and composer state
- **AND** it MUST return to the default global `learning_home` assistant context
- **AND** it MUST NOT delete existing local history entries.

#### Scenario: Unsupported controls are absent
- **WHEN** the root assistant composer renders
- **THEN** the composer MUST expose only supported text-entry and send controls
- **AND** it MUST NOT show upload, attachment, model picker, microphone, voice waveform, image generation, or external X/Grok controls.

#### Scenario: Root composer prompt matches experiment learning
- **WHEN** the root assistant composer renders before the student types
- **THEN** the placeholder SHOULD read `问实验现象、步骤或原理`
- **AND** the placeholder MUST NOT use generic open-chat phrasing such as `随便问点什么`
- **AND** contextual detail assistant routes SHOULD use a separate current-content placeholder rather than the root experiment-starting placeholder.

#### Scenario: Send action is embedded in composer
- **WHEN** the root assistant composer renders
- **THEN** the send action MUST sit visually inside the composer container rather than as a separate external button beside it
- **AND** the composer MUST read as a single rounded bottom chat capsule with a larger vertical presence than a standard form field
- **AND** the root composer SHOULD target approximately 82px minimum height and a large rounded radius near 24px on common phone widths
- **AND** the root composer SHOULD follow the reference page's spacing rhythm by using approximately 12px side margins from the phone surface and a compact 34px circular send action aligned to the bottom-right inside the capsule
- **AND** the composer MUST still expose a clear text input area and one supported send action.

#### Scenario: Root composer text-entry state replaces the empty welcome
- **WHEN** the root assistant has no messages and the student has not entered text
- **THEN** the Atom welcome pictogram and welcome phrase MAY occupy the empty chat stream
- **WHEN** the student enters non-whitespace text into the root composer
- **THEN** the textarea placeholder MUST disappear through normal textarea behavior
- **AND** the Atom welcome group MUST disappear until the input is cleared or a new empty root chat is started.

#### Scenario: Root composer grows before becoming scrollable
- **WHEN** the student enters multi-line text in the root assistant composer
- **THEN** the input capsule SHOULD grow upward with the content while the textarea's natural content height is at or below approximately `61.8%` of the effective chat panel height
- **AND** the embedded send action MUST remain reachable inside the capsule
- **WHEN** the natural content height would exceed approximately `61.8%` of the effective chat panel height
- **THEN** the input capsule MUST stop growing
- **AND** the textarea content MUST scroll vertically inside the capsule instead of expanding the page or hiding behind the soft keyboard.

### Requirement: Root AI chat history entry
The student H5 AI root SHALL provide a history entry point for reviewing prior student AI conversations from the AI root page.

#### Scenario: Student opens history from AI root
- **WHEN** an authenticated student opens the `/ai` root route
- **THEN** the page MUST show a student-readable history action in the root chat top area
- **AND** activating the action MUST open a history list, panel, or sheet without leaving the AI root route.

#### Scenario: Contextual chat omits history entry
- **WHEN** a student opens the contextual `/ai/chat` detail route from another page
- **THEN** the contextual chat page MUST NOT show the root history action
- **AND** history review MUST remain reachable by returning to the `/ai` root route.

### Requirement: First-round local conversation history
The student H5 AI chat SHALL persist first-round conversation history in client-side browser storage without requiring a backend chat-session migration.

#### Scenario: Root chat is saved
- **WHEN** a student sends a question from the `/ai` root chat shell
- **THEN** the app MUST create or update a local history entry for that conversation
- **AND** the entry MUST include enough information to restore visible user and assistant turns.

#### Scenario: Contextual chat is saved without exposing local history chrome
- **WHEN** a student sends a question from `/ai/chat`
- **THEN** the app MAY save the contextual conversation into the same local history store
- **AND** the contextual page MUST still omit the root history action.

#### Scenario: Student restores a local history entry
- **WHEN** a student selects a history entry from the `/ai` root history list
- **THEN** the root chat shell MUST restore the saved conversation turns
- **AND** follow-up questions MUST send recent restored turns as `conversation_history`.

#### Scenario: No local history exists
- **WHEN** the student opens the history panel and no local conversations are available
- **THEN** the app MUST show an empty state that explains there are no recent AI conversations
- **AND** the student MUST be able to return to the root chat composer.

### Requirement: History rows identify context
The student H5 AI history SHALL identify whether a conversation was global or contextual without exposing teacher/admin diagnostics.

#### Scenario: History row comes from global root chat
- **WHEN** a history entry was created from the `/ai` root route
- **THEN** the row MUST label it as a global course assistant conversation or equivalent student-facing copy.

#### Scenario: History row comes from contextual chat
- **WHEN** a history entry was created from a point, chapter, video result, or assessment context
- **THEN** the row MUST show a concise context title or context type cue
- **AND** it MUST NOT expose raw RAG traces, policy codes, internal node diagnostics, or admin-only metadata.

### Requirement: Dynamic follow-up prompts
The student H5 Atom assistant SHALL display model-generated follow-up prompts only for the latest successful assistant turn.

#### Scenario: Successful answer returns follow-up prompts
- **WHEN** the student assistant stream emits a successful `final` event for a completed answer
- **THEN** the final response MAY include `suggested_prompts` as an array of student-facing follow-up questions
- **AND** the H5 app MUST store those suggestions on that assistant turn's metadata
- **AND** the H5 app MUST render the suggestions in the quick prompt row when at least one valid suggestion is present.

#### Scenario: Suggestions are absent
- **WHEN** a successful `final` event does not include valid `suggested_prompts`
- **THEN** the H5 app MUST NOT render static fallback prompt chips for that turn
- **AND** the chat composer MUST remain usable for free-form student input.

#### Scenario: Turn is still streaming
- **WHEN** a student sends a question and the assistant turn is loading or streaming
- **THEN** the H5 app MUST hide any previous quick prompt suggestions
- **AND** it MUST NOT show new suggestions until the current turn receives a successful `final` event.

#### Scenario: Assistant turn fails
- **WHEN** the student assistant stream emits an `error` event or the frontend catches a failed assistant request
- **THEN** the H5 app MUST show no follow-up prompt chips for that failed turn
- **AND** stale suggestions from previous successful turns MUST remain hidden.

#### Scenario: New successful turn replaces previous suggestions
- **WHEN** a later assistant turn completes successfully with valid `suggested_prompts`
- **THEN** the quick prompt row MUST show only that latest turn's suggestions
- **AND** suggestions from earlier turns MUST NOT be accumulated, merged, or reused.

#### Scenario: Restored history has suggestions
- **WHEN** the student restores a local chat history entry whose latest assistant turn includes valid `suggested_prompts`
- **THEN** the H5 app MAY render those latest-turn suggestions
- **AND** activating a suggestion MUST submit it using the restored active context and restored visible conversation history.

### Requirement: Follow-up prompt stream contract
The student H5 assistant stream SHALL return follow-up prompts as sanitized student-only final metadata without changing the existing answer streaming contract.

#### Scenario: Backend attaches suggestions to final metadata
- **WHEN** `/api/student/assistant/ask/stream` completes a student answer successfully
- **THEN** the backend SHOULD attempt to generate follow-up prompts from the current student question, completed answer, active assistant context, and recent conversation history
- **AND** the backend MUST attach valid suggestions as `response.suggested_prompts` on the `final` event rather than as answer text.

#### Scenario: Suggestion generation fails
- **WHEN** the answer succeeds but follow-up suggestion generation fails, times out, returns malformed output, or filters to zero valid suggestions
- **THEN** the backend MUST still send the successful answer final event
- **AND** the backend MUST omit `suggested_prompts` or send it as an empty array
- **AND** the frontend MUST render no quick prompt chips for that turn.

#### Scenario: Suggestion count is sanitized
- **WHEN** the model returns follow-up suggestions
- **THEN** the backend MUST keep at most five valid suggestions
- **AND** the backend MAY return fewer than three suggestions when only one or two valid suggestions remain after filtering
- **AND** the frontend MUST display any valid suggestions returned by the backend.

#### Scenario: Suggestion text is sanitized
- **WHEN** a model-generated follow-up suggestion is evaluated for display
- **THEN** the backend MUST trim whitespace, remove empty values, remove duplicates, and reject suggestions outside the 8-24 visible-character range
- **AND** the backend MUST reject values that are not plain student-facing question strings.

#### Scenario: Static context prompts no longer drive post-turn chips
- **WHEN** a chat turn has started or completed
- **THEN** the H5 app MUST NOT render post-turn quick prompt chips from frontend-authored `AssistantContext.prompts`
- **AND** any retained `AssistantContext.prompts` field MUST NOT override latest-turn model-generated suggestions.

#### Scenario: Student activates a generated suggestion
- **WHEN** the student taps a displayed follow-up suggestion
- **THEN** the H5 app MUST submit the suggestion text through the existing student assistant stream path
- **AND** the request MUST include the current active assistant context and recent conversation history exactly as a manually typed follow-up would.

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
The student H5 Atom root assistant SHALL keep running and failed assistant states clear while successful replies use the flat turn model. Root running turns SHALL display the best available authentic visible thinking message from the stream: model reasoning summary first, real agent execution trace second, and legacy normalized status only as compatibility fallback.

#### Scenario: Running root assistant turn uses authentic visible thinking when available
- **WHEN** Atom is generating a root assistant response on the `/ai` root route
- **AND** the student assistant stream emits a valid `thinking` event
- **THEN** the root running line MUST display the sanitized `thinking.message`
- **AND** it MUST prefer that message over locally preset labels such as `正在生成回答`
- **AND** it MUST NOT append the thinking message to the answer body
- **AND** streaming answer text MUST remain readable on the root canvas.

#### Scenario: Model reasoning summary drives the running line
- **WHEN** a `thinking` event arrives with `source` equal to `reasoning_summary`
- **THEN** the root running line MUST treat the event message as the current visible thinking text
- **AND** the UI MUST NOT relabel it as a generic phase while it remains the latest valid thinking message
- **AND** the UI MUST NOT show raw source labels, provider names, model names, or debugging metadata beside the student-facing text.

#### Scenario: Agent trace fallback remains honest
- **WHEN** a `thinking` event arrives with `source` equal to `agent_trace`
- **THEN** the root running line MUST display the sanitized trace message as truthful agent progress
- **AND** the UI MUST NOT present the trace fallback as model chain-of-thought
- **AND** the displayed message MUST remain student-facing rather than diagnostic.

#### Scenario: Legacy status remains fallback
- **WHEN** Atom is generating a root assistant response and no valid `thinking` event has arrived for the active turn
- **THEN** the root running line MUST continue to derive a concise student-facing fallback label from the existing stream `status` and answer presence
- **AND** the fallback MUST use existing normalized labels such as judging scope, retrieving course material, returning learning suggestions, or generating an answer
- **AND** the UI MUST NOT expose raw backend policy wording, RAG labels, provider connection details, exception text, or implementation-specific status strings as the normal running label.

#### Scenario: Answer text does not erase fresh reasoning summary
- **WHEN** the active assistant turn receives streamed answer text through `delta`, `replace`, or equivalent response state
- **AND** the latest valid visible thinking message came from `reasoning_summary`
- **THEN** the root running line SHOULD keep the reasoning-summary message until a newer valid thinking event, final completion, or error replaces it
- **AND** the UI MUST NOT automatically overwrite it with generic `正在生成回答` solely because answer text exists.

#### Scenario: Thinking text changes preserve fade-through behavior
- **WHEN** the displayed root thinking text changes from one valid visible thinking message to another while the assistant turn is still running
- **THEN** the text MUST continue to use the established fade-through transition where the previous message fades away before the next message becomes visually prominent
- **AND** the transition MUST be keyed to actual displayed-message changes rather than a continuous timer
- **AND** the root running turn MUST preserve stable line height and avoid vertical jumping during replacement.

#### Scenario: Root running turn remains flat
- **WHEN** Atom is generating a root assistant response on the `/ai` root route
- **THEN** the active assistant turn MUST render on the root canvas as a flat full-width turn
- **AND** the active assistant turn MUST NOT use a white assistant card background, bordered card shell, card-like shadow, rounded loading card, skeleton block, or filled progress pill as its primary surface
- **AND** the active assistant turn MUST NOT render the repeated assistant meta row containing `Atom 学习助手` and `生成中`
- **AND** the active assistant turn MUST NOT render the successful-reply action row while it is still running
- **AND** the root canvas background MUST remain visible around the running turn.

#### Scenario: Running line remains accessible
- **WHEN** the root running line displays a visible thinking message
- **THEN** assistive technology SHOULD receive a polite status update for the current displayed text
- **AND** decorative marks, dots, Lottie animation, and outgoing fade-through labels MUST NOT cause duplicate announcements
- **AND** reduced-motion preferences MUST preserve the current text while reducing or disabling movement.

#### Scenario: Successful completion removes thinking status
- **WHEN** the active root assistant turn receives a successful `final` event and is no longer loading
- **THEN** the thinking line MUST be removed from the completed assistant turn
- **AND** the completed assistant reply MUST render as the established flat markdown answer with its lightweight action row
- **AND** the completed assistant reply MUST NOT retain visible thinking text, fallback status text, `Atom 学习助手`, `生成中`, or any other running-only status header as persistent success chrome.

#### Scenario: Failed root assistant turn remains visibly bounded
- **WHEN** the latest root assistant turn fails
- **THEN** the error message MAY remain in a distinct error block or bounded error treatment
- **AND** the failed turn MUST not render the successful-reply action row
- **AND** the failed turn MUST not render dynamic follow-up chips
- **AND** the failed turn MUST not keep the running thinking line as if generation were still in progress.

#### Scenario: Quick prompt chips remain hidden during root thinking
- **WHEN** Atom is streaming a root assistant reply and the thinking line is visible
- **THEN** dynamic follow-up prompt chips MUST be hidden or disabled according to the established loading behavior
- **AND** stale suggestions from previous successful turns MUST NOT be visible beside or below the running thinking line.

#### Scenario: Contextual assistant route keeps its distinct surface
- **WHEN** a student opens the contextual `/ai/chat` detail route
- **THEN** the contextual chat page MUST NOT inherit the root-only flat successful reply styling or root-only flat thinking-line styling unless explicitly scoped by a later change
- **AND** contextual detail header, contextual reset behavior, detail-route message boundaries, and existing detail-route running state behavior MUST remain distinct from the root Atom assistant page.

### Requirement: Root assistant supports learning-background attachment action
The student H5 Atom root assistant SHALL treat the composer `+` as a supported learning-background action while preserving direct free-form asking.

#### Scenario: Root assistant composer renders plus action
- **WHEN** the `/ai` root assistant composer renders
- **THEN** the `+` action MUST be available only as a learning-background picker entry
- **AND** it MUST NOT imply generic file upload, image upload, model selection, microphone input, or unsupported external tools.

#### Scenario: Student asks globally
- **WHEN** the student submits text from the root assistant without selecting a point
- **THEN** the assistant request MUST use the existing active global or restored context
- **AND** the UI MUST NOT block submission with a required point-selection step.

#### Scenario: Student asks with selected point
- **WHEN** the student submits text from the root assistant after selecting a point background
- **THEN** the assistant request MUST use the selected point `AssistantContext`
- **AND** the user-authored question text MUST be preserved without adding visible picker text into the question field.

### Requirement: Root assistant preserves bound context across local history
The student H5 Atom root assistant SHALL preserve selected point context when saving and restoring local chat history.

#### Scenario: Bound point chat is saved
- **WHEN** a student sends the first question from a root chat with a selected point
- **THEN** the local history entry for that conversation MUST include enough context to restore the selected point title, context type, ids, summary, and catalog path
- **AND** restoring the entry MUST continue sending follow-up turns with that restored point context.

#### Scenario: Global chat is saved
- **WHEN** a student sends from the root chat without selecting a point
- **THEN** the local history entry MUST remain a global Atom conversation
- **AND** restoring the entry MUST NOT show a false selected-point chip.

#### Scenario: New root chat starts from restored bound chat
- **WHEN** a restored bound-point conversation is visible
- **AND** the student activates the new-chat action
- **THEN** the root assistant MUST clear the visible conversation and selected point binding
- **AND** the new chat MUST use the default global context.

### Requirement: Root assistant communicates one-point lock
The student H5 Atom root assistant SHALL make the selected point binding understandable before and after the first submitted message.

#### Scenario: Selected point is editable before sending
- **WHEN** the root chat has a selected point and no submitted user message
- **THEN** the selected-point chip MUST communicate that this learning background will be used for the next question
- **AND** the student MUST be able to remove or replace the selected point before submitting.

#### Scenario: Selected point is locked after sending
- **WHEN** the root chat has submitted at least one user message with a selected point context
- **THEN** the selected-point chip MUST communicate that the chat is bound to that point
- **AND** the app MUST require a new chat before binding a different point.


## MODIFIED Requirements

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

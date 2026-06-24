## MODIFIED Requirements

### Requirement: Root flat replies preserve assistant state semantics
The student H5 Atom root assistant SHALL keep running and failed assistant states clear while successful replies use the flat turn model. Root running turns SHALL use a Gemini-inspired flat thinking line with animated dots and fade-through phase text instead of a card-like loading surface.

#### Scenario: Running root assistant turn uses a flat thinking surface
- **WHEN** Atom is generating a root assistant response on the `/ai` root route
- **THEN** the active assistant turn MUST render on the root canvas as a flat full-width turn
- **AND** the active assistant turn MUST NOT use the previous white assistant card background, bordered card shell, card-like shadow, or rounded card container as its primary surface
- **AND** the active assistant turn MUST NOT render the repeated assistant meta row containing `Atom 学习助手` and `生成中`
- **AND** the active assistant turn MUST NOT render the successful-reply action row while it is still running
- **AND** the root canvas background MUST remain visible around the running turn.

#### Scenario: Running root assistant turn shows a thinking line
- **WHEN** Atom is generating a root assistant response before final completion
- **THEN** the running turn MUST show a lightweight thinking line containing an animated dot cluster and a student-facing phase label
- **AND** the thinking line MUST read as inline conversation status rather than as a pill, badge, card, or separate loading panel
- **AND** the thinking line MUST NOT use a visible border, filled capsule background, or skeleton block as the primary waiting affordance
- **AND** the dot cluster MUST be visually secondary to the phase label and MUST NOT obscure or shift answer text.

#### Scenario: Phase label starts with scope judgment when policy status arrives
- **WHEN** the student assistant stream emits a `status` event whose message indicates question judgment, safety, scope, problem type, or policy strategy
- **THEN** the root thinking line MUST expose the normalized student-facing label `正在判断问题范围`
- **AND** the UI MUST use the normalized student-facing label rather than showing raw backend policy wording such as `正在判断问题类型与安全策略`.

#### Scenario: Phase label uses course retrieval language for retrieval status
- **WHEN** the student assistant stream emits a `status` event whose message indicates retrieval, course material, RAG, sources, data, or evidence lookup
- **THEN** the root thinking line MUST expose the normalized student-facing label `正在检索课程资料`
- **AND** the label MUST remain concise enough to fit common 360px to 430px phone widths without horizontal overflow.

#### Scenario: Phase label switches to answer generation after answer text appears
- **WHEN** the active assistant turn has received non-whitespace streamed answer text through `delta`, `replace`, or equivalent response state
- **THEN** the root thinking line MUST expose the normalized label `正在生成回答`
- **AND** the streamed answer text MUST remain readable on the root canvas below or after the thinking line
- **AND** the thinking line MUST NOT cover, overlap, or push the composer out of its established layout.

#### Scenario: Unknown running status falls back to generation copy
- **WHEN** Atom is generating a root assistant response and the stream status is missing, empty, unsupported, or implementation-specific
- **THEN** the root thinking line MUST fall back to a generic student-facing generating label such as `正在生成回答`
- **AND** the UI MUST NOT expose internal model connection details, fallback modes, raw policy codes, raw RAG trace labels, exception text, or developer-facing status strings as the normal running phase label.

#### Scenario: Phase label changes use fade-through transition
- **WHEN** the normalized root thinking phase changes from one label to another while the assistant turn is still running
- **THEN** the visible status text MUST transition with a fade-through effect in which the previous label fades out before the next label becomes visibly prominent
- **AND** the transition MUST be keyed to semantic phase changes rather than running on a continuous timer
- **AND** the incoming label SHOULD use a short delayed fade-in rather than starting at the exact same instant as the outgoing label fade-out
- **AND** semantic phases SHOULD remain visible long enough for students to perceive the stage change when backend status events arrive in quick succession
- **AND** the transition MUST NOT present the phase label as a perpetual blinking, pulsing, marquee, or typewriter effect
- **AND** the final visible label after the transition MUST exactly match the latest normalized phase.

#### Scenario: Fade-through keeps context during phase replacement
- **WHEN** a root thinking phase changes from `正在判断问题范围` to `正在检索课程资料`, `正在返回学习建议`, or `正在生成回答`
- **THEN** the outgoing label MUST remain visible long enough to fade away rather than disappearing as an instantaneous DOM replacement
- **AND** the incoming label MUST appear with a subtle fade-in, optionally with a small vertical settle or very light blur settle
- **AND** the text container MUST maintain stable line height so the running turn does not jump vertically during the phase replacement.

#### Scenario: Dots continue independently while text changes
- **WHEN** the root thinking phase label changes
- **THEN** the dot cluster SHOULD continue its thinking animation independently of the label fade-through
- **AND** the dot cluster MUST remain decorative and `aria-hidden`
- **AND** the dot cluster MUST use Atom-compatible ink or green-muted coloring rather than copying Gemini's dark-theme white-on-black palette.

#### Scenario: Successful completion removes thinking status
- **WHEN** the active root assistant turn receives a successful `final` event and is no longer loading
- **THEN** the thinking line MUST be removed from the completed assistant turn
- **AND** the completed assistant reply MUST render as the established flat markdown answer with its lightweight action row
- **AND** the completed assistant reply MUST NOT retain `正在判断问题范围`, `正在检索课程资料`, `正在返回学习建议`, `正在生成回答`, `Atom 学习助手`, `生成中`, or any other running-only status header as persistent success chrome.

#### Scenario: Reduced motion preserves meaning without movement
- **WHEN** the student device or browser requests reduced motion
- **THEN** the root thinking line MUST continue to show the current student-facing phase label
- **AND** dot movement, text translation, blur animation, and repeated opacity motion MUST be disabled or reduced to a minimal non-distracting opacity change
- **AND** changing phases MUST still update the visible label without requiring animation to understand the state.

#### Scenario: Thinking line is announced accessibly
- **WHEN** the root thinking line phase label changes while Atom is generating a response
- **THEN** assistive technology SHOULD receive a polite status update for the current phase label
- **AND** decorative dots and outgoing visual-only labels MUST NOT cause duplicate announcements
- **AND** the final answer text MUST remain reachable as normal message content after completion.

#### Scenario: Quick prompt chips remain hidden during root thinking
- **WHEN** Atom is streaming a root assistant reply and the thinking line is visible
- **THEN** dynamic follow-up prompt chips MUST be hidden or disabled according to the established loading behavior
- **AND** stale suggestions from previous successful turns MUST NOT be visible beside or below the running thinking line.

#### Scenario: Failed root assistant turn remains visibly bounded
- **WHEN** the latest root assistant turn fails
- **THEN** the error message MAY remain in a distinct error block or bounded error treatment
- **AND** the failed turn MUST not render the successful-reply action row
- **AND** the failed turn MUST not render dynamic follow-up chips
- **AND** the failed turn MUST not keep the running thinking line as if generation were still in progress.

#### Scenario: Contextual assistant route keeps its distinct surface
- **WHEN** a student opens the contextual `/ai/chat` detail route
- **THEN** the contextual chat page MUST NOT inherit the root-only flat thinking-line styling unless explicitly scoped by a later change
- **AND** contextual detail header, contextual reset behavior, detail-route message boundaries, and existing detail-route running state behavior MUST remain distinct from the root Atom assistant page.

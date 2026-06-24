## MODIFIED Requirements

### Requirement: Root flat replies preserve assistant state semantics
The student H5 Atom root assistant SHALL keep running and failed assistant states clear while successful replies use the flat turn model. Root running turns SHALL use a flat inline thinking line with an Atom Lottie thinking mark and a student-facing phase label instead of a generic animated dot cluster, card-like loading surface, or persistent success header.

#### Scenario: Running root assistant turn uses a flat thinking surface
- **WHEN** Atom is generating a root assistant response on the `/ai` root route
- **THEN** the active assistant turn MUST render on the root canvas as a flat full-width turn
- **AND** the active assistant turn MUST NOT use the previous white assistant card background, bordered card shell, card-like shadow, or rounded card container as its primary surface
- **AND** the active assistant turn MUST NOT render the repeated assistant meta row containing `Atom 学习助手` and `生成中`
- **AND** the active assistant turn MUST NOT render the successful-reply action row while it is still running
- **AND** the root canvas background MUST remain visible around the running turn.

#### Scenario: Running root assistant turn shows an Atom thinking line
- **WHEN** Atom is generating a root assistant response before final completion
- **THEN** the running turn MUST show a lightweight thinking line containing a decorative Atom Lottie animation mark and a student-facing phase label
- **AND** the thinking line MUST read as inline conversation status rather than as a pill, badge, card, or separate loading panel
- **AND** the thinking line MUST NOT use a visible border, filled capsule background, or skeleton block as the primary waiting affordance
- **AND** the Atom animation mark MUST replace the previous three-dot cluster for the root running turn
- **AND** the Atom animation mark MUST be visually secondary to the phase label and MUST NOT obscure, overlap, or shift answer text.

#### Scenario: Atom thinking mark uses local Lottie asset
- **WHEN** the root thinking line renders the Atom animation mark
- **THEN** the animation MUST be loaded from a bundled local Lottie JSON asset owned by `apps/web-student`
- **AND** the animation MUST NOT be loaded from a third-party animation CDN, remote embed URL, or runtime network request
- **AND** the animation asset MUST be vector-based without external image, font, or video resources
- **AND** the implementation MUST only bundle the provided asset when the product has appropriate rights for source control, web delivery, and student-facing production use.

#### Scenario: Atom thinking mark uses product color
- **WHEN** the Atom thinking animation is rendered in the root thinking line
- **THEN** its visible stroke or fill color MUST use the student service's main green visual system, such as `#005826` or the equivalent `--green` token
- **AND** the animation MUST NOT render with the downloaded asset's original pure black stroke in the shipped student app
- **AND** the animation color MUST remain compatible with the root assistant's warm paper background and the existing thinking label color.

#### Scenario: Atom thinking mark has stable inline geometry
- **WHEN** the Atom thinking line renders at 360px, 390px, or 430px CSS-pixel phone widths
- **THEN** the animation container MUST reserve a stable square or near-square inline footprint before and during playback
- **AND** the phase label MUST remain readable beside the mark without wrapping caused by animation frame changes
- **AND** the animation mark MUST NOT resize, push, or reflow the thinking text while it loops.

#### Scenario: Phase label starts with scope judgment when policy status arrives
- **WHEN** the student assistant stream emits a `status` event whose message indicates question judgment, safety, scope, problem type, or policy strategy
- **THEN** the root thinking line MUST expose the normalized student-facing label `正在判断问题范围`
- **AND** the UI MUST use the normalized student-facing label rather than showing raw backend policy wording such as `正在判断问题类型与安全策略`.

#### Scenario: Phase label moves to retrieval when evidence status arrives
- **WHEN** the stream emits a `status` event whose message indicates retrieval, RAG, course material, evidence, or learning resource lookup
- **THEN** the root thinking line MUST expose the normalized student-facing label `正在检索课程资料`.

#### Scenario: Phase label moves to returning when return status arrives
- **WHEN** the stream emits a `status` event whose message indicates returning or preparing learning suggestions
- **THEN** the root thinking line MUST expose the normalized student-facing label `正在返回学习建议`.

#### Scenario: Phase label moves to generation once answer text exists
- **WHEN** the active assistant turn has non-empty streamed answer content
- **THEN** the root thinking line MUST expose the normalized student-facing label `正在生成回答`
- **AND** the streamed answer text MUST remain visually distinct from the running-only thinking line.

#### Scenario: Unknown status falls back to generation
- **WHEN** Atom is generating a root assistant response and the stream status is missing, empty, unsupported, or implementation-specific
- **THEN** the root thinking line MUST expose `正在生成回答` as the safe fallback student-facing label
- **AND** it MUST NOT expose raw backend status strings.

#### Scenario: Phase labels fade through without layout jump
- **WHEN** a root thinking phase changes from `正在判断问题范围` to `正在检索课程资料`, `正在返回学习建议`, or `正在生成回答`
- **THEN** the outgoing label MUST remain visible long enough to fade away rather than disappearing as an instantaneous DOM replacement
- **AND** the incoming label MUST appear with a subtle fade-in, vertical settle, or equivalent non-disruptive transition
- **AND** the text container MUST maintain stable line height so the running turn does not jump vertically during the phase replacement.

#### Scenario: Atom mark continues independently while text changes
- **WHEN** the root thinking phase label changes
- **THEN** the Atom animation mark MUST continue or remain visually stable independently of the label fade-through
- **AND** the Atom animation mark MUST remain decorative and `aria-hidden`
- **AND** label transitions MUST NOT restart, remount, or visually glitch the Atom animation mark unless reduced-motion behavior intentionally freezes the mark.

#### Scenario: Successful completion removes thinking status
- **WHEN** the active root assistant turn receives a successful `final` event and is no longer loading
- **THEN** the thinking line MUST be removed from the completed assistant turn
- **AND** the completed assistant reply MUST render as the established flat markdown answer with its lightweight action row
- **AND** the completed assistant reply MUST NOT retain `正在判断问题范围`, `正在检索课程资料`, `正在返回学习建议`, `正在生成回答`, `Atom 学习助手`, `生成中`, the Atom thinking animation, or any other running-only status header as persistent success chrome.

#### Scenario: Failed root assistant turn remains visibly bounded
- **WHEN** the latest root assistant turn fails
- **THEN** the error message MUST remain in a distinct error block or bounded error treatment
- **AND** the failed turn MUST NOT render the successful-reply action row
- **AND** the failed turn MUST NOT render dynamic follow-up chips
- **AND** the failed turn MUST NOT continue playing the Atom thinking animation after failure is visible.

#### Scenario: Reduced motion preserves meaning without repeated animation
- **WHEN** the student device or browser requests reduced motion
- **THEN** the root thinking line MUST continue to show the current student-facing phase label
- **AND** the Atom thinking mark MUST be static, non-looping, or replaced by an equivalent static Atom mark
- **AND** text translation, blur animation, and repeated opacity motion MUST be disabled or reduced to a minimal non-distracting state
- **AND** changing phases MUST still update the visible label without requiring animation to understand the state.

#### Scenario: Thinking line is announced accessibly
- **WHEN** the root thinking line phase label changes while Atom is generating a response
- **THEN** assistive technology MUST receive a polite status update for the current phase label
- **AND** the decorative Atom animation mark and outgoing visual-only labels MUST NOT cause duplicate announcements
- **AND** the final answer text MUST remain reachable as normal message content after completion.

#### Scenario: Quick prompt chips remain hidden during root thinking
- **WHEN** Atom is streaming a root assistant reply and the thinking line is visible
- **THEN** dynamic follow-up prompt chips MUST be hidden or disabled according to the established loading behavior
- **AND** stale suggestions from previous successful turns MUST NOT be visible beside or below the running thinking line.

#### Scenario: Contextual assistant route keeps its distinct surface
- **WHEN** a student opens the contextual `/ai/chat` detail route
- **THEN** the contextual chat page MUST NOT inherit the root-only flat successful reply styling unless explicitly scoped
- **AND** contextual detail header, contextual reset behavior, detail-route message boundaries, and existing detail-route running-state behavior MUST remain distinct from the root Atom assistant page.

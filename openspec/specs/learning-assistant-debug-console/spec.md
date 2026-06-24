# learning-assistant-debug-console Specification

## Purpose
TBD - created by archiving change upgrade-learning-assistant-debug-rag. Update Purpose after archive.
## Requirements
### Requirement: Admin multi-turn debug console
The system SHALL provide an admin-only learning assistant debug console that supports multi-turn chat testing with persistent turn history for the current page session.

#### Scenario: Admin opens learning assistant debug console
- **WHEN** an authenticated admin opens `/admin/learning-assistant`
- **THEN** the page SHALL show a chat-oriented debug console with context controls, a message timeline, and a per-turn diagnostics inspector
- **AND** it SHALL retain submitted turns in the current page session until the admin clears the conversation.

#### Scenario: Admin submits a follow-up question
- **WHEN** the admin sends a new question after one or more previous turns
- **THEN** the request SHALL include the relevant prior conversation context
- **AND** the new assistant answer SHALL appear as a new assistant turn rather than replacing the prior result.

### Requirement: Streaming Markdown answers without admin hard truncation
The admin debug console SHALL stream assistant answers and render Markdown without applying the student mobile hard truncation by default.

#### Scenario: Assistant response streams
- **WHEN** the backend emits partial answer events
- **THEN** the page SHALL append the new content to the active assistant turn
- **AND** it SHALL show the turn as running until the final event is received.

#### Scenario: Assistant response contains Markdown
- **WHEN** the final or streaming answer contains Markdown headings, lists, bold text, code, or paragraph breaks
- **THEN** the page SHALL render the Markdown as formatted content without enabling raw HTML execution.

#### Scenario: Admin debug answer exceeds student mobile cap
- **WHEN** an admin debug run produces an answer longer than the student mobile cap
- **THEN** the backend SHALL NOT hard-truncate it solely because of the student mobile policy
- **AND** any admin-requested length control SHALL be explicit in the request or admin settings.

### Requirement: Turn-level diagnostics inspector
The system SHALL expose guardrail, classification, retrieval-decision, tool-call, RAG, source, and raw response diagnostics for each assistant turn.

#### Scenario: Admin selects a completed turn
- **WHEN** the admin selects a completed assistant turn
- **THEN** the inspector SHALL show the answer status, classification, retrieval decision, guardrail decisions, tool calls, selected sources, and raw structured response for that turn.

#### Scenario: Retrieval decision diagnostics are available
- **WHEN** a completed turn includes a retrieval decision
- **THEN** the inspector SHALL show the retrieval mode, decision source, strict-evidence state, confidence when available, decision reason, override state when applicable, and whether dynamic RAG or platform resource lookup executed
- **AND** it SHALL distinguish skipped dynamic RAG from RAG disabled, no usable match, fixed evidence only, and strict evidence failure.

#### Scenario: Retrieval diagnostics are available
- **WHEN** a turn uses RAG
- **THEN** the inspector SHALL show the generated retrieval queries, recall sources, rerank scores when available, and final evidence selected for the answer.

#### Scenario: Retrieval is skipped by decision
- **WHEN** a turn skips dynamic RAG because the retrieval decision selected ordinary model-knowledge answering or fixed evidence only
- **THEN** the inspector SHALL show the retrieval decision empty state for RAG diagnostics
- **AND** it SHALL NOT show stale retrieval diagnostics from a previous turn.

#### Scenario: Runtime performance is available
- **WHEN** hybrid BGE RAG is enabled
- **THEN** the debug console SHALL show whether the optional BGE service is reachable
- **AND** it SHALL show useful runtime metrics such as model loaded state, container memory, process/container CPU time, request counts, and service probe latency when available.

#### Scenario: BGE warmup status is available
- **WHEN** the optional BGE service is configured to warm up on startup
- **THEN** the debug console SHALL show whether warmup is disabled, not started, running, succeeded, or failed
- **AND** it SHALL show warmup duration or error details when available.

#### Scenario: Retrieval diagnostics are unavailable
- **WHEN** a turn does not use RAG or diagnostics are not returned
- **THEN** the inspector SHALL show an explicit empty state rather than stale diagnostics from a previous turn.

### Requirement: Chapter-scoped experiment point intent starter
The admin learning assistant debug console SHALL present a chat empty state that lets the user choose an experiment, a video point under that experiment, and a question intent for the currently selected chapter before starting normal multi-turn chat.

#### Scenario: Empty chat shows experiment point intent panel
- **WHEN** an authenticated admin opens the learning assistant debug console with no chat turns
- **AND** a chapter is selected in the left-side context controls
- **THEN** the central chat area SHALL show experiments associated with that chapter
- **AND** selecting an experiment SHALL show its video points
- **AND** selecting a point SHALL show available question intents.

#### Scenario: Chapter selection remains outside the chat starter
- **WHEN** the admin changes the selected chapter in the left-side context controls
- **THEN** the empty-state starter panel SHALL refresh its experiment and point options from the new chapter
- **AND** stale experiment, point, and intent selections from the previous chapter SHALL NOT be submitted.

#### Scenario: Intent prepares a point-context question
- **WHEN** the admin selects an experiment, a video point, and a question intent
- **THEN** the console SHALL automatically prepare and sync a natural-language student question for that point and intent into the normal composer
- **AND** the starter preview SHALL expose one prominent primary action to start with that question
- **AND** that primary action SHALL use an open-source designed animated button component pattern rather than page-local bespoke animation markup
- **AND** the action copy SHALL read `从这个问题开始`
- **AND** the action SHALL keep a visible, slow, non-orbiting green AI glow by default
- **AND** the default glow SHALL use internal shimmer, subtle text shine, and a soft breathing backlight instead of rotating border motion
- **AND** the default glow SHALL include multiple larger irregular green light clusters with independent slow motion and shape variation
- **AND** hover or keyboard focus SHALL preserve the glow and add a slower left-to-right green ink-wash lightening pass rather than a white glare
- **AND** submitting it SHALL include the selected `chapter_id`, `experiment_id`, and stable `point_key`.

#### Scenario: Chat behavior continues after first send
- **WHEN** the first question is submitted from the starter panel
- **THEN** the central area SHALL switch to the normal multi-turn chat timeline
- **AND** streaming answers, follow-up questions, turn selection, clearing turns, and diagnostics SHALL continue to work as in the existing chat console.

#### Scenario: Manual questions can use or clear selected point context
- **WHEN** a point context is active after a starter-panel submission
- **THEN** typed follow-up questions SHALL continue to include that point context
- **AND** the console SHALL provide a visible way to clear the active point context before sending a chapter-only question.

#### Scenario: Chapter has no video points
- **WHEN** the selected chapter has no experiments with video points
- **THEN** the empty-state starter panel SHALL show an explicit empty state
- **AND** the normal composer SHALL remain available for chapter-only questions.

### Requirement: Structured point prompt suggestions
The admin debug console SHALL present empty-chat video-point prompt suggestions as centered starting prompts and submit their structured point context.

#### Scenario: Empty chat shows point suggestions
- **WHEN** the admin opens the learning assistant debug console with no chat turns
- **THEN** the chat area SHALL show centered video-point prompt suggestions for the selected chapter
- **AND** the admin SHALL still be able to type a custom question instead.

#### Scenario: Admin selects a point prompt
- **WHEN** the admin clicks a video-point prompt suggestion
- **THEN** the debug console SHALL submit the prompt question with `chapter_id`, `experiment_id`, and `point_key`
- **AND** the resulting turn SHALL retain diagnostics that identify the selected point context.

#### Scenario: Point diagnostics show reviewed evidence source
- **WHEN** a turn includes a fixed point evidence package
- **THEN** the debug console SHALL show that the evidence came from manual-reviewed point bindings
- **AND** it SHALL show experiment evidence count, theory evidence count, manual review status, and review grade separately from supplemental RAG.

#### Scenario: Platform resource miss is not shown as a learning refusal
- **WHEN** a true platform-resource availability query finds no ready and published resource
- **THEN** the debug console SHALL label the result as resource unavailable or platform not found
- **AND** it SHALL NOT present that state as an unsafe, out-of-course, or generic guardrail refusal.

#### Scenario: Chapter changes before first prompt
- **WHEN** the admin changes the chapter before starting a chat
- **THEN** the prompt suggestions SHALL update to the new chapter's experiment video points
- **AND** suggestions from the previous chapter SHALL NOT be submitted accidentally.

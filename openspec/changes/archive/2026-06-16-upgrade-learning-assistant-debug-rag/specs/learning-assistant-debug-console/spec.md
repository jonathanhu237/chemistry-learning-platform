## ADDED Requirements

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
The system SHALL expose guardrail, classification, tool-call, RAG, source, and raw response diagnostics for each assistant turn.

#### Scenario: Admin selects a completed turn
- **WHEN** the admin selects a completed assistant turn
- **THEN** the inspector SHALL show the answer status, classification, guardrail decisions, tool calls, selected sources, and raw structured response for that turn.

#### Scenario: Retrieval diagnostics are available
- **WHEN** a turn uses RAG
- **THEN** the inspector SHALL show the generated retrieval queries, recall sources, rerank scores when available, and final evidence selected for the answer.

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

# student-ai-visible-thinking-stream Specification

## Purpose
TBD - created by archiving change student-ai-visible-reasoning-summary. Update Purpose after archive.
## Requirements
### Requirement: Student assistant stream emits visible thinking events
The student assistant stream SHALL support a `thinking` SSE event that carries student-safe visible thinking or progress text separately from answer text and lifecycle status.

#### Scenario: Thinking event schema is emitted
- **WHEN** the backend emits student-visible thinking during `/api/student/assistant/ask/stream`
- **THEN** the SSE event name MUST be `thinking`
- **AND** the payload MUST include `message` as the displayable student-facing text
- **AND** the payload MUST include `source` with either `reasoning_summary` or `agent_trace`
- **AND** the payload MAY include `phase` and `sequence` for ordering and frontend state handling.

#### Scenario: Existing stream events remain compatible
- **WHEN** the backend adds `thinking` events to a student assistant turn
- **THEN** it MUST continue to emit existing answer and lifecycle events using the established `status`, `delta`, `replace`, `final`, and `error` names
- **AND** clients that ignore unknown `thinking` events MUST still receive a complete answer stream.

#### Scenario: Thinking is not answer text
- **WHEN** a `thinking` event is emitted
- **THEN** its `message` MUST NOT be appended to the assistant answer content
- **AND** the final answer returned in the `final` response MUST NOT include the visible thinking text unless the model independently wrote the same content as part of the answer.

### Requirement: Model reasoning summary is the preferred thinking source
The student assistant SHALL prefer provider-supported model reasoning summaries for visible thinking when the configured provider, model, and runtime settings explicitly support them.

#### Scenario: Reasoning summary is supported and enabled
- **WHEN** a student assistant request runs with a configured Responses-compatible provider and reasoning summaries are enabled
- **THEN** the backend SHOULD request a model reasoning summary from the same answer-generation model/API when supported
- **AND** reasoning summary text that passes sanitization MUST be emitted as `thinking` events with `source` set to `reasoning_summary`
- **AND** answer text from the same model stream MUST continue to be emitted as existing `delta` events.

#### Scenario: Reasoning summary is unavailable
- **WHEN** the configured provider, model, SDK, API mode, or deployment settings do not support model reasoning summaries
- **THEN** the backend MUST NOT synthesize model-thinking text
- **AND** it MUST fall back to real agent execution trace events with `source` set to `agent_trace`
- **AND** the student answer MUST continue streaming when an answer path is otherwise available.

#### Scenario: Reasoning summary stream fails
- **WHEN** reasoning summary streaming fails, returns an unsupported event shape, times out, or produces no sanitized displayable summary
- **THEN** the backend MUST continue the student assistant turn through the available answer fallback path
- **AND** it MUST use sanitized `agent_trace` thinking events if the turn continues
- **AND** it MUST NOT expose the raw provider error, SDK exception, or unsupported event payload to the student UI.

#### Scenario: Custom compatible provider is not assumed to support summaries
- **WHEN** the deployment uses an OpenAI-compatible custom base URL or provider whose Responses reasoning-summary capability has not been explicitly enabled
- **THEN** the backend MUST treat model reasoning summaries as unsupported for student-visible thinking
- **AND** it MUST use `agent_trace` fallback rather than calling an unverified summary interface.

### Requirement: Raw reasoning and diagnostics are never student-visible
The student assistant SHALL expose only safe reasoning summaries or high-level trace messages and MUST NOT expose raw chain-of-thought or internal diagnostics to students.

#### Scenario: Raw reasoning text event is received
- **WHEN** a provider stream includes raw reasoning text, chain-of-thought-like content, hidden reasoning fields, or lower-level reasoning events that are not explicit summary text
- **THEN** the backend MUST ignore those fields for student display
- **AND** it MUST NOT forward them through `thinking`, `status`, `delta`, `final`, metadata, debug payloads, or error messages.

#### Scenario: Internal diagnostics exist during the turn
- **WHEN** the agent has policy classifications, guardrail decisions, tool calls, RAG trace details, rerank scores, source chunk identifiers, tool arguments, model names, provider names, stack traces, or exception text
- **THEN** the student stream MUST NOT expose those raw details as visible thinking messages
- **AND** those details MAY remain in backend logs or teacher/admin diagnostics only where existing specs allow them.

#### Scenario: Unsafe summary content is produced
- **WHEN** a model reasoning summary mentions hidden prompts, chain-of-thought, internal tools, policy labels, raw evidence ids, unsafe experiment operations, direct assessment answers, or teacher/admin diagnostics
- **THEN** the sanitizer MUST drop that thinking message
- **AND** the backend MUST NOT replace it with a fake model summary.

### Requirement: Visible thinking messages are sanitized and concise
The backend SHALL sanitize every student-visible thinking message before emitting it to the H5 client.

#### Scenario: Thinking message is prepared
- **WHEN** the backend prepares a `thinking.message`
- **THEN** it MUST trim whitespace, collapse repeated whitespace, and remove Markdown or JSON-like structure
- **AND** it MUST keep the visible text short enough for a mobile running line
- **AND** it MUST emit only plain student-facing Chinese learning language.

#### Scenario: Thinking message fails sanitization
- **WHEN** a candidate thinking message is empty, too long, diagnostic, unsafe, implementation-specific, or not student-readable after sanitization
- **THEN** the backend MUST omit that `thinking` event
- **AND** answer generation MUST continue when possible.

#### Scenario: Agent trace message is emitted
- **WHEN** a visible thinking event is derived from agent execution trace rather than model summary text
- **THEN** the message MUST come from a fixed safe copy set or fixed safe template
- **AND** the message MUST describe a real operation that occurred or is starting in the current turn.

### Requirement: Agent trace fallback reflects real execution
When model reasoning summaries are unavailable, the student assistant SHALL expose truthful high-level agent progress rather than preset fake thinking, including the retrieval decision actually made for the current turn.

#### Scenario: Policy gate starts
- **WHEN** the agent actually begins student policy, safety, scope, or question-type evaluation for the current turn
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="policy"` when agent trace fallback is active
- **AND** it MUST NOT include policy codes, policy prompts, guardrail arrays, or internal classification labels.

#### Scenario: Retrieval decision starts
- **WHEN** the agent actually begins deciding whether the turn needs course material, fixed evidence, dynamic RAG, or platform resource lookup
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="retrieval_decision"` when agent trace fallback is active
- **AND** the message MUST be a fixed student-safe status that does not expose retrieval mode names, confidence values, policy labels, or tool names.

#### Scenario: Course context is prepared
- **WHEN** the agent actually prepares fixed point evidence, curriculum context, conversation context, or other course context for the current turn
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="context"` when agent trace fallback is active
- **AND** it MUST NOT expose source ids, chunk ids, catalog internals, or teacher-only metadata.

#### Scenario: Fixed point evidence is used
- **WHEN** the retrieval decision uses hydrated fixed point evidence for the selected point or experiment context
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="fixed_evidence"` when agent trace fallback is active
- **AND** it MUST describe only that the assistant is reading current course context in student-facing language.

#### Scenario: Retrieval is skipped
- **WHEN** the retrieval decision skips dynamic RAG because the turn can be answered as an ordinary learning explanation
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="retrieval_skip"` when agent trace fallback is active
- **AND** it MUST NOT claim that course material search, source lookup, or platform resource lookup ran.

#### Scenario: Retrieval runs
- **WHEN** the agent actually performs RAG, curriculum, source, or platform evidence lookup for the current turn
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="retrieval"` when agent trace fallback is active
- **AND** it MUST NOT claim retrieval ran when the retrieval decision or feature switch skipped retrieval.

#### Scenario: Evidence quality is evaluated
- **WHEN** dynamic RAG or platform lookup returns and the agent evaluates whether results are usable for the requested evidence claim
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="evidence_quality"` when agent trace fallback is active
- **AND** it MUST NOT expose raw no-match diagnostics, disabled feature flags, RAG implementation names, source ids, or rerank scores to the student.

#### Scenario: Retrieval has no usable match
- **WHEN** retrieval is disabled, skipped by policy, or produces no usable evidence and the turn continues from model chemistry knowledge or local fallback
- **THEN** the backend SHALL emit a high-level student-safe trace message that the assistant is organizing the answer from available course knowledge when agent trace fallback is active
- **AND** it MUST NOT expose raw no-match diagnostics, disabled feature flags, or RAG implementation names to the student.

#### Scenario: Answer generation starts
- **WHEN** the agent actually starts model or local answer generation for the current turn
- **THEN** it SHALL emit a `thinking` event with `source="agent_trace"` and `phase="generation"` when agent trace fallback is active
- **AND** it MUST NOT describe that message as model reasoning unless it came from a reasoning summary event.

#### Scenario: Local fallback is used
- **WHEN** model streaming fails or no model is configured and the agent continues through a local fallback answer path
- **THEN** the backend SHALL emit a `thinking` event with `source="agent_trace"` and `phase="fallback"` when agent trace fallback is active
- **AND** it MUST NOT expose provider error details or stack traces to the student.

### Requirement: Final answer behavior remains unchanged
Visible thinking SHALL be an additive stream feature and MUST NOT change the successful answer contract.

#### Scenario: Successful answer completes
- **WHEN** a student assistant turn completes successfully after emitting `thinking` events
- **THEN** the backend MUST emit the established `final` event with the normal student assistant response payload
- **AND** the response text, sources, source count, suggested prompts, mode, and output guardrail replacement behavior MUST remain governed by the existing student assistant contracts.

#### Scenario: Output guardrail replaces answer text
- **WHEN** output guardrails replace or sanitize a generated answer
- **THEN** the backend MUST continue to emit the established `replace` event for answer content
- **AND** it MUST NOT use a `thinking` event to deliver replacement answer text.

#### Scenario: Turn fails
- **WHEN** the student assistant turn fails and emits an `error` event
- **THEN** the error message MUST remain student-safe
- **AND** no pending reasoning summary, raw diagnostic, or internal trace payload may be emitted after the failure as visible thinking.


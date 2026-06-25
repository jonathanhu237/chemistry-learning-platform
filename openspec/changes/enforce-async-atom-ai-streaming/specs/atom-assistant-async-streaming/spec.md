## ADDED Requirements

### Requirement: Active Atom assistant streams use async provider streaming
The shared Atom assistant SSE runtime SHALL use asynchronous provider streaming for every OpenAI-backed student or teacher Atom assistant stream.

#### Scenario: Student stream uses async provider helper
- **WHEN** `/api/student/assistant/ask/stream` handles a request that reaches OpenAI-backed answer generation
- **THEN** the request MUST flow through `run_agent_stream`
- **AND** the provider stream MUST be consumed by an `AsyncOpenAI` helper using `async for`
- **AND** the stream MUST NOT use a synchronous `OpenAI` client or a synchronous provider iterator loop.

#### Scenario: Teacher debug stream uses same async provider helper
- **WHEN** `/api/admin/learning-assistant/ask/stream` handles a request that reaches OpenAI-backed answer generation
- **THEN** the request MUST flow through the same async-safe `run_agent_stream` provider helpers
- **AND** the teacher debug stream MUST NOT use a separate synchronous OpenAI stream implementation.

#### Scenario: Reasoning summaries are enabled
- **WHEN** the configured provider supports Responses reasoning summaries and reasoning summaries are enabled
- **THEN** the runtime MUST use async Responses streaming
- **AND** answer deltas and sanitized reasoning-summary thinking events MUST be emitted without blocking the event loop.

#### Scenario: Reasoning summaries are not enabled
- **WHEN** the configured provider is OpenAI-compatible but reasoning summaries are disabled or unsupported
- **THEN** the runtime MUST use async Chat Completions streaming
- **AND** answer deltas MUST be emitted without blocking the event loop.

### Requirement: Legacy synchronous Atom assistant stream code is absent
The shared Atom assistant runtime SHALL not keep unused legacy synchronous OpenAI stream helpers in the active assistant domain module.

#### Scenario: Assistant domain is scanned for legacy stream helpers
- **WHEN** backend architecture or assistant tests inspect `server/app/domains/assistant`
- **THEN** helper functions whose purpose is synchronous OpenAI streaming for Atom assistant answers MUST be absent
- **AND** functions named as legacy always-RAG OpenAI stream implementations MUST be absent.

#### Scenario: Synchronous OpenAI stream loop is reintroduced
- **WHEN** code under `server/app/domains/assistant` imports the synchronous OpenAI client and consumes a provider `stream=True` response with a normal `for` loop
- **THEN** the static regression check MUST fail
- **AND** the failure MUST identify the file and pattern that reintroduced event-loop blocking risk.

#### Scenario: Dead rollback code is proposed
- **WHEN** an implementation adds an unused synchronous OpenAI helper only for possible rollback or compatibility
- **THEN** the assistant async-streaming contract MUST reject it
- **AND** rollback MUST rely on git or deployment rollback instead of dormant sync provider code.

### Requirement: Atom assistant one-shot model calls are async-safe
OpenAI-backed one-shot model calls executed as part of Atom assistant async request handling SHALL use `AsyncOpenAI` or be removed from the active runtime path.

#### Scenario: Policy gate calls the model
- **WHEN** the Atom assistant policy gate uses an OpenAI-backed model call
- **THEN** that call MUST use an async OpenAI client and await the provider response.

#### Scenario: Non-streaming assistant answer path calls the model
- **WHEN** `run_agent` or another Atom assistant async request handler uses an OpenAI-backed non-streaming answer call
- **THEN** that call MUST be async-safe
- **AND** it MUST NOT block the event loop through a synchronous `client.chat.completions.create(...)` call.

#### Scenario: Student final metadata generation calls the model
- **WHEN** a completed student assistant turn generates follow-up prompts or a conversation title
- **THEN** that metadata generation MUST use an async OpenAI client
- **AND** cancellation observed before metadata generation MUST still skip the metadata call entirely.

### Requirement: Cancellation semantics remain intact
Async streaming enforcement SHALL preserve the existing cancellation and disconnect behavior for student and teacher Atom assistant streams.

#### Scenario: Browser aborts active student stream
- **WHEN** the student H5 frontend aborts an active Atom stream
- **THEN** the backend MUST observe cancellation through the disconnect or cancellation predicate
- **AND** the stream MUST stop without emitting stale `delta`, `final`, suggested prompt, or conversation title events.

#### Scenario: Teacher debug stream is cleared or unmounted
- **WHEN** the teacher learning-assistant debug console clears, replaces, or unmounts an active stream
- **THEN** the frontend MUST abort the request
- **AND** the backend stream MUST stop without appending stale success or error diagnostics to the cleared or replaced turn.

#### Scenario: Cancellation happens during provider streaming
- **WHEN** cancellation is observed while async provider streaming is in progress
- **THEN** the generator MUST stop neutrally
- **AND** it MUST NOT run fallback answer generation
- **AND** it MUST NOT emit a user-visible `error` event for the cancellation.

### Requirement: Successful SSE event contracts remain compatible
Removing synchronous provider paths SHALL NOT change successful student or teacher Atom assistant stream payload contracts.

#### Scenario: Student answer completes successfully
- **WHEN** a student Atom assistant request completes successfully after the cleanup
- **THEN** the stream MUST continue to use the established `status`, `thinking`, `delta`, `replace`, `final`, and `error` event names
- **AND** the final response payload MUST remain compatible with existing student frontend parsing and local history behavior.

#### Scenario: Teacher debug answer completes successfully
- **WHEN** a teacher debug assistant request completes successfully after the cleanup
- **THEN** the stream MUST continue to emit answer and diagnostic events in the shape consumed by the existing debug console
- **AND** turn-level diagnostics MUST remain available for completed turns.

#### Scenario: Provider failure while connected
- **WHEN** an OpenAI-backed provider call fails while the client remains connected
- **THEN** existing safe fallback or error behavior MUST remain intact
- **AND** the failure MUST NOT be misclassified as a user cancellation.

### Requirement: Async-streaming regression tests are required
The backend test suite SHALL include explicit regression coverage proving Atom assistant streams do not reintroduce synchronous provider blocking.

#### Scenario: Static assistant-domain enforcement runs
- **WHEN** backend tests run
- **THEN** a static test MUST scan the assistant domain for disallowed synchronous OpenAI stream patterns
- **AND** the test MUST allow `AsyncOpenAI` usage.

#### Scenario: Slow provider stream allows unrelated async work
- **WHEN** a fake provider stream awaits before yielding an answer delta
- **THEN** unrelated async work scheduled on the same event loop MUST complete before the delayed provider delta
- **AND** the test MUST fail if provider streaming blocks the event loop.

#### Scenario: Legacy helper call sites are checked
- **WHEN** backend tests or static checks inspect `run_agent_stream`
- **THEN** no active branch MUST call removed legacy synchronous stream helpers
- **AND** the only OpenAI-backed stream branches MUST point to async provider helpers.

### Requirement: Scope boundary for non-Atom OpenAI usage is explicit
This capability SHALL govern the shared Atom assistant runtime and SHALL NOT silently expand to unrelated OpenAI usage outside the Atom assistant stream path.

#### Scenario: Unrelated question generation uses OpenAI
- **WHEN** synchronous OpenAI usage exists in question generation, catalog equation extraction, platform AI settings probes, or retrieval utilities
- **THEN** this capability MUST NOT require changing it unless that code is invoked by the Atom assistant SSE path
- **AND** a broader repository-wide OpenAI async hardening effort MUST be specified separately.

#### Scenario: Future code calls unrelated sync helper from Atom stream
- **WHEN** the Atom assistant stream path begins invoking a previously unrelated synchronous OpenAI helper
- **THEN** that helper becomes in scope for this capability
- **AND** the assistant async-streaming regression check MUST fail until the call is removed, converted to async, or isolated without blocking the event loop.

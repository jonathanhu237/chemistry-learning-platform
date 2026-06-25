## ADDED Requirements

### Requirement: Shared Agent Runtime facade
The backend SHALL provide a shared Agent Runtime facade that is the canonical entrypoint for chemistry assistant execution across student, teacher, assessment, and posttest consumers.

#### Scenario: Consumer requests a non-streaming answer
- **WHEN** a backend consumer needs a one-shot chemistry assistant answer
- **THEN** it MUST call the shared Agent Runtime facade or an approved compatibility wrapper that delegates to the facade
- **AND** it MUST NOT orchestrate policy, retrieval, tools, provider calls, and output guardrails itself.

#### Scenario: Consumer requests a streaming answer
- **WHEN** a backend consumer needs a streamed chemistry assistant answer
- **THEN** it MUST call the shared Agent Runtime facade or an approved compatibility wrapper that delegates to the facade
- **AND** the runtime MUST own stream lifecycle, cancellation checkpoints, provider streaming, output replacement, and final response construction.

#### Scenario: Existing public entrypoints remain during migration
- **WHEN** existing code imports `run_agent` or `run_agent_stream`
- **THEN** those names MAY remain available as compatibility wrappers
- **AND** they MUST delegate to the shared Agent Runtime facade rather than containing independent orchestration logic.

### Requirement: Consumer adapters isolate product-specific concerns
Each assistant consumer SHALL use an adapter layer to translate local request context into the shared Agent Runtime contract and project runtime output back into consumer-specific responses.

#### Scenario: Student chat invokes the agent
- **WHEN** the student Atom assistant receives a `StudentAssistantAskRequest`
- **THEN** the student adapter MUST translate the request and authenticated student into the shared runtime input
- **AND** it MUST project runtime output into student-safe SSE events and final metadata
- **AND** it MUST keep follow-up prompts and conversation-title generation as student-specific post-processing.

#### Scenario: Teacher debug console invokes the agent
- **WHEN** the teacher learning-assistant debug console submits a request
- **THEN** the teacher debug adapter MUST translate debug request fields into the shared runtime input
- **AND** it MUST project runtime output into the existing debug stream and diagnostics contract
- **AND** it MUST retain teacher/admin diagnostics that are intentionally unavailable to students.

#### Scenario: Assessment report invokes the agent
- **WHEN** assessment report generation uses the chemistry assistant
- **THEN** the assessment adapter MUST build the runtime input from report context
- **AND** it MUST return the generated report response without importing private runtime internals.

#### Scenario: Posttest summary or mistake explanation invokes the agent
- **WHEN** posttest summary or mistake explanation uses the chemistry assistant
- **THEN** the posttest adapter MUST build the runtime input from posttest session, experiment, and attempt context
- **AND** cache lookup and cache storage MUST remain outside the core Agent Runtime.

### Requirement: Runtime modules have single-responsibility ownership
The assistant domain SHALL split shared agent execution into focused modules with documented ownership boundaries instead of keeping active orchestration in one monolithic module.

#### Scenario: Runtime context and result contracts are inspected
- **WHEN** runtime context, decision, result, and event contract types are inspected
- **THEN** they MUST live in a runtime contract module such as `runtime.py`
- **AND** they MUST NOT depend on student H5 UI, teacher debug page, assessment cache, or FastAPI endpoint modules.

#### Scenario: Provider code is inspected
- **WHEN** provider model calls are inspected
- **THEN** OpenAI or OpenAI-compatible client creation and model invocation MUST live in a provider-focused module
- **AND** provider code MUST preserve the async streaming requirements from the assistant async-streaming capability.

#### Scenario: Stream lifecycle code is inspected
- **WHEN** cancellation, checkpoint, event emission, and stream helper code is inspected
- **THEN** it MUST live in a stream lifecycle module or clearly owned runtime component
- **AND** it MUST be reused by both student and teacher streamed consumers.

#### Scenario: Tool registry is inspected
- **WHEN** RAG, curriculum, platform resource, and progress lookup tools are inspected
- **THEN** approved tool registration and tool wrappers MUST live in a tool-focused module
- **AND** consumer adapters MUST NOT register ad hoc private tool sets by bypassing the runtime.

#### Scenario: Diagnostics are inspected
- **WHEN** runtime logs, guardrail trace, retrieval trace, tool-call summaries, and teacher debug diagnostics are inspected
- **THEN** diagnostic shaping MUST be owned by runtime diagnostics or adapter projection modules
- **AND** student-facing projections MUST remain separated from teacher/admin diagnostic projections.

### Requirement: Runtime events and results are canonical
The shared Agent Runtime SHALL produce canonical internal events and final results that adapters can project into their existing public contracts.

#### Scenario: Runtime streams answer progress
- **WHEN** the runtime streams an answer
- **THEN** it MUST emit canonical events for status, visible thinking, answer delta, answer replacement, final result, and error
- **AND** adapters MUST map those events to existing public SSE names without changing public event contracts.

#### Scenario: Runtime completes successfully
- **WHEN** the runtime completes a successful answer
- **THEN** it MUST produce a canonical final result containing answer text, mode, classification, retrieval decision, sources, tool-call summaries, guardrail decisions, and diagnostics needed by trusted adapters
- **AND** student adapters MUST project only student-safe fields.

#### Scenario: Runtime fails
- **WHEN** the runtime encounters a non-cancellation failure
- **THEN** it MUST produce or raise a canonical failure that adapters can convert to their existing safe error behavior
- **AND** teacher/admin adapters MAY preserve internal diagnostics where existing role boundaries allow them.

#### Scenario: Runtime is cancelled
- **WHEN** cancellation is observed through a stream cancellation predicate or request disconnect
- **THEN** the runtime MUST stop neutrally
- **AND** adapters MUST NOT project cancellation as a normal completed answer or provider failure.

### Requirement: Student-safe and teacher-debug projections remain separate
The shared runtime SHALL preserve different visibility rules for student and teacher/admin consumers.

#### Scenario: Student projection is produced
- **WHEN** a student-facing adapter projects runtime events or final results
- **THEN** it MUST NOT expose raw policy decisions, RAG trace internals, chunk ids, tool arguments, provider names, stack traces, or teacher-only diagnostics
- **AND** it MUST keep visible thinking sanitized according to existing student-visible thinking requirements.

#### Scenario: Teacher debug projection is produced
- **WHEN** a teacher/admin debug adapter projects runtime events or final results
- **THEN** it MUST retain guardrail, classification, retrieval decision, tool-call, source, and raw structured diagnostics currently expected by the debug console
- **AND** it MUST distinguish skipped retrieval, disabled retrieval, no usable match, fixed evidence, resource lookup, and strict evidence failure.

#### Scenario: Projection tests compare student and teacher outputs
- **WHEN** the same runtime scenario is projected for student and teacher/admin consumers
- **THEN** tests MUST prove the student projection omits diagnostics that the teacher projection retains
- **AND** both projections MUST preserve answer text and safe source count semantics.

### Requirement: Import boundaries protect runtime internals
Backend code SHALL use documented public Agent Runtime or adapter entrypoints and SHALL NOT import private runtime internals across consumer boundaries.

#### Scenario: API endpoint imports are inspected
- **WHEN** FastAPI endpoint modules import assistant functionality
- **THEN** they MUST import consumer adapters or public facade entrypoints
- **AND** they MUST NOT import private provider, retrieval, tool, or diagnostics modules directly.

#### Scenario: Domain consumer imports are inspected
- **WHEN** assessment, posttest, or future domain consumers import assistant functionality
- **THEN** they MUST import the approved adapter or public runtime entrypoint for their consumer type
- **AND** they MUST NOT import private runtime internals to assemble partial agent pipelines.

#### Scenario: New consumer is added
- **WHEN** a new backend feature wants to use the chemistry assistant
- **THEN** it MUST add or reuse an adapter
- **AND** it MUST NOT add feature-specific branches directly into the core runtime unless the branch is a general runtime capability.

#### Scenario: Architecture validation runs
- **WHEN** backend architecture or assistant modularity validation runs
- **THEN** it MUST fail on disallowed direct imports of private runtime internals
- **AND** the failure message MUST identify the importing module and the allowed public entrypoint.

### Requirement: Behavior is preserved during modular migration
Modularizing the Agent Runtime SHALL be a behavior-preserving refactor for current consumers.

#### Scenario: Student stream behavior is characterized
- **WHEN** student assistant stream tests run after modularization
- **THEN** they MUST prove existing event names, cancellation behavior, visible thinking behavior, final metadata behavior, and local history assumptions remain compatible.

#### Scenario: Teacher debug behavior is characterized
- **WHEN** teacher learning-assistant debug tests run after modularization
- **THEN** they MUST prove streaming answers, turn diagnostics, clear/replacement cancellation, and retrieval diagnostics remain compatible.

#### Scenario: Assessment report behavior is characterized
- **WHEN** assessment report agent tests run after modularization
- **THEN** they MUST prove report generation still receives the expected generated answer and mode without changing public report contracts.

#### Scenario: Posttest generated response behavior is characterized
- **WHEN** posttest summary and mistake explanation tests run after modularization
- **THEN** they MUST prove cached responses, generated responses, context construction, and fallback text behavior remain compatible.

#### Scenario: Existing helper tests are migrated
- **WHEN** tests currently import helper functions from the old monolithic agent module
- **THEN** each test MUST either import the helper from its new owning module or use a documented compatibility export
- **AND** compatibility exports MUST not become a second implementation path.

### Requirement: Migration shrinks the monolithic agent module
The existing monolithic assistant agent module SHALL become a compatibility shim or be removed once consumers and tests use the shared runtime modules.

#### Scenario: Runtime orchestration is moved
- **WHEN** modularization is complete
- **THEN** active policy, retrieval, provider, streaming, tool, guardrail, and diagnostics orchestration MUST live behind the shared runtime facade
- **AND** the old monolithic module MUST NOT remain the owner of active orchestration logic.

#### Scenario: Compatibility shim remains temporarily
- **WHEN** a compatibility shim remains for `run_agent`, `run_agent_stream`, or historically imported helper symbols
- **THEN** the shim MUST delegate to new module owners
- **AND** it MUST contain no independent provider calls, retrieval pipelines, or stream loops.

#### Scenario: Final cleanup is possible
- **WHEN** all runtime and test imports have migrated to public facade, adapters, or new owning modules
- **THEN** the compatibility shim MAY be removed
- **AND** architecture validation MUST prevent reintroducing a monolithic agent implementation.

### Requirement: Async-streaming enforcement remains compatible
The shared Agent Runtime SHALL preserve the async provider and cancellation guarantees defined for Atom assistant streaming.

#### Scenario: Runtime provider stream is inspected
- **WHEN** provider streaming code is moved into new modules
- **THEN** it MUST continue to use async provider streaming and cancellation checkpoints
- **AND** it MUST continue to satisfy the assistant async-streaming static checks.

#### Scenario: Async cleanup and modularization overlap
- **WHEN** `enforce-async-atom-ai-streaming` and this modularization change both touch provider or stream code
- **THEN** implementation MUST preserve the stricter async-streaming requirement
- **AND** modularization MUST NOT move legacy synchronous stream helpers into another module.

#### Scenario: Local fallback remains available
- **WHEN** no model is configured or provider generation fails while connected
- **THEN** the runtime MAY use the existing local fallback behavior
- **AND** cancellation MUST still stop neutrally rather than running fallback after the client has gone away.

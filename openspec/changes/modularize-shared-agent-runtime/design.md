## Context

Current backend agent usage already converges on a shared request/response shape:

```text
student H5 Atom chat
teacher learning-assistant debug console
assessment reports
posttest summary / mistake explanation
future point-centered consumers
        |
        v
AgentAskRequest
        |
        v
run_agent / run_agent_stream
        |
        v
server/app/domains/assistant/agent.py
```

The shared entrypoint is useful, but the implementation boundary is still weak. `agent.py` owns too many responsibilities: classification, policy gate, retrieval decision, fixed evidence hydration, RAG/resource tools, provider calls, streaming lifecycle, output normalization, output guardrails, diagnostics, and persistence logging. That makes every new consumer tempting to support with more request flags and more conditional behavior inside the same module.

There is already a small `server/app/domains/assistant/runtime.py` containing `AgentRunContext`, decisions, response construction, and stream chunk helpers. This is a good seed, but it is not yet a full Agent Runtime boundary.

The adjacent `enforce-async-atom-ai-streaming` change should remain focused on async provider safety and legacy sync stream deletion. This change is the broader modular architecture cleanup that follows once the active stream path is safe.

## Goals / Non-Goals

**Goals:**

- Establish a stable shared Agent Runtime facade for all current chemistry assistant consumers.
- Separate consumer adapters from the core agent execution engine.
- Split the oversized `agent.py` implementation into focused modules without changing public API contracts.
- Preserve the existing `AgentAskRequest`, `AgentAskResponse`, student SSE events, teacher debug diagnostics, and assessment/report outputs.
- Keep student-safe projection and teacher/admin diagnostics as explicit adapter responsibilities.
- Prevent new consumers from importing private runtime internals directly.
- Make future capabilities easier: new contexts can add an adapter or policy/retrieval extension without bloating one central file.

**Non-Goals:**

- Do not redesign student or teacher frontend UI.
- Do not introduce backend chat-session persistence.
- Do not change database schema.
- Do not change RAG ranking, policy rules, output guardrail semantics, or evidence payload content beyond moving code.
- Do not merge all consumer-specific schemas into one mega-request model.
- Do not require all non-agent AI utilities in the repository to use this runtime.

## Decisions

### Build a runtime facade first, then move internals behind it

The first implementation step should introduce a stable facade such as:

```text
assistant/runtime_facade.py
  AgentRuntime.run(request, options) -> AgentAskResponse
  AgentRuntime.stream(request, options) -> AsyncIterator[AgentEvent]
```

Existing `run_agent` and `run_agent_stream` can initially delegate to the facade so external imports remain stable while internals move.

Alternative considered: rename every caller to a new class immediately. Rejected because it creates a wide refactor with little safety gain. A facade lets behavior stay characterized while modules are extracted.

### Consumer adapters convert caller-specific concerns into Agent requests/options

Consumers should not know how policy, retrieval, provider, tools, and guardrails are wired. They should translate their local context into the runtime contract:

```text
student adapter:
  StudentAssistantAskRequest + user -> AgentRunInput + student projection/followups

teacher debug adapter:
  LearningAssistantAskRequest + admin -> AgentRunInput + full diagnostics projection

assessment adapter:
  report/posttest context -> AgentRunInput + cached generated text response
```

This prevents `AgentAskRequest` from becoming a dumping ground for every endpoint detail.

Alternative considered: keep adding flags to `AgentAskRequest`. Rejected because flags blur product boundaries and make the core runtime responsible for UI-specific and cache-specific behavior.

### Runtime events are canonical, projections are adapter-specific

The runtime should produce canonical internal events, for example:

- `status`
- `thinking`
- `delta`
- `replace`
- `final`
- `error`
- optional diagnostics fields available to trusted adapters

Student adapters project these into student-safe SSE and final metadata. Teacher adapters can expose richer diagnostics. The runtime should not contain UI-specific copy or frontend layout assumptions.

Alternative considered: runtime directly emits student SSE and teacher debug SSE variants. Rejected because that keeps consumer-specific output inside the core and makes adding a third consumer awkward.

### Split modules by responsibility, not by current function length

Suggested ownership:

```text
assistant/
  runtime.py              dataclasses, result/event contracts, context primitives
  runtime_facade.py       AgentRuntime facade and stable run/stream entrypoints
  orchestrator.py         policy -> retrieval -> generation -> guardrail pipeline
  providers.py            AsyncOpenAI clients and model calls
  streaming.py            cancellation, stream checkpoints, event helpers
  retrieval_decision.py   retrieval mode and tool allowlist decision logic
  evidence.py             point/static evidence and answer-context payload preparation
  tools.py                approved tool registry and tool wrappers
  diagnostics.py          logs, trace payload, teacher/admin diagnostic shaping
  adapters/
    student.py
    admin_debug.py
    assessment.py
```

The exact filenames can vary, but the boundaries should stay visible and testable.

Alternative considered: one `Agent` class with many private methods. Rejected because it hides complexity rather than reducing coupling.

### Keep `agent.py` as a temporary compatibility shim only

During migration, `agent.py` may continue exporting `run_agent`, `run_agent_stream`, and historically imported helper symbols required by tests. Its final role should shrink to a compatibility shim or be removed after call sites migrate.

Compatibility shims must not contain active orchestration logic.

Alternative considered: leave `agent.py` as the main owner and just move a few helpers. Rejected because it does not address the architectural risk that prompted this change.

### Coordinate with async-streaming enforcement

The shared runtime must preserve the async streaming guarantee:

- provider streaming remains `AsyncOpenAI` + `async for`
- cancellation checkpoints remain available to student and teacher streams
- dead synchronous stream helpers do not move into new modules
- static tests keep guarding the assistant domain

This modularization should either depend on or run after `enforce-async-atom-ai-streaming`.

## Risks / Trade-offs

- [Risk] A large module split can accidentally change behavior. -> Mitigation: keep public entrypoints stable first and add characterization tests before moving logic.
- [Risk] Adapters can become thin wrappers that still pass too many flags. -> Mitigation: define adapter responsibilities and reject consumer-specific flags that belong in adapter options or projection logic.
- [Risk] Student-safe and teacher-debug projections can leak into each other. -> Mitigation: enforce separate adapter modules and tests that student outputs never include diagnostics while teacher outputs retain them.
- [Risk] Static import-boundary tests may block legitimate tests. -> Mitigation: allow test-only imports of documented public helpers while blocking runtime modules from importing private internals.
- [Risk] Migration may overlap with async-stream cleanup. -> Mitigation: keep the async-streaming change focused and complete before moving provider/stream modules.
- [Risk] Existing tests import private helpers from `agent.py`. -> Mitigation: migrate tests gradually to new module owners or keep documented test-only exports until characterization coverage is moved.

## Migration Plan

1. Complete or account for `enforce-async-atom-ai-streaming` so provider streaming is already safe.
2. Add runtime facade and adapter contracts while leaving existing `run_agent` and `run_agent_stream` imports working.
3. Add characterization tests for student stream, teacher debug stream, assessment report, posttest summary, and posttest mistake explanation.
4. Extract provider and streaming lifecycle code behind the facade.
5. Extract retrieval decision, evidence preparation, tools, diagnostics, and output guardrail orchestration.
6. Introduce student, teacher debug, and assessment adapters and migrate consumers one at a time.
7. Add architecture/static tests that block direct runtime imports of private internals from API/domain consumers.
8. Shrink `agent.py` to a shim or remove it once all runtime imports are migrated.

Rollback should use git/deployment rollback. Do not reintroduce duplicated agent implementations for individual consumers.

## Open Questions

- Whether the facade should be a class instance with injected repositories/settings/policy or a small set of functions with explicit options.
- Whether assessment/posttest generation should share the streaming event model internally or stay one-shot over the same runtime result model.
- How much of teacher diagnostics should come from canonical runtime diagnostics versus adapter-assembled debug payloads.
- Whether to archive the existing `agent.py` compatibility exports in the same change or defer final removal to a follow-up once imports are fully migrated.

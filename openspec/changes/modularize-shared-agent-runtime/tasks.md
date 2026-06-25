## 1. Baseline Audit And Characterization

- [x] 1.1 Re-run import and call-site search for `run_agent`, `run_agent_stream`, `AgentAskRequest`, `AgentAskResponse`, and deep imports from `server.app.domains.assistant.agent`.
- [x] 1.2 Document current consumers: student chat stream, teacher debug ask/stream, assessment report generation, posttest summary, and posttest mistake explanation.
- [x] 1.3 Identify helper functions currently imported directly from `agent.py` by tests and classify their future owner modules.
- [x] 1.4 Run the existing assistant characterization tests before refactor to establish a green baseline.
- [x] 1.5 Confirm `enforce-async-atom-ai-streaming` requirements are either complete or not violated by the planned module split.

## 2. Runtime Facade And Contracts

- [x] 2.1 Add or expand a shared runtime contract module for canonical agent context, decisions, events, final result, and failure/cancellation types.
- [x] 2.2 Introduce an `AgentRuntime` facade or equivalent public functions with `run` and `stream` entrypoints.
- [x] 2.3 Keep existing `run_agent` and `run_agent_stream` exports delegating to the facade for migration compatibility.
- [x] 2.4 Define runtime options for repositories, settings, policy, cancellation predicate, and diagnostics mode without adding consumer-specific UI flags.
- [x] 2.5 Add facade-level tests proving one-shot and streamed execution still return the existing `AgentAskResponse` and stream event shapes.

## 3. Consumer Adapter Layer

- [x] 3.1 Add a student assistant adapter that translates `StudentAssistantAskRequest` plus authenticated user into runtime input.
- [x] 3.2 Keep student follow-up prompt and conversation-title generation outside the core runtime and inside student-specific post-processing.
- [x] 3.3 Add a teacher/admin debug adapter that translates `LearningAssistantAskRequest` into runtime input and projects full diagnostics.
- [x] 3.4 Add an assessment/report adapter for report-generation agent use.
- [x] 3.5 Add a posttest adapter for summary and mistake-explanation agent use while preserving cache lookup/storage outside the core runtime.
- [x] 3.6 Migrate consumers to call adapters or the public facade rather than private `agent.py` internals.

## 4. Module Extraction

- [x] 4.1 Extract provider client creation and model-call helpers into a provider-focused assistant module.
- [x] 4.2 Extract stream lifecycle helpers, cancellation checkpoints, and canonical stream event helpers into a streaming-focused module.
- [x] 4.3 Extract policy and retrieval-decision orchestration into focused modules while preserving current decision payloads.
- [x] 4.4 Extract fixed point evidence, static evidence hydration, RAG answer-context payload shaping, and platform resource evidence preparation into an evidence-focused module.
- [x] 4.5 Extract approved tool registry and tool wrappers into a tool-focused module.
- [x] 4.6 Extract runtime diagnostics, log payload helpers, RAG trace shaping, and teacher-debug diagnostic projection into diagnostics-focused modules.
- [x] 4.7 Keep output normalization and guardrail ownership explicit and imported through the orchestrator/facade rather than consumers.

## 5. Behavior Preservation Tests

- [x] 5.1 Update student assistant stream tests to use public adapter/facade imports where possible and verify event compatibility.
- [x] 5.2 Update teacher learning-assistant debug tests to verify diagnostics and stream compatibility after adapter migration.
- [x] 5.3 Update assessment report agent tests to verify generated report behavior after adapter migration.
- [x] 5.4 Update posttest summary and mistake-explanation tests to verify cache, context construction, fallback, and generated response behavior.
- [x] 5.5 Update visible-thinking, retrieval-decision, image-evidence, guardrail, and LaTeX normalization tests to import helpers from new owning modules or documented compatibility exports.
- [x] 5.6 Add a projection test proving student output omits diagnostics that teacher/admin output retains for the same runtime scenario.

## 6. Architecture Enforcement

- [x] 6.1 Add a static import-boundary test that blocks FastAPI endpoints from importing private provider, retrieval, tool, diagnostics, or orchestrator internals.
- [x] 6.2 Add a static import-boundary test that blocks assessment/posttest/future domain consumers from assembling partial agent pipelines through private internals.
- [x] 6.3 Allow documented public imports: consumer adapters, `AgentRuntime`, compatibility `run_agent`, compatibility `run_agent_stream`, and explicitly exported test helpers.
- [x] 6.4 Add a test or architecture assertion that `agent.py`, if retained, contains only compatibility delegation and no independent orchestration pipeline.
- [x] 6.5 Keep async-streaming static enforcement passing after provider and streaming code move to new modules.

## 7. Compatibility Shim Cleanup

- [x] 7.1 Shrink `agent.py` to a compatibility shim once migrated consumers use adapters/facade.
- [x] 7.2 Move historically imported helper symbols to their owning modules and update tests/imports accordingly.
- [x] 7.3 Remove compatibility exports that no runtime or test code still imports.
- [x] 7.4 Verify no new consumer-specific branch was added to the core runtime when an adapter would have been more appropriate.

## 8. Verification

- [x] 8.1 Run `python -m pytest server/tests/test_assistant_runtime_characterization.py server/tests/test_student_chat_guardrails.py server/tests/test_student_chat_image_evidence.py -q`.
- [x] 8.2 Run `python -m pytest server/tests/test_student_assistant.py server/tests/test_student_assistant_visible_thinking.py server/tests/test_student_assistant_length_guardrail.py -q`.
- [x] 8.3 Run teacher learning-assistant debug backend/frontend tests affected by the adapter migration.
- [x] 8.4 Run assessment report and posttest generated-response tests affected by the adapter migration.
- [x] 8.5 Run the new architecture/import-boundary tests directly.
- [x] 8.6 Run `python -m py_compile` for all changed assistant modules and affected API/domain modules.
- [x] 8.7 Run `openspec validate modularize-shared-agent-runtime --strict`.
- [x] 8.8 If backend runtime code changed, rebuild or hot-update the backend container and smoke-check backend health.

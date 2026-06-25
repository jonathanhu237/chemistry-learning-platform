## Why

The same chemistry assistant agent now serves multiple consumers: student Atom chat, teacher learning-assistant debug, assessment reports, posttest summary and mistake explanation, and future point-centered scenarios. They all converge on `AgentAskRequest`, `run_agent`, and `run_agent_stream`, but orchestration still lives in a large `agent.py` module that mixes consumer adaptation, policy, retrieval, provider streaming, tools, output guardrails, logging, diagnostics, and compatibility helpers.

This change defines a real shared Agent Runtime boundary so every consumer can use the same agent execution engine through explicit adapters instead of growing one monolithic module with more flags.

## What Changes

- Introduce a shared Agent Runtime module boundary with stable `run` and `stream` entrypoints for all chemistry assistant consumers.
- Separate consumer adapters from agent execution:
  - student chat adapter
  - teacher/admin debug adapter
  - assessment/report adapter
  - posttest summary and mistake-review adapter
- Move core orchestration responsibilities out of the current oversized `agent.py` shape into focused modules for runtime orchestration, provider access, stream lifecycle, tool execution, retrieval decision, evidence preparation, output guardrails, and diagnostics.
- Preserve existing public API request/response schemas and SSE event contracts while moving implementation behind the new runtime boundary.
- Keep student-safe output and teacher diagnostics as adapter-controlled projections of the same runtime result/events.
- Make the new runtime compatible with `enforce-async-atom-ai-streaming`: async provider streaming and cancellation stay required.
- Add architecture/static tests so new consumers cannot import deep agent internals directly.
- Add characterization tests proving student, teacher debug, assessment, and posttest flows keep current behavior after modularization.

## Capabilities

### New Capabilities
- `shared-agent-runtime`: Defines the shared chemistry assistant runtime boundary, consumer adapter contract, canonical runtime events/results, module ownership, and migration rules for all current and future agent consumers.

### Modified Capabilities
- None. Existing student, teacher, assessment, and posttest feature behavior should remain externally compatible; this change introduces a backend architecture capability rather than changing user-facing requirements.

## Impact

- Backend assistant modules:
  - `server/app/domains/assistant/agent.py`
  - `server/app/domains/assistant/runtime.py`
  - new focused assistant runtime/provider/streaming/tool/adapter modules as needed
- Consumers:
  - `server/app/api/admin/admin_learning_assistant.py`
  - `server/app/domains/assistant/student_assistant.py`
  - `server/app/domains/assessments/reports.py`
  - posttest summary and mistake explanation paths
- Tests:
  - assistant runtime characterization
  - student assistant stream tests
  - teacher learning-assistant debug tests
  - assessment/report agent tests
  - architecture/static import-boundary tests
- No database migration.
- No frontend UI change required.
- No public API schema change intended.

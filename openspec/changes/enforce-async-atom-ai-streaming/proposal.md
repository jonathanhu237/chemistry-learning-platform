## Why

Atom assistant streaming is now mostly on the correct async path, but the codebase still contains legacy synchronous OpenAI stream helpers in the shared assistant module. Because student Atom chat and the teacher learning-assistant debug console share `run_agent_stream`, dead synchronous provider code is a future regression risk: one accidental call path can reintroduce event-loop blocking and make abandoned AI streams delay unrelated student or teacher pages.

This change turns the current investigation result into an enforceable contract: active Atom assistant SSE paths must use `AsyncOpenAI` or explicitly non-blocking local fallbacks, and legacy synchronous OpenAI stream code must be removed and guarded against returning.

## What Changes

- Remove unused legacy synchronous OpenAI answer and stream helpers from `server/app/domains/assistant/agent.py`.
- Replace or remove the remaining synchronous OpenAI one-shot helper in the Atom assistant runtime path so assistant model calls executed from async request handlers do not block the event loop.
- Keep non-Atom one-shot OpenAI usage in question generation, equation extraction, retrieval utilities, and platform settings out of scope unless it is invoked by the Atom assistant SSE path.
- Add a static regression check that fails if `server/app/domains/assistant` reintroduces synchronous `OpenAI` client imports, synchronous `stream=True` loops, or sync provider factories in the shared Atom assistant runtime.
- Preserve the existing successful SSE contract for students and teachers: `status`, `thinking`, `delta`, `replace`, `final`, and `error` events remain unchanged.
- Preserve existing cancellation behavior: frontend abort, backend disconnect checks, generator cancellation checkpoints, skipped final metadata on cancellation, and neutral cancellation UI.
- Add or extend tests that prove the active stream path uses async provider helpers and that unrelated async work can proceed while a provider stream is pending.

## Capabilities

### New Capabilities
- `atom-assistant-async-streaming`: Defines the shared Atom assistant streaming runtime contract, including async provider usage, removal of legacy synchronous stream code, cancellation compatibility, and static regression checks.

### Modified Capabilities
- None. Existing student and teacher UI behavior remains unchanged; this change adds a backend/runtime engineering contract for the shared Atom assistant stream path.

## Impact

- Backend assistant runtime:
  - `server/app/domains/assistant/agent.py`
  - `server/app/domains/assistant/student_assistant.py`
  - student and admin streaming endpoints only as needed for verification
- Tests and validation:
  - assistant stream lifecycle tests under `server/tests/`
  - a static architecture or regression test preventing sync OpenAI stream code in the assistant runtime
- No API schema changes.
- No frontend UI changes required beyond preserving the existing abort-capable stream clients.
- No new external dependencies expected.

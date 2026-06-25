## Context

The previous `harden-ai-stream-lifecycle` change established the right runtime shape for Atom assistant streams:

```text
Student/Teacher UI AbortController
  -> fetch(..., signal)
  -> FastAPI StreamingResponse checks request.is_disconnected()
  -> run_agent_stream(..., should_cancel)
  -> AsyncOpenAI provider streaming or local fallback
```

The investigation after that change found the active `run_agent_stream` provider path now calls:

- `_run_openai_responses_stream(...)`, which uses `AsyncOpenAI` Responses streaming with `async for`.
- `_run_openai_chat_completion_stream(...)`, which uses `AsyncOpenAI` Chat Completions streaming with `async for`.

It also found legacy synchronous OpenAI helpers still present in `server/app/domains/assistant/agent.py`, including a synchronous `stream=True` loop and a synchronous one-shot chat completion helper. The legacy stream helpers appear unreferenced today, but keeping them in the shared Atom assistant module makes the guarantee fragile: a future refactor could reconnect them and reintroduce backend event-loop blocking.

This change is therefore a cleanup and enforcement layer, not a UI redesign or protocol redesign.

## Goals / Non-Goals

**Goals:**

- Remove unused legacy synchronous OpenAI stream helpers from the shared Atom assistant runtime.
- Ensure the active Atom assistant SSE path cannot use synchronous provider streaming.
- Convert or isolate remaining synchronous Atom assistant OpenAI one-shot calls that run under async request handlers.
- Add a static regression test that fails if synchronous OpenAI client usage is reintroduced under `server/app/domains/assistant`.
- Preserve all existing student and teacher SSE event names and payload shapes.
- Preserve current cancellation semantics: frontend abort, backend disconnect checkpoints, neutral cancellation, and skipped final metadata on cancellation.

**Non-Goals:**

- Do not convert unrelated non-Atom OpenAI calls in question generation, catalog equation extraction, platform settings probes, or retrieval utilities unless they are called from the Atom assistant SSE path.
- Do not add backend-persisted chat sessions.
- Do not change frontend visual behavior, prompt chips, history behavior, or point binding behavior.
- Do not rely on additional uvicorn workers as the primary concurrency fix.
- Do not change model prompts except where necessary to preserve behavior while switching from sync to async client calls.

## Decisions

### Delete dead synchronous stream helpers instead of leaving comments

The legacy helpers should be removed, not merely marked deprecated. Comments are weak guardrails; tests and absence are stronger.

Alternative considered: keep them for rollback. Rejected because rollback should use git/deployment version rollback, not dormant sync code in the active runtime module.

### Keep the active stream path on `AsyncOpenAI`

The current provider stream helpers already use `AsyncOpenAI`, so implementation should preserve that shape:

```text
run_agent_stream
  -> _run_openai_responses_stream    # AsyncOpenAI responses.stream + async for
  -> _run_openai_chat_completion_stream # AsyncOpenAI chat.completions.create(stream=True) + async for
```

Any provider failure should continue to fall back to local answer generation as today, but cancellation must still bypass fallback and stop neutrally.

Alternative considered: run synchronous OpenAI stream in a worker thread bridge. Rejected for this codebase because the active provider path now supports official async streaming directly; a bridge would add complexity and keep sync streaming alive.

### Treat one-shot Atom assistant model calls as part of async safety

Streaming was the original blocking risk, but a synchronous one-shot OpenAI call inside an async FastAPI request handler can still block the event loop while waiting for the provider. The Atom assistant runtime should therefore avoid synchronous OpenAI one-shot calls in `run_agent`, `run_agent_stream`, student final metadata generation, and teacher debug paths.

Implementation can either:

- Convert the one-shot helper to `AsyncOpenAI`, or
- Remove it if no active path still uses it.

Alternative considered: leave one-shot sync calls because they are shorter lived than streams. Rejected because the user goal is multi-user AI concurrency, and provider latency is still event-loop blocking even when the request is not streamed.

### Static enforcement belongs in tests

The codebase should include a focused architecture/static test that scans `server/app/domains/assistant` and rejects:

- `from openai import OpenAI`
- `OpenAI(...)`
- synchronous `stream=True` provider usage followed by `for ... in stream`
- sync OpenAI client factories in the shared assistant runtime

The test should allow `AsyncOpenAI` and should not scan unrelated domains by default.

Alternative considered: rely on code review. Rejected because this regression is easy to miss and has product-level concurrency impact.

### Keep unrelated synchronous OpenAI usage out of this change

The investigation found other synchronous OpenAI usage outside the Atom assistant SSE path, such as question generation, catalog equation extraction, retrieval utilities, and platform AI configuration probing. Those paths may deserve future hardening, but they are not the abandoned-stream risk described here.

This change should document the boundary so the implementation stays small and avoids surprise refactors.

## Risks / Trade-offs

- [Risk] Static grep can be too broad and fail on comments or fixtures. -> Mitigation: implement a small Python test with path allowlists and clear failure messages rather than a fragile shell-only grep.
- [Risk] Removing legacy helpers accidentally removes behavior still used by old tests. -> Mitigation: first prove there are no call sites, then run assistant stream and posttest helper tests after removal.
- [Risk] Converting one-shot helper calls to async could change exception timing or fallback behavior. -> Mitigation: preserve existing error handling and add focused tests for provider failure fallback and real connected errors.
- [Risk] `AsyncOpenAI` behavior differs for OpenAI-compatible custom base URLs. -> Mitigation: keep the existing `openai_compatible` async chat-completions path and keep Responses reasoning summaries opt-in/force-gated as currently designed.
- [Risk] Local fallback generation remains synchronous Python work. -> Mitigation: local fallback is bounded CPU/string assembly without provider waiting; cancellation checkpoints before and after fallback remain required.

## Migration Plan

1. Remove unreferenced legacy synchronous stream and always-RAG helper code from `agent.py`.
2. Convert or remove remaining synchronous Atom assistant OpenAI one-shot helper usage.
3. Add the static regression test for assistant-domain sync OpenAI usage.
4. Run backend assistant tests, stream lifecycle tests, and OpenSpec validation.
5. Deploy normally. No schema migration or API migration is required.

Rollback should use git/deployment rollback. Do not reintroduce sync helper compatibility wrappers as a rollback mechanism.

## Open Questions

- Whether to create a later broader change for non-Atom synchronous OpenAI usage across question generation, catalog equation extraction, retrieval utilities, and platform configuration probes.
- Whether production readiness validation should include the new static assistant async enforcement test directly or rely on the backend test suite that contains it.

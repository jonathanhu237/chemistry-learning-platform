## 1. Stream Contract And Configuration

- [x] 1.1 Add backend settings for reasoning summary enablement, mode, and effort with safe defaults.
- [x] 1.2 Add provider/capability helper logic that enables reasoning summaries only for explicitly supported Responses-compatible deployments.
- [x] 1.3 Define backend helper functions for sanitized `thinking` stream payloads with `source`, `message`, optional `phase`, and optional `sequence`.
- [x] 1.4 Extend student frontend stream event typing to include `thinking` while preserving unknown-event compatibility.

## 2. Backend Thinking Sources

- [x] 2.1 Add a student-visible thinking sanitizer that trims, bounds, and rejects raw reasoning, diagnostics, identifiers, stack traces, and unsafe/internal text.
- [x] 2.2 Emit `thinking(source="agent_trace")` only from real agent operations such as policy evaluation, context preparation, retrieval, generation start, and local fallback.
- [x] 2.3 Refactor the OpenAI model stream path so answer deltas still emit existing `delta` events and final output behavior remains unchanged.
- [x] 2.4 Add a Responses-compatible streaming helper that maps reasoning summary text events to sanitized `thinking(source="reasoning_summary")` events.
- [x] 2.5 Ignore raw reasoning text or lower-level reasoning events for student display even if the provider stream includes them.
- [x] 2.6 Fall back to Chat Completions/local answer paths plus `agent_trace` thinking when reasoning summaries are disabled, unsupported, malformed, or fail.
- [x] 2.7 Preserve output guardrail `replace`, final response metadata, follow-up prompt generation, logging, and existing `status` compatibility events.

## 3. Student H5 Presentation

- [x] 3.1 Track active-turn visible thinking state in `StudentAiChatPanel` separately from answer text and legacy status.
- [x] 3.2 Prioritize `thinking.message` over local preset phase labels when rendering the root Atom thinking line.
- [x] 3.3 Keep legacy `status` normalization as fallback when no valid `thinking` event has arrived.
- [x] 3.4 Prevent streamed answer text from immediately overwriting a fresh model `reasoning_summary` message with generic `正在生成回答`.
- [x] 3.5 Clear active thinking state on `final`, `error`, reset, new chat, and restored-history transitions.
- [x] 3.6 Reuse the existing root fade-through/dwell thinking-line motion for authentic thinking message changes.
- [x] 3.7 Keep contextual `/ai/chat` running state behavior distinct unless the implementation intentionally scopes support there later.

## 4. Backend Tests

- [x] 4.1 Cover reasoning-summary enabled flow: sanitized summary emits `thinking(source="reasoning_summary")` and answer deltas/final still stream.
- [x] 4.2 Cover unsupported/disabled summary flow: no fake model thinking is emitted and `agent_trace` fallback is used.
- [x] 4.3 Cover reasoning-summary failure flow: the answer continues through fallback and student-safe thinking remains available when possible.
- [x] 4.4 Cover sanitizer rejection for raw chain-of-thought, policy internals, RAG traces, tool args, chunk ids, exception text, and provider debug payloads.
- [x] 4.5 Cover that `thinking` text is never appended to the answer body or final answer text.
- [x] 4.6 Cover that existing stream clients can ignore `thinking` events and still receive `delta`, `replace`, `final`, or `error` as before.

## 5. Frontend Tests And QA

- [x] 5.1 Add or update H5 tests proving root running line displays `thinking.message` before legacy status fallback.
- [x] 5.2 Add or update H5 tests proving legacy `status` fallback still works when no `thinking` event arrives.
- [x] 5.3 Add or update H5 tests proving `final` and `error` remove running-only thinking state.
- [x] 5.4 Add or update H5 tests proving the thinking message does not enter assistant markdown answer content or copied answer text.
- [x] 5.5 Add or update role-boundary/static checks preventing raw `rag_trace`, guardrail arrays, tool calls, provider errors, and reasoning internals from rendering in student UI.
- [x] 5.6 Run focused backend tests for student assistant streaming and guardrails.
- [x] 5.7 Run focused student frontend tests and typecheck.
- [x] 5.8 Run `openspec validate student-ai-visible-reasoning-summary --strict`.

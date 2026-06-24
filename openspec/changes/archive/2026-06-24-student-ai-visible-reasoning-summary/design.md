## Context

The student Atom assistant already streams answers through `/api/student/assistant/ask/stream`. The route converts items from `stream_student_assistant_answer(...)` into SSE events, and the student frontend parses them as `StudentAssistantStreamEvent`. Today the stream contract is answer-centric: `status`, `delta`, `replace`, `final`, and `error`. The current visible running line in `StudentAiChatPanel` is therefore driven by local phase normalization over backend status strings and answer presence.

That solved the visual problem of the previous card-like loading state, but it did not solve the authenticity problem: labels such as `正在生成回答` or `正在判断问题范围` are still product stages, not necessarily the model's visible reasoning. The backend also currently emits `正在连接模型...` before `_run_openai_chat_completion_stream(...)` performs curriculum lookup and RAG lookup, so the UI can say "generating" while the agent is still preparing evidence.

OpenAI's current Responses API documentation describes opt-in reasoning summaries and streaming summary text events such as `response.reasoning_summary_text.delta` and `response.reasoning_summary_text.done`. It also exposes lower-level reasoning text event types in the streaming reference. This change must consume only safe summary text when available and must not expose raw chain-of-thought, raw reasoning text, or internal diagnostic payloads to students.

The existing agent already records real execution facts: policy classification, guardrail decisions, tool calls, source refs, RAG trace, output guardrail replacement, and final mode. Those facts are useful for backend/admin diagnostics, but the student UI must receive only a short sanitized trace sentence when model reasoning summaries are unavailable.

## Goals / Non-Goals

**Goals:**

- Surface authentic student-visible thinking/progress during student Atom streaming turns.
- Prefer model-provided reasoning summaries when the configured provider/model/API supports them.
- Fall back to truthful agent execution trace events when model reasoning summaries are unavailable.
- Keep the fallback honest by labeling it as agent execution trace internally, not model thought.
- Preserve the existing SSE answer streaming contract and existing clients.
- Reuse the root Atom thinking line and fade-through text transition already implemented for the flat running surface.
- Keep all visible copy concise, Chinese, student-readable, and safe for H5 mobile widths.
- Prevent raw chain-of-thought, raw reasoning text, policy codes, RAG internals, tool arguments, source chunk identifiers, and exception details from reaching the student UI.

**Non-Goals:**

- Do not expose full model chain-of-thought.
- Do not promise that every model/provider supports reasoning summaries.
- Do not require an additional model solely for visible thinking.
- Do not change the final answer payload shape, citation metadata, follow-up prompt contract, or local history storage.
- Do not expose teacher/admin learning-assistant diagnostics in the student surface.
- Do not redesign the existing fade-through motion, dot/Lottie mark, composer geometry, root header, or action row.
- Do not make `status` events disappear; old clients should keep functioning.

## Decisions

1. **Add a new `thinking` SSE event instead of overloading `status`.**

   New event payload:

   ```ts
   type StudentAssistantThinkingEvent = {
     event: "thinking";
     source: "reasoning_summary" | "agent_trace";
     message: string;
     phase?: "policy" | "retrieval" | "reasoning" | "generation" | "fallback";
     sequence?: number;
   };
   ```

   `status` remains a lifecycle compatibility event. `thinking` is the student-visible content source. This prevents raw backend status strings from being treated as thought and lets the frontend display authentic messages first while preserving legacy fallback behavior.

   Alternative considered: keep using `status.message`. Rejected because `status` already contains implementation-flavored strings and cannot distinguish model reasoning summary from local product phase labels.

2. **Use provider capability gates before attempting reasoning summaries.**

   Add settings that let the deployment opt into reasoning summaries without changing the configured answer model:

   - `AGENT_REASONING_SUMMARY_ENABLED`, default `false`
   - `AGENT_REASONING_SUMMARY_MODE`, default `auto`
   - `AGENT_REASONING_EFFORT`, default `low`

   The implementation should attempt Responses streaming only when the current provider is truly Responses-compatible and a model is configured. For custom `openai_compatible` base URLs, default to agent trace fallback unless configuration explicitly enables Responses-compatible reasoning summaries for that provider.

   Alternative considered: always call Responses API when `AGENT_LLM_PROVIDER=openai`. Rejected because existing deployments may rely on Chat Completions-compatible providers/base URLs.

3. **Support two backend streaming paths with the same answer output contract.**

   The current Chat Completions path stays as a compatibility path. A new Responses path can be introduced for reasoning-summary-capable turns:

   - Build the same curriculum/RAG evidence package before the model stream.
   - Stream `thinking(source="agent_trace")` for real pre-model steps such as policy gate and retrieval.
   - Start Responses streaming with reasoning summary opt-in.
   - Convert answer text deltas to existing `delta` events.
   - Convert `response.reasoning_summary_text.delta` / completed summary chunks into sanitized `thinking(source="reasoning_summary")` events.
   - Ignore or suppress raw reasoning text events for student display.
   - Build the same final `AgentAskResponse`, apply output guardrails, persist logs, and emit existing `final`.

   Alternative considered: call a second "summary model" after generation to invent visible thinking. Rejected because it adds latency/cost and still would not represent actual in-turn progress.

4. **Agent trace fallback must be real and source-labeled.**

   When model reasoning summaries are unsupported, disabled, or fail, emit only facts the agent actually performed. Examples:

   - `正在判断问题范围`
   - `正在整理课程上下文`
   - `正在检索课程资料`
   - `正在根据资料组织回答`
   - `正在使用本地兜底生成回答`

   The stream payload source is `agent_trace`. The UI may display only the message, but logs/tests should preserve the source so the system never represents trace fallback as model reasoning.

   Alternative considered: keep current preset phase sequence. Rejected because it is the exact behavior the user is trying to replace.

5. **Sanitize every visible thinking message at the backend boundary.**

   Backend sanitizer rules:

   - Trim whitespace and collapse repeated whitespace.
   - Limit visible length, recommended 6 to 28 Chinese characters or an equivalent short phrase.
   - Strip Markdown, JSON-looking structures, stack traces, URLs, raw ids, chunk ids, model/provider names, policy labels, and debug jargon.
   - Drop messages that mention chain-of-thought, system prompt, tool arguments, raw RAG trace, scores, guardrail arrays, exceptions, or teacher/admin diagnostics.
   - Replace dropped model summary content with no event rather than a fake substitute.
   - Allow fallback agent trace messages only from a fixed allowlist or fixed templates.

   Alternative considered: sanitize in the frontend. Rejected because student-visible safety should be enforced before data leaves the backend.

6. **Frontend priority order is `thinking` > legacy normalized status > generic fallback.**

   `apps/web-student/src/api.ts` should extend the event union with `thinking`. `StudentAiChatPanel` should maintain a current visible thinking message/source for the active turn:

   - On `thinking` with a safe string, update the thinking line phase/message.
   - On `status`, keep the existing legacy status state for compatibility.
   - When no `thinking` has arrived, derive the current label from the existing `assistantStreamPhase(status, hasAnswer)`.
   - When answer text starts, do not overwrite a fresh model `reasoning_summary` message with generic `正在生成回答` unless the stream enters final answer generation and no newer thinking message is available.
   - On `final`, clear running-only thinking state.
   - On `error`, clear running thinking state and show the error treatment.

   Alternative considered: always convert answer text presence to `正在生成回答`. Rejected because it can hide actual reasoning-summary text during models that provide it.

7. **Keep fade-through as a presentation mechanism only.**

   The previous `AssistantThinkingLine` minimum-visible-duration and fade-through behavior remains valuable, but it should animate authentic thinking labels rather than define the truth. The animation should continue to run on semantic message changes and remain reduced-motion friendly.

   Alternative considered: remove phase dwell and show every thinking event instantly. Rejected because streaming APIs may emit small summary fragments too quickly for a mobile UI.

8. **Preserve admin/teacher diagnostics while separating student visibility.**

   `tool_calls`, `guardrail_decisions`, and `rag_trace` should continue to exist in backend logs and teacher/admin debug surfaces where specs already allow them. The new student stream must not expose them directly. If a trace event is derived from an internal operation, it must be a high-level phrase from the allowed student copy set.

## Risks / Trade-offs

- [Risk] Some configured providers may not support Responses reasoning summaries. -> Mitigation: gate by provider/capability and fall back to `agent_trace` without failing the answer.
- [Risk] Reasoning summary event names or SDK shapes can vary by OpenAI SDK version. -> Mitigation: isolate parsing in a helper with tests using representative events and keep Chat Completions fallback.
- [Risk] Model summary text can be verbose or unsafe for students. -> Mitigation: backend sanitizer drops unsafe messages and frontend never renders raw summary payloads.
- [Risk] Trace fallback can still feel like preset stages if emitted too mechanically. -> Mitigation: emit only when the corresponding agent operation actually runs, including retrieval/no-retrieval decisions.
- [Risk] Too many thinking updates can make the line flicker. -> Mitigation: frontend keeps the existing semantic dwell/fade-through behavior and backend coalesces duplicate messages.
- [Risk] Adding Responses streaming touches shared agent code used by admin streams. -> Mitigation: scope `thinking` event consumption to student H5, preserve existing admin `status`/`delta`/`final`, and add compatibility tests.
- [Risk] Raw lower-level reasoning text could be mistaken for displayable summary. -> Mitigation: explicitly ignore raw reasoning text events and only display summary events that pass sanitizer.

## Migration Plan

1. Add settings and provider capability helpers for reasoning summary support.
2. Add backend event helpers for sanitized `thinking` events and trace sequence numbering.
3. Refactor the student agent stream so real execution steps can emit `thinking(source="agent_trace")` at policy, context, retrieval, generation, and fallback boundaries.
4. Add a Responses streaming helper that maps answer text deltas to existing `delta` events and reasoning summary text to sanitized `thinking(source="reasoning_summary")` events.
5. Keep Chat Completions stream as fallback and emit agent trace thinking events when Responses summaries are not used.
6. Extend frontend event types and active-turn state to prioritize `thinking.message`.
7. Reuse existing `AssistantThinkingLine` fade-through/dwell behavior for the new visible message source.
8. Add backend tests for supported summary, unsupported fallback, sanitizer drops, and compatibility.
9. Add frontend tests for `thinking` priority, legacy `status` fallback, final cleanup, error cleanup, and root/detail scoping.
10. Run OpenSpec validation, backend focused tests, student frontend focused tests, and typecheck.

Rollback is safe because the stream remains backward-compatible. If reasoning summaries misbehave, disable `AGENT_REASONING_SUMMARY_ENABLED` and the UI will continue with `agent_trace` or legacy status fallback. If the frontend change must roll back, old `status` events still provide the previous running labels.

## Open Questions

- Should teacher/admin streaming surfaces display `thinking` events for debugging? Recommendation: no for this change; keep them available only as raw stream events if needed, but do not redesign teacher/admin UI.
- Should the H5 UI visibly distinguish `reasoning_summary` from `agent_trace`? Recommendation: not in the first UI pass; keep source in telemetry/tests while displaying only one student-readable line.
- Should retrieval no-match be visible to students? Recommendation: yes only as high-level copy such as `正在根据课程知识组织回答`; never expose "RAG no match" wording.
- Should the Responses helper replace Chat Completions completely later? Recommendation: defer until provider configuration and regression coverage prove it is stable.

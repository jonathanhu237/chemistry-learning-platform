## Context

The student Atom chat currently carries `prompts` inside `AssistantContext`. Those prompts are authored in frontend route code and are rendered after `messages.length > 0`, which means they can appear after a failed assistant turn and can remain unrelated to the actual answer.

The student stream endpoint already sends answer text as `delta` events and sends final metadata as a `final` event. The frontend stores that final metadata on the assistant message and persists it through local history. This is the right integration point for per-turn follow-up prompts because the metadata belongs to the completed assistant answer.

## Goals / Non-Goals

**Goals:**

- Generate follow-up prompt chips from the model after a successful student Atom answer.
- Preserve context by generating suggestions from the current student question, completed answer, active assistant context, and recent conversation history.
- Display only the latest successful assistant turn's suggestions.
- Hide suggestions while streaming, after failed turns, and when no valid suggestions are available.
- Let the model choose 3-5 suggestions, while displaying any valid suggestions that survive backend filtering.
- Keep suggestions short enough for the mobile chip row: 8-24 visible characters after trimming.

**Non-Goals:**

- Do not change teacher/admin assistant contracts.
- Do not add a new public endpoint for suggestions unless implementation discovers the stream final event cannot carry them safely.
- Do not make frontend fallback prompts when model suggestions are missing or invalid.
- Do not accumulate old suggestions across turns.
- Do not redesign the Atom chat layout, keyboard behavior, history shell, or stream answer rendering.

## Decisions

1. **Attach suggestions to the student stream `final.response`.**

   - Decision: Add `suggested_prompts: string[]` to the final metadata returned by `/api/student/assistant/ask/stream`.
   - Rationale: The prompt row is a property of the completed assistant turn, not of the page context. The final event already marks successful completion and already feeds assistant-message metadata.
   - Alternative considered: emit a separate `suggestions` SSE event. This separates answer completion from suggestion completion but introduces another frontend state and ordering path. The final response is simpler and keeps "show only after success" precise.

2. **Generate suggestions in the student assistant wrapper, not in the shared agent response model.**

   - Decision: Intercept the student stream final item in `server/app/domains/assistant/student_assistant.py`, generate student follow-ups, sanitize them, and attach them to the final response.
   - Rationale: The feature is student-web-specific. Keeping it outside `AgentAskResponse` avoids changing teacher/admin assistant behavior and avoids broad API surface changes.
   - Alternative considered: add `suggested_prompts` to `AgentAskResponse`. This is more uniform but affects admin learning assistant response typing, logs, and tests for no student benefit.

3. **Fail quietly when suggestion generation fails.**

   - Decision: A successful answer remains successful even if follow-up suggestion generation fails, returns malformed output, or filters to zero items.
   - Rationale: Suggestions are a convenience layer. They must not turn a good answer into a failed chat turn.
   - Alternative considered: show static fallback prompts when suggestions fail. This would reintroduce the stale-prompt problem the change is meant to remove.

4. **Sanitize model output on the backend.**

   - Decision: Ask the model for a JSON array of 3-5 strings, then backend-filter to 1-5 valid strings. Each valid string must be unique after normalization and 8-24 visible characters after trimming.
   - Rationale: The model can choose 3, 4, or 5, but mobile UI quality still needs hard bounds. "有就显示" means the frontend may show 1 or 2 valid suggestions if the model output was partially valid after filtering.
   - Alternative considered: require exactly 3 suggestions after filtering. This is brittle and can force low-quality filler suggestions.

5. **Render suggestions from the latest assistant message only.**

   - Decision: The frontend derives visible chips from the most recent assistant message metadata where the message is a successful final answer. It clears visible chips when a new question starts.
   - Rationale: This prevents old suggestions from carrying over after the student asks something new or after a failed turn.
   - Alternative considered: keep suggestions on `activeContext.prompts`. That loses per-turn specificity and cannot distinguish stale suggestions from current answer suggestions.

6. **Preserve context on suggestion clicks through the existing submit path.**

   - Decision: Clicking a suggestion calls the existing `submitQuestion(promptText)` path using the current `activeContext` and current visible conversation history.
   - Rationale: This keeps the same context propagation already used for manual follow-ups, including restored local history and contextual `/ai/chat` entries.
   - Alternative considered: store a hidden context snapshot per suggestion. This is unnecessary because the active chat already owns the context and history.

## Risks / Trade-offs

- [Risk] Suggestion generation adds latency before the `final` event. Mitigation: answer deltas have already streamed; keep suggestion generation short, JSON-only, and fail quietly on timeout/error.
- [Risk] The model may return unsafe, answer-revealing, or off-course suggestions. Mitigation: backend prompt constraints plus deterministic filtering and guardrail checks before attaching suggestions.
- [Risk] Strict 8-24 character filtering may remove useful mixed-language chemistry suggestions. Mitigation: display any remaining valid suggestions and do not force a minimum count.
- [Risk] Local history may contain older entries without `suggested_prompts`. Mitigation: treat missing or invalid metadata as no suggestions.
- [Risk] Static `AssistantContext.prompts` fields may remain for backward compatibility. Mitigation: stop using them for post-turn prompt chips; future cleanup can remove them once no callers depend on the field.
- [Risk] Suggestion prompts might imply direct assessment answers. Mitigation: reuse student assessment-answer protection rules for suggestions and avoid question forms that ask for "答案选哪个" or equivalent direct-answer requests.

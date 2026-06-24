## 1. Backend Final Metadata Contract

- [x] 1.1 Add a student-only `suggested_prompts` field to the stream final response typing and serialization path without changing teacher/admin assistant response contracts.
- [x] 1.2 Intercept successful student assistant `final` stream events in `server/app/domains/assistant/student_assistant.py` so suggestions can be attached before the event is yielded.
- [x] 1.3 Keep successful answer finalization independent from suggestion generation so suggestion errors, malformed output, or empty results do not fail the assistant turn.

## 2. Backend Suggestion Generation

- [x] 2.1 Implement a prompt-suggestion generator that uses the active student assistant context, latest raw student question, completed answer text, and recent conversation history.
- [x] 2.2 Instruct the model to return a JSON array of 3-5 concise student-facing follow-up questions, with no explanations or markdown.
- [x] 2.3 Sanitize generated suggestions by trimming whitespace, removing duplicates, rejecting non-string/empty values, enforcing 8-24 visible characters, and keeping at most five items.
- [x] 2.4 Apply student guardrail filtering so suggestions stay course-scoped, avoid unsafe experiment-operation requests, avoid direct assessment-answer requests, and do not expose diagnostics.
- [x] 2.5 Return any remaining valid suggestions, including one or two items when fewer than three survive filtering, and return none when no valid suggestions remain.

## 3. Student Web Prompt State

- [x] 3.1 Extend `apps/web-student/src/api.ts` metadata types to include `suggested_prompts?: string[]`.
- [x] 3.2 Update `StudentAiChatPanel` so the quick prompt row reads only the latest successful assistant message metadata, not `activeContext.prompts`.
- [x] 3.3 Clear visible quick prompts immediately when a new question starts streaming.
- [x] 3.4 Ensure failed turns show no prompt chips and do not revive suggestions from earlier successful turns.
- [x] 3.5 Keep suggestion clicks on the existing `submitQuestion(prompt)` path so current active context and visible conversation history are preserved.
- [x] 3.6 Preserve local history compatibility: older entries without suggestions render normally, and restored entries only show latest-turn suggestions when present.

## 4. Static Prompt Cleanup

- [x] 4.1 Remove or stop relying on frontend-authored `AssistantContext.prompts` values for post-turn quick prompt chips.
- [x] 4.2 Keep any retained `prompts` field strictly as compatibility data until a later cleanup removes it from route contexts and stored context normalization.
- [x] 4.3 Verify root, contextual point, assessment report, and video-library Atom chat entries no longer display hardcoded post-turn prompt chips.

## 5. Verification

- [x] 5.1 Add backend tests for successful final events with suggestions, suggestion-generation failure, filtering to fewer than three items, and guardrail removal.
- [x] 5.2 Add student-web tests for final metadata suggestions rendering, per-turn replacement, loading-time hiding, failed-turn hiding, and restored-history behavior.
- [x] 5.3 Run focused backend tests for student assistant streaming.
- [x] 5.4 Run focused student-web e2e/typecheck tests for Atom chat prompt behavior.
- [x] 5.5 Run `openspec validate student-ai-dynamic-followup-prompts --strict` and, if practical, `openspec validate --all --strict`.

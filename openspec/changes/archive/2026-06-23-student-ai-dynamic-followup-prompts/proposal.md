## Why

The student Atom chat currently displays static, frontend-defined quick prompts after a turn starts, including after failed assistant turns. This makes the prompt row feel disconnected from the actual answer and can show stale or irrelevant suggestions.

Dynamic follow-up prompts should be generated from the just-completed model answer, current assistant context, and recent conversation so the student can continue naturally without losing context.

## What Changes

- Replace student-web static quick prompts with model-generated follow-up prompts returned by the student assistant stream final event.
- Show follow-up prompts only after a successful, complete assistant response.
- Hide follow-up prompts while a new turn is streaming and after failed turns.
- Treat suggestions as per-turn data: each successful assistant response replaces the previous prompt row; prior-turn suggestions are not accumulated or reused.
- Let the model decide whether to return 3, 4, or 5 suggestions, while the backend sanitizes suggestions to useful student-facing length and content.
- Preserve the existing student assistant request fields, streaming text behavior, local history behavior, Atom visual identity, and route structure.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `student-h5-ai-assistant`: Add the dynamic follow-up prompt contract for student Atom chat final responses and prompt-row rendering.
- `student-chat-guardrails`: Require generated follow-up prompts to respect the same student safety, assessment, and course-scope boundaries as assistant answers.

## Impact

- Backend student assistant stream: `/api/student/assistant/ask/stream` final response metadata gains a student-only `suggested_prompts` array.
- Backend assistant domain: generates and sanitizes 3-5 follow-up suggestions from the current question, answer, active page context, and recent conversation.
- Frontend student API types: `StudentAssistantFinalMetadata` supports suggested prompts.
- Frontend student chat panel: removes visible reliance on `AssistantContext.prompts` for post-turn chips and renders only latest successful assistant-message suggestions.
- Frontend local history: keeps suggestions on the assistant turn metadata when present, but only the latest assistant turn controls visible chips.
- Tests: cover successful final suggestions, failed-turn hiding, replacement per turn, and no teacher/admin behavior changes.

## Why

The student Atom assistant currently shows preset product phases such as `正在生成回答`, but those phases are not the model's actual reasoning signal and can feel fake once students notice the mismatch. We need the running state to surface authentic progress: prefer model-provided reasoning summaries when the configured model/API supports them, and otherwise fall back to truthful agent execution trace events without pretending they are model thoughts.

## What Changes

- Add a student assistant streaming contract for visible thinking updates separate from answer text.
- Prefer safe model reasoning summaries from a Responses-compatible model/API when explicitly supported and enabled.
- Fall back to sanitized real agent execution trace events when reasoning summaries are unavailable, unsupported, disabled, or fail during a turn.
- Keep the existing answer stream behavior (`status`, `delta`, `replace`, `final`, `error`) compatible for old clients.
- Update the H5 Atom running line to display the new visible thinking message before using normalized legacy status fallback copy.
- Preserve the existing fade-through thinking-line animation and root flat running surface while changing its content source from preset phases to authentic thinking/progress updates.
- Add safeguards that prevent raw chain-of-thought, policy internals, RAG traces, tool arguments, exception text, source chunk identifiers, and teacher/admin diagnostics from reaching the student UI.

## Capabilities

### New Capabilities
- `student-ai-visible-thinking-stream`: Defines student-safe visible thinking updates for the student assistant stream, including model reasoning summary preference, agent trace fallback, SSE event contract, sanitization, and frontend presentation priority.

### Modified Capabilities
- `student-h5-ai-assistant`: The student H5 assistant running state must consume authentic visible thinking updates when available instead of relying only on preset local phase labels.

## Impact

- Backend streaming agent path: `server/app/domains/assistant/agent.py`
- Student assistant stream wrapper: `server/app/domains/assistant/student_assistant.py`
- Student assistant SSE route: `server/app/api/student/student_assistant.py`
- Settings for provider capability and reasoning-summary opt-in: `server/app/infrastructure/settings.py`
- Student API stream event typing/parsing: `apps/web-student/src/api.ts`
- Student Atom chat running UI: `apps/web-student/src/features/assistant/StudentAiChatPanel.tsx`
- Student assistant CSS/tests for root thinking line behavior
- Backend and frontend tests covering reasoning-summary support, agent-trace fallback, sanitization, compatibility, and no raw diagnostic exposure

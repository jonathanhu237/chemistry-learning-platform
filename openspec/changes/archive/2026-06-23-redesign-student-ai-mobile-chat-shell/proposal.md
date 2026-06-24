## Why

The student AI entry currently behaves like an AI center that routes into a separate detail chat page, while the desired product feel is closer to a mobile chat app: opening the AI tab should immediately expose a course assistant conversation surface. This also separates two different jobs that are now visually blurred: the root AI tab is the place to start and review chats, while contextual AI launched from learning, point, and assessment pages remains a second-level task page.

## What Changes

- Redesign the student `/ai` root route into a mobile-first direct chat shell inspired by the teacher learning assistant chat area, adapted for phone use and student-facing copy.
- Keep unsupported generic-AI controls out of the first round: no attachment upload, no model picker, and no voice input.
- Add a root-only history affordance in the `/ai` top-right area so students start history review from the AI tab.
- Preserve `/ai/chat` as a second-level contextual chat page for calls from home, learning, point detail, chapter/detail pages, video-library AI results, and assessment reports.
- Share the underlying chat stream, message rendering, status, source summary, and composer behavior between `/ai` and `/ai/chat`, while keeping their page chrome and navigation semantics separate.
- De-emphasize structured starter prompts and point-selection flows for this first round; they may remain as later optional affordances, but the default first screen is the direct chat composer.
- Preserve backend student AI guardrails, RAG/resource grounding, assessment-answer protection, and feature-switch enforcement.

## Capabilities

### New Capabilities

- `student-ai-chat-history`: Defines the root-only student AI history entry and first-round chat session history behavior.

### Modified Capabilities

- `student-h5-route-stack-navigation`: The AI root route changes from an AI center that only launches detail chat into a root chat shell, while `/ai/chat` remains the shared contextual second-level page.
- `student-chat-guardrails`: Student chat presentation requirements change to support the direct mobile chat shell, shared stream behavior, unsupported-control omissions, and root-only history entry.
- `student-h5-assistant-mobile-starter`: The initial assistant experience changes from mandatory starter surfaces before the first turn to a direct composer-first chat shell; starter prompts become optional future/secondary affordances.
- `student-h5-assistant-point-starter`: Point starter behavior is no longer a default first-screen path for the AI root; contextual point chat is entered from point-aware source pages or optional later controls.

## Impact

- Frontend student app routes and shell:
  - `apps/web-student/src/routes/ai/AiRootPage.tsx`
  - `apps/web-student/src/routes/ai/AiChatPage.tsx`
  - `apps/web-student/src/features/assistant/*`
  - `apps/web-student/src/app/router/navigation.ts`
  - `apps/web-student/src/styles/assistant.css`
  - `apps/web-student/src/styles/app-shell.css`
- Student frontend API types may need a lightweight history/session model if implemented in the first round.
- Backend student assistant streaming contract should remain compatible; no first-round change is required for model selection, uploads, or voice.
- Tests should cover root AI chat rendering, root-only history access, contextual `/ai/chat` navigation, feature-disabled states, and mobile viewport layout.

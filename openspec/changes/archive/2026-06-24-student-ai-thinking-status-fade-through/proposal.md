## Why

The root Atom assistant now renders completed answers as flat text, but the active loading turn still reads as an old card-like status surface with a meta header, pill, and skeleton. This breaks the new flat chat model at the exact moment students are waiting for feedback.

We want the running state to feel like Gemini-style thinking feedback: a lightweight inline row with animated dots and stage text that fades through between phases, then disappears cleanly when the answer completes.

## What Changes

- Replace the root Atom running assistant card treatment with a flat inline thinking line.
- Remove the repeated `Atom 学习助手 / 生成中` meta row from root running turns.
- Replace the current progress pill and skeleton-only empty response with a Gemini-inspired dot animation plus stage label.
- Animate stage label changes using a fade-through text transition: the old label fades out, the next label fades in, and the transition only happens when the normalized assistant phase changes.
- Keep streaming answer text readable below or after the thinking line while the response is still running.
- Remove the thinking line after final completion so successful answers remain flat markdown plus the existing action row.
- Keep failed turns visually bounded and keep detail-route `/ai/chat` behavior distinct unless explicitly scoped later.
- Preserve the existing student assistant streaming API and status/delta/final event semantics.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-ai-assistant`: Root Atom assistant running turns must use a flat thinking line with animated dots and fade-through status text instead of a card-like loading surface.

## Impact

- Student frontend only:
  - `apps/web-student/src/features/assistant/StudentAiChatPanel.tsx`
  - `apps/web-student/src/styles/assistant.css`
  - `apps/web-student/src/App.e2e.test.tsx`
  - `apps/web-student/src/roleBoundaries.test.ts`
- OpenSpec:
  - `openspec/specs/student-h5-ai-assistant/spec.md`
- No backend API, database, or SSE contract changes are expected.
- No new animation dependency is expected; CSS keyframes should cover the dots and fade-through text behavior.

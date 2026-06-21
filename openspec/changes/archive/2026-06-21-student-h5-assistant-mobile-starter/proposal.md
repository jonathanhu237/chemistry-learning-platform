## Why

The student H5 `问答` tab already moved AI into a phone-first app destination, but its first screen is still a sparse chat panel with horizontal prompt chips and limited interaction guidance. Teachers already have a stronger learning-assistant workbench pattern: choose context, choose question intent, preview a useful starter question, then continue into streaming chat.

This change brings that teacher-side prompt scaffolding into the student mobile experience without turning the phone UI into a compressed admin console.

## What Changes

- Add a mobile starter experience for the student `问答` tab that helps students begin from a course question, chapter context, experiment group, or experiment point.
- Replace the current empty-state-only first screen with student-readable starter cards or chips for learning intents such as `观察什么`, `现象说明什么`, `背后原理`, `为什么这样设计`, `易错点`, and `我自己问`.
- Show a generated starter-question preview before sending when a structured context is available.
- Keep the existing student assistant backend contract and request fields: `context_type`, `context_title`, `context_summary`, optional `chapter_id`, `experiment_id`, `point_key`, and `conversation_history`.
- Improve in-chat feedback by showing compact running, done, error, context, and source states inspired by the teacher chat, but not the teacher diagnostic inspector.
- Use student-compatible markdown/chemistry rendering for assistant answers so chemical notation and structured answers match the rest of the student H5.
- Preserve the existing bottom-tab app shell, assistant feature-switch behavior, student guardrails, source summaries, and contextual handoff from learning or experiment pages.
- No breaking API change is expected.

## Capabilities

### New Capabilities
- `student-h5-assistant-mobile-starter`: Defines the mobile starter flow for the student `问答` tab, including context cards, intent choices, starter preview, first-send behavior, and empty/global states.

### Modified Capabilities
- `student-chat-guardrails`: Extends student assistant presentation requirements so richer starter prompts, chat status, markdown chemistry rendering, source summaries, and dismissible context cues remain student-readable and policy-safe.
- `student-h5-mobile-design-system`: Adds mobile layout requirements for the assistant starter, composer, keyboard-safe input, horizontal prompt overflow prevention, and viewport QA coverage.

## Impact

- Affected student frontend modules:
  - `apps/student-web/src/features/assistant/StudentAiChatTab.tsx`
  - `apps/student-web/src/features/assistant/StudentAiChatPanel.tsx`
  - `apps/student-web/src/features/assistant/assistantContext.ts`
  - `apps/student-web/src/styles/assistant.css`
  - `apps/student-web/src/shared/markdown/AiMarkdownBlock.tsx` or equivalent answer renderer
- Potentially reused existing student APIs:
  - `getStudentLearningHome()`
  - `getStudentExperimentGroup(parentCode)`
  - `getStudentExperimentDetail(experimentId)`
  - `streamStudentAssistantAsk(payload, onEvent)`
- Affected tests and QA:
  - `apps/student-web/src/App.e2e.test.tsx`
  - `apps/student-web/scripts/mobile-viewport-qa.mjs`
  - `npm run typecheck --prefix apps/student-web`
  - `npm run test:e2e --prefix apps/student-web`
  - `npm run build --prefix apps/student-web`
- No admin workflow, teacher diagnostics, backend guardrail policy, or student assistant endpoint schema is expected to change.

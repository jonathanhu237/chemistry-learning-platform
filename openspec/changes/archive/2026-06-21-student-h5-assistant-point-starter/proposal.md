## Why

The student H5 `问答` tab now has a much stronger mobile starter, but its global entry still cannot proactively choose a concrete experiment video point the way the teacher learning assistant can. Students should be able to start from a specific student-visible experiment point and a question template without leaving the mobile assistant, while the already-visible chat turn state makes the separate bottom status bubble redundant.

## What Changes

- Add a phone-first `按实验点位提问` starter path inside the student `问答` tab.
- Let students choose from student-visible experiment groups, concrete experiments/video points, and mobile-friendly question templates before sending.
- Reuse existing student learning and experiment APIs to build `learning_point` assistant context; do not expose teacher/admin experiment workbench data or diagnostics.
- Keep the existing global course starter for broad questions, and let students switch between global starter and point starter before the first chat turn.
- Remove the redundant bottom chat status text below the composer, while preserving per-turn running/done/error feedback inside assistant messages.
- Preserve the current student assistant stream request contract and guardrail ownership.

## Capabilities

### New Capabilities

- `student-h5-assistant-point-starter`: Defines the mobile assistant flow for selecting student-visible experiment groups, video points, and question templates before launching a point-aware assistant question.

### Modified Capabilities

- `student-chat-guardrails`: Removes redundant bottom-level chat status copy while requiring student-readable per-turn status and guardrail-safe point starter copy.
- `student-h5-mobile-design-system`: Adds mobile layout requirements for the point starter selector, nested selection controls, starter preview, composer, and bottom navigation coexistence.

## Impact

- Affected student frontend areas:
  - `apps/student-web/src/features/assistant/StudentAiChatPanel.tsx`
  - `apps/student-web/src/features/assistant/assistantStarter.ts`
  - likely new assistant-local helpers/components for point starter data and context construction
  - `apps/student-web/src/styles/assistant.css`
  - `apps/student-web/src/App.e2e.test.tsx`
  - `apps/student-web/scripts/mobile-viewport-qa.mjs`
- Existing student APIs to reuse:
  - `getStudentLearningHome()`
  - `getStudentExperimentGroup(parentCode)`
  - `getStudentExperimentDetail(experimentId)`
  - `streamStudentAssistantAsk()`
- Backend API contract impact: none expected for the first implementation.
- Guardrail impact: backend classification, RAG grounding, unsafe experiment refusal, and assessment-answer protection remain backend-owned.

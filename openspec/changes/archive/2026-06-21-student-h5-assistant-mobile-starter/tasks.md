## 1. Baseline And Safety

- [x] 1.1 Read current `apps/student-web/src/features/assistant/StudentAiChatTab.tsx`, `StudentAiChatPanel.tsx`, `assistantContext.ts`, and `apps/student-web/src/styles/assistant.css` before editing because the worktree may already contain user changes.
- [x] 1.2 Reconfirm current student assistant context handoff paths from `LearningHomePanel.tsx`, `LearningChapterHeader.tsx`, `ExperimentGroupPanel.tsx`, `ExperimentDetailPanel.tsx`, and `StudentAppShell.tsx`.
- [x] 1.3 Reconfirm teacher-side starter behavior in `apps/admin-web/src/features/learning-assistant/LearningAssistantPage.tsx`, especially intent labels, starter preview, running states, and composer behavior.
- [x] 1.4 Capture the pre-change mobile `问答` screenshot or QA baseline at 390x844, including prompt overflow and composer reachability.

## 2. Starter Model And Context Semantics

- [x] 2.1 Create a student assistant starter intent model near `apps/student-web/src/features/assistant/` with labels, descriptions, and `buildQuestion` helpers.
- [x] 2.2 Support at least observation, phenomenon explanation, principle explanation, mistake review, and custom asking intents for all structured contexts.
- [x] 2.3 Add experiment design and comparison intents when the active context includes experiment or point information.
- [x] 2.4 Build preview text from existing `AssistantContext` fields without changing `StudentAssistantAskRequest`.
- [x] 2.5 Define explicit behavior for clearing context: preserve existing turns with a visible global context switch, or clear turns and restart the starter state.

## 3. Mobile Starter UI

- [x] 3.1 Replace the no-message empty bubble with a phone-first starter surface in the `问答` tab.
- [x] 3.2 Add a merged active context header/card area for global, learning profile, experiment group, experiment detail, and point handoff contexts.
- [x] 3.3 Render starter intent choices as wrapped mobile controls rather than long horizontally clipped first-screen prompt chips.
- [x] 3.4 Add a `准备提问` preview region that updates when the selected starter intent changes.
- [x] 3.5 Add a clear starter launch action that sends the previewed question through `streamStudentAssistantAsk`.
- [x] 3.6 Keep free-form asking available on the starter screen and make typed-input-versus-preview send behavior unambiguous.
- [x] 3.7 Keep follow-up quick prompts compact after the first chat turn.

## 4. Chat Turn Feedback And Rendering

- [x] 4.1 Move running status feedback into or near the active assistant turn with student-readable status text.
- [x] 4.2 Add an assistant skeleton or equivalent placeholder while streaming has started but no answer text has arrived.
- [x] 4.3 Add distinct done and error visual states without exposing admin diagnostics.
- [x] 4.4 Preserve compact source summaries and limit student-visible source chips to concise course-material labels.
- [x] 4.5 Replace or wrap `MarkdownLite` with the shared student markdown renderer so chat answers support GFM, KaTeX, and `mhchem`.
- [x] 4.6 Confirm fallback plain-text streaming still renders safely if richer markdown rendering is unavailable.

## 5. Mobile Layout And Keyboard Behavior

- [x] 5.1 Update `apps/student-web/src/styles/assistant.css` so starter cards, intent controls, preview, chat stream, and composer fit 360px to 430px phone widths.
- [x] 5.2 Prevent first-screen starter controls from causing horizontal page overflow.
- [x] 5.3 Ensure long Chinese labels, context titles, and preview text wrap, clamp, or otherwise stay readable.
- [x] 5.4 Ensure the composer and starter launch action remain reachable above the bottom navigation and mobile safe area.
- [x] 5.5 Ensure the assistant panel uses the available height between the app header and bottom navigation with only necessary breathing room.
- [x] 5.6 Evaluate whether to keep `MobileField` or introduce a mobile textarea-style composer for longer chemistry questions.

## 6. Optional Experiment Starter Data

- [x] 6.1 Decide whether this implementation loads experiment-module summaries inside the global `问答` starter or leaves that path for a later change.
- [x] 6.2 If experiment-module starter data is included, load it through existing `getStudentLearningHome()` and avoid adding a new backend starter-suggestion endpoint.
- [x] 6.3 If experiment group or point choices are included, reuse existing `getStudentExperimentGroup()` and `getStudentExperimentDetail()` only on demand.
- [x] 6.4 Ensure the global starter still works if optional experiment data is loading, unavailable, or fails.

## 7. Tests And Verification

- [x] 7.1 Update `apps/student-web/src/App.e2e.test.tsx` to cover global assistant starter rendering and launch.
- [x] 7.2 Add or update e2e coverage for assistant context handoff from a learning chapter or experiment point.
- [x] 7.3 Add e2e coverage for markdown or chemistry answer rendering in the student assistant chat.
- [x] 7.4 Update `apps/student-web/scripts/mobile-viewport-qa.mjs` to check the assistant starter at 360x780, 390x844, and 430x932.
- [x] 7.5 Ensure mobile viewport QA checks no horizontal overflow, reachable composer, reachable starter launch action, and visible bottom navigation.
- [x] 7.6 Verify assistant-disabled feature configuration still hides, disables, or redirects the `问答` tab according to current app-config behavior.
- [x] 7.7 Run `npm run typecheck --prefix apps/student-web`.
- [x] 7.8 Run `npm run test:e2e --prefix apps/student-web`.
- [x] 7.9 Run `npm run build --prefix apps/student-web`.
- [x] 7.10 Run student mobile viewport QA.
- [x] 7.11 Run `openspec validate student-h5-assistant-mobile-starter --strict`.

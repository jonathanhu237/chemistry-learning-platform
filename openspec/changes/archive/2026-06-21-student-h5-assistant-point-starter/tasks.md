## 1. Baseline And Context Preservation

- [x] 1.1 Re-read `student-h5-assistant-mobile-starter` proposal, design, specs, and completed tasks before implementation.
- [x] 1.2 Re-read current `apps/student-web/src/features/assistant/StudentAiChatPanel.tsx`, `StudentAiChatTab.tsx`, `assistantStarter.ts`, and `assistantContext.ts` before editing because the worktree may contain user changes.
- [x] 1.3 Reconfirm teacher-side starter behavior in `apps/admin-web/src/features/learning-assistant/LearningAssistantPage.tsx`, especially experiment selection, point selection, template labels, preview generation, and launch behavior.
- [x] 1.4 Reconfirm student-visible data contracts in `apps/student-web/src/api.ts` for `getStudentLearningHome`, `getStudentExperimentGroup`, `getStudentExperimentDetail`, and `streamStudentAssistantAsk`.
- [x] 1.5 Reconfirm existing student point context construction in `ExperimentGroupPanel.tsx`, `ExperimentDetailPanel.tsx`, `LearningExperimentsView.tsx`, and `LearningPointGroupView.tsx`.

## 2. Remove Redundant Bottom Status

- [x] 2.1 Remove the bottom `ai-chat-status` render from `StudentAiChatPanel.tsx`.
- [x] 2.2 Remove `assistantStatusLabel` if it no longer has callers.
- [x] 2.3 Remove unused `.ai-chat-status` CSS from `apps/student-web/src/styles/assistant.css`.
- [x] 2.4 Verify per-turn assistant running, done, and error states remain visible after deleting the bottom status copy.
- [x] 2.5 Update tests or QA assertions so they do not expect bottom status text and do verify message-level status instead.

## 3. Point Starter Data Model

- [x] 3.1 Add assistant-local point starter types for mode, group selection, experiment selection, point options, loading state, and errors.
- [x] 3.2 Add helpers to derive stable point options from `StudentExperimentDetailResponse.videos` and `video_candidates`.
- [x] 3.3 Ensure point-option derivation prefers published video point metadata and falls back to deterministic candidate keys.
- [x] 3.4 Add helper to construct `AssistantContext` with `context_type: "learning_point"` from selected group, experiment, detail, and point.
- [x] 3.5 Add point-aware question builders for observation, phenomenon explanation, principle explanation, experiment design, comparison, mistake review, and custom asking.
- [x] 3.6 Ensure helpers do not require backend fields beyond existing `StudentAssistantAskRequest`.

## 4. Point Starter Data Loading

- [x] 4.1 Load experiment groups only when the student enters point starter mode or otherwise explicitly needs point choices.
- [x] 4.2 Default point starter group selection to the recommended parent code when available, otherwise the first visible group.
- [x] 4.3 Load experiments through `getStudentExperimentGroup(parentCode)` after group selection.
- [x] 4.4 Load experiment detail through `getStudentExperimentDetail(experimentId)` after experiment selection.
- [x] 4.5 Reset dependent selections when group or experiment changes so point and template preview do not become stale.
- [x] 4.6 Add compact loading, empty, retry, and error states for each optional point starter data layer.
- [x] 4.7 Ensure global starter and free-form composer remain usable if optional point starter data loading fails.

## 5. Mobile Point Starter UI

- [x] 5.1 Add a phone-first starter mode control for `课程问答` and `实验点位` before the first chat turn.
- [x] 5.2 Keep the existing global course starter as the default mode.
- [x] 5.3 Render student-visible experiment group controls in point mode without horizontal overflow.
- [x] 5.4 Render experiment/video-point controls after a group is selected, with clear selected states.
- [x] 5.5 Render point options after experiment detail loads, distinguishing published-video points from candidate-only points.
- [x] 5.6 Render point template choices as wrapped mobile controls.
- [x] 5.7 Render a point-aware `准备提问` preview that updates when group, experiment, point, or template changes.
- [x] 5.8 Ensure custom asking preserves selected point context but asks the student to type instead of sending an empty generated prompt.
- [x] 5.9 Ensure launch action sends previewed point question and transitions to normal chat.
- [x] 5.10 Ensure typed input send and preview launch remain unambiguous when both typed input and preview text exist.

## 6. Chat Context And Follow-Up Behavior

- [x] 6.1 Send point starter questions through `streamStudentAssistantAsk` with `context_type: "learning_point"`.
- [x] 6.2 Include selected `chapter_id`, `experiment_id`, `point_key`, and `context_summary` in the point starter request.
- [x] 6.3 Preserve existing `conversation_history` behavior for point starter launches and follow-ups.
- [x] 6.4 Ensure the merged context header updates to the selected point context after point starter launch.
- [x] 6.5 Ensure follow-up quick prompts remain relevant to the active point context.
- [x] 6.6 Ensure clearing context returns to `defaultAssistantContext()` and restarts the global starter state.

## 7. Mobile Styling And Accessibility

- [x] 7.1 Update `apps/student-web/src/styles/assistant.css` for point starter mode controls, point lists, template grid, preview, and loading/empty states.
- [x] 7.2 Ensure point starter controls fit 360px, 390px, and 430px phone widths without horizontal page overflow.
- [x] 7.3 Ensure long Chinese group, experiment, point, and preview text wraps or clamps cleanly.
- [x] 7.4 Ensure selected states are visible without hover.
- [x] 7.5 Ensure composer, send button, and starter launch action remain reachable above bottom navigation and mobile safe area.
- [x] 7.6 Ensure point starter scrolling does not trap the composer or create confusing nested scroll behavior.
- [x] 7.7 Ensure controls have accessible labels or readable text for testing-library role queries.

## 8. Tests And QA

- [x] 8.1 Update `apps/student-web/src/App.e2e.test.tsx` mocks for `getStudentLearningHome`, `getStudentExperimentGroup`, and `getStudentExperimentDetail` point starter data.
- [x] 8.2 Add e2e coverage for opening point starter mode from the global `问答` tab.
- [x] 8.3 Add e2e coverage for selecting a group, experiment/point, template, and launching the generated point question.
- [x] 8.4 Assert the point starter stream request includes `context_type: "learning_point"`, `experiment_id`, `point_key`, and selected context summary.
- [x] 8.5 Add e2e coverage that global course starter still launches as before.
- [x] 8.6 Add e2e coverage that the bottom `ai-chat-status` row is not rendered after sending.
- [x] 8.7 Add e2e coverage that per-turn running/done/error state remains visible.
- [x] 8.8 Update `apps/student-web/scripts/mobile-viewport-qa.mjs` mock API routes for point starter data.
- [x] 8.9 Update mobile viewport QA to exercise point starter mode at 360x780, 390x844, and 430x932.
- [x] 8.10 Update mobile viewport QA to assert no horizontal overflow, no composer overlap, no launch-action overlap, and no bottom-navigation overlap.
- [x] 8.11 Verify assistant-disabled feature config still hides or redirects away from `问答`.

## 9. Validation

- [x] 9.1 Run `npm run typecheck --prefix apps/student-web`.
- [x] 9.2 Run `npm run test:e2e --prefix apps/student-web`.
- [x] 9.3 Run `npm run build --prefix apps/student-web`.
- [x] 9.4 Run `STUDENT_H5_QA_MOCK=1 npm run qa:mobile --prefix apps/student-web`.
- [x] 9.5 Run `openspec validate student-h5-assistant-point-starter --strict`.
- [x] 9.6 Summarize implementation choices, verification commands, and any remaining risks.


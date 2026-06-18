## 1. Baseline And Context Lock

- [x] 1.1 Confirm the branch starts from a clean worktree after commit `d0998a1 Add student bottom tab navigation shell`.
- [x] 1.2 Read `openspec/changes/student-h5-bottom-tab-navigation/proposal.md`, `design.md`, and `tasks.md` to preserve the bottom-tab, assistant-tab, profile-feedback, and mobile QA decisions.
- [x] 1.3 Read this change's `proposal.md`, `design.md`, and `specs/student-web-frontend-maintainability/spec.md` before editing application code.
- [x] 1.4 Record current file sizes for `apps/student-web/src/App.tsx`, `styles.css`, `api.ts`, and `mobile/primitives.tsx` as the baseline for measuring modularization.
- [x] 1.5 Run `npm run typecheck --prefix apps/student-web` to confirm the baseline compiles before moving files.
- [x] 1.6 Run `npm run test:e2e --prefix apps/student-web` to confirm the baseline behavior tests pass.
- [x] 1.7 Run `npm run build --prefix apps/student-web` to confirm the baseline production build passes.
- [x] 1.8 Run `STUDENT_H5_QA_MOCK=1 npm run qa:mobile --prefix apps/student-web` against a local student-web dev server to confirm the baseline mobile QA passes.
- [x] 1.9 Use `rg` to confirm authenticated floating AI/feedback controls are not rendered by current student app code except negative QA checks.
- [x] 1.10 Do not change product behavior, backend routes, request payloads, app-config flags, visual design, or test intent during this refactor.

## 2. Module Skeleton And Shared Types

- [x] 2.1 Create the target top-level folders under `apps/student-web/src`: `app`, `features`, `shared`, and `styles` as needed.
- [x] 2.2 Create feature folders for `auth`, `pretest`, `learning`, `periodic-table`, `experiments`, `assistant`, `feedback`, and `assessment`.
- [x] 2.3 Create `apps/student-web/src/app/routes.ts` for `ViewState`, `StudentTab`, `LearningRoute`, `AssessmentRoute`, and `ExperimentTabRoute`.
- [x] 2.4 Create `apps/student-web/src/app/appConfig.ts` for `defaultStudentAppConfig`, `assistantEnabled`, and `feedbackEnabled`.
- [x] 2.5 Move only type aliases and pure config helpers first; do not move JSX in this step.
- [x] 2.6 Update imports in `App.tsx` after the type/config move and ensure there are no circular imports.
- [x] 2.7 Run `npm run typecheck --prefix apps/student-web` after the shared type/config extraction.
- [x] 2.8 Keep `App.tsx` behavior identical after this step; no UI text, class name, or route behavior should change.

## 3. App Shell Extraction

- [x] 3.1 Create `apps/student-web/src/app/StudentAppShell.tsx`.
- [x] 3.2 Move `LearningSurface` app-level tab orchestration into `StudentAppShell` without changing its state shape.
- [x] 3.3 Move `defaultAssistantContext`, `studentTabMeta`, `studentTabItems`, `StudentAppHeader`, and `StudentBottomNav` into app-level modules or a shell component file.
- [x] 3.4 Keep `App.tsx` responsible for session restore, login/password/pretest gates, and mounting `StudentAppShell`.
- [x] 3.5 Preserve app-config polling, disabled assistant redirect, tab switching scroll-to-top behavior, and finish-learning posttest handoff.
- [x] 3.6 Verify `App.tsx` no longer owns bottom-tab rendering details after extraction.
- [x] 3.7 Run `npm run typecheck --prefix apps/student-web`.
- [x] 3.8 Run `npm run test:e2e --prefix apps/student-web`.

## 4. Assistant Feature Extraction

- [x] 4.1 Create `apps/student-web/src/features/assistant/StudentAiChatTab.tsx`.
- [x] 4.2 Create `apps/student-web/src/features/assistant/StudentAiChatPanel.tsx`.
- [x] 4.3 Move `StudentAiChatTab`, `StudentAiChatPanel`, `AssistantSourceSummary`, `normalizeAssistantMetadata`, and assistant status/context helpers into the assistant feature.
- [x] 4.4 Keep markdown rendering behavior identical, including markdown list, strong, divider, and KaTeX behavior.
- [x] 4.5 Keep assistant stream handling identical, including `status`, `delta`, `replace`, `final`, and `error` event handling.
- [x] 4.6 Keep the JSDOM-safe chat scroll fallback introduced during bottom-tab work.
- [x] 4.7 Keep the default `learning_home` context and context handoff reset behavior unchanged.
- [x] 4.8 Update imports so the app shell only imports the assistant feature's public tab component.
- [x] 4.9 Run `npm run typecheck --prefix apps/student-web`.
- [x] 4.10 Run `npm run test:e2e --prefix apps/student-web`.

## 5. Feedback Feature Extraction

- [x] 5.1 Create `apps/student-web/src/features/feedback/StudentFeedbackForm.tsx`.
- [x] 5.2 Create `apps/student-web/src/features/feedback/feedbackTypes.ts` or an equivalent local helper file.
- [x] 5.3 Move `FeedbackContext`, `feedbackTypes`, screenshot validation, attachment clearing, and submit handling into the feedback feature.
- [x] 5.4 Preserve allowed screenshot types: PNG, JPG/JPEG, and WebP.
- [x] 5.5 Preserve the 5 MB attachment size limit and file input reset behavior.
- [x] 5.6 Preserve feedback metadata submission: context title, viewport, user agent, page path, chapter, experiment, point key, and feature-provided metadata.
- [x] 5.7 Keep `ProfileTabPanel` behavior identical when feedback is enabled or disabled.
- [x] 5.8 Run `npm run typecheck --prefix apps/student-web`.
- [x] 5.9 Run `npm run test:e2e --prefix apps/student-web`.

## 6. Assessment Feature Extraction

- [x] 6.1 Create `apps/student-web/src/features/assessment/PosttestPanel.tsx`.
- [x] 6.2 Create `apps/student-web/src/features/assessment/PosttestSummaryPanel.tsx`.
- [x] 6.3 Create `apps/student-web/src/features/assessment/assessmentFormat.ts`.
- [x] 6.4 Move `PosttestPanel`, `PosttestSummaryPanel`, `AssessmentHomePanel`, `answerLabel`, `formatPercent`, `formatScore`, and posttest answer helpers into the assessment feature.
- [x] 6.5 Preserve answer collection for single-choice, true/false, and fill-blank question types.
- [x] 6.6 Preserve posttest submit button enable/disable behavior and loading labels.
- [x] 6.7 Preserve AI summary and AI mistake explanation rendering behavior.
- [x] 6.8 Keep the app shell as the owner of `AssessmentRoute` and posttest start/submit orchestration.
- [x] 6.9 Run `npm run typecheck --prefix apps/student-web`.
- [x] 6.10 Run `npm run test:e2e --prefix apps/student-web`.

## 7. Experiments Feature Extraction

- [x] 7.1 Create `apps/student-web/src/features/experiments/ExperimentsOverviewPanel.tsx`.
- [x] 7.2 Create `apps/student-web/src/features/experiments/ExperimentGroupPanel.tsx`.
- [x] 7.3 Create `apps/student-web/src/features/experiments/ExperimentDetailPanel.tsx`.
- [x] 7.4 Create `apps/student-web/src/features/experiments/experimentFormat.ts` for `stripExperimentPrefix` and related experiment-specific formatting.
- [x] 7.5 Move experiment overview loading/error handling without changing `getStudentLearningHome()` usage.
- [x] 7.6 Move experiment group loading/error handling without changing `getStudentExperimentGroup(parentCode)` usage.
- [x] 7.7 Move experiment detail loading/error handling without changing `getStudentExperimentDetail(experimentId)` or `studentMediaUrl()` behavior.
- [x] 7.8 Preserve assistant context handoff from experiment group and experiment detail pages.
- [x] 7.9 Preserve finish-learning action behavior from experiment group/detail surfaces.
- [x] 7.10 Run `npm run typecheck --prefix apps/student-web`.
- [x] 7.11 Run `npm run test:e2e --prefix apps/student-web`.

## 8. Periodic Table Feature Extraction

- [x] 8.1 Create `apps/student-web/src/features/periodic-table/PeriodicTable.tsx`.
- [x] 8.2 Create `apps/student-web/src/features/periodic-table/PeriodicElementCell.tsx` or equivalent smaller rendering components if useful.
- [x] 8.3 Create `apps/student-web/src/features/periodic-table/periodicHelpers.ts`.
- [x] 8.4 Move `AreaId`, `PeriodicArea`, `periodicAreaIdForElement`, grid column/row helpers, area label maps, integrated-element symbols, and element tile style logic into periodic-table modules.
- [x] 8.5 Keep `apps/student-web/src/periodic.ts` as the stable periodic data source; do not rewrite the generated data blob in this change.
- [x] 8.6 Preserve the six-area teaching model from bottom-tab work: p, s, ds, d, f, and hydrogen/noble gases.
- [x] 8.7 Preserve recommended area cue text and recommended learnable element symbol display.
- [x] 8.8 Preserve no-selection-effect behavior for chapter cards and selected-area behavior for periodic areas.
- [x] 8.9 Run `npm run typecheck --prefix apps/student-web`.
- [x] 8.10 Run `npm run test:e2e --prefix apps/student-web`.

## 9. Learning Feature Extraction

- [x] 9.1 Create `apps/student-web/src/features/learning/LearningEntryPanel.tsx`.
- [x] 9.2 Create `apps/student-web/src/features/learning/LearningHomePanel.tsx`.
- [x] 9.3 Create `apps/student-web/src/features/learning/LearningChapterHeader.tsx`.
- [x] 9.4 Create `apps/student-web/src/features/learning/LearningFactsView.tsx`.
- [x] 9.5 Create `apps/student-web/src/features/learning/LearningExperimentsView.tsx`.
- [x] 9.6 Create `apps/student-web/src/features/learning/LearningElementChips.tsx`.
- [x] 9.7 Create `apps/student-web/src/features/learning/LearningPointGroupView.tsx`.
- [x] 9.8 Create `apps/student-web/src/features/learning/learningFormat.ts`.
- [x] 9.9 Move chapter/profile formatting helpers such as family number labels, nickname parentheses, chapter prefix stripping, and area profile labels into learning or periodic-table helper modules.
- [x] 9.10 Preserve `getStudentLearningPage(profileId)` loading behavior for entry and chapter surfaces.
- [x] 9.11 Preserve selected element initialization, property section selection, facts/experiments view switching, and return-to-entry behavior.
- [x] 9.12 Preserve learning point selection payloads that feed experiment detail route state.
- [x] 9.13 Preserve `LearningProfileTabs` behavior if retained, even if it is currently secondary or hidden by the newer entry flow.
- [x] 9.14 Run `npm run typecheck --prefix apps/student-web`.
- [x] 9.15 Run `npm run test:e2e --prefix apps/student-web`.

## 10. Auth And Pretest Extraction

- [x] 10.1 Create `apps/student-web/src/features/auth/LoginPanel.tsx`.
- [x] 10.2 Create `apps/student-web/src/features/auth/PasswordPanel.tsx`.
- [x] 10.3 Create `apps/student-web/src/features/auth/authUtils.ts` for `normalizeStudentId` and `isStudent`.
- [x] 10.4 Create `apps/student-web/src/features/pretest/AssessmentPanel.tsx`.
- [x] 10.5 Create `apps/student-web/src/features/pretest/PretestErrorPanel.tsx`.
- [x] 10.6 Move pretest answer option helpers into the pretest feature or a shared assessment-question helper if used by posttest.
- [x] 10.7 Preserve login, forced password change, pretest loading, pretest error, and temporary pretest skip barrier behavior.
- [x] 10.8 Keep unauthenticated/onboarding pages outside the authenticated bottom-tab shell.
- [x] 10.9 Run `npm run typecheck --prefix apps/student-web`.
- [x] 10.10 Run `npm run test:e2e --prefix apps/student-web`.

## 11. Shared Markdown, Mobile, And Utility Cleanup

- [x] 11.1 Decide whether `MarkdownLite` remains in the assistant feature or moves to `shared/markdown` based on actual usage after assessment extraction.
- [x] 11.2 Keep `AiMarkdownBlock` wired to the existing lazy `AiMarkdown` component without changing lazy loading behavior.
- [x] 11.3 Move `compactText` and generic small helpers into `shared/utils` only if they have more than one feature consumer.
- [x] 11.4 Review `apps/student-web/src/mobile/primitives.tsx` for unused floating overlay exports.
- [x] 11.5 Use `rg "MobileFloatingOverlay|useFloatingOverlayState|FloatingOverlay"` across the repo before deleting or moving floating overlay primitives.
- [x] 11.6 Remove obsolete floating overlay primitives only if no live imports remain; otherwise move them to a clearly named future overlay/sheet primitive module.
- [x] 11.7 Ensure `MobileButton`, `MobileIconButton`, `MobileField`, `MobileTextArea`, `MobileStatus`, and `MobileEmptyState` remain stable for all feature modules.
- [x] 11.8 Run `npm run typecheck --prefix apps/student-web`.

## 12. CSS Modularization

- [x] 12.1 Create `apps/student-web/src/styles/index.css` or an equivalent single cascade entry file.
- [x] 12.2 Split base/global styles from `styles.css` into `styles/base.css`.
- [x] 12.3 Split authenticated shell and bottom nav styles into `styles/app-shell.css`.
- [x] 12.4 Split login/password/pretest/onboarding styles into `styles/auth.css` and/or `styles/pretest.css`.
- [x] 12.5 Split periodic table and chapter entry selection styles into `styles/periodic-table.css`.
- [x] 12.6 Split learning chapter/facts/experiment-point list styles into `styles/learning.css`.
- [x] 12.7 Split experiment overview/group/detail styles into `styles/experiments.css`.
- [x] 12.8 Split assistant tab/chat styles into `styles/assistant.css`.
- [x] 12.9 Split profile feedback styles into `styles/feedback.css`.
- [x] 12.10 Split posttest/report styles into `styles/assessment.css`.
- [x] 12.11 Preserve current selector names and cascade order unless a rename is necessary to complete the split safely.
- [x] 12.12 Keep `apps/student-web/src/mobile/tokens.css` as shared token input and do not duplicate token values across feature CSS files.
- [x] 12.13 Update `main.tsx` or the CSS entry import to load the new style entry.
- [x] 12.14 Run `npm run build --prefix apps/student-web` to catch CSS syntax/minification issues.
- [x] 12.15 Run mobile viewport QA to catch safe-area, bottom nav, and primary action overlap regressions.

## 13. Optional API Domain Split

- [x] 13.1 Decide whether `api.ts` split is included in this change or deferred; document the decision in final task notes.
- [x] 13.2 If included, create `shared/api/client.ts` for token storage, request helper, error handling, and media URL helper. Deferred for this change.
- [x] 13.3 If included, create domain API files for auth, app config, learning, experiments, assistant, feedback, and assessment. Deferred for this change.
- [x] 13.4 If included, preserve a compatibility barrel so migration can proceed without breaking feature imports mid-refactor. Deferred for this change.
- [x] 13.5 If included, verify `streamStudentAssistantAsk()` event parsing and callback semantics remain stable. Deferred for this change.
- [x] 13.6 If deferred, leave `api.ts` intact except for import path updates required by extracted components.
- [x] 13.7 Run `npm run typecheck --prefix apps/student-web`.
- [x] 13.8 Run `npm run test:e2e --prefix apps/student-web`.

## 14. App Root Shrink Review

- [x] 14.1 Verify `apps/student-web/src/App.tsx` primarily contains app bootstrap, session restore, top-level view gates, and imports of feature/app shell modules.
- [x] 14.2 Verify `App.tsx` no longer contains periodic table rendering, assistant chat implementation, feedback form implementation, posttest report rendering, or experiment detail rendering.
- [x] 14.3 Verify feature modules do not import from `App.tsx`.
- [x] 14.4 Verify feature modules do not create duplicate app-config polling or duplicate bottom-tab state.
- [x] 14.5 Verify imports do not form circular dependencies using TypeScript/build output and manual import review.
- [x] 14.6 Record final file sizes for `App.tsx`, CSS entry files, and major feature modules.

## 15. Test And QA Updates

- [x] 15.1 Update `apps/student-web/src/App.e2e.test.tsx` imports or helper paths only as required by file moves.
- [x] 15.2 Keep e2e coverage for login, pretest fallback, periodic table, bottom tabs, assistant tab, profile feedback, experiment flow, posttest, report, markdown, and feature-disabled config.
- [x] 15.3 Update `apps/student-web/scripts/mobile-viewport-qa.mjs` only for import/path or selector changes caused by modularization.
- [x] 15.4 Preserve QA checks for 360x780, 390x844, and 430x932 viewports.
- [x] 15.5 Preserve QA checks that bottom nav does not overlap chat composer, feedback submit, finish-learning action, and chapter switcher.
- [x] 15.6 Add focused unit tests for extracted pure helpers only if a helper becomes non-trivial or easier to regress outside `App.tsx`.
- [x] 15.7 Avoid tests that assert feature file names or internal folder structure; behavior remains the contract.

## 16. Final Verification

- [x] 16.1 Run `npm run typecheck --prefix apps/student-web`.
- [x] 16.2 Run `npm run test:e2e --prefix apps/student-web`.
- [x] 16.3 Run `npm run build --prefix apps/student-web`.
- [x] 16.4 Run `STUDENT_H5_QA_MOCK=1 npm run qa:mobile --prefix apps/student-web` against a local student-web dev server.
- [x] 16.5 Run `openspec validate student-web-frontend-modularization --strict`.
- [x] 16.6 Run `git diff --check`.
- [x] 16.7 Run `rg "ai-chat-toggle|feedback-toggle|ai-chat-fab|feedback-fab" apps/student-web/src apps/student-web/scripts apps/student-web/src/App.e2e.test.tsx` and confirm any remaining matches are intentional negative QA checks only.
- [x] 16.8 Review final diff by module group: app shell, assistant, feedback, assessment, experiments, periodic table, learning, auth/pretest, shared/mobile, CSS, tests, and OpenSpec.
- [x] 16.9 Confirm no backend files, migrations, package dependencies, or product text/behavior changed unless explicitly documented as refactor-only import fallout.
- [x] 16.10 Update `tasks.md` checkboxes as work is completed during apply.

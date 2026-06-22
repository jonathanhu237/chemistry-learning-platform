## 1. Baseline And Architecture Prep

- [x] 1.1 Confirm `git status --short` is clean or only contains this change before implementation begins.
- [x] 1.2 Read `apps/student-web/src/App.tsx`, `apps/student-web/src/styles.css`, `apps/student-web/src/api.ts`, and current e2e/mobile QA scripts to identify all floating AI, floating feedback, topbar, and route-state references.
- [x] 1.3 Record the final tab model and nested route state in implementation notes or code comments where it helps future maintainers.
- [x] 1.4 Verify no backend API or migration is required before editing server code.

## 2. Authenticated App Shell And Routing

- [x] 2.1 Introduce authenticated student app shell state with app-level tabs: `学习`, `实验`, `问答`, `测评`, and `我的`.
- [x] 2.2 Keep login, password, pretest loading/error, and pretest question surfaces outside the bottom-tab shell.
- [x] 2.3 Move the existing learning entry/chapter/point route state under the `学习` tab without losing chapter, selected element, point, or return behavior.
- [x] 2.4 Route unavailable assistant state back to a safe tab after app-config refresh.
- [x] 2.5 Ensure tab switching does not log out the student and preserves nested learning state where practical.

## 3. Mobile Header And Bottom Navigation UI

- [x] 3.1 Replace the authenticated large brand rail with compact mobile app headers for shell tabs.
- [x] 3.2 Add bottom navigation markup with concise labels and icon buttons using the existing icon library.
- [x] 3.3 Add CSS tokens and layout rules for bottom nav height, safe-area padding, active state, and phone-width label fitting.
- [x] 3.4 Ensure page content reserves bottom spacing so posttest actions, point cards, video controls, chat composer, and feedback submit remain reachable.
- [x] 3.5 Keep `性质通识 / 实验视频` as a chapter-local switcher visually associated with the current chapter.
- [x] 3.6 Prevent scroll states where only the chapter-local switcher remains visible without current chapter context.

## 4. AI Assistant Tab

- [x] 4.1 Split the current `StudentAiChat` into a reusable chat panel/workbench component and remove its authenticated floating toggle wrapper.
- [x] 4.2 Add the `问答` tab using a full-page mobile assistant layout inspired by admin `LearningAssistantPage`, adapted for student density.
- [x] 4.3 Use `learning_home` as the default assistant context when no learning or point context is active.
- [x] 4.4 Support optional chapter/experiment/point context handoff into the assistant tab with a visible dismissible context cue.
- [x] 4.5 Preserve markdown rendering, streaming status, quick prompts, source summaries, and student chat guardrail behavior.
- [x] 4.6 Hide or disable the assistant tab when app config disables either assistant entry or student AI capability.

## 5. Profile Feedback And Account Actions

- [x] 5.1 Split `StudentFeedbackFab` into a reusable `StudentFeedbackForm` or equivalent form component without floating positioning.
- [x] 5.2 Add the `我的` tab with student identity, feedback entry, password/account actions as applicable, and logout.
- [x] 5.3 Move screenshot add/change/remove validation into the profile feedback form.
- [x] 5.4 Submit feedback through the existing authenticated feedback API with screenshot attachment, route metadata when available, viewport, and user-agent metadata.
- [x] 5.5 Hide or disable the profile feedback section when app config disables feedback.
- [x] 5.6 Remove authenticated page feedback floating entry behavior from learning, point, posttest, and summary screens.

## 6. Experiments And Assessment Tabs

- [x] 6.1 Add the `实验` tab as a real experiment or point-resource overview using existing student-visible learning or experiment payloads.
- [x] 6.2 Reuse existing experiment group/detail components where practical and keep back behavior inside the experiments tab.
- [x] 6.3 Add the `测评` tab for current assessment state, post-learning assessment entry, and report access where data exists.
- [x] 6.4 Ensure the existing finish-learning/posttest flow still works from chapter learning content.
- [x] 6.5 Avoid placeholder marketing copy; empty states must state the actual data or action state.

## 7. Cleanup Of Obsolete Floating Entries

- [x] 7.1 Remove authenticated `.ai-chat-toggle` and `.feedback-toggle` rendering paths.
- [x] 7.2 Remove or narrow obsolete floating overlay CSS that no authenticated student page uses after the refactor.
- [x] 7.3 Check z-index and pointer-event layers so dialogs, bottom nav, sticky switchers, and forms do not conflict.
- [x] 7.4 Confirm no page still depends on floating AI or floating feedback controls for a primary action.

## 8. Tests And Mobile QA

- [x] 8.1 Update `apps/student-web/src/App.e2e.test.tsx` for bottom-tab navigation, assistant tab, profile feedback, and preserved learning flow.
- [x] 8.2 Update `apps/student-web/scripts/mobile-viewport-qa.mjs` to check bottom nav instead of floating AI/feedback toggles.
- [x] 8.3 Add or update checks for 360x780, 390x844, and 430x932 viewports.
- [x] 8.4 Verify assistant-disabled and feedback-disabled app-config states hide or disable the expected entries.
- [x] 8.5 Verify chapter switcher remains local and does not overlap bottom nav.

## 9. Final Verification

- [x] 9.1 Run `npm run typecheck --prefix apps/student-web`.
- [x] 9.2 Run `npm run test:e2e --prefix apps/student-web`.
- [x] 9.3 Run `npm run build --prefix apps/student-web`.
- [x] 9.4 Run student mobile viewport QA.
- [x] 9.5 Run `openspec validate student-h5-bottom-tab-navigation --strict`.
- [x] 9.6 Run `git diff --check`.
- [x] 9.7 Review final diff by shell/routing, AI tab, profile feedback, experiments/assessment tabs, CSS, tests, and specs.

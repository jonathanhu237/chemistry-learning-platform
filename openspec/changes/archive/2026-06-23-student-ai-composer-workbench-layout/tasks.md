## 1. Composer State Model

- [x] 1.1 Audit current root and contextual `StudentAiChatPanel` composer rendering, textarea measurement, keyboard-active behavior, and submit/reset flows.
- [x] 1.2 Define derived composer modes for compact empty, compact one-line typing, expanded multi-line typing, expanded scroll, and loading without adding persisted UI state where derived metrics are sufficient.
- [x] 1.3 Update textarea measurement so the one-line threshold controls compact versus expanded mode and the existing `61.8%` growth cap applies only to the input zone.
- [x] 1.4 Ensure composer metrics recalculate on input changes, visual viewport changes, restored history, reset/new chat, and loading completion.

## 2. Composer Markup and Semantics

- [x] 2.1 Refactor the root composer markup into an input zone and a bottom workbench zone while preserving the form submit path.
- [x] 2.2 Add a left-side `+` workbench action with accessible labeling for injecting learning/background context.
- [x] 2.3 Keep the send action in the workbench and preserve disabled/loading behavior.
- [x] 2.4 Prevent unsupported upload, attachment, microphone, model picker, voice waveform, image-generation, or external-service controls from appearing in the workbench.
- [x] 2.5 Preserve root-only history/new-chat behavior and contextual `/ai/chat` route separation.

## 3. Workbench Layout Styling

- [x] 3.1 Implement compact race-track styling for empty and one-line root composer states.
- [x] 3.2 Implement expanded rounded-rectangle styling with upper textarea zone and lower fixed workbench zone for multi-line input.
- [x] 3.3 Anchor the `+` action at the left side and send action at the right side so their visual positions remain stable across compact, expanded, scrollable, keyboard-active, and loading states.
- [x] 3.4 Keep typed content from overlapping or occupying the workbench zone, including during internal textarea scrolling.
- [x] 3.5 Preserve the existing root composer side margins, bottom breathing gap, keyboard-active behavior, and bottom-navigation collision rules.
- [x] 3.6 Keep generated follow-up prompt chips outside the composer workbench.

## 4. Background Knowledge Action Behavior

- [x] 4.1 Decide the first implementation behavior for `+`: expose available context state, inject current page/video-point context, or open a minimal context sheet.
- [x] 4.2 Implement the selected behavior using existing `AssistantContext` data without adding upload or attachment APIs.
- [x] 4.3 Handle no-context cases by keeping free-form chat usable and avoiding blocking sends.
- [x] 4.4 Add accessible status/copy that makes the `+` action read as learning background context rather than file attachment.

## 5. Regression Coverage

- [x] 5.1 Add student-web tests that compact empty and one-line input states retain the race-track composer and stable workbench controls.
- [x] 5.2 Add tests that multi-line input enters expanded mode with textarea above the workbench and controls remaining fixed.
- [x] 5.3 Add tests that long input clamps the textarea/input zone, enables internal scrolling, and leaves the workbench visible.
- [x] 5.4 Add keyboard-active tests that bottom navigation hides, the breathing gap remains, and workbench controls stay above the keyboard.
- [x] 5.5 Add route separation tests proving contextual `/ai/chat` does not gain root-only history/new-chat affordances through the workbench refactor.
- [x] 5.6 Add assertions that unsupported controls are still absent from the composer workbench.

## 6. Validation

- [x] 6.1 Run focused student-web tests for Atom root composer and route separation.
- [x] 6.2 Run `npm run typecheck` in `apps/web-student`.
- [x] 6.3 Run `npm run build` in `apps/web-student`.
- [x] 6.4 Run `npx openspec validate student-ai-composer-workbench-layout --strict --no-interactive`.
- [x] 6.5 If deployed to the running local container, refresh the student dist and verify `/ai` on a phone or phone preview for compact, expanded, scrollable, and keyboard-active states.

## 7. Visual Calibration Follow-Up

- [x] 7.1 Update the spec/design artifacts so compact text centering and composer-level `61.8%` growth budgeting are explicit.
- [x] 7.2 Slim the compact race-track height while keeping the `+`, text lane, and send action vertically aligned.
- [x] 7.3 Increase and unify root composer textarea font sizing across compact, expanded, and scrollable states.
- [x] 7.4 Rework root composer height measurement so `61.8%` caps the whole composer surface, not only the textarea.
- [x] 7.5 Update tests and validation for compact centering, unified text size, and composer-level height cap.

## 8. Compact Boundary Stabilization

- [x] 8.1 Update the spec/design artifacts so compact-lane width owns the compact-to-expanded threshold.
- [x] 8.2 Add canonical compact-lane measurement for the root composer expansion decision.
- [x] 8.3 Add regression coverage for boundary-length one-line input that must not oscillate between compact and expanded states.
- [x] 8.4 Run focused student-web tests, build, and OpenSpec validation.
- [x] 8.5 Refresh the running student container after validation.

## 9. Chat Body Typography Calibration

- [x] 9.1 Update the spec/design artifacts so root textarea, message body, and Markdown paragraph/list body share one typography role.
- [x] 9.2 Add a shared chat body typography token using the existing mobile large text scale.
- [x] 9.3 Apply the token to root composer textarea, message bubble body, and Markdown paragraph/list body without changing title/status/badge hierarchy.
- [x] 9.4 Update regression/source coverage for the shared body typography.
- [x] 9.5 Run focused student-web tests, build, and OpenSpec validation.
- [x] 9.6 Refresh the running student container after validation.

## 10. Compact Measurement Row Baseline

- [x] 10.1 Update spec/design artifacts so the hidden compact measurement textarea must mirror the visible compact input's one-row baseline.
- [x] 10.2 Force the hidden compact measurement textarea to use `rows=1` in markup and measurement code.
- [x] 10.3 Add regression coverage that a single-character root composer input remains compact.
- [x] 10.4 Run focused student-web tests, build, and OpenSpec validation.
- [x] 10.5 Refresh the running student container after validation.

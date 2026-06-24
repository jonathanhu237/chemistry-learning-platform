## Why

The root Atom composer currently behaves like a single textarea with an overlaid send button, so multi-line input competes with the same space that should anchor chat actions. The next composer refinement needs a stable workbench area for supported chat capabilities while preserving the successful Grok/Gemini-like mobile rhythm already established.

## What Changes

- Restructure the student Atom root composer into two conceptual zones: a text-entry zone and a fixed bottom workbench zone.
- Preserve the compact single-line "race track" composer state for empty and one-line input.
- When input exceeds one line, transition the composer into a rounded-rectangle expanded state where the textarea occupies the upper zone and the workbench occupies the lower zone.
- Measure the compact-to-expanded threshold against the compact race-track text lane width, not the currently rendered textarea width, so one-line boundary text cannot oscillate between states.
- Ensure the hidden compact threshold measurement mirrors the visible compact textarea's one-row configuration, so a single typed character cannot be misclassified as multi-line input.
- Keep the workbench controls visually anchored regardless of composer height, keyboard state, loading state, or textarea scroll state.
- Calibrate compact composer height and text baseline so the one-line input reads as a slightly slimmer race-track with text visually centered beside the `+` action.
- Unify the chat body reading/writing typography across the root textarea, message body, and Markdown paragraph/list content while leaving titles, status labels, badges, and metadata on their own smaller hierarchy.
- Treat the `61.8%` growth budget as an outer composer-height cap, not as a textarea-only cap; the textarea receives the remaining height after workbench row and composer padding are reserved.
- Introduce a supported left-side `+` workbench action for injecting available course/background knowledge, such as the current video point or page context, into the chat turn.
- Keep the right-side send action inside the workbench and never allow typed text to overlap, push, or resize it.
- Preserve existing root/detail route separation, Atom welcome behavior, keyboard-aware layout, history/new-chat actions, local history, and streaming behavior.
- Do not add unsupported controls such as upload, attachment, model picker, microphone, waveform voice input, or image generation.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `student-h5-ai-assistant`: Define the root Atom composer workbench states, `+` background-knowledge action semantics, and control anchoring invariants.
- `student-h5-mobile-design-system`: Define mobile ergonomic layout rules for the compact-to-expanded composer transition and fixed workbench zone.

## Impact

- `apps/web-student/src/features/assistant/StudentAiChatPanel.tsx`: likely splits the root composer markup into input and workbench zones while preserving detail-route behavior.
- `apps/web-student/src/styles/assistant.css`: likely updates root composer layout, shape transition, control positioning, textarea sizing, and scroll behavior.
- `apps/web-student/src/mobile/primitives.tsx`: may remain unchanged unless reusable action primitives are needed.
- `apps/web-student/src/App.e2e.test.tsx` and `apps/web-student/src/roleBoundaries.test.ts`: add coverage for compact/expanded/scroll states and invariant button positions.
- OpenSpec specs for `student-h5-ai-assistant` and `student-h5-mobile-design-system` gain composer workbench requirements.

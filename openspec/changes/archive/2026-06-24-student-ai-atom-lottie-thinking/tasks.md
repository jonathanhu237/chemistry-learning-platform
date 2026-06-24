## 1. Dependency and Asset Setup

- [x] 1.1 Confirm the provided `Atom.json` Lottie asset is licensed for bundled student-web production use, or choose an approved replacement asset before committing it.
- [x] 1.2 Add the selected React Lottie runtime dependency to `apps/web-student/package.json` and update the lockfile.
- [x] 1.3 Add the local Atom thinking animation JSON under `apps/web-student/src/assets/lottie/`.
- [x] 1.4 Recolor the committed animation asset from black stroke values to the student service main green `#005826`.
- [x] 1.5 Verify the committed Lottie JSON has no external image, font, video, or remote URL assets.

## 2. Assistant Thinking Mark Implementation

- [x] 2.1 Add an `AtomThinkingMark` or equivalent small component for rendering the local Lottie animation as a decorative inline mark.
- [x] 2.2 Add reduced-motion detection or equivalent runtime handling so the Atom mark is static, non-looping, or replaced with a static Atom mark when reduced motion is requested.
- [x] 2.3 Replace the root `AssistantThinkingLine` three-dot markup with the Atom thinking mark while preserving the existing phase-label state machine.
- [x] 2.4 Keep the Atom animation `aria-hidden` and preserve the outer thinking line's polite status announcement using the current phase label.
- [x] 2.5 Ensure the Atom mark is removed after success or failure and never persists inside completed assistant replies.

## 3. Styling and Layout

- [x] 3.1 Replace root `.ai-thinking-dots` styling with `.ai-thinking-atom-mark` styling sized for a stable inline footprint.
- [x] 3.2 Tune the Atom mark's width, height, alignment, and gap so it remains secondary to the phase label on 360px, 390px, and 430px phone widths.
- [x] 3.3 Preserve the flat root thinking line treatment with no pill, badge, border, skeleton block, card surface, or loading panel.
- [x] 3.4 Update reduced-motion CSS and remove or deprecate root dot-specific keyframes that are no longer used.

## 4. Tests and Quality Checks

- [x] 4.1 Update student-web tests that assert `.ai-thinking-dots` to assert `.ai-thinking-atom-mark`, decorative `aria-hidden`, and preserved status text behavior.
- [x] 4.2 Update role-boundary or CSS contract tests that currently require dot-specific CSS or `@keyframes ai-thinking-dot`.
- [x] 4.3 Add or update a focused test for reduced-motion behavior so the phase label remains meaningful without repeated Atom animation.
- [x] 4.4 Verify successful completion removes the Atom thinking mark and leaves only the established flat markdown answer and action row.
- [x] 4.5 Verify contextual `/ai/chat` running-state behavior remains distinct from the root Atom assistant change.

## 5. Validation

- [x] 5.1 Run focused student-web tests covering the root assistant thinking line.
- [x] 5.2 Run `npm run typecheck --prefix apps/web-student`.
- [x] 5.3 Run the relevant student mobile viewport QA or focused Playwright/Vitest check for common phone widths.
- [x] 5.4 Run `openspec validate student-ai-atom-lottie-thinking --strict`.

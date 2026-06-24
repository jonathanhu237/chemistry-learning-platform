## 1. Research And Existing State

- [x] 1.1 Record external chat UI findings and target constraints in the design notes.
- [x] 1.2 Re-read the current AI root/detail components and assistant styles before editing.

## 2. Fullscreen Root AI Canvas

- [x] 2.1 Remove the root AI card/panel visual framing so `/ai` reads as a fullscreen chat canvas.
- [x] 2.2 Reposition root identity and history action to match the target Grok-like top rhythm.
- [x] 2.3 Move the empty-state prompt block low near the composer and keep the middle canvas visually calm.
- [x] 2.4 Keep only supported text input and send controls in the root composer.
- [x] 2.5 Ensure local history restore and streaming behavior still work after the visual refactor.

## 3. Detail Variant Separation

- [x] 3.1 Keep `/ai/chat` visually scoped to the detail variant with pagebar/back behavior.
- [x] 3.2 Ensure root-only history chrome does not render in `/ai/chat`.
- [x] 3.3 Ensure contextual handoff routes still open `/ai/chat` rather than changing root tab identity.

## 4. Mobile Layout And Styles

- [x] 4.1 Tune root canvas width, height, and safe-area spacing at 360px, 390px, and 430px phone widths.
- [x] 4.2 Ensure the root composer sits above bottom navigation without overlap.
- [x] 4.3 Remove or neutralize styles that make the root assistant look like nested cards.
- [x] 4.4 Check document width against viewport width to prevent horizontal overflow.

## 5. Tests And Verification

- [x] 5.1 Update student e2e tests for fullscreen root canvas, low prompt, composer, and unsupported-control absence.
- [x] 5.2 Update student e2e tests for detail route separation and root-history omission.
- [x] 5.3 Run focused student frontend tests and typecheck.
- [x] 5.4 Run OpenSpec strict validation.
- [x] 5.5 Start or reuse local student dev server and perform mobile viewport verification for `/ai` and `/ai/chat`.

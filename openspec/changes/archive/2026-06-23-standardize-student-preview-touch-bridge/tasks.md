## 1. Scope And Baseline Audit

- [x] 1.1 Confirm all current `@use-gesture/react` imports and dependency entries are limited to the teacher student-preview input bridge.
- [x] 1.2 Confirm current teacher/student preview protocol modules have matching event type definitions before changing either side.
- [x] 1.3 Identify existing focused tests for `PreviewGestureSurface`, `PreviewInputRuntime`, and preview input protocol parsing.
- [x] 1.4 Record the existing manual QA routes needed for popover dismissal, horizontal element rails, vertical scroll, and ordinary tap activation.

## 2. Protocol Contract

- [x] 2.1 Replace student-facing conclusion event types with lifecycle event types in both preview input protocol modules.
- [x] 2.2 Remove teacher-originated `tap` and `longPress` from the active student-facing protocol or guard them behind a rejected legacy version.
- [x] 2.3 Add or verify protocol version handling so mismatched teacher/student bundles reject stale messages safely.
- [x] 2.4 Add protocol tests for accepted lifecycle messages and rejected malformed, stale-version, stale-frame, and unexpected-origin messages.

## 3. Teacher Pointer State Machine

- [x] 3.1 Replace the `@use-gesture/react` binding in `PreviewGestureSurface` with native Pointer Events handlers.
- [x] 3.2 Implement one active sequence owner that handles primary-button `pointerdown`, ordered pressed `pointermove`, `pointerup`, `pointercancel`, `lostpointercapture`, disablement, iframe reload, and unmount.
- [x] 3.3 Preserve coordinate mapping for zoomed, rotated, and scaled phone shells using viewport-relative CSS pixels.
- [x] 3.4 Preserve requestAnimationFrame-driven touch indicator updates without React state updates per pointer move.
- [x] 3.5 Prevent desktop text selection and browser drag artifacts only inside the active phone-screen input surface.
- [x] 3.6 Add teacher-side tests for lifecycle ordering, sequence id stability, coordinate mapping, pointer capture cancellation, and no teacher-side tap/long-press conclusion messages.

## 4. Student Runtime State Machine

- [x] 4.1 Rewrite `PreviewInputRuntime` around an explicit sequence state record with start point, last point, start timestamp, phase, target references, accumulated movement, axis lock, scroll owner, and pointerdown cancellation state.
- [x] 4.2 Dispatch standards-aligned synthetic `PointerEvent` objects with `pointerType: "touch"` for `pointerdown`, `pointermove`, `pointerup`, and `pointercancel`.
- [x] 4.3 Add optional synthetic `TouchEvent` dispatch only if target desktop browsers can construct valid events in tests; otherwise document Pointer Events as the required baseline.
- [x] 4.4 Classify short taps only on `touchEnd` using centralized tap duration and movement thresholds.
- [x] 4.5 Classify drag after movement crosses the drag threshold and ensure drag release never triggers click activation.
- [x] 4.6 Classify long-press-ready state after the long-press threshold when movement remains below threshold and ensure release does not fall through to normal tap activation.
- [x] 4.7 Ensure `touchCancel`, stale sequence ids, rejected origins, unload, and runtime unmount dispatch cancel/clear state without click activation.
- [x] 4.8 Keep ordinary student sessions from registering or applying preview input messages.

## 5. Scroll And Activation Semantics

- [x] 5.1 Keep tap activation on real DOM elements through focus and click semantics after `pointerup`.
- [x] 5.2 Preserve editable element focus without introducing a preview-only editor.
- [x] 5.3 Lock horizontal scroll owners after horizontal drag intent so rails keep sliding even when the pointer leaves the rail bounds.
- [x] 5.4 Preserve vertical phone-scroll direction for page and nested scroll containers.
- [x] 5.5 Keep scroll boundary promotion and clamping inside the centralized preview scroll helper with no page-local special cases.
- [x] 5.6 Verify popover outside-press dismissal works through the lifecycle state machine without click-through activation.

## 6. Dependency And Boundary Cleanup

- [x] 6.1 Remove `@use-gesture/react` from `web-teacher` dependencies and lockfiles after no imports remain.
- [x] 6.2 Run source-boundary checks or focused searches proving `web-teacher` preview input code does not import `web-student` route/page/business modules.
- [x] 6.3 Run focused searches proving ordinary `web-student` route and feature modules do not contain raw preview touch-emulation branches.
- [x] 6.4 Keep implementation changes inside preview input surface/protocol/runtime modules, tests, and dependency metadata unless a task explicitly justifies otherwise.

## 7. Verification

- [x] 7.1 Run focused `web-teacher` tests for the preview input surface and protocol.
- [x] 7.2 Run focused `web-student` tests for the preview input runtime and scroll helper behavior.
- [x] 7.3 Run relevant frontend typecheck/build validation for changed packages.
- [x] 7.4 Start the local teacher/student preview environment and verify the iframe loads the student app.
- [x] 7.5 Browser-QA short tap: tap navigation/buttons/cards inside student preview and verify exactly one activation.
- [x] 7.6 Browser-QA outside tap: open the learning-area bubble/popover and verify pressing outside dismisses it like a phone with no unintended click-through.
- [x] 7.7 Browser-QA vertical drag: drag upward/downward on scrollable pages and verify phone-like scroll direction and no text selection.
- [x] 7.8 Browser-QA horizontal drag: drag element rails left/right in student preview and verify they continue sliding until release.
- [x] 7.9 Browser-QA long press/cancel: hold without movement, move after hold, cancel by leaving/reloading, and verify no stale indicator or accidental click remains.
- [x] 7.10 Document any unavailable validation command with the concrete blocker before marking the change complete.

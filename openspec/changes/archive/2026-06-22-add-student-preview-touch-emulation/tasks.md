## 1. Boundary Audit and Current Cursor Cleanup

- [x] 1.1 Audit current teacher student preview files and identify the exact phone screen container that should own pointer capture.
- [x] 1.2 Audit current student preview cursor implementation and document the files to remove, replace, or disable.
- [x] 1.3 Confirm no existing student route or feature module needs page-local touch-emulation logic before implementation starts.
- [x] 1.4 Add or update source-boundary allowlists so new touch-emulation code is allowed only in teacher preview input modules and student preview runtime modules.
- [x] 1.5 Add `@use-gesture/react` to `web-teacher` only and confirm it is not installed or imported as a student-business dependency.

## 2. Teacher-Side Gesture Surface and Input Protocol

- [x] 2.1 Create a feature-local teacher preview input module under the student preview feature owner.
- [x] 2.2 Define the versioned preview input message TypeScript contract with namespace, version, frame/session identity, sequence id, event type, timestamp, and viewport point.
- [x] 2.3 Implement `@use-gesture/react` bindings for tap, drag start, drag move, drag end, cancel, press state, and long-press-ready intent.
- [x] 2.4 Configure tap-vs-drag movement thresholds and press timing thresholds in the teacher preview input module.
- [x] 2.5 Implement iframe viewport coordinate mapping that accounts for phone screen rectangle, preview zoom, device preset, and orientation.
- [x] 2.6 Implement iframe lifecycle cleanup so active sequences cancel on refresh, reload, session replacement, or preview unmount.

## 3. Teacher-Side Screen Surface and Selection Control

- [x] 3.1 Add a transparent phone-screen input surface above the iframe while keeping teacher toolbar/sidebar controls outside the surface.
- [x] 3.2 Apply `touch-action: none`, active-gesture `preventDefault`, and scoped `user-select` suppression only to the phone screen input surface.
- [x] 3.3 Ensure `@use-gesture/react` receives non-passive events where needed so drag gestures can prevent desktop selection.
- [x] 3.4 Ensure pointer events outside the phone screen do not start simulated student input.
- [x] 3.5 Ensure the overlay still allows simulated tap activation inside the iframe through the input protocol.

## 4. Teacher-Side Touch Indicator Performance

- [x] 4.1 Move the DevTools-like touch indicator ownership to the teacher preview input surface.
- [x] 4.2 Implement indicator movement with refs, one pending `requestAnimationFrame`, and direct `translate3d` style updates.
- [x] 4.3 Remove per-pointer-move React state updates from the touch indicator path.
- [x] 4.4 Remove transform transitions that cause pointer lag; keep only safe opacity or pressed-state transitions.
- [x] 4.5 Hide the native cursor inside the phone screen only while the touch indicator is active.
- [x] 4.6 Hide or reset the indicator on pointer leave, idle timeout, sequence end, sequence cancel, iframe reload, and preview teardown.

## 5. Student-Side Preview Input Runtime

- [x] 5.1 Create a student preview input runtime module under the existing preview/runtime ownership boundary.
- [x] 5.2 Register the runtime only when the active session is teacher student-preview mode.
- [x] 5.3 Validate message namespace, version, origin, frame/session identity, sequence id, event type, and coordinate sanity before applying input.
- [x] 5.4 Clear active sequence state on invalid messages, unload, runtime unmount, preview session exit, and cancel messages.
- [x] 5.5 Keep normal student sessions free of preview input listeners and behavior.

## 6. Student Runtime Tap and Focus Behavior

- [x] 6.1 Implement viewport-coordinate hit testing with `document.elementFromPoint`.
- [x] 6.2 Record the initial sequence target on simulated touch start.
- [x] 6.3 Implement tap activation that prefers the initial target when still connected and actionable.
- [x] 6.4 Implement focus behavior for input, textarea, select, and contenteditable targets without adding preview-only editors.
- [x] 6.5 Implement safe re-hit-test or cancel behavior when the original tap target disappears before release.
- [x] 6.6 Add compatibility click handling through the real DOM element without importing teacher code or student route internals.

## 7. Student Runtime Drag Scroll Behavior

- [x] 7.1 Implement a centralized scrollable ancestor helper based on computed overflow and scroll dimensions.
- [x] 7.2 Implement vertical drag scrolling with `scrollTop += previousY - currentY`.
- [x] 7.3 Support document-level scrolling when no inner scrollable ancestor can scroll.
- [x] 7.4 Clamp scroll positions to valid ranges at container boundaries.
- [x] 7.5 Allow ancestor fallback only through the centralized scroll helper, not through page-specific selectors.
- [x] 7.6 Verify the runtime does not add preview-only bottom-navigation hiding, opacity, position, or route behavior.
- [x] 7.7 Specify that real student bottom-navigation visibility is a scroll-direction state machine owned by the student shell.

## 8. Automated Tests

- [x] 8.1 Add teacher-side unit tests for `@use-gesture/react` binding output, tap threshold, drag threshold, press/long-press-ready behavior, cancel cleanup, and sequence ids.
- [x] 8.2 Add teacher-side unit tests for coordinate mapping across zoom, device preset, and orientation changes.
- [x] 8.3 Add teacher-side unit tests for message construction and target-origin handling.
- [x] 8.4 Add student-side unit tests for origin/session rejection and malformed message handling.
- [x] 8.5 Add student-side unit tests for tap activation, editable focus, disconnected target safety, and no-op behavior in normal sessions.
- [x] 8.6 Add student-side unit tests for scrollable ancestor selection, drag-up direction, drag-down direction, document fallback, and boundary clamping.
- [x] 8.7 Add source-boundary tests that reject `web-teacher` imports from `web-student` and raw touch-emulation logic in ordinary student feature modules.

## 9. Browser QA and Visual Verification

- [x] 9.1 Run browser QA on the teacher student preview page and confirm press-and-drag upward scrolls the framed real student app.
- [x] 9.2 Run browser QA on the teacher student preview page and confirm press-and-drag downward scrolls the framed real student app.
- [x] 9.3 Confirm simulated dragging does not create selected text in the teacher page or framed student page.
- [x] 9.4 Confirm tapping bottom navigation, learning cards, feedback entry, and profile controls activates the real student UI.
- [x] 9.5 Confirm the bottom navigation behavior remains owned by the real student app and is not changed by preview-specific CSS or logic.
- [x] 9.6 Confirm the touch indicator stays aligned with the pointer at supported zoom levels and device orientations.
- [x] 9.7 Confirm no stale touch indicator remains after pointer cancel, pointer leave, iframe refresh, route reload, or preview session regeneration.
- [x] 9.8 Confirm the real student bottom navigation slides fully offscreen on downward root-route scroll, stays hidden while idle, and slides back only on upward scroll, top reset, or root-route change.

## 10. Validation and Documentation

- [x] 10.1 Run focused `web-teacher` tests for student preview input modules.
- [x] 10.2 Run focused `web-student` tests for preview input runtime modules.
- [x] 10.3 Run `npm run typecheck` for affected frontend apps.
- [x] 10.4 Run existing preview boundary tests and import-boundary validation.
- [x] 10.5 Run `openspec validate add-student-preview-touch-emulation --strict`.
- [x] 10.6 Run `git diff --check` and fix whitespace issues before implementation is considered complete.
- [x] 10.7 Document any remaining limitation, such as keyboard text input or inertial scrolling, as a follow-up rather than page-local workaround.
- [x] 10.8 Add a source/contract test that rejects the old idle-timeout reveal and partially visible compressed bottom-nav state.

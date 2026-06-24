## Context

The teacher student-preview embeds the real `web-student` app in an iframe and overlays a teacher-owned input surface above the phone screen. The current input surface uses `@use-gesture/react` plus raw React pointer capture handlers. It emits both low-level phases (`touchStart`, `touchMove`, `touchEnd`, `touchCancel`) and conclusion events (`tap`, `longPress`). The student runtime then converts those messages into partial synthetic DOM behavior.

That split is the root mismatch with real mobile input. On phones, the browser observes a continuous lifecycle: contact starts, contact moves zero or more times, contact ends or is canceled, and only then does the platform/component stack classify the sequence as activation, drag/scroll, long press, or cancel. MDN and W3C Pointer Events describe the same lifecycle through `pointerdown`, `pointermove`, `pointerup`, and `pointercancel`; Touch Events describe it through `touchstart`, `touchmove`, `touchend`, and `touchcancel`.

The preview must behave like a phone for interaction debugging, but it must not become a browser debugging subsystem. `web-teacher` cannot safely inspect or mutate the framed DOM directly; all real interaction outcomes must remain owned by `web-student`.

## Goals / Non-Goals

**Goals:**

- Remove `@use-gesture/react` from the teacher student-preview input bridge.
- Use a single self-owned teacher-side Pointer Events state machine to transport pointer-derived touch lifecycle phases.
- Make `web-student` the authoritative classifier for short tap, drag/scroll, long press, and cancel.
- Preserve phone-like semantics:
  - quick press and release with minimal movement activates once;
  - movement beyond the drag threshold scrolls/drags and suppresses click;
  - long press is explicitly modeled and does not accidentally fall through to tap;
  - cancel/lost-capture terminates without activation.
- Keep all emulation behavior inside the preview input surface, protocol, and preview runtime. Ordinary student pages and teacher feature modules must remain untouched.
- Add tests that exercise the event sequence rather than only the final UI outcome.

**Non-Goals:**

- Do not implement a full remote browser, Chrome DevTools Protocol bridge, user-agent emulation, network throttling, or arbitrary DOM inspector.
- Do not duplicate student page logic in `web-teacher`.
- Do not add page-local workarounds to student feature components for this preview mode.
- Do not attempt to emulate the mobile virtual keyboard perfectly; editable focus should use the real DOM element, but desktop browser keyboard behavior remains outside this change.
- Do not change production student behavior outside teacher-preview sessions.

## Decisions

### 1. Use native Pointer Events on the teacher input surface

The teacher overlay will use `pointerenter`, `pointermove`, `pointerdown`, `pointerup`, `pointercancel`, and `lostpointercapture` directly. On primary-button `pointerdown`, it creates one active sequence, captures the pointer, prevents desktop text selection/drag artifacts inside the surface, and sends `touchStart`. While pressed, every valid move sends `touchMove`. `pointerup` sends `touchEnd`; cancel/lost-capture/teardown sends `touchCancel`.

Alternative considered: keep `@use-gesture/react` and tune thresholds. That preserves a library dependency that is optimized for consuming gestures inside the same React tree, but this bridge needs the unclassified lifecycle for another browsing context. Keeping both raw pointer handlers and the library also leaves two owners for the same terminal state.

### 2. Protocol messages represent lifecycle phases, not conclusions

The input protocol will stop using teacher-originated `tap` and `longPress` as action conclusions. A sequence message should carry:

- namespace and protocol version;
- frame/session identity;
- sequence id;
- lifecycle type: `hover`, `touchStart`, `touchMove`, `touchEnd`, or `touchCancel`;
- current point in framed viewport CSS pixels;
- previous point where applicable;
- started timestamp and event timestamp;
- primary-button/pressed state and modifier keys.

`hover` remains teacher-only feedback for the visual indicator and must not trigger student DOM behavior. If the protocol shape changes incompatibly, bump the version and make both sides reject stale versions safely.

Alternative considered: send higher-level `tap`, `drag`, and `longPress` intents from teacher. That is easier to wire but repeats the current flaw: the iframe never receives a standards-like press/move/release stream and cannot make mobile-equivalent decisions from real target state.

### 3. Student runtime owns mobile classification

The student preview runtime will keep a per-sequence state record:

- sequence id;
- start point, last point, accumulated movement, and start timestamp;
- initial hit-test target and active press target;
- current phase: `idle`, `pressing`, `dragging`, `longPressReady`, `ended`, or `canceled`;
- scroll target and axis lock after drag intent is established;
- whether a synthetic `pointerdown` was canceled by the target.

On `touchStart`, it hit-tests `document.elementFromPoint`, dispatches a synthetic `PointerEvent("pointerdown", { pointerType: "touch", isPrimary: true })` to the target, and records whether the event was canceled. Where the runtime can construct standards-compliant `TouchEvent` objects safely, it may also dispatch matching `touchstart`/`touchmove`/`touchend`/`touchcancel` events; Pointer Events remain the required baseline.

On `touchMove`, it dispatches `pointermove`, updates movement, classifies drag after the movement threshold, clears long-press eligibility after drag intent, and applies scroll through the centralized scroll helper.

On `touchEnd`, it dispatches `pointerup`, computes duration and movement, then activates only if the sequence is still tap-eligible. A tap-eligible sequence has small movement, duration below the tap limit, no long-press state, and no canceled `pointerdown`.

On `touchCancel`, it dispatches `pointercancel`, clears state, and never activates.

Suggested centralized defaults:

- tap movement threshold: 8 CSS px;
- drag movement threshold: 8 CSS px;
- tap maximum duration: 300 ms;
- long-press delay: 500-520 ms.

The exact constants may be adjusted during implementation, but they must live in one preview input runtime module and be covered by tests.

### 4. Scroll uses locked target and axis semantics

After movement crosses the drag threshold, the runtime should choose the scroll owner from the initial target path and the current hit target, prefer the nearest scrollable ancestor that can move in the intended direction, and lock that target/axis for the rest of the sequence unless it reaches a boundary and the centralized helper intentionally promotes to an ancestor.

Horizontal rails must keep receiving horizontal scroll deltas even if the pointer leaves the rail visually during the drag. Vertical page scroll must continue to behave like a finger swipe: dragging upward increases scroll position; dragging downward decreases it.

Alternative considered: re-hit-test every move and scroll whichever element is currently under the pointer. That is why horizontal carousel-like regions can lose the drag when the pointer exits the rail during mouse movement; it does not match how a touch sequence stays associated with its gesture context.

### 5. Activation uses real DOM semantics after classification

If the runtime classifies `touchEnd` as a tap, it should activate the real target once. Editable elements should receive focus and native click behavior where appropriate. Buttons, links, tab items, and ARIA/actionable elements should receive a single click activation after `pointerup`.

Click must not fire for drag, long press, canceled sequences, stale sequence ids, disabled controls, disconnected targets without safe re-hit-test fallback, or rejected origins.

### 6. Preserve preview and product boundaries

The teacher app will continue to post messages only to the current iframe window and configured student preview origin. The student runtime will continue to reject unexpected origins, stale frame ids, malformed payloads, unsupported protocol versions, and messages outside teacher-preview sessions.

Implementation must stay within:

- teacher preview input surface/protocol/tests;
- student preview input runtime/protocol/tests;
- package dependency removal and lockfile updates.

Ordinary student routes, feature modules, catalog pages, and learning UI must not receive preview-only event branches.

## Risks / Trade-offs

- Synthetic browser events are not a perfect phone browser. → Treat Pointer Events as the required baseline, optionally dispatch Touch Events only when constructible, and verify user-facing interactions with browser QA.
- Thresholds can feel too sensitive or too sticky. → Centralize constants and write tests around named behavior rather than scattering magic numbers.
- Protocol version mismatches can leave previews inert. → Bump only when needed, reject stale versions safely, and update teacher/student protocol modules together.
- Cross-origin iframe boundaries prevent teacher-side DOM inspection. → Keep the runtime inside `web-student`; teacher sends only validated messages.
- Removing `@use-gesture/react` may regress touch indicator hover behavior. → Keep indicator rendering as a small RAF-driven pointer visual independent from gesture classification.
- Long press behavior may not have product UI yet. → Model long press as state and suppression first; only add product long-press action in a future spec if needed.

## Migration Plan

1. Add/adjust tests that document the current desired sequence behavior.
2. Replace the teacher input surface's `@use-gesture/react` binding with raw Pointer Events and a single active sequence owner.
3. Update the protocol type to remove teacher-originated `tap` and `longPress` conclusions, bumping the version if necessary.
4. Rewrite the student runtime around lifecycle state classification.
5. Remove `@use-gesture/react` from `web-teacher` dependencies after no imports remain.
6. Run focused unit tests, typecheck/build checks, and browser QA in the teacher student preview.

Rollback is straightforward: revert the preview input bridge/protocol/runtime changes and restore the dependency. No persistent data migration is involved.

## Open Questions

- Whether to dispatch optional synthetic `TouchEvent` objects in addition to required `PointerEvent` objects depends on constructor support and tests in the target desktop preview browsers.
- Whether long press should eventually open a context affordance is product behavior and remains out of scope for this change.

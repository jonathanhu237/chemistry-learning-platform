## Context

The full teacher student preview already uses a clean product boundary: `web-teacher` owns the phone shell and iframe lifecycle, while the iframe runs the real `web-student` SPA with a teacher-owned preview student session. The remaining interaction gap is input fidelity. A desktop mouse drag inside the preview can still behave like desktop selection, and the current touch dot is a visual-only student-side cursor driven by React state updates on pointer movement, which can visibly lag.

Research confirmed that Chrome DevTools and Firefox Responsive Design Mode do not solve this with a normal page library. Browser tools translate mouse input into touch input at browser/tooling level. CDP can do this for a real Chromium target, but embedding that in the teacher console would require a remote browser, extension, Electron shell, or streaming surface. That is intentionally out of scope for this product feature.

Research inside the current app also showed that existing drag behavior is not a match for this problem by itself. The catalog tree uses `react-arborist` for tree node reordering, related-link ordering uses native HTML5 Drag and Drop, and the atom viewer uses local Pointer Events for a canvas. Those are useful precedents for choosing a focused interaction owner, but none of them translates teacher mouse gestures into phone-like interaction inside a framed student app.

This design keeps the existing iframe preview and adds a pure-web, preview-only input bridge:

```text
web-teacher phone screen input surface
  @use-gesture/react tap/drag/press recognition, touch dot rendering
        |
        | postMessage with normalized screen coordinates
        v
web-student preview input runtime
  origin/session validation, hit testing, scroll container selection
        |
        v
real web-student DOM
  normal routes, normal components, normal CSS
```

The design is intentionally simulator-like rather than browser-engine-perfect. It must feel correct for common teacher review actions: hover/touch dot, tap, drag up/down to scroll, and no text selection while dragging. It must not introduce a second student frontend or page-specific preview behavior.

## Goals / Non-Goals

**Goals:**

- Make mouse press-and-drag over the phone screen behave like a mobile finger drag for the framed student app.
- Prevent desktop text selection and drag artifacts during active simulated touch gestures.
- Keep the touch dot visually attached to the pointer by rendering it in the teacher shell with requestAnimationFrame and CSS transforms.
- Keep all simulated input behavior behind preview-only teacher and student runtime modules.
- Preserve the real student app as the rendered UI, including real bottom navigation, route stack, cards, forms, and page styles.
- Validate origin, session, and frame ownership before accepting cross-frame input messages.
- Use `@use-gesture/react` for teacher-side gesture recognition while keeping iframe messaging, student-side execution, and cursor rendering as explicit preview infrastructure.

**Non-Goals:**

- Do not implement CDP, Electron, browser extension, remote Chromium, WebRTC streaming, VNC, or browserless rendering.
- Do not claim full real-device or browser-engine touch equivalence.
- Do not add page-local scroll hacks for learning, profile, feedback, assessment, bottom navigation, or any other student business page.
- Do not hide, fade, or alter the student bottom navigation for preview input simulation.
- Do not simulate virtual keyboard, OS-level gestures, browser toolbar, multi-touch pinch/zoom, inertial physics, or native iOS rubber-band overscroll in this change.
- Do not import student app pages or styles into `web-teacher`.

## Decisions

### Decision 1: Use `@use-gesture/react` for teacher-side gesture recognition

The teacher-side phone screen surface will use `@use-gesture/react` to recognize the gesture sequence. This is the right layer for a library because the teacher shell owns the mouse/pointer input, tap-vs-drag thresholds, cancellation, press state, and the visual touch dot. The library prevents us from hand-rolling common gesture classification details while keeping the rest of the simulator explicit.

`@use-gesture/react` is not the emulator by itself. It does not cross iframe boundaries, does not know the student DOM, does not create trusted browser touch events, and does not choose scroll containers. It only translates teacher mouse/pointer input into normalized gesture intent:

- hover/press state for the dot
- tap
- drag start/move/end
- cancel
- long-press-ready press state or future long-press intent
- movement and timing thresholds

Alternatives considered:

- Native Pointer Events only: rejected as the primary teacher-side recognizer because it would duplicate solved gesture-threshold and cancellation work. Native events remain acceptable for low-level fallback and tests, but the feature should use the interaction library for gesture recognition.
- `hammerjs/touchemulator`: rejected as a dependency because it is old, global, and page-monkey-patching oriented. Its state-machine ideas are useful, but its implementation model is too invasive for this app boundary.
- CDP/remote browser: rejected because it is architecturally heavy for a teacher product preview.

### Decision 2: Capture input in `web-teacher`, apply behavior in `web-student`

The teacher app cannot directly read or mutate the framed student DOM across different origins, and it should not own student behavior. The teacher side will therefore only capture screen-relative input and send messages to the iframe. The student side will be responsible for applying those messages to its own DOM.

Teacher-side owner:

- `apps/web-teacher/src/features/student-preview/input/*` or an equivalent feature-local module.
- Owns the transparent screen input surface, `@use-gesture/react` bindings, coordinate mapping, message sender, and visual dot.
- Does not import `web-student` source.

Student-side owner:

- `apps/web-student/src/app/preview/input/*` or an equivalent preview runtime module.
- Owns message validation, hit testing, scroll container selection, tap activation, and cleanup.
- Is enabled only when the session is the teacher student preview.

This keeps the behavior non-invasive: ordinary student routes render the same components and receive normal DOM effects, while only the preview runtime translates teacher-side input into those effects.

### Decision 3: Use a versioned postMessage protocol

Input messages will be plain structured objects with a stable namespace and version. A representative payload:

```ts
type PreviewInputMessage = {
  namespace: "chemistry.studentPreview.input";
  version: 1;
  sessionId: string;
  frameId: string;
  sequenceId: string;
  type: "hover" | "touchStart" | "touchMove" | "touchEnd" | "touchCancel" | "tap" | "longPress";
  point: {
    x: number;
    y: number;
  };
  previousPoint?: {
    x: number;
    y: number;
  };
  startedAt?: number;
  timestamp: number;
  primaryButton: boolean;
  modifiers?: {
    alt: boolean;
    ctrl: boolean;
    meta: boolean;
    shift: boolean;
  };
};
```

Coordinates are CSS pixels in the student iframe viewport, not teacher page coordinates. The teacher surface computes them from the phone screen content rectangle and current preview scale. The student runtime treats negative/out-of-bounds coordinates as cancel/ignore depending on active sequence state.

The teacher shell sends only to the iframe `contentWindow` and expected student origin. The student runtime validates:

- namespace/version
- `event.origin`
- active preview mode and preview purpose
- session id or frame id when available
- active sequence ownership
- coordinate sanity

Messages that fail validation are ignored without falling back to unsafe behavior.

The first implementation may treat long press as a press-state and cancel-safe gesture without adding business-specific long-press actions. If a future student feature needs long-press behavior, the intent should be added to this protocol and implemented in the student preview input runtime rather than in ordinary student pages.

### Decision 4: Tap and scroll are first-class behaviors

The student runtime will not depend on synthetic `TouchEvent` alone. Script-dispatched events are not trusted browser events and cannot reliably trigger native scrolling. The runtime will implement the two user-visible behaviors the teacher needs:

Tap:

- On `touchStart`, record the initial target using `document.elementFromPoint(x, y)`.
- On `tap`, hit-test again, prefer the original target when still connected and compatible, focus focusable controls, and call `click()` on the actionable element.
- If the target is an input/textarea/select/contenteditable, allow focus and normal typing behavior where the app supports it.

Drag scroll:

- Once movement exceeds the drag threshold, treat the sequence as a scroll gesture.
- Find the nearest scrollable ancestor from the original target or current hit-test target.
- A container is scrollable when computed overflow allows scrolling and its scroll size exceeds its client size.
- If no inner container can scroll, use `document.scrollingElement` or the window scroll path.
- For vertical movement, apply `scrollTop += previousY - currentY`. Dragging the pointer upward therefore increases scroll position, matching the phone mental model.
- Respect scroll boundaries; if an inner container cannot scroll further, allow fallback to the next scrollable ancestor only through a deliberate helper rather than page-specific logic.

Synthetic pointer/touch events may be dispatched as secondary compatibility signals only if needed by existing student widgets. They are not the source of truth for scroll.

### Decision 5: Prevent desktop selection only during active simulated touch

The teacher-side input surface will use `touch-action: none`, `user-select: none`, and `event.preventDefault()` on active pointer sequences. This is scoped to the phone screen surface and active gesture. It must not disable selection, pointer events, or normal controls in the teacher toolbar, sidebar, page header, or outside the preview phone screen.

The student iframe does not need global `user-select: none` to solve the drag-selection problem once the overlay captures active drag sequences. If any student-side selection suppression is needed for fallback compatibility, it must be scoped to preview input runtime activity and removed on sequence end/cancel.

### Decision 6: Render the touch dot in the teacher shell with rAF

The current student-side cursor can lag because it updates React state on every pointer movement and includes transform transitions. The touch dot should move to the teacher-side input surface, where the pointer is captured.

Rendering contract:

- Store the latest pointer position in refs or module state.
- Schedule at most one `requestAnimationFrame` update at a time.
- Apply `style.transform = translate3d(x, y, 0) scale(...)` directly to the dot element.
- Do not call React state setters for every pointer move.
- Do not transition `transform`; only opacity or scale may be transitioned briefly.
- Use `pointer-events: none`, `will-change: transform`, and containment where appropriate.
- Hide the dot outside the phone screen, when the iframe is not ready, and after a short idle timeout.

The dot belongs to the teacher preview shell, not the student app. This avoids cross-frame lag, keeps visual feedback aligned with the captured pointer, and avoids extra work inside the framed student runtime.

### Decision 7: Keep the bottom navigation real and direction-driven

The touch emulator must not special-case the bottom navigation. The real student shell owns the bottom-navigation scroll behavior, and the simulator only sends tap/scroll intent.

The intended product behavior is the mobile feed pattern, not a timer-based reveal:

- scrolling content downward hides the bottom navigation by sliding the entire view off the bottom edge,
- scrolling content upward reveals it,
- returning near the top or switching root routes reveals it,
- pausing after a downward scroll does not reveal it automatically,
- hiding must not be implemented as a partially transparent or partially compressed remnant.

X itself is not open source, so this design does not claim to copy X source code. The public platform analogue is Material's hide-on-scroll behavior: consume downward nested scroll to slide the bottom view fully offscreen, consume upward nested scroll to slide it back onscreen. The web implementation should follow the same state-machine shape in the real student shell.

The teacher preview must not add preview-only bottom-nav hiding, page overlays, route rewrites, CSS targeting normal student shell elements, or idle timers. If the bottom navigation hides or appears while the teacher drags in the phone simulator, that must be because the framed student app received scroll intent and ran its own shell behavior.

### Decision 8: Verification treats boundary failures as regressions

This feature is easy to turn into scattered preview hacks. Tests should deliberately guard against that:

- `web-teacher` boundary tests reject imports from `web-student` route/feature/style modules.
- `web-student` source checks reject raw touch-emulation branching in ordinary routes/features.
- Unit tests cover `@use-gesture/react` binding behavior, gesture thresholds, tap-vs-drag classification, coordinate mapping, and message validation.
- Student runtime tests cover scroll container selection, tap activation, and origin/session rejection.
- Browser QA verifies drag-up and drag-down on the learning page, profile page, and at least one long content page without text selection.
- Browser QA verifies the dot stays attached to the pointer under current preview zoom levels.

## Risks / Trade-offs

- [Risk] Synthetic events are not trusted browser input and will not perfectly match iOS/Android native touch. -> Mitigation: implement visible tap and scroll behavior directly, and document that this is a lightweight teacher preview simulator rather than a real device emulator.
- [Risk] Gesture-library behavior is mistaken for full touch emulation. -> Mitigation: document and test that `@use-gesture/react` only owns teacher-side recognition; the student preview runtime remains responsible for click/focus/scroll execution.
- [Risk] Scroll target selection can be wrong in nested scroll containers. -> Mitigation: centralize the scrollable ancestor algorithm and add targeted tests with nested fixtures before touching page code.
- [Risk] The overlay blocks normal iframe mouse events unexpectedly. -> Mitigation: treat the overlay as the single input route for the preview phone screen and implement tap/click/focus faithfully; keep toolbar and outside-screen controls separate.
- [Risk] Future developers add page-local preview scroll hacks. -> Mitigation: keep a preview input runtime owner and source-boundary tests that flag direct touch-emulation logic in student feature modules.
- [Risk] Dot rendering still lags under zoom or resized frames. -> Mitigation: compute the screen rect on pointer start, refresh it on resize/orientation/zoom, and update transform through rAF without transitions.
- [Risk] A stale iframe accepts messages from an old teacher session. -> Mitigation: include frame/session ids, clear state on iframe reload, and validate origin/session on the student side.
- [Risk] Text inputs need real typing after simulated tap. -> Mitigation: tap focuses controls through the student runtime; keyboard typing can remain normal browser keyboard input into the focused iframe element where same-browser focus allows it, with follow-up protocol work only if QA exposes a gap.

## Migration Plan

1. Add `@use-gesture/react` to `web-teacher` only.
2. Remove or disable the current student-side visual-only preview cursor once the teacher-side input surface owns the dot.
3. Add the teacher-side input surface behind the existing student preview page only.
4. Add the student-side preview input runtime behind preview-mode bootstrap/runtime checks only.
5. Wire the versioned postMessage protocol and reject unsupported origins/sessions by default.
6. Add unit tests for gesture bindings, coordinate mapping, protocol validation, tap, and scroll helpers.
7. Run browser QA against the existing preview page at supported phone presets and zoom levels.
8. If the feature has to be rolled back, disable the input surface/runtime and remove the teacher-only dependency while leaving the iframe preview page unchanged.

## Open Questions

- Whether keyboard text entry after simulated tap needs a dedicated postMessage text-input bridge depends on QA across the preview iframe focus behavior.
- Whether to add basic inertial scrolling can be decided after the first drag-scroll implementation feels stable; it is not required for this change.
- Whether multi-touch pinch should exist in the future is separate from this change and should not shape the first implementation.

## Follow-up Limitations Confirmed During Implementation

- The first implementation covers preview tap, focus, click, press state, cancel cleanup, and vertical drag scrolling. Virtual keyboard text bridging remains a follow-up if browser focus behavior is not enough for future teacher workflows.
- Inertial scrolling and native iOS or Android rubber-band physics are intentionally not implemented in this change. Any future physics work should stay in the centralized preview input runtime rather than in page-local student route logic.
- Multi-touch gestures such as pinch zoom remain out of scope and should be proposed as a separate simulator capability if needed later.

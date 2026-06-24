# student-preview-touch-emulation Specification

## Purpose
Define the teacher student-preview touch bridge, including preview-scoped pointer translation, cross-frame messaging, real DOM tap/drag behavior, and verification requirements.
## Requirements
### Requirement: Teacher preview captures phone-like pointer gestures
The teacher student preview SHALL provide a phone-screen input surface that uses native Pointer Events to capture desktop primary-pointer input and convert it into simulated phone lifecycle phases for the framed student app.

#### Scenario: Pointer state machine is mounted in the teacher preview shell
- **WHEN** the teacher student preview page renders the phone screen surface
- **THEN** the surface MUST use a self-owned Pointer Events state machine for press, move, release, cancel, capture, and threshold-independent lifecycle transport
- **AND** it MUST NOT import or configure `@use-gesture/react` for the preview input bridge
- **AND** `web-student` route pages and feature components MUST NOT import or configure the teacher-side input state machine.

#### Scenario: Teacher starts a simulated touch inside the phone screen
- **WHEN** the teacher presses the primary pointer button inside the active phone screen area
- **THEN** the preview MUST start one simulated touch sequence
- **AND** it MUST send `touchStart` with viewport-relative CSS pixel coordinates
- **AND** it MUST capture subsequent pointer movement for that sequence until pointer up, pointer cancel, lost pointer capture, iframe reload, preview disablement, or preview teardown.

#### Scenario: Pointer drag does not select desktop text
- **WHEN** the teacher holds the primary pointer button and drags inside the phone screen area
- **THEN** the preview MUST prevent desktop text selection and browser drag artifacts for that active sequence
- **AND** it MUST NOT apply global text-selection suppression outside the phone screen surface.

#### Scenario: Teacher moves the pointer while pressed
- **WHEN** the teacher moves the primary pointer while an active sequence is pressed
- **THEN** the preview MUST send ordered `touchMove` messages for the same sequence id
- **AND** each message MUST include the current point and previous point in framed viewport CSS pixels
- **AND** the teacher side MUST NOT decide whether the sequence is a tap, drag, or long press.

#### Scenario: Teacher releases the primary pointer
- **WHEN** the teacher releases the primary pointer after an active sequence
- **THEN** the preview MUST send `touchEnd` for the same sequence id
- **AND** it MUST NOT send a teacher-originated `tap` conclusion event.

#### Scenario: Teacher drag maps to phone scroll direction
- **WHEN** the teacher presses inside the phone screen and drags the pointer upward or downward
- **THEN** the preview MUST transport the movement as lifecycle messages
- **AND** the framed student app MUST scroll in the same direction a phone would scroll after the student runtime classifies the sequence as dragging.

#### Scenario: Teacher long presses the phone screen
- **WHEN** the teacher keeps the primary pointer pressed inside the phone screen past the long-press threshold
- **THEN** the preview MUST keep the simulated touch sequence active without creating desktop text selection or a browser drag artifact
- **AND** it MUST NOT emit a teacher-originated `longPress` action that bypasses the student runtime lifecycle classifier.

#### Scenario: Pointer starts outside the phone screen
- **WHEN** the teacher presses, drags, or clicks outside the phone screen area
- **THEN** the preview MUST NOT start a simulated student touch sequence
- **AND** teacher toolbar, sidebar, page header, and ordinary browser interactions MUST remain unaffected.

#### Scenario: Pointer sequence is canceled
- **WHEN** the active pointer receives `pointercancel`, loses capture, the iframe reloads, the preview becomes disabled, or the input surface unmounts
- **THEN** the preview MUST send `touchCancel` for the active sequence when possible
- **AND** it MUST clear teacher-side active sequence state and hide or idle the touch indicator.

### Requirement: Preview input bridge uses a controlled cross-frame protocol
The teacher preview SHALL send simulated input to the framed student app through a versioned preview-only message protocol whose student-facing behavior is based on low-level lifecycle phases rather than teacher-side gesture conclusions.

#### Scenario: Teacher emits an input message
- **WHEN** a teacher-side simulated touch sequence starts, moves, ends, cancels, or hovers for indicator feedback
- **THEN** the teacher preview MUST send a structured message with namespace, version, frame/session identity, sequence id, lifecycle type, timestamp, and viewport-relative point coordinates
- **AND** the message MUST use CSS pixel coordinates relative to the framed student viewport.

#### Scenario: Protocol transports lifecycle phases only
- **WHEN** the teacher sends student-preview input messages after this change
- **THEN** the student-facing event types MUST be limited to low-level lifecycle phases such as `touchStart`, `touchMove`, `touchEnd`, and `touchCancel`
- **AND** `hover` MAY be used only for teacher-side indicator state
- **AND** the protocol MUST NOT rely on teacher-originated `tap` or `longPress` messages for student DOM activation.

#### Scenario: Teacher sends to the student iframe
- **WHEN** the teacher preview sends an input message
- **THEN** it MUST target only the current preview iframe window and configured student preview origin
- **AND** it MUST clear or invalidate active sequence state when the iframe reloads or the preview session changes.

#### Scenario: Student runtime receives a message from an unexpected origin
- **WHEN** the framed student app receives a preview input message from an origin that is not allowed for the active preview session
- **THEN** it MUST ignore the message
- **AND** it MUST NOT perform tap, focus, click, scroll, or synthetic event behavior.

#### Scenario: Student runtime receives a stale or malformed message
- **WHEN** the framed student app receives a message with an unsupported namespace, unsupported version, stale frame/session identity, missing sequence identity, invalid lifecycle type, or invalid coordinates
- **THEN** it MUST ignore the message or cancel the affected active sequence
- **AND** it MUST NOT fall back to unsafe direct DOM behavior.

#### Scenario: Protocol changes incompatibly
- **WHEN** implementation removes student-facing `tap` or `longPress` event handling from the active protocol
- **THEN** the protocol version MUST be bumped or otherwise guarded so mismatched teacher and student bundles fail closed
- **AND** both protocol modules MUST document the same supported event type set.

### Requirement: Student preview input runtime is preview-scoped
The student frontend SHALL apply cross-frame simulated input only through a runtime that is enabled for teacher student-preview sessions.

#### Scenario: Normal student session loads the app
- **WHEN** a normal student session opens `web-student`
- **THEN** the preview input runtime MUST NOT listen for or apply teacher preview input messages
- **AND** normal student pointer, touch, click, scroll, keyboard, and route behavior MUST remain unchanged.

#### Scenario: Teacher preview session loads the app
- **WHEN** the framed student app runs with a valid teacher student-preview session
- **THEN** the preview input runtime MUST register the preview message listener
- **AND** it MUST unregister listeners and clear active sequence state when the session exits, iframe unloads, or preview runtime unmounts.

#### Scenario: Student feature code needs no touch-specific preview branch
- **WHEN** drag, tap, scroll, hover, or cursor behavior is implemented for the teacher preview
- **THEN** the behavior MUST be owned by the preview input runtime and teacher preview input surface
- **AND** ordinary student route pages and feature components MUST NOT contain page-local touch-emulation branches.

### Requirement: Student runtime applies tap to the real DOM
The student preview input runtime SHALL translate tap-eligible lifecycle sequences into interaction with the real rendered student DOM only after the sequence ends.

#### Scenario: Tap begins on a rendered element
- **WHEN** a simulated touch sequence starts inside the student viewport
- **THEN** the runtime MUST record the initial target using viewport-coordinate hit testing
- **AND** it MUST dispatch a synthetic `pointerdown` with `pointerType` set to `touch` to the press target when possible
- **AND** that target MUST be used as the preferred tap target while it remains connected and actionable.

#### Scenario: Tap ends on an actionable element
- **WHEN** a simulated sequence ends while still tap-eligible on a button, link, tab item, card, form control, or other actionable student element
- **THEN** the runtime MUST dispatch `pointerup` before activation
- **AND** it MUST activate that real element through focus and click semantics appropriate for the element
- **AND** the student route, component, and API behavior triggered by the tap MUST be the same behavior owned by the normal student frontend.

#### Scenario: Tap targets an editable field
- **WHEN** a tap-eligible simulated sequence targets an input, textarea, select, or contenteditable element
- **THEN** the runtime MUST focus the real editable element when the element is enabled
- **AND** it MUST NOT replace the field with a preview-only editor.

#### Scenario: Tap target disappears before release
- **WHEN** the initial tap target is removed, disabled, or disconnected before the sequence resolves
- **THEN** the runtime MUST re-hit-test the release point or cancel the tap safely
- **AND** it MUST NOT activate an unrelated stale element.

#### Scenario: Drag or long press ends over an actionable element
- **WHEN** a dragging or long-press-ready sequence ends over a button, link, tab item, card, or form control
- **THEN** the runtime MUST dispatch the terminal pointer event for the sequence
- **AND** it MUST NOT synthesize click activation from that terminal event.

### Requirement: Student runtime applies drag to real scroll containers
The student preview input runtime SHALL translate drag-classified lifecycle sequences into scrolling of the appropriate real student scroll container.

#### Scenario: Drag starts over a nested scrollable area
- **WHEN** a simulated drag starts over content inside a nested scrollable container
- **THEN** the runtime MUST choose the nearest scrollable ancestor that can scroll in the requested direction
- **AND** it MUST apply scroll deltas to that container rather than a hard-coded page element.

#### Scenario: Drag starts over ordinary page content
- **WHEN** a simulated drag starts over content with no scrollable ancestor other than the page
- **THEN** the runtime MUST scroll the document scrolling element or equivalent page scroll owner
- **AND** it MUST use the same student page content rendered by the real app.

#### Scenario: Horizontal rail keeps its drag owner
- **WHEN** a drag sequence begins on a horizontally scrollable rail and crosses the drag threshold with horizontal intent
- **THEN** the runtime MUST lock the horizontal scroll owner for that sequence
- **AND** it MUST continue applying horizontal deltas to that owner even if later pointer coordinates fall outside the rail's current visual bounds.

#### Scenario: Drag dispatches move semantics
- **WHEN** the runtime receives `touchMove` for an active sequence
- **THEN** it MUST dispatch `pointermove` with `pointerType` set to `touch` to the active press or hit-test target when possible
- **AND** it MUST update the sequence's last point before processing subsequent movement.

#### Scenario: Scroll reaches a boundary
- **WHEN** the selected scroll container reaches its top, bottom, left, or right boundary during a drag
- **THEN** the runtime MUST clamp the scroll position to the valid scroll range
- **AND** it MAY continue with the next scrollable ancestor only through the centralized scroll helper, never through page-specific special cases.

#### Scenario: Student bottom navigation is visible during scroll
- **WHEN** the student app's bottom navigation changes visibility, opacity, compression, or position during simulated scrolling
- **THEN** that behavior MUST come from the real student frontend shell
- **AND** the touch emulation layer MUST NOT add preview-only bottom-navigation hiding or styling.

### Requirement: Real student bottom navigation follows mobile feed hide-on-scroll behavior
The real student H5 shell SHALL implement bottom-navigation visibility as a scroll-direction state machine, matching the mobile feed pattern used by apps such as X and the platform behavior represented by Material `HideBottomViewOnScrollBehavior`.

#### Scenario: Content scrolls downward through a root route
- **WHEN** a root-level student route consumes enough downward page scroll after the student is no longer near the top of the page
- **THEN** the bottom navigation MUST enter a hidden state
- **AND** the hidden state MUST move the entire bottom navigation off the bottom edge of the viewport.

#### Scenario: Hidden navigation remains hidden while scrolling is idle
- **WHEN** the bottom navigation is hidden because content scrolled downward
- **AND** scrolling stops without an upward scroll or route/top reset
- **THEN** the bottom navigation MUST remain hidden
- **AND** the implementation MUST NOT use an idle timeout to reveal the navigation automatically.

#### Scenario: Content scrolls upward
- **WHEN** a root-level student route consumes enough upward page scroll
- **THEN** the bottom navigation MUST leave the hidden state
- **AND** the entire navigation MUST slide back into its fixed bottom position.

#### Scenario: Content returns near the top or root route changes
- **WHEN** the page scroll position returns near the top of a root route
- **OR** the authenticated shell switches root routes
- **THEN** the bottom navigation MUST be visible.

#### Scenario: Hidden state avoids translucent remnants
- **WHEN** the bottom navigation is hidden
- **THEN** no visible portion, shadow, border, icon, label, or tap target from the navigation may remain inside the viewport
- **AND** partial opacity or a compressed/translucent state MUST NOT be the primary hiding mechanism
- **AND** opacity or pointer-event changes MAY only be used as secondary safeguards after the navigation is fully translated offscreen.

#### Scenario: Visible navigation covers content beneath it
- **WHEN** the bottom navigation is visible on a root-level student route
- **THEN** it MUST be fixed to the bottom edge of the student viewport
- **AND** it MUST use an opaque chrome background so scrolling page text cannot show through or appear below the navigation layer.

#### Scenario: Touch activation does not leave desktop focus chrome
- **WHEN** the student bottom navigation is activated through a mouse-backed simulated touch or ordinary pointer click
- **THEN** the active tab MUST use the student app's selected visual state
- **AND** it MUST NOT show the browser's default black focus outline
- **AND** keyboard focus visibility MAY use a custom app-styled focus treatment.

#### Scenario: Teacher preview scrolls the real student app
- **WHEN** the teacher preview input runtime scrolls the framed student app
- **THEN** the same real student bottom-navigation state machine MUST run
- **AND** the teacher preview MUST NOT add a separate bottom-navigation state, timer, style override, or route-specific workaround.

### Requirement: Touch indicator follows the pointer without per-move React rerenders
The teacher preview SHALL render a DevTools-like touch indicator that visually tracks pointer movement efficiently.

#### Scenario: Pointer hovers over the phone screen
- **WHEN** the pointer is inside the active phone screen area and the preview iframe is ready
- **THEN** the preview MUST show a circular touch indicator aligned to the current pointer position
- **AND** it MUST hide the normal cursor within the phone screen when the indicator is active.

#### Scenario: Pointer moves across the phone screen
- **WHEN** the pointer moves across the phone screen
- **THEN** the touch indicator MUST update through requestAnimationFrame-driven transform changes
- **AND** it MUST NOT call React state setters for every pointer movement.

#### Scenario: Pointer presses the phone screen
- **WHEN** an active simulated touch sequence is pressed
- **THEN** the touch indicator MUST show an active pressed state
- **AND** the active state MUST stay visually attached to the pointer during drag.

#### Scenario: Indicator exits or idles
- **WHEN** the pointer leaves the phone screen, the active sequence ends, the iframe reloads, or the preview becomes unavailable
- **THEN** the touch indicator MUST hide or fade out without leaving stale dots on the teacher page.

#### Scenario: Preview zoom or orientation changes
- **WHEN** the teacher changes preview zoom, device preset, or orientation
- **THEN** the touch indicator coordinate mapping MUST use the updated phone screen rectangle
- **AND** it MUST remain aligned with the pointer after the layout change.

### Requirement: Touch emulation preserves product and security boundaries
The touch emulation implementation SHALL remain an isolated preview infrastructure concern and SHALL NOT become a duplicate student frontend or browser-debugging system.

#### Scenario: Developer implements teacher touch emulation
- **WHEN** implementation adds or modifies the touch emulation layer
- **THEN** `web-teacher` MUST NOT import `web-student` route pages, feature components, student CSS files, router internals, or business logic
- **AND** `web-student` MUST remain the owner of student page rendering and interaction outcomes.

#### Scenario: Developer adds new preview input behavior
- **WHEN** a new simulated input behavior is needed after this change
- **THEN** it MUST be added to the teacher preview input surface, versioned input protocol, or student preview input runtime
- **AND** it MUST NOT be implemented as page-local logic in ordinary student feature modules unless a follow-up spec documents a narrow exception.

#### Scenario: Teacher preview is mistaken for DevTools
- **WHEN** the teacher opens the student preview page
- **THEN** the page MUST remain a focused student preview tool
- **AND** it MUST NOT expose DOM inspection, CDP controls, remote browser streaming, arbitrary user-agent editing, CPU throttling, network throttling, or browser-debugger panels.

#### Scenario: Preview input fails
- **WHEN** the input bridge, runtime validation, or iframe readiness check fails
- **THEN** the preview MUST fail closed for simulated input
- **AND** it MUST keep the existing iframe preview visible or show a controlled input-unavailable state without granting unsafe cross-frame access.

### Requirement: Touch emulation is verified with focused automated and browser QA
The change SHALL include verification that proves phone-like press/move/release behavior, cursor performance, and product-boundary safety.

#### Scenario: Unit tests run for teacher lifecycle transport
- **WHEN** focused teacher preview tests run
- **THEN** they MUST cover raw Pointer Events lifecycle behavior, primary-button filtering, sequence id stability, coordinate mapping, pointer capture/lost-capture cancellation, ordered `touchStart`/`touchMove`/`touchEnd`/`touchCancel` message construction, and the absence of `@use-gesture/react` imports in the input bridge.

#### Scenario: Unit tests run for student runtime classification
- **WHEN** focused student preview runtime tests run
- **THEN** they MUST cover origin/session rejection, short-tap activation, editable focus, drag click suppression, long-press click suppression, cancel handling, stale-sequence rejection, scrollable ancestor selection, horizontal scroll-owner locking, drag-up scroll direction, drag-down scroll direction, and boundary clamping.

#### Scenario: Source-boundary checks run
- **WHEN** frontend boundary validation runs
- **THEN** it MUST detect forbidden `web-teacher` imports from `web-student`
- **AND** it MUST detect raw touch-emulation logic in ordinary student route or feature modules outside the preview runtime owner.

#### Scenario: Dependency checks run
- **WHEN** implementation removes the gesture library from the preview input bridge
- **THEN** `web-teacher` dependencies and lockfiles MUST no longer include `@use-gesture/react` unless another non-preview feature still imports it
- **AND** any retained gesture dependency MUST be justified by an in-repo import outside the student-preview input bridge.

#### Scenario: Browser QA validates drag behavior
- **WHEN** browser QA runs against the teacher student preview page
- **THEN** it MUST verify that press-and-drag upward and downward scrolls the framed real student app
- **AND** it MUST verify that horizontal element rails can be dragged left and right
- **AND** it MUST verify that drag release does not click the element under the release point
- **AND** it MUST verify that no desktop text selection is created by the gesture.

#### Scenario: Browser QA validates touch indicator behavior
- **WHEN** browser QA runs against the teacher student preview page
- **THEN** it MUST verify that the touch indicator remains aligned with the pointer at supported preview zoom levels
- **AND** it MUST verify that stale indicators are not left behind after release, cancel, iframe refresh, or route reload.

#### Scenario: Browser QA validates popover dismissal parity
- **WHEN** browser QA opens a student-page popover or bubble through the teacher preview and then presses outside it
- **THEN** the popover MUST dismiss the same way it dismisses on a real phone
- **AND** the outside press MUST NOT produce an extra unintended click-through activation.

### Requirement: Student runtime classifies phone touch lifecycles
The student preview input runtime SHALL classify simulated phone input from standards-aligned lifecycle phases after observing the complete sequence inside the framed student app.

#### Scenario: Short press and release activates once
- **WHEN** the runtime receives `touchStart` followed by `touchEnd` for the same sequence within the tap duration limit
- **AND** total movement remains within the tap movement threshold
- **AND** the initial `pointerdown` was not canceled
- **THEN** the runtime MUST dispatch `pointerdown` before release, `pointerup` on release, and exactly one click activation for the real actionable target
- **AND** it MUST clear the active sequence after activation.

#### Scenario: Drag movement suppresses tap activation
- **WHEN** the runtime receives `touchMove` events whose accumulated movement exceeds the drag threshold before `touchEnd`
- **THEN** the runtime MUST classify the sequence as dragging
- **AND** it MUST dispatch move semantics and apply scroll or drag behavior through the preview runtime
- **AND** the final `touchEnd` MUST NOT activate a click target.

#### Scenario: Long press suppresses normal tap activation
- **WHEN** the runtime observes a sequence whose press duration reaches the long-press threshold before drag movement occurs
- **THEN** the runtime MUST mark the sequence as long-press-ready
- **AND** it MUST keep the press sequence active until `touchEnd` or `touchCancel`
- **AND** the final release MUST NOT fall through to normal tap activation unless a future spec defines an explicit long-press action.

#### Scenario: Canceled sequence fails closed
- **WHEN** the runtime receives `touchCancel`, a stale sequence id, iframe unload, runtime unmount, or another terminal cancellation path
- **THEN** it MUST dispatch `pointercancel` when a press target exists
- **AND** it MUST clear sequence state
- **AND** it MUST NOT dispatch click activation.

#### Scenario: Classification constants are centralized
- **WHEN** implementation defines tap movement, drag movement, tap duration, or long-press duration thresholds
- **THEN** those constants MUST be owned by the preview input runtime or a shared preview input utility
- **AND** ordinary student feature components MUST NOT define page-local touch-emulation thresholds.


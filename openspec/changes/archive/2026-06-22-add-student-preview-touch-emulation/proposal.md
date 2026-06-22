## Why

The current teacher student preview renders the real `web-student` app in a phone shell, but desktop mouse drag still behaves like desktop input: it can select text and the visual touch dot can lag behind the pointer. Teachers need the preview to feel like a lightweight phone simulator for common touch interactions while preserving the existing clean boundary: no CDP/remote-browser service, no copied student pages, and no preview-specific business forks inside ordinary student routes.

## What Changes

- Add a lightweight touch emulation layer for the teacher student preview page.
- Use `@use-gesture/react` in the teacher-side phone screen surface to recognize tap, drag, long-press-ready press state, cancel, and threshold behavior.
- Route simulated input into the framed `web-student` app through a narrow preview-only `postMessage` protocol.
- Add a student-side preview input runtime that is enabled only for teacher student-preview sessions and translates the protocol into real DOM interaction semantics: tap/click/focus and mobile-like scrolling.
- Replace the current visual-only touch cursor with a requestAnimationFrame-driven touch indicator that follows the pointer without React state updates on every move.
- Prevent desktop text selection and drag artifacts only while an active simulated touch gesture is running inside the preview surface.
- Keep unsupported or future gesture differences centralized in the preview input runtime rather than page-local `previewMode` branches.
- Do not introduce the CDP/remote Chromium streaming approach; this change remains a pure web/iframe preview enhancement.

## Capabilities

### New Capabilities

- `student-preview-touch-emulation`: Defines the teacher preview touch input simulator, cross-frame input bridge, student preview input runtime, touch cursor performance contract, and verification requirements.

### Modified Capabilities

- None.

## Impact

- Affected teacher frontend:
  - `apps/web-teacher/src/features/student-preview/*` for the `@use-gesture/react` phone-screen gesture surface, input protocol sender, touch indicator, and frame coordinate mapping.
  - Existing student preview route/components remain iframe-based and must not import `web-student` business modules.
- Affected student frontend:
  - `apps/web-student/src/app/preview/*` or equivalent preview runtime owner for receiving and applying simulated input messages.
  - Removal or replacement of the current visual-only `PreviewTouchCursor` behavior so it no longer performs React state updates per pointer move.
  - Student route/feature modules should not gain page-local touch-emulation logic.
- Affected tests and QA:
  - Unit/contract tests for protocol shape, origin/session gating, scroll container selection, tap behavior, and source-boundary rules.
  - Browser QA proving drag-up/drag-down scrolls the real framed student app without selecting text and the touch indicator stays visually attached to the pointer.
- Dependencies:
  - No CDP, Electron, browser extension, remote browser streaming, VNC, or browserless runtime.
  - Add `@use-gesture/react` to `web-teacher` only. It is the teacher-side gesture recognizer, not the full touch emulator; iframe messaging and student-side execution remain owned by the preview runtime.

## Why

The teacher student-preview currently behaves differently from a real phone because its mouse-backed input bridge mixes raw pointer handlers with `@use-gesture/react` classification and sends conclusion events such as `tap` and `longPress` before the framed student app has observed a complete mobile-style press/move/release sequence. This causes preview-only regressions such as overlays not dismissing like mobile taps, horizontal rails not sliding consistently, and long press state being ignored.

This change makes the preview input bridge follow mobile input standards: the teacher surface transports a low-level pointer-derived touch sequence, and the student preview runtime classifies short taps, drags, long presses, and cancels from that sequence inside the iframe.

## What Changes

- Remove `@use-gesture/react` from the teacher student-preview input surface.
- Replace gesture-library recognition with a single self-owned Pointer Events state machine on the teacher preview surface.
- Change the preview input protocol so teacher messages represent low-level lifecycle phases (`touchStart`, `touchMove`, `touchEnd`, `touchCancel`, plus hover only for the indicator) rather than teacher-side `tap` or `longPress` conclusion events.
- Move tap/drag/long-press classification into the `web-student` preview input runtime, using timestamp and movement thresholds that match common mobile touch behavior.
- Ensure short press-and-release activates the real DOM target once, drag/scroll sequences do not produce click activation, long press is modeled explicitly and does not fall through to normal tap activation, and cancel/lost-capture paths fail closed.
- Keep the preview feature isolated to teacher preview infrastructure and the student preview runtime; ordinary student pages, routes, and feature components must not receive page-local emulation branches.
- Add focused tests for the teacher input state machine, protocol validation, student runtime classification, scroll target locking, tap activation, long press suppression, and cancel handling.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-preview-touch-emulation`: Replace gesture-library-based recognition with a standards-aligned touch bridge that transports pointer-derived touch phases and lets the student runtime classify mobile interactions.

## Impact

- Affected teacher code:
  - `apps/web-teacher/src/features/student-preview/input/PreviewGestureSurface.tsx`
  - `apps/web-teacher/src/features/student-preview/input/previewInputProtocol.ts`
  - `apps/web-teacher/package.json` and lockfile dependency entries for `@use-gesture/react`
  - focused teacher preview input tests
- Affected student code:
  - `apps/web-student/src/app/preview/input/PreviewInputRuntime.tsx`
  - `apps/web-student/src/app/preview/input/previewInputProtocol.ts`
  - focused student preview runtime tests
- The cross-frame preview input message contract will be updated. If a version bump is required, the runtime must reject stale or mismatched versions safely.
- The change must not alter normal student sessions, normal teacher preview framing/security behavior, or unrelated app pages.

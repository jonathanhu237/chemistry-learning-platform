## Why

The root Atom assistant currently uses a three-dot loading cluster while generating, which feels generic and weaker than the student-facing `Atom` identity now used across the AI root, contextual AI actions, and assistant states. We have a lightweight vector Lottie asset (`Atom.json`) that can replace the dots with an Atom-branded thinking mark without changing chat behavior or backend contracts.

## What Changes

- Replace the root `/ai` running-turn three-dot thinking cluster with an inline Atom Lottie animation mark.
- Keep the existing phase label behavior, including normalized labels, fade-through transitions, minimum visible timing, polite status announcements, and removal after successful completion.
- Add a local Lottie JSON asset for the Atom thinking mark and render it only in the root assistant running state.
- Add a React Lottie runtime dependency suitable for rendering local Lottie JSON in `apps/web-student`.
- Recolor the Atom animation to the student service's main green visual system instead of using the downloaded asset's pure black stroke.
- Preserve the existing contextual/detail-route loading affordance unless it is already using the root thinking line.
- Preserve reduced-motion behavior by showing the current phase label and a non-looping or static Atom mark when motion is reduced.
- No backend API, streaming, routing, permissions, history, or assistant context behavior changes are introduced.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `student-h5-ai-assistant`: Root Atom assistant running turns should use an Atom Lottie thinking mark instead of an animated dot cluster while preserving phase-label semantics, accessibility, and flat root chat layout.

## Impact

- Affected app: `apps/web-student`.
- Expected code touch points:
  - `apps/web-student/src/features/assistant/StudentAiChatPanel.tsx`
  - `apps/web-student/src/styles/assistant.css`
  - `apps/web-student/src/assets/` or equivalent local asset folder for `Atom.json`
  - `apps/web-student/package.json` and lockfile for the Lottie runtime dependency
  - student-web tests that currently assert `.ai-thinking-dots`
- Expected dependency: `lottie-react` or an equivalent lightweight React wrapper around `lottie-web`.
- OpenSpec impact: update the existing `student-h5-ai-assistant` running-state contract from "animated dot cluster" to "Atom Lottie thinking mark".

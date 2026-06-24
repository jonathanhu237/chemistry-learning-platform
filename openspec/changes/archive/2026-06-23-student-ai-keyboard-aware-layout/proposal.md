## Why

On real phones, focusing the Atom root composer can open the soft keyboard while the app still lays out the AI root against the old full viewport and fixed bottom navigation. This leaves the bottom Atom navigation visible above the keyboard and exposes a band of the underlying page background between the app chrome and keyboard, which breaks the intended fullscreen chat feel.

This matters now because the `/ai` root has become a Grok/Gemini-like direct chat surface. Its keyboard-open state must feel like a native chat screen: the composer stays attached to the keyboard edge, and the app's own bottom navigation disappears until the keyboard closes.

## What Changes

- Add a keyboard-aware layout state for the student H5 Atom root assistant when the root composer is focused.
- Hide the app's bottom Atom navigation while the root assistant composer is focused and the mobile keyboard is expected to be visible.
- Size the Atom root assistant against the visible viewport while the keyboard is open so no raw page background band appears between the composer/bottom chrome area and the keyboard.
- Keep the empty-state Atom welcome visible during keyboard-open entry by shifting it upward within the chat content area instead of letting it collide with the composer or keyboard.
- Preserve normal bottom navigation behavior when the keyboard is closed, when focus leaves the composer, and on non-AI root routes.
- Preserve contextual `/ai/chat` detail-route behavior: it already hides bottom navigation and must not inherit root-only keyboard chrome.
- Keep system keyboard UI outside scope; the app only controls its own shell, bottom navigation, and assistant layout.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-ai-assistant`: Define the `/ai` root composer keyboard-open behavior, including root-only navigation hiding and visible-viewport layout.
- `student-h5-mobile-design-system`: Define the mobile shell contract for soft-keyboard-aware bottom navigation and visual viewport sizing.

## Impact

- `apps/web-student/src/app/shell/AuthenticatedAppLayout.tsx`: likely adds focus/blur or visual viewport listeners and a root-only keyboard-active shell state.
- `apps/web-student/src/styles/app-shell.css`: likely adds shell classes/CSS variables to hide bottom navigation and size root content to the visible viewport while focused.
- `apps/web-student/src/styles/assistant.css`: likely adjusts root assistant panel/composer behavior under keyboard-active layout.
- `apps/web-student/index.html`: may add viewport metadata such as `interactive-widget=resizes-content` if validated as helpful, but implementation must not rely on it alone.
- `apps/web-student/src/App.e2e.test.tsx`, `apps/web-student/src/roleBoundaries.test.ts`, and mobile QA scripts may gain coverage for keyboard-active root behavior.
- No backend API, data model, or chat-session migration changes are required.

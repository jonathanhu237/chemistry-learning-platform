## Why

The current student AI root still reads like a compact card-based center instead of the Grok/X-style first-screen chat experience the product is targeting. This change makes the root AI tab a true fullscreen mobile chat canvas while preserving the separate contextual `/ai/chat` route for page handoffs.

## What Changes

- Replace the `/ai` root visual structure with a full-height, full-bleed chat canvas between the app header and bottom navigation.
- Remove root-level card framing around the assistant panel; keep only lightweight text, a history icon action, one low prompt panel, and the bottom composer.
- Move the empty-state prompt block close to the composer, leaving a large calm middle area like Grok, ChatGPT, Claude, and Gemini mobile chat starts.
- Keep unsupported controls out of the composer: no attachment, model selector, or voice input.
- Keep `/ai/chat` as the second-level contextual chat page without the root history action.
- Preserve existing local history behavior, streaming behavior, and `conversation_history`.
- Add tests and mobile viewport checks that assert the root page is not a card shell and the composer sits above bottom navigation.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `student-h5-assistant-mobile-starter`: Replace the old starter-card requirement with a fullscreen direct-chat starter that uses a minimal prompt block and visible composer.
- `student-h5-route-stack-navigation`: Clarify that the `ai` root is allowed to host the global/default conversation directly, while contextual conversations from other pages continue to use `/ai/chat`.
- `student-h5-mobile-design-system`: Add mobile layout requirements for fullscreen chat canvases, fixed composer spacing, and bottom navigation coexistence.

## Impact

- Student frontend AI route files: `apps/web-student/src/routes/ai/*`.
- Student assistant components and local history wiring: `apps/web-student/src/features/assistant/*`.
- Student mobile shell styles: `apps/web-student/src/styles/assistant.css` and `apps/web-student/src/styles/app-shell.css`.
- Student e2e/mobile verification around `/ai` and `/ai/chat`.
- No backend API behavior changes are required for this visual refinement.

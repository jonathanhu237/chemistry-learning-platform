## Why

The Atom root assistant currently mixes two visual models. The header is moving toward a soft mobile chat overlay, but assistant replies still render as bounded white cards. That card treatment limits the available reading width, repeats status chrome inside every answer, and makes long educational explanations feel boxed off from the root chat canvas. The desired direction is closer to a modern mobile assistant surface: user questions remain compact right-aligned bubbles, while successful Atom replies become full-width text flowing directly on the background, with each assistant turn separated by a lightweight action bar.

This change formalizes that root-only chat surface. It keeps the existing CSS-safe header veil context, adds a flat assistant reply model, preserves dynamic follow-up chips, and keeps student source disclosure limited to safe citation counts. The goal is not to copy an external product, but to make the student Atom root page read as one continuous learning assistant surface without breaking the recently stabilized composer, keyboard, streaming, and history behavior.

## What Changes

- Add a root-only header overlay treatment for the Atom root assistant title row.
- Render the header background as a semi-transparent gradient veil layer, not as a copied page background.
- Keep the title text and root actions fully opaque and independently layered above the veil.
- Convert the two root header actions into one compact real-background action capsule, with history and new-chat each occupying one half.
- Allow root chat content to visually exist behind the header overlay while preserving safe initial spacing.
- Convert successful root assistant replies from white card bubbles into full-width flat text blocks on the root canvas.
- Keep user messages as right-aligned green bubbles so user input remains visually distinct.
- Move assistant turn separation to a lightweight action row below each successful reply, with feedback/copy/more actions on the left and safe citation count information on the right.
- Preserve dynamic follow-up chips so only the latest successful assistant response contributes currently visible suggestions.
- Preserve all existing root composer, keyboard-aware layout, local history, streaming, welcome, and contextual `/ai/chat` behavior.
- Add QA expectations for light-theme mobile viewports, long Markdown replies, action rows, citations, dynamic chips, and overlap/scroll cases.

No breaking backend API, data model, streaming, prompt, or persistence changes are expected for the first implementation. Feedback actions may be local UI state unless a later change explicitly wires them into the student feedback API.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-ai-assistant`: Adds root assistant header veil behavior, root assistant flat reply turns, action row semantics, safe citation placement, dynamic chip placement, and root/detail separation requirements.
- `student-h5-mobile-design-system`: Adds mobile overlay/veil design rules for transparent-light header chrome and cardless assistant reply surfaces without background duplication.

## Impact

- Affected frontend areas:
  - `apps/web-student/src/features/assistant/StudentAiChatPanel.tsx`
  - `apps/web-student/src/styles/assistant.css`
  - `apps/web-student/src/shared/markdown/AiMarkdownBlock.tsx` or markdown styling only if flat reply typography requires scoped adjustments
  - existing root assistant viewport, component, and source-boundary tests that assert message layout, citation rendering, dynamic chips, header/composer layout, or root/detail separation
- Existing tests around source privacy, dynamic follow-up prompts, root history, composer geometry, and root/detail route separation will need updates.
- No backend API, data model, streaming, prompt, local history, or routing contract changes are required.
- No new runtime dependency should be introduced; the effect should rely on scoped React structure, existing lucide icons, CSS layering, and alpha-gradient backgrounds. The accepted root header veil should not depend on `backdrop-filter` blur.

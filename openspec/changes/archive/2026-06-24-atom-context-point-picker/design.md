## Context

The Atom root assistant (`/ai`) currently renders a composer-first chat surface. Its `activeContext` is local React state initialized from the `context` prop in `StudentAiChatPanel.tsx`. The root route passes `defaultAssistantContext()`, which produces the global `learning_home` context titled `Atom learning assistant`. Restored local history entries can replace that active context with the history entry's stored context.

The contextual `/ai/chat` detail route already supports explicit context handoff through `navigateToAiChat()`, `assistantContextStore`, and `loadAssistantContext(search.contextKey)`. Existing producers include the home video feed, the video-library search page, catalog point detail, and assessment report pages. Those producers already know how to create an `AssistantContext` with `context_type`, `context_title`, `context_summary`, `chapter_id`, `experiment_id`, `point_node_id`, `source_node_id`, `catalog_path`, and related ids.

The root composer `+` currently behaves like a context affordance only when `hasLearningBackgroundContext` is true. It does not load catalog data, open a picker, create context, or let a global `learning_home` chat bind itself to a point. Submitting a question sends either the override context or the current `activeContext` to `streamStudentAssistantAsk()`.

The video-library/search page has already become a useful model for point discovery. It can run `searchStudentVideoLibrary(query)` and map results into point/video learning targets. It also has learning-scope behavior that mixes video results with catalog directory results. This picker should reuse the search data contract, but it should not navigate to the full `/search` or `/video-library` page because the product intent is to remain inside Atom.

The learning catalog flow already has lazy catalog browsing primitives through chapter catalog and catalog-node APIs, plus row/card renderers for directory and point nodes. The picker should reuse those structures for empty-query browsing instead of attempting to load every point at once.

The Atom history sheet gives the closest existing layout baseline for a bottom sheet inside the assistant. Its sheet uses `max-height: min(72dvh, 640px)`, bottom anchoring, a soft backdrop, `8px 8px 0 0` top radius, and safe-area bottom padding. The student shell also already exposes visual-viewport and keyboard CSS variables such as `--student-visual-viewport-height` and `--student-keyboard-bottom-inset`.

## Goals / Non-Goals

**Goals:**
- Make the root `+` useful when the chat has only the default global context.
- Let the student bind exactly one concrete point placement before asking.
- Keep the selection inside Atom through a half-height picker.
- Support both ways students find a point:
  - browse the catalog/directory forest when the search field is empty;
  - type to search point placements when the search field has text.
- Reuse existing catalog APIs and video-library search APIs.
- Surface the bound point as an attachment-like learning-background chip/card near the composer.
- Preserve direct free-form asking: students can still ask globally without selecting a point.
- Keep keyboard behavior mobile-safe so the bottom search field remains usable and the underlying Atom title/header is not covered.

**Non-Goals:**
- Do not build a new full-screen point search route.
- Do not replace the existing `/search` or `/video-library` pages.
- Do not introduce a many-context chat model; one chat binds at most one point.
- Do not allow directory-only context binding in this change unless a later spec explicitly allows it.
- Do not require a backend chat-session migration.
- Do not change the assistant stream endpoint contract beyond using the already-supported `AssistantContext` fields.
- Do not index or search raw video-resource metadata for this picker.

## Decisions

1. Use one Atom picker shell with two body modes.

   The sheet component should be route-local to Atom, for example `AtomContextPickerSheet`. Its stable structure is header, scrollable body, and bottom search footer. When `query.trim()` is empty, the body renders the catalog picker. When query has content, the body renders a compact point-search list.

   Alternative considered: use two separate sheets, one for browse and one for search. That would duplicate keyboard, height, selection, loading, and dismissal behavior. A single shell preserves the mental model: the student is always choosing a learning background.

2. Use a stable half-height sheet rather than the full search page.

   The default height should follow the Atom history baseline: `height: min(72dvh, 640px)`. Because a picker needs stable browsing space, it should prefer `height` with a `max-height` safety cap rather than only `max-height`. The safety cap should use the visual viewport and reserve the Atom title/header area, for example `max-height: calc(var(--student-visual-viewport-height) - var(--ai-root-header-overlay-height) - 12px)`.

   Alternative considered: open `/search` or `/video-library`. That provides existing lists but breaks the sense that the student is still in Atom and makes point binding feel like navigation instead of attaching context to the current chat.

3. Put the picker search field at the bottom.

   The bottom field matches the provided reference and keeps the picker feeling like a compact command/input surface. The body above it can scroll independently. Keyboard-active layout should use the existing shell visual-viewport variables and/or bottom inset so the field stays above the soft keyboard.

   Alternative considered: put search at the top like the full video-library page. That is familiar for search pages, but this picker is not a search destination; it is a bottom tool sheet inside a chat composer flow.

4. Browse mode is a catalog forest with lazy expansion.

   Empty-query mode should show chapter/profile roots and catalog directories as navigable rows. Directory rows open/expand the next layer; point rows are selectable. The implementation should not prefetch all descendant points. It should call the existing chapter/root catalog APIs and load child directories only as needed.

   Alternative considered: show all points in one default list. The point set is too large and loses textbook/catalog organization, which is exactly the structure students can understand before they know what to type.

5. Query mode is a compact point-placement search list.

   Non-empty query mode should reuse `searchStudentVideoLibrary(query)` and render one row per bindable point placement, without thumbnails. Rows should emphasize title, direct path/catalog context, and a compact snippet or reason. If a search result maps only to a directory or non-point navigation target, it should be omitted from the binding list or shown as non-bindable only if that helps orientation.

   Alternative considered: reuse the full video-library result cards. Those cards are designed for a second-level page and include more visual affordance than a half-height picker can comfortably hold.

6. Binding uses the existing `AssistantContext` shape.

   Selecting a point should build the same kind of `AssistantContext` already produced by point detail, video-library result AI actions, and home feed AI actions. The active root chat should then use that context for subsequent sends.

   Alternative considered: introduce a new `boundPoint` request payload. That would duplicate existing context fields and create avoidable backend/frontend branching.

7. One chat binds one point.

   Before the first message, the student may remove or replace the selected point. Once the first message is sent, the chat is locked to that point context; changing the point requires a new Atom chat. This keeps conversation history coherent and prevents later turns from mixing incompatible evidence/context.

   Alternative considered: allow point switching mid-chat. That would be more flexible but makes `conversation_history` ambiguous and weakens the guarantee that the assistant's answer is about the same point throughout the chat.

8. Show bound state as a chip/card, not by overloading the `+` icon alone.

   The `+` remains the entry point for learning-background actions. The selected point appears as an attachment-like chip/card near the composer with title, concise path, and remove/replace affordance when editable. After lock, the chip becomes read-only and communicates that the chat is bound to that point.

   Alternative considered: turn the `+` into a selected icon only. That is too subtle for a one-point binding rule and does not carry enough context title/path information.

## Risks / Trade-offs

- Picker content may feel cramped on small phones -> use a fixed shell height with independently scrollable body and compact rows; verify 360px, 390px, and 430px widths.
- Keyboard can cover the bottom search footer -> use existing visual-viewport and keyboard inset variables; keep the body `min-height: 0` and footer outside the scroll body.
- Catalog root data may be slow or incomplete -> show local loading rows and allow search mode without blocking on full catalog load.
- Search results may include non-point targets -> filter to bindable point placements for the picker so the one-chat-one-point rule stays clear.
- Existing search result mapping logic may be route-oriented -> extract or reuse a small mapping helper that builds `AssistantContext` without navigating.
- History restore can reintroduce old contexts -> store and restore the selected/bound context with the existing local history entry; global history rows should continue to label global chats separately.
- Student may want to switch after asking -> keep the read-only chip clear and make the new-chat path obvious; do not silently mutate the existing chat context.

## Migration Plan

1. Add the picker behind the existing root composer `+` action.
2. Keep the default global `learning_home` behavior unchanged when the student dismisses the picker or sends without selecting a point.
3. Reuse existing APIs first; add only frontend mapping/helpers unless implementation proves a missing data field.
4. Update local history persistence/restoration to include the selected context if it is not already preserved by the existing `activeContext` snapshot.
5. Rollback is safe by hiding the picker trigger behavior and returning `+` to its current no-op/context-active behavior.

## Open Questions

- Which exact chapter/profile roots should appear first in the default catalog forest: all enabled student learning profiles, the recommended profile first, or a recent/current profile first?
- Should the picker show a small "current recommendation" or "recently viewed" section above the catalog roots, or should it stay purely directory-first?
- Should a locked bound chip offer a "new chat with another point" shortcut, or rely on the existing new-chat action?

## Context

The Atom root assistant already uses a fullscreen, light chat canvas with a centered Atom title, root-only history/new-chat actions, a welcome group, dynamic follow-up chips, and a bottom composer. The current root AI page has two separate visual issues that should be solved together:

1. The title row reads as a hard page header instead of a translucent mobile chat overlay.
2. Successful assistant replies render as white cards, which constrains long educational answers and repeats assistant/status chrome inside every reply.

The intended surface is a continuous Atom learning assistant page. User questions should still read as compact right-aligned green bubbles. Atom replies should read as content on the canvas, using the background as the primary surface. Each assistant turn should be separated by a lightweight action row, not by a card boundary.

The root panel background contains warm paper, pale yellow-green, and sage-green glows. Re-copying that full background into the header or message blocks would create duplicated coordinate systems and visible seams. The root assistant canvas must remain the single background source of truth.

## Goals / Non-Goals

**Goals:**

- Make the root Atom title row read as a translucent chat overlay rather than a hard page header.
- Keep the header title and root actions fully opaque, stable, and touch-safe.
- Use a root-only alpha-gradient veil whose opacity is strongest near the safe-area/top edge and fades to transparent at the lower edge of the header.
- Keep the actual root assistant background painted only once by the root panel/canvas.
- Wrap the root history and new-chat actions in one compact real-background capsule so those controls remain legible over moving content.
- Convert successful root assistant replies from white cards into flat full-width text turns on the root canvas.
- Keep user messages as right-aligned green bubbles.
- Use a lightweight assistant turn action row as the primary visual delimiter between assistant replies and subsequent conversation content.
- Keep safe citation disclosure visible as a right-aligned citation-count affordance, not as raw source details.
- Keep dynamic follow-up chips tied only to the latest successful assistant reply and visually placed after that reply's action row.
- Preserve the existing welcome, composer, keyboard-aware layout, local history, bottom navigation, streaming API, and contextual `/ai/chat` behavior.

**Non-Goals:**

- Do not copy the root panel radial-gradient glow stack into the header, reply blocks, or action rows.
- Do not use `opacity` on the whole header or whole reply group if that would fade foreground text or controls.
- Do not use `backdrop-filter` blur as the primary root header veil effect.
- Do not redesign the root composer, compact/expanded state machine, `61.8%` growth rule, keyboard-active behavior, prompt generation, history storage, or assistant API calls.
- Do not expose raw RAG/chunk/source titles, sections, scores, trace details, or teacher-only data in the student reply action row.
- Do not wire thumbs up/down to a new backend endpoint in this change. First implementation may use local UI state only. A later change can define analytics or durable feedback if needed.
- Do not apply the flat root reply style to contextual `/ai/chat` detail pages unless explicitly requested later.
- Do not introduce a dark theme or external product controls.

## Current Structure

Current root assistant rendering is concentrated in `StudentAiChatPanel`:

- Each message renders as `.ai-message`.
- User messages render as `.ai-message.user` with a right-aligned green bubble.
- Assistant messages render as `.ai-message.assistant` with a white background, border, rounded card, status/meta row, Markdown body, and optional source summary.
- `AssistantSourceSummary` currently displays only a citation count label and intentionally avoids raw source fields.
- `latestSuggestedPrompts()` already ensures dynamic chips are only visible after a successful latest assistant response and hidden while loading or after error.
- The root composer and keyboard-aware layout have dedicated measuring logic and route-level classes that should not be disturbed.

## Target Structure

The root message stream should conceptually render turns like this:

```text
Root chat stream
  User turn
    .ai-message.user
      right-aligned green bubble

  Assistant turn, running
    .ai-message.assistant.running
      lightweight Atom running status
      streaming Markdown text or skeleton

  Assistant turn, done
    .ai-message.assistant.done
      full-width flat Markdown body
      .ai-message-actions
        left: thumbs up, thumbs down, copy, more
        right: citation count pill when metadata says sources exist

  Latest successful follow-up chips
    .ai-quick-prompts
```

The DOM does not need to introduce a new persisted message type. It may keep the existing `StudentAiChatMessage` shape and render assistant messages with additional action-row markup derived from role/status/metadata.

## Decisions

1. **Keep root user messages as bubbles.**

   - Decision: `.ai-message.user` remains a right-aligned green bubble with constrained max width.
   - Rationale: The user prompt should be visually compact and distinct. It provides the "question" anchor in the conversation.

2. **Make successful root assistant replies flat and full width.**

   - Decision: For the root variant, `.ai-message.assistant.done` should remove white card background, border, card shadow, and tight card padding. It should use available stream width with controlled inline padding and typographic rhythm.
   - Rationale: Long chemistry explanations, lists, formulas, and Markdown paragraphs need reading width. The root canvas already provides the surface.
   - Scope: This applies to successful root assistant replies. Detail-route assistant cards may remain unchanged unless later explicitly scoped.

3. **Use the action row as the assistant turn delimiter.**

   - Decision: Each successful root assistant reply should render a low-contrast action row below the Markdown body.
   - Rationale: Removing card boundaries requires a new delimiter. The action row communicates both "this turn ended" and "you can act on this answer."
   - Shape: left cluster contains icon buttons; right cluster contains citation count if present.
   - Buttons: first implementation should include thumbs up, thumbs down, copy, and more. Speech/share can be deferred or placed behind more if not needed immediately.

4. **Do not show the full assistant identity/status chrome after success.**

   - Decision: The repeated "Atom learning assistant / completed" meta row should not be shown on every successful root reply.
   - Rationale: On a flat surface it wastes space and visually recreates a card header. The root page title already establishes the assistant identity.
   - Exception: Running and error states still need status affordances.

5. **Keep running state lightweight.**

   - Decision: The active assistant reply may show a small running indicator and/or "generating" status above the streaming body.
   - Rationale: During streaming, the student needs feedback that Atom is working. Once final succeeds, the status should collapse into the flat reply/action-row pattern.

6. **Keep failure state clearly bounded.**

   - Decision: Error assistant turns may remain in a visually distinct error block.
   - Rationale: Errors are exceptional states and should not blend into the flat answer text. This also preserves the prior debugging/product decision that failed turns do not show dynamic chips.

7. **Move safe citations into the action row.**

   - Decision: `AssistantSourceSummary` should become or feed a compact right-side citation affordance, e.g. `Sources 2` or `References 2`, scoped to student-safe count-only display.
   - Rationale: The student role-boundary tests currently prevent exposure of raw `chunk_id`, title, section, or score. The action-row right side is enough to signal grounding without leaking details.
   - Future: If detailed citation drawers are desired, they need a separate source-safety spec.

8. **Keep dynamic follow-up chips after the latest assistant turn.**

   - Decision: Chips remain outside the message itself, below the latest completed assistant action row and above the composer.
   - Rationale: They are next-turn affordances, not metadata inside the answer. This matches the existing behavior: only the latest successful reply matters, and older suggestions are ignored.

9. **Keep root/detail route separation.**

   - Decision: Flat reply styling and root action rows are root-only unless explicitly safe to share.
   - Rationale: Contextual `/ai/chat` pages live inside detail route constraints and may need their current card affordance for context boundaries.
   - Implementation: Use root variant classes such as `.ai-chat-panel.root` to scope CSS and JSX branches.

10. **Make the root header an overlay layer, not a blocking grid row.**

   - Decision: Scope root header styling so `.ai-chat-head.root` is positioned above the root chat surface and no longer visually depends on a hard opaque grid-row background.
   - Rationale: A fade header only matters if root chat content can exist behind it. If the header continues to push the stream down as an opaque layout row, transparency reveals only empty page background.

11. **Drive root header spacing from explicit layout states.**

   - Decision: The root panel should expose explicit layout states for empty welcome, no-message draft, and conversation/restored-message content, using classes, data attributes, or equivalently specific selectors.
   - Rationale: Empty welcome layout, draft-without-messages layout, and conversation scroll layout need different spacing. A single `.ai-chat-panel.root .ai-chat-stream` padding rule makes the empty state inherit message-only header spacing, which creates false scrollbars and pushes the welcome/composer region out of the established arrangement.
   - Shape:
     - Empty welcome: preserve the established welcome placement and avoid conversation-only header top padding.
     - No-message draft: hide the welcome according to the existing input rule while preserving composer geometry and header protection.
     - Conversation/restored-message: apply header-safe top padding or `scroll-padding-top` so messages can pass behind the veil without being hidden at rest.

12. **Use a pseudo-element veil instead of header opacity.**

   - Decision: Add a root-only background layer such as `.ai-chat-head.root::before` with a vertical `linear-gradient()` from warm light opacity to transparent.
   - Rationale: The veil can soften underlying content while title text and actions remain fully opaque.

13. **Do not duplicate the root background in the header.**

   - Decision: The header veil must use a simple semi-transparent warm-light gradient, not the full root radial-gradient background stack.
   - Rationale: Full gradient duplication uses the header box as its own coordinate system, so glows can drift relative to the root background.

14. **Protect root header actions with one compact capsule.**

   - Decision: The root history and new-chat actions should sit inside one compact capsule with two equal action cells.
   - Rationale: The right-side controls need local protection above variable content. A single capsule is visually calmer than two isolated cards.

15. **Use an alpha-only root header veil.**

   - Decision: The accepted root header veil uses translucent gradient opacity stops and does not apply `backdrop-filter` blur.
   - Rationale: The desired visual is sharp underlying content becoming progressively less visible toward the top, not blurred content. Removing blur also avoids fuzzy title/content artifacts and keeps the header chrome visually crisp.
   - Shape: Keep the title and action capsule above the veil layer, then tune top, mid, low, and transparent alpha stops on the veil itself.

16. **Make overlay selectors win the real CSS cascade.**

   - Decision: Root overlay selectors must be specific enough to override generic root foreground-layer rules that set `position`, `z-index`, or pointer behavior.
   - Rationale: A lower-specificity `.ai-chat-head.root` rule can look correct in static source tests while losing to a higher-specificity `.ai-chat-panel.root .ai-chat-head` rule in the browser. Regression protection must verify the scoped/cascade contract, not only that desired declarations exist somewhere in the file.

17. **Hide root stream scrollbar chrome without disabling scroll.**

   - Decision: The root conversation stream keeps internal scrolling for conversation/restored-message content, but hides persistent desktop scrollbar chrome in preview/iframe environments.
   - Rationale: The teacher preview embeds the mobile student page inside a desktop browser context, where the nested stream scrollbar can appear over the phone canvas. The mobile UI should still scroll; the desktop chrome is not part of the intended phone surface.
   - Scope: Apply this only to the root assistant stream. Do not hide all student scrollbars globally, and do not change composer textarea scrolling.

## Interaction Details

- **Thumbs up/down:** First implementation may store per-turn state in React state only. Selecting one should visually toggle that choice and clear the opposite choice. No history persistence is required unless later specified.
- **Copy:** Copy the assistant turn plain text to the clipboard. If clipboard API fails, use an existing fallback pattern if available. The copy control should expose an accessible label and a transient copied state if practical.
- **More:** Reserve for future actions or use a lightweight menu if already available. If no menu is implemented in the first pass, the button can be hidden until there is an action behind it.
- **Citation affordance:** Render only when `metadata.source_count` or sanitized `metadata.sources.length` is positive. Display count only.
- **Dynamic chips:** Keep disabled while loading. Hide after failed turns. Show only if latest successful metadata contains sanitized suggestions.

## Typography and Layout

- Flat assistant Markdown should retain the established Atom body font variables:
  - `--ai-chat-body-font-size`
  - `--ai-chat-body-line-height`
  - `--mobile-font-family`
- Flat replies should use enough vertical rhythm for paragraphs, bullet lists, formulas, and code spans without relying on a card interior.
- Inline width should avoid edge collision with the phone frame, header overlay, composer, and scrollbar gutter.
- User bubbles should keep a stable max width so long user questions do not become full-screen blocks.
- Action row buttons should use icon-only controls with accessible names and phone-appropriate hit targets.
- The action row should be low contrast and not read as a new card. It can use transparent or lightly tinted backgrounds for individual icon hit areas.

## Risks / Trade-offs

- [Risk] Removing assistant cards can make turn boundaries ambiguous. -> Mitigation: action row becomes the explicit delimiter, with spacing around each assistant turn.
- [Risk] Full-width assistant text can collide visually with phone edges. -> Mitigation: keep root stream inline padding and safe max-width rules.
- [Risk] The action row can become cluttered. -> Mitigation: start with a minimal left cluster and place less common actions behind More or defer them.
- [Risk] Copy action may require fallback handling on restricted mobile browsers. -> Mitigation: reuse the existing clipboard fallback shape from mobile debug if needed.
- [Risk] Raw source fields may leak if citation UI becomes too ambitious. -> Mitigation: display count only in this change; keep role-boundary tests.
- [Risk] Dynamic chips can feel attached to the wrong turn after layout changes. -> Mitigation: place chips after the latest assistant action row and preserve latest-only logic.
- [Risk] Root styles can leak into contextual `/ai/chat`. -> Mitigation: scope selectors to `.ai-chat-panel.root` and add route-separation checks.
- [Risk] Header overlay and flat messages can overlap badly near scroll top. -> Mitigation: tune root stream top safe spacing and QA empty, one-message, restored-history, and scroll-near-top states.
- [Risk] Empty welcome and conversation messages require different header spacing. -> Mitigation: use explicit root layout states and apply header-safe stream padding only to the conversation/restored-message state.
- [Risk] Static CSS tests can pass while browser cascade chooses a higher-specificity generic rule. -> Mitigation: remove header from generic root foreground-layer selectors or use a stronger scoped overlay selector, then test that cascade contract directly.
- [Risk] Keyboard-active layout may regress. -> Mitigation: do not change composer measurement logic; verify focused keyboard states.
- [Risk] Blur can make the title or underlying text look smeared instead of translucent. -> Mitigation: use an alpha-only veil and test that no header `backdrop-filter` is present.
- [Risk] Desktop teacher preview can show an internal chat scrollbar over the phone canvas. -> Mitigation: hide scrollbar chrome only on the root chat stream while preserving overflow scrolling.

## Migration Plan

1. Add CSS variables for root header height, veil color stops, z-index, action capsule sizing, flat assistant inline padding, and action-row spacing.
2. Add explicit root panel layout state hooks for empty welcome, no-message draft, and conversation/restored-message content.
3. Convert the root header to an overlay layer with a selector that wins over generic root foreground-layer rules, while preserving existing JSX semantics and handlers.
4. Add the root header pseudo-element veil with a simple warm-light alpha gradient, no blur dependency, and no duplicated radial background.
5. Scope header-safe stream padding or scroll-padding to the conversation/restored-message state only; keep empty welcome and no-message draft states out of message scroll spacing.
6. Restyle `.ai-root-actions` as one capsule with two equal cells.
7. Update root assistant message rendering so successful assistant replies omit the repeated meta row and render as flat full-width Markdown.
8. Add an assistant action row component for successful root assistant replies.
9. Move safe citation count rendering into the action row's right side.
10. Add local UI state for thumbs up/down if feedback controls are included.
11. Add copy behavior for assistant turn text.
12. Keep running and error states visually distinct and keep dynamic chips hidden during loading/error.
13. Preserve root quick prompts after the latest completed assistant turn and above the composer.
14. Verify contextual `/ai/chat` retains current detail behavior.
15. Hide root conversation stream scrollbar chrome in desktop/iframe preview contexts while preserving internal scroll.
16. Update focused tests and mobile viewport QA, including cascade-sensitive CSS checks, alpha-only veil checks, hidden-scrollbar checks, and empty/draft/conversation viewport checks.

## Open Questions

- Should the first implementation show only thumbs up/down/copy, or also More as a visible but inactive reserved affordance? Recommendation: include only controls with behavior, unless product wants a visual placeholder.
- Should copy state show a toast, transient icon state, or no visible feedback? Recommendation: transient icon/label state is enough.
- Should citation count text be localized as "References", "Sources", or the existing Chinese label? Recommendation: keep the existing product copy semantics and only move placement.
- Should feedback eventually submit to the `ai_answer` student feedback type? Recommendation: separate change, because durable feedback needs payload shape, preview behavior, and admin review semantics.

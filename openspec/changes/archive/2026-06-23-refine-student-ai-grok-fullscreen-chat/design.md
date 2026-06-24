## Context

The previous student AI root implementation preserved the route/history split, but visually it still behaved like a centered card page. The user-provided target is closer to X/Grok mobile: a top identity area, large uninterrupted chat canvas, low starter prompt, and a bottom composer that sits above the app bottom navigation.

External UI research used for this pass:

- Grok mobile examples show a sparse mobile chat surface with a top title, history/menu/new-chat affordances, an "Ask anything" composer near the bottom, and a large empty canvas before the first turn.
- ChatGPT mobile patterns center the first interaction around a bottom message bar and lightweight suggestion chips, with history reachable through navigation rather than embedded intro cards.
- Gemini mobile examples use a simple greeting plus suggested actions above the bottom prompt box; recent Gemini redesign coverage emphasizes fullscreen navigation/history surfaces rather than card-heavy centers.
- Claude and general AI chat interface critiques reinforce the same baseline: the chat screen should prioritize input, readable conversation state, and restrained onboarding copy.

The student app constraints differ from those products: this app must not expose upload, voice, model selection, or external account controls in this round. It must also keep the chemistry-learning tone and bottom tab navigation.

## Goals / Non-Goals

**Goals:**

- Make `/ai` look and behave like a fullscreen mobile chat start, not a card-based landing center.
- Keep the header/identity copy minimal and anchored near the top, with history as a single icon action.
- Keep a large calm empty middle area and place the starter prompt block low, close to the composer.
- Keep the composer visible on first load, above the bottom nav, with only text input and send.
- Keep `/ai/chat` as the contextual second-level chat page, visually related but without the root history action.
- Preserve local history, streaming, and restored `conversation_history` behavior from the previous implementation.

**Non-Goals:**

- Do not add attachment upload, model selection, voice input, image generation shortcuts, or external Grok/X navigation.
- Do not redesign unrelated student root tabs.
- Do not introduce backend-persisted chat sessions in this round.
- Do not implement dark mode just because Grok screenshots often use dark mode; match the current chemistry course visual system.

## Decisions

1. **Root `/ai` becomes a full-bleed chat canvas inside the route content**
   - The route content will remove the inherited centered card feel for the AI root.
   - The assistant panel will use `width: calc(100% + route padding)` and negative margins where needed to visually occupy the available phone width.
   - Alternative considered: keeping the bordered panel but reducing radius. Rejected because the user explicitly asked for no card and full occupancy.

2. **Use one low prompt block instead of starter cards or prompt grids**
   - The empty state keeps a single compact prompt block near the composer.
   - This matches Grok/ChatGPT/Gemini first-screen rhythm without reintroducing complex starter choices.
   - Alternative considered: multiple suggestion chips. Rejected for this pass because the target screenshot has one low prompt block and the user already asked to simplify prompts.

3. **History remains root-only and icon-only**
   - `/ai` keeps the history action in the top-right area of the chat canvas.
   - `/ai/chat` does not render history chrome, preserving the separation between root chat and contextual handoff.
   - Alternative considered: global history in detail. Rejected because the user explicitly wants history accessed from the main AI page.

4. **Keep chemistry tone through text, not heavy cards**
   - Copy can say "课程 AI", "AI 学习助手", and concise course support text.
   - Visual identity comes from the current green/grid learning motif, but the grid must be a background plane, not a framed card.

5. **Verification must inspect layout geometry**
   - Tests should assert root vs detail class contracts and unsupported controls absence.
   - Mobile viewport checks should verify composer/nav vertical separation and absence of horizontal overflow.

## Risks / Trade-offs

- Full-bleed AI root may differ from other root tabs that use centered panels → limit the exception to `.ai-root-page` and `.assistant-tab-panel.root`.
- Negative margins can introduce horizontal overflow → add automated checks for document width and viewport width.
- Low prompt block could still read like a card if styled too heavily → keep border/shadow minimal and avoid nested sections.
- Detail chat may inherit too much root styling → keep `root` and `detail` classes explicit and tested.

## Context

The current student Atom composer is a single textarea with an absolutely positioned send button. That worked for the first Grok-like pass, but it makes the input text and actions share the same physical area. As soon as the textarea grows or scrolls, the text can visually compete with the send button and there is no stable area for future supported chat actions.

The desired behavior follows the Gemini-style composer grammar:

```
compact state
┌──────────────────────────────────────┐
│  +    Ask / typed one-line text   send│
└──────────────────────────────────────┘

expanded state
┌──────────────────────────────────────┐
│ multi-line textarea                  │
│ textarea may scroll when long        │
├──────────────────────────────────────┤
│  +                              send │
└──────────────────────────────────────┘
```

The bottom workbench is the visual anchor. The textarea may grow upward or scroll internally, but it must never push, overlap, or resize the `+` action or send action.

There is an active `student-ai-dynamic-followup-prompts` change that owns model-generated prompt chips after successful assistant turns. This change should not change that backend/frontend prompt contract. It only creates the composer workbench surface that can later host supported composer-level abilities.

## Goals / Non-Goals

**Goals:**

- Preserve the current Atom root chat behavior in empty and one-line input states.
- Introduce a stable bottom workbench row inside the composer for `+` and send actions.
- Let the composer shape transition from race-track capsule to rounded rectangle only when text exceeds one-line capacity.
- Keep the textarea in the upper zone once expanded so typed content never occupies the workbench zone.
- Keep `+` and send positions invariant across compact, expanded, scrollable, keyboard-active, loading, and restored-history states.
- Define `+` as a supported "inject background knowledge" action for course/video/point context, not an upload or attachment affordance.
- Preserve the existing keyboard-aware visible-viewport behavior and apply the `61.8%` growth cap to the outer composer height.
- Keep compact-mode text visually centered on the same row as the `+` action and send action, with root composer text using the same font sizing in compact, expanded, and scrollable states.

**Non-Goals:**

- Do not implement file upload, attachment selection, microphone input, voice waveform input, model selection, image generation, or arbitrary external tools.
- Do not change the student assistant streaming API.
- Do not change model-generated follow-up prompt chips from `student-ai-dynamic-followup-prompts`.
- Do not redesign the top title bar, welcome phrase, history panel, local history store, or message rendering.
- Do not merge root `/ai` and contextual `/ai/chat` route semantics.

## Decisions

1. **Use a two-zone composer structure instead of absolute overlays.**

   - Decision: Treat the composer as a container with an input zone and a workbench zone. The send action lives in the workbench, not over the textarea.
   - Rationale: The invariant is structural: text cannot overlap controls if the controls are not part of the textarea's layout area.
   - Alternative considered: keep the absolute send button and add extra textarea padding. This is fragile because padding still changes perceived text width and does not create a real expansion surface for `+`.

2. **Drive the visual mode from measured text capacity, not just focus.**

   - Decision: The composer stays compact while the textarea content fits the one-line compact lane. It enters expanded mode when content would require a second line.
   - Rationale: Focus alone should not make the composer jump. Empty focus and one-line typing should preserve the current successful compact feel.
   - Alternative considered: expand on focus. This creates unnecessary movement and makes the first screen feel heavier.

3. **Use compact-lane measurement as the canonical expansion threshold.**

   - Decision: The compact-to-expanded decision is measured with the compact race-track text lane width even while the composer is currently expanded. A hidden measurement textarea may mirror the visible textarea typography, one-row configuration, padding, and compact lane width to provide this canonical scroll-height signal.
   - Rationale: The compact and expanded states have different text widths. If the current rendered textarea decides the next state, boundary-length text can expand because it wraps in compact mode, then immediately collapse because the wider expanded textarea no longer wraps.
   - Constraint: The hidden compact measurement textarea MUST explicitly use `rows=1`; relying on the browser default `rows=2` makes even single-character input look taller than the compact threshold after typography changes.
   - Alternative considered: add hysteresis around the current textarea scroll height. This reduces flicker but leaves the rule device-dependent and still tied to the wrong width.

4. **Keep the existing growth cap, but apply it to the whole composer.**

   - Decision: The outer composer height, including textarea/input zone, padding, and workbench row, MUST stay within the existing `~61.8%` effective panel-height cap. The textarea/input zone receives the remaining height after composer padding and the fixed workbench row are reserved, then becomes internally scrollable.
   - Rationale: This preserves the keyboard work from the previous change while keeping the visual budget honest. If the cap only applies to the textarea, the final composer can exceed the intended height once the workbench and padding are added.
   - Alternative considered: let the entire composer scroll. This would hide or move the actions and breaks the visual anchor.

5. **Use one root composer text scale across all states.**

   - Decision: The compact placeholder/typed text, expanded typed text, and scrollable typed text use the same root composer font size and line-height. Compact mode vertically centers that line in the race-track lane so it reads on the same row as the `+` action and send action.
   - Rationale: The compact state is the first-read visual. Smaller inherited textarea text makes the composer look like a generic form field instead of a chat input surface.
   - Alternative considered: use a smaller compact placeholder and larger expanded textarea. That creates a visible jump when crossing the one-line threshold.

6. **Make workbench controls position-invariant.**

   - Decision: The `+` action sits at the left edge of the workbench and send sits at the right edge. Their visual centers should remain stable for a given viewport width across all composer modes.
   - Rationale: The user's strongest invariant is that `+` and send never drift when the chat box changes state.
   - Alternative considered: align controls to the textarea baseline in compact mode and to the workbench in expanded mode. This produces subtle jumps at the exact moment the composer expands.

7. **Define `+` as context injection, not attachment.**

   - Decision: The `+` action represents "inject available background knowledge" from the current learning context, such as video point, catalog point, or page context.
   - Rationale: This gives the icon a product-specific meaning and avoids implying unsupported file upload.
   - Alternative considered: hide `+` until a background-knowledge picker exists. That would delay the visual grammar and make the compact composer diverge from the reference layout.

8. **Keep route variants distinct.**

   - Decision: The root Atom composer is the primary target. Contextual `/ai/chat` may reuse the underlying component pattern only if it preserves detail-route navigation, context, and no-root-history behavior.
   - Rationale: Earlier work separated root history and contextual chat. This change should not erase that boundary.
   - Alternative considered: force the same root workbench everywhere. That risks leaking root-only actions or visual assumptions into second-level pages.

9. **Unify chat body reading and writing typography.**

   - Decision: The root composer textarea, message bubble body text, and Markdown paragraph/list body text share one chat body typography token: the mobile large text size (`17px`) with a comfortable reading line-height (`1.52`) and the app mobile font family.
   - Rationale: The previous `22px` composer text read like a heading, while `14px` message body read like secondary copy. The student is reading and writing the same conversational content, so these surfaces should feel like one text system.
   - Alternative considered: use the arithmetic midpoint `18px`. This is visually plausible, but it creates a one-off font size outside the existing mobile token scale. `17px` keeps the system tokenized while still moving both surfaces toward the same center.
   - Scope note: Titles, status labels, metadata, badges, quick prompt chips, and code snippets keep their specialized typography roles.

## Risks / Trade-offs

- [Risk] The compact-to-expanded threshold can be noisy across fonts and devices. -> Mitigation: derive it from measured textarea scroll height/line height and cover it with viewport tests that mock one-line and multi-line scroll heights.
- [Risk] Boundary-length text can oscillate if measurement follows the current textarea width. -> Mitigation: use compact-lane width as the canonical threshold measurement in both compact and expanded modes.
- [Risk] A hidden measurement textarea can accidentally use browser defaults that differ from the visible composer. -> Mitigation: force the measurement textarea to mirror the visible compact textarea's `rows=1` configuration and cover single-character compact input in tests.
- [Risk] Raising message body text can make bubbles feel heavier. -> Mitigation: limit the change to conversational body text and preserve smaller typography for metadata/status labels.
- [Risk] The workbench row can make expanded composer height feel too large above the keyboard. -> Mitigation: keep the workbench compact and subtract its reserved height from the textarea's growth budget.
- [Risk] Users may interpret `+` as file upload. -> Mitigation: accessible label and any future popover copy must say background knowledge/context, not attachment/upload.
- [Risk] Dynamic follow-up prompt chips could visually compete with the workbench. -> Mitigation: keep post-turn prompt chips outside the composer; the workbench is for pre-send composer actions only.
- [Risk] Detail chat might inherit root-only behavior accidentally. -> Mitigation: test root and detail variants separately, including history/new-chat action visibility and route chrome.

## Context

The root Atom assistant recently moved successful assistant replies to a flat canvas turn: completed assistant text no longer appears inside a white card, and the action row now acts as the turn delimiter. The running state did not receive the same treatment. Today the active assistant turn still inherits the generic assistant card shell, renders the repeated `Atom 学习助手 / 生成中` meta row, shows a pill-like `.ai-stream-progress`, and falls back to a skeleton while no answer text has arrived.

The desired interaction is closer to Gemini's thinking status pattern:

```text
   dots    phase text
   . . .   正在判断问题范围
           old label fades away
   . . .   正在检索课程资料
           next label fades in
   . . .   正在生成回答
           answer text starts streaming
```

This is not a typing animation and not a continuously blinking label. The text behavior is a phase replacement transition, commonly described in motion systems as a fade-through transition: outgoing content fades out, incoming content fades in, and the replacement is keyed to a semantic state change rather than time alone.

The existing backend already streams enough state for this:

- `/api/student/assistant/ask/stream` emits `status`, `delta`, `replace`, `final`, and `error` events.
- `status` messages such as `正在判断问题类型与安全策略` already reach `StudentAiChatPanel`.
- `assistantStreamPhaseLabel(status, hasAnswer)` already normalizes raw status text into student-facing labels such as `正在判断问题范围`, `正在检索课程资料`, `正在返回学习建议`, and `正在生成回答`.

The change should therefore be frontend-only and should preserve the existing stream contract.

## Goals / Non-Goals

**Goals:**

- Make the root Atom running assistant turn visually consistent with flat successful replies.
- Replace the card-like running surface with a lightweight inline thinking line.
- Preserve semantic phase feedback so students can tell Atom is judging scope, retrieving course material, returning suggestions, or generating the answer.
- Animate phase label replacement with a true fade-through effect.
- Keep the dots animated continuously while the status text changes independently.
- Remove the thinking line when the turn completes successfully.
- Keep failed turns visibly bounded.
- Keep contextual `/ai/chat` behavior distinct unless a later change explicitly changes it.
- Respect reduced-motion preferences.

**Non-Goals:**

- Do not change the student assistant backend API, SSE event names, request payloads, or final metadata shape.
- Do not introduce Lottie, Motion, Framer Motion, GSAP, or another animation dependency.
- Do not copy Gemini branding, colors, or exact asset geometry.
- Do not change successful answer markdown rendering, action row behavior, citation privacy, local history, quick prompt logic, or composer measurement.
- Do not redesign teacher/admin learning-assistant running states.
- Do not add durable assistant feedback or server-side chat sessions.

## Decisions

1. **Use a root-only flat running surface.**

   Root running assistant messages should use the same flat canvas family as successful replies: full-width, no white card, no card border, no card shadow, and no repeated meta row. This keeps the conversation visually coherent from waiting state to final answer.

   Alternative considered: keep the running card but restyle the pill. Rejected because it preserves the old visual hierarchy and keeps the most visible waiting state inconsistent with the completed answer surface.

2. **Represent waiting with a thinking line, not a skeleton.**

   The running turn should render one inline line with an animated dot cluster and one phase label. If answer text has not started streaming, this line is the waiting affordance. Once answer text exists, the same line can remain above the streaming answer with a generating label until final completion.

   Alternative considered: keep the existing skeleton below the phase label. Rejected for root because skeleton blocks read as a card-era loading component and compete with the desired text-first thinking line. Detail route may keep existing skeleton behavior.

3. **Treat phase text changes as keyed semantic transitions.**

   The text should animate only when the normalized phase changes. The transition should be fade-through:

   ```text
   previous phase visible
   0ms      outgoing text starts opacity 1 -> 0
   140ms    outgoing text is gone
   90ms     incoming text is still held at opacity 0
   90ms     incoming text starts opacity 0 -> 1
   350ms    incoming text settles fully visible
   420ms    local transition cleanup may remove the outgoing node
   ```

   A small `translateY(3px -> 0)` and optional `filter: blur(2px -> 0)` can be used on incoming text if it stays subtle. The outgoing text may move by `-1px` to `-2px` or remain still. The effect should feel like the next stage "appears" after the previous one clears, not like a simultaneous crossfade.

   Alternative considered: animate only the new text from opacity 0 to 1. Rejected because the user-observed effect includes the old phrase disappearing first. A true fade-through needs either a tiny local transition state that keeps the outgoing label mounted briefly, or an equivalent stacked text implementation.

   Follow-up interaction QA showed that a technically valid but simultaneous `outgoing`/`incoming` animation was too subtle to perceive. Later comparison against public Material fade-through behavior suggested the text replacement itself should stay quick and clean, while the semantic phase should remain visible long enough to be noticed. The root thinking line should therefore apply a minimum visible duration per semantic phase, currently about `1400ms`, and keep the incoming label animation short, currently about `260ms` with a `90ms` delay. This makes fast SSE status changes feel like staged thinking without turning the text fade itself into a slow dissolve.

4. **Keep dot animation independent of label replacement.**

   The dot cluster should continue animating while phase text changes. Dots should not restart on every label change unless the visual restart is imperceptible. A CSS-only dot cluster is enough: three small dots can use staggered opacity and transform keyframes to approximate a Gemini-like thinking constellation.

   Alternative considered: embed the captured SVG/Lottie snippet. Rejected because it increases asset coupling, is harder to theme, and is unnecessary for three small dots.

5. **Normalize phase labels before animating.**

   Raw backend status strings should not be used as the animation key. The UI should animate on a small normalized phase key so similar raw messages do not cause distracting churn:

   | Phase key | Student label | Triggers |
   | --- | --- | --- |
   | `scope` | `正在判断问题范围` | raw status includes 判断, 安全, 问题, 策略 |
   | `retrieval` | `正在检索课程资料` | raw status includes 检索, 课程, RAG, 资料, 证据 |
   | `returning` | `正在返回学习建议` | raw status includes 返回 |
   | `generating` | `正在生成回答` | answer text exists, model connection starts, fallback generation starts, or no more specific phase applies |

   If answer text exists, `generating` should win because the student's visible experience has moved from preparation into answer generation.

6. **Use the product's Atom colors, not Gemini's dark theme.**

   The reference screenshots use white dots and white text on black. Atom runs on a warm pale learning canvas, so the thinking line should use Atom text variables and muted green/ink tones. The motion can be inspired by Gemini; the visual language should remain Atom.

7. **Use `aria-live` carefully.**

   The thinking line should expose the current phase to assistive technology with polite live updates. Dots should be `aria-hidden`. The animated visual text should avoid producing duplicate announcements if two spans are mounted for fade-through; only the active label should be live-readable.

8. **Reduced motion disables movement, not meaning.**

   Under `prefers-reduced-motion: reduce`, dot transforms and text movement should stop. The UI may keep static dots and instant or simple opacity-only label replacement. The phase label must remain visible and current.

9. **Final completion removes running-only chrome.**

   On `final`, the running thinking line must disappear. The successful root assistant turn should render the existing flat markdown and action row only. This prevents a completed answer from keeping a stale success header.

10. **Error remains bounded.**

    If the request fails, the failed assistant turn may keep a distinct error block or bounded treatment. It should not render the successful action row and should not render quick prompt chips.

## Risks / Trade-offs

- [Risk] Fade-through can become distracting if raw status changes are frequent. -> Mitigation: animate only normalized phase key changes, not every raw status string.
- [Risk] Keeping outgoing and incoming labels mounted can confuse screen readers. -> Mitigation: hide outgoing visual text from assistive tech or expose only one atomic live label.
- [Risk] Removing skeleton may make long pre-answer waits feel too empty. -> Mitigation: the thinking line remains explicit and the phase label should be specific; if later user testing needs more weight, add subtle line spacing rather than a skeleton.
- [Risk] Dots can look like loading chrome from a different product. -> Mitigation: use Atom colors, sizing, and spacing; do not copy Gemini's exact dark theme or brand geometry.
- [Risk] Running flat styles may leak into `/ai/chat`. -> Mitigation: scope all flat thinking selectors to `.ai-chat-panel.root`.
- [Risk] CSS-only fade-through may not produce a true outgoing animation if the old text unmounts immediately. -> Mitigation: implement a small transition state or stacked label pair so the outgoing text can animate before removal.
- [Risk] Static tests can assert source text but miss the cascade. -> Mitigation: add role-boundary/static CSS checks and an e2e DOM check for root running turns.

## Migration Plan

1. Introduce a root-only thinking-line component or render branch inside `StudentAiChatPanel`.
2. Derive a stable phase key and label from the existing `status` plus `hasAnswer` state.
3. Replace root running meta row, progress pill, and skeleton with the thinking line.
4. Add local text transition state so old phase text can fade out before the new label fades in.
5. Add CSS for flat root running messages, dot motion, fade-through text, and reduced-motion fallback.
6. Preserve detail route selectors and existing detail running visuals.
7. Add focused tests for root running shape, phase label transition semantics, final cleanup, hidden chips, and route scoping.
8. Run student frontend tests and mobile QA for common phone widths.

Rollback is frontend-only: revert the component/style/test changes and root running turns return to the prior card/pill/skeleton behavior. No data migration or backend rollback is required.

## Open Questions

- Should the root thinking line stay visible above streaming text until final, or disappear as soon as the first answer token arrives? Recommendation: keep it visible with `正在生成回答` until final so students retain a clear running affordance.
- Should `正在连接模型` be a visible student phase? Recommendation: no for the first pass; normalize model connection and fallback into `正在生成回答` to avoid implementation-flavored copy.
- Should the fade-through include blur? Recommendation: allow a very subtle blur on incoming text, but keep opacity and small vertical motion as the core so low-end mobile browsers remain smooth.

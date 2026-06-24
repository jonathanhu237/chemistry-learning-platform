## 1. Phase Model

- [x] 1.1 Add a small root assistant phase model that returns a stable phase key and student-facing label from the existing stream `status` and `hasAnswer` state.
- [x] 1.2 Keep current status event handling and backend SSE payloads unchanged.
- [x] 1.3 Ensure answer text presence normalizes the running phase to `正在生成回答`.
- [x] 1.4 Ensure missing, unknown, model-connection, or fallback status strings normalize to student-facing generation copy rather than implementation details.

## 2. Thinking Line Rendering

- [x] 2.1 Add a root-only thinking line render path for active assistant turns in `StudentAiChatPanel`.
- [x] 2.2 Remove the root running turn's repeated `Atom 学习助手 / 生成中` meta row.
- [x] 2.3 Replace the root running progress pill and skeleton primary loading affordance with the thinking line.
- [x] 2.4 Keep streamed answer text readable below or after the thinking line while the turn is still running.
- [x] 2.5 Remove the thinking line after successful final completion and preserve the existing flat markdown answer plus action row.
- [x] 2.6 Keep failed root assistant turns visibly bounded and free of successful action rows or dynamic chips.
- [x] 2.7 Preserve contextual `/ai/chat` running behavior unless selectors are explicitly scoped to root.

## 3. Motion And Styling

- [x] 3.1 Add root-scoped CSS that makes running assistant turns flat, full-width, and free of card background, card border, card shadow, and card-radius treatment.
- [x] 3.2 Add an Atom-colored animated dot cluster using CSS keyframes without adding an animation dependency.
- [x] 3.3 Implement fade-through text replacement so the outgoing phase label can fade out before the incoming phase label fades in.
- [x] 3.4 Keep dot animation independent of phase label replacement so dots do not visibly restart on every label change.
- [x] 3.5 Keep thinking-line line height stable during phase replacement to avoid vertical jumping.
- [x] 3.6 Add `prefers-reduced-motion: reduce` handling that preserves the current phase label while disabling or minimizing dot movement, text translation, blur, and repeated opacity motion.
- [x] 3.7 Strengthen the fade-through rhythm with a minimum visible phase duration and delayed incoming label so the effect reads as staged animated content replacement rather than a simultaneous crossfade.
- [x] 3.8 Slow the staged transition further after visual QA so phase changes remain perceptible in normal use.
- [x] 3.9 Retune text motion to a quicker Gemini-like fade-through with longer semantic phase dwell rather than a slow text dissolve.

## 4. Accessibility And Copy

- [x] 4.1 Expose the thinking line as polite status text for assistive technology.
- [x] 4.2 Hide decorative dots and outgoing visual-only labels from assistive technology to avoid duplicate announcements.
- [x] 4.3 Verify root phase labels use concise student-facing Chinese copy: `正在判断问题范围`, `正在检索课程资料`, `正在返回学习建议`, and `正在生成回答`.
- [x] 4.4 Ensure raw backend status strings, model details, policy codes, fallback modes, RAG traces, and exception text do not appear as normal running labels.

## 5. Tests And QA

- [x] 5.1 Add a root assistant streaming test that observes a running turn before final completion.
- [x] 5.2 Assert the root running turn has no `.ai-message-meta`, no successful action row, no source summary, and no card-like loading skeleton.
- [x] 5.3 Assert the root running turn shows the thinking line with `正在判断问题范围` when policy/scope status arrives.
- [x] 5.4 Assert a later normalized phase change updates the visible label and keeps exactly one current live status label.
- [x] 5.5 Assert the thinking line disappears after final completion and the completed answer keeps the existing flat action row.
- [x] 5.6 Assert dynamic quick prompt chips remain hidden during loading and reappear only after a successful final response with suggestions.
- [x] 5.7 Add or update static CSS/role-boundary checks proving root running flat styles are scoped to `.ai-chat-panel.root` and do not leak to contextual `/ai/chat`.
- [x] 5.8 Run `npm test -- --run` or the relevant student-web test command for the touched tests.
- [x] 5.9 Run mobile viewport QA for common root AI states if visual/layout changes are implemented in the apply phase.
- [x] 5.10 Update tests to assert outgoing and incoming phase labels are both present during staged fade-through transitions.
- [x] 5.11 Update motion-boundary tests for the slower perceptible transition timing.
- [x] 5.12 Update motion-boundary tests for the long-dwell, short-transition text-only tuning.

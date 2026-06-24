## 1. Current-State Audit

- [x] 1.1 Audit `StudentAiChatPanel` root and detail header markup, root action handlers, and route variant classes.
- [x] 1.2 Audit `assistant.css` root header, stream, panel background, composer, keyboard-active, and bottom-navigation rules to identify the minimum selectors that need changes.
- [x] 1.3 Confirm the current root panel background is painted once by the root assistant canvas and document which selectors must not receive duplicated radial-gradient backgrounds.
- [x] 1.4 Audit root assistant message rendering, assistant metadata rendering, dynamic follow-up chip placement, and source-boundary tests.
- [x] 1.5 Confirm the student assistant metadata currently supports safe citation counts and dynamic suggestions without requiring backend API changes.

## 2. Root Header Overlay and Veil

- [x] 2.1 Add root-scoped CSS variables for header overlay height, safe-area top spacing, veil color stops, z-index, and capsule sizing.
- [x] 2.2 Convert `.ai-chat-head.root` into a root-only overlay layer above the chat surface while keeping title and actions in the foreground.
- [x] 2.3 Add a `.ai-chat-head.root::before` veil layer using a simple warm-light translucent linear gradient that fades to transparent at the lower header edge.
- [x] 2.4 Ensure the veil layer does not copy the root panel radial-gradient/glow background, does not use whole-header opacity, and sits behind header foreground content.
- [x] 2.5 Keep the accepted root header veil alpha-only, with no `backdrop-filter` blur dependency and foreground title/actions remaining sharp.

## 3. Stream Spacing and Visual Continuity

- [x] 3.1 Adjust only root chat stream top safe spacing so empty welcome, restored messages, first messages, and flat assistant replies remain readable under the overlay header.
- [x] 3.2 Ensure scrollable root chat content can visually pass behind the header veil without creating a separate extra fade zone below the header.
- [x] 3.3 Verify the lower edge of the header veil fades into the existing warm paper / pale green canvas without a hard horizontal strip.
- [x] 3.4 Preserve the existing root welcome disappearance rule when the student enters non-whitespace composer text.
- [x] 3.5 Preserve the existing bottom composer, quick prompt, and bottom-navigation spacing rules while adding flat assistant turn spacing.

## 4. Root Header Action Capsule

- [x] 4.1 Restyle `.ai-root-actions` as one compact rounded capsule with a real local background and restrained border/shadow.
- [x] 4.2 Make the history and new-chat controls occupy equal halves of the capsule while preserving their accessible names, click handlers, and touch hit areas.
- [x] 4.3 Keep the action capsule aligned with the Atom root title row and avoid making it read as two separate cards.
- [x] 4.4 Confirm contextual `/ai/chat` does not render the root history/new-chat capsule.

## 5. Root Assistant Flat Reply Structure

- [x] 5.1 Refactor root assistant message rendering so successful assistant replies can omit the repeated assistant meta/completed row.
- [x] 5.2 Keep running assistant turns with a lightweight generating indicator and streaming text or skeleton.
- [x] 5.3 Keep failed assistant turns visually bounded and ensure they do not render success action rows or dynamic chips.
- [x] 5.4 Preserve user messages as right-aligned green bubbles with constrained width.
- [x] 5.5 Scope flat successful assistant reply rendering to the root variant unless an implementation review explicitly confirms detail route parity is safe.

## 6. Root Assistant Reply Action Row

- [x] 6.1 Add an assistant turn action row below each successful root assistant reply.
- [x] 6.2 Add behavior-backed icon controls for positive feedback, negative feedback, and copy.
- [x] 6.3 Keep feedback selection local to the current UI state unless a later backend feedback spec is created.
- [x] 6.4 Make positive and negative feedback mutually exclusive for the same rendered assistant turn.
- [x] 6.5 Implement copy so it copies only assistant answer text, excluding metadata, citations, prompt chips, traces, and hidden fields.
- [x] 6.6 Add accessible names and stable touch targets for every visible action button.
- [x] 6.7 Hide or defer any More/share/speech controls that do not have implemented behavior in this change.

## 7. Safe Citation Placement

- [x] 7.1 Replace the current in-card source summary placement with a compact right-aligned action-row citation count for successful root replies.
- [x] 7.2 Derive the citation count only from safe metadata such as `source_count` or sanitized source array length.
- [x] 7.3 Do not render source title, section, score, chunk ID, RAG trace, tool-call details, guardrail internals, or teacher-only metadata.
- [x] 7.4 Hide the citation affordance when the safe citation count is zero.
- [x] 7.5 Update source-boundary tests so the new citation placement still proves raw source fields are not rendered.

## 8. Dynamic Follow-Up Chips

- [x] 8.1 Preserve the existing latest-successful-only dynamic prompt selection logic.
- [x] 8.2 Place visible dynamic chips after the latest successful assistant action row and before the composer.
- [x] 8.3 Keep chips hidden or disabled while streaming.
- [x] 8.4 Keep chips hidden after failed assistant turns and prevent fallback to older successful suggestions.
- [x] 8.5 Verify that selecting a chip still submits that chip as the next user question with the existing conversation history.

## 9. Typography and CSS Constraints

- [x] 9.1 Keep flat assistant Markdown on established Atom chat font variables: `--mobile-font-family`, `--ai-chat-body-font-size`, and `--ai-chat-body-line-height`.
- [x] 9.2 Tune flat assistant reply spacing for paragraphs, headings, lists, strong text, inline code, formulas, and markdown fallback text.
- [x] 9.3 Remove root successful assistant card background, border, and card shadow without changing detail route cards unless scoped.
- [x] 9.4 Ensure flat assistant replies, action rows, citation affordances, dynamic chips, and composer controls do not overlap or horizontally overflow on common phone widths.
- [x] 9.5 Avoid nested-card styling and avoid copying the root radial-gradient background into reply blocks, action rows, or header layers.

## 10. Regression Protection

- [x] 10.1 Add or update focused student-web tests proving root header foreground remains present and root actions still invoke history/new-chat behavior.
- [x] 10.2 Add source or style regression checks that root header CSS does not duplicate the root panel radial-gradient background and does not apply whole-header opacity.
- [x] 10.3 Add route separation coverage proving contextual `/ai/chat` keeps its detail header behavior and does not inherit root overlay actions or root-only flat reply styling.
- [x] 10.4 Add tests proving successful root assistant replies render action rows, safe citation counts, and no raw source fields.
- [x] 10.5 Add tests proving user messages remain bubbles while successful assistant messages use the flat root turn treatment.
- [x] 10.6 Add tests proving dynamic chips remain latest-successful-only and hidden during loading/error states.
- [x] 10.7 Confirm composer compact/expanded/scrollable measurement, `61.8%` growth budgeting, workbench action placement, and keyboard-active bottom breathing gap are unchanged.

## 11. Validation

- [x] 11.1 Run focused student-web tests covering Atom root header, flat assistant replies, action row behavior, dynamic chips, source privacy, route separation, and composer regression protection.
- [x] 11.2 Run `npm run typecheck` in `apps/web-student`.
- [x] 11.3 Run `npm run build` in `apps/web-student`.
- [x] 11.4 Run `npx openspec validate student-ai-header-gradient-veil --strict --no-interactive`.
- [x] 11.5 Verify or record mobile viewport QA for 360x780, 390x844, and 430x932 CSS-pixel views, including empty, one-message, long-answer, restored/scroll, dynamic-chip, and keyboard-active states.
- [x] 11.6 If deployed to the running local container, refresh the student dist and visually check that no duplicated-background seam, hard header strip, clipped title, unreadable action capsule, assistant card shell, action-row overflow, citation leak, or composer overlap appears.

## 12. State-Driven Header Overlay Repair

- [x] 12.1 Add explicit root layout state hooks for empty welcome, no-message draft, and conversation/restored-message states.
- [x] 12.2 Refactor root header CSS so the overlay selector wins the cascade over generic root foreground-layer rules, and ensure generic root layer selectors do not force the header back to non-overlay positioning.
- [x] 12.3 Scope header-safe top padding, scroll-padding, or first-content spacing to the conversation/restored-message state only.
- [x] 12.4 Preserve empty welcome and no-message draft placement without overlay-caused scrollbars, welcome downward drift, composer compression, or bottom-navigation movement.
- [x] 12.5 Update regression tests to cover the explicit root layout states, cascade-sensitive header selector contract, and absence of conversation-only stream padding in empty/draft states.
- [x] 12.6 Re-run mobile viewport QA for empty, no-message draft, one-message, restored-history/scroll-near-top, dynamic-chip, and keyboard-active states before refreshing the container.

## 13. Accepted Visual Refinements

- [x] 13.1 Replace the root header blur enhancement with alpha-only veil stops so underlying content becomes progressively less visible toward the top without becoming blurred.
- [x] 13.2 Tune the root header overlay height and veil lower edge so the title/action row remains compact while content still passes behind it.
- [x] 13.3 Hide persistent desktop scrollbar chrome on the root chat stream while preserving internal scrolling for conversation/restored-message content.
- [x] 13.4 Update regression tests to assert no header `backdrop-filter` is used and root stream scrollbar hiding remains scoped.
- [x] 13.5 Refresh the running student container after the accepted visual refinements for user-side verification.

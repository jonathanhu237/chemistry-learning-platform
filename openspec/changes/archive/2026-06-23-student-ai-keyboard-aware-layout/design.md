## Context

The student H5 Atom root is now a fullscreen chat surface. Its current root layout is sized from `100dvh` and subtracts the fixed bottom navigation height. This is acceptable while the keyboard is closed, but real mobile keyboards split the browser's layout viewport from the visible viewport. On some Android/WebView environments, `100dvh` continues to represent the old page height while the keyboard consumes the lower portion of the visible screen.

The screenshot supplied by the user shows that failure mode: the Atom bottom navigation remains visible above the keyboard, and a raw background band appears between the app chrome/navigation area and the keyboard. The intended behavior is native-chat-like: when the Atom root composer is focused, the app's own bottom navigation hides and the assistant surface is laid out against the visible viewport so the keyboard touches the bottom of the app content.

## Goals / Non-Goals

**Goals:**

- Hide the student app's bottom Atom navigation while the `/ai` root composer is focused and the keyboard is expected to be open.
- Keep the root composer and send action reachable directly above the keyboard without a bottom-navigation-sized gap.
- Size the `/ai` root assistant against the visible viewport during keyboard-open state to prevent exposed raw page background.
- Keep the empty-state Atom welcome visible when the keyboard is open by moving it upward within the chat stream.
- Restore the normal bottom Atom navigation when focus leaves the root composer or the keyboard closes.
- Keep contextual `/ai/chat` detail routes distinct; they already hide bottom navigation and should not inherit root-only keyboard chrome.
- Provide regression coverage for the keyboard-active shell state and visual viewport sizing contract.

**Non-Goals:**

- Do not attempt to control the operating system keyboard UI, input-method toolbar, emoji row, microphone row, or language-switch controls.
- Do not redesign the Atom root visual language, composer copy, history behavior, or chat streaming behavior.
- Do not change backend assistant APIs or local history storage.
- Do not make the bottom navigation permanently hidden on the Atom root; hiding is only for the focused keyboard state.

## Decisions

1. **Use `visualViewport` as the keyboard-aware height source, with CSS fallback.**

   - Decision: When available, mirror `window.visualViewport.height` into a CSS variable such as `--student-visual-viewport-height`.
   - Rationale: CSS `100dvh` is not reliable enough across Android WebView/browser keyboard behavior. `visualViewport.height` more closely represents the actual screen area above the soft keyboard.
   - Alternative considered: rely only on `interactive-widget=resizes-content` in the viewport meta tag. This is useful as progressive enhancement but not sufficient because support and host WebView behavior vary.

2. **Track root composer focus at the shell level.**

   - Decision: The authenticated shell should derive a `keyboard-active` class when the active route is the `/ai` root and focus is inside the root assistant composer.
   - Rationale: The bottom navigation and route content height are shell concerns, not local input-field styling concerns. Handling this at shell level lets the app hide navigation and resize root content consistently.
   - Alternative considered: style only `.ai-chat-compose textarea:focus`. That cannot reliably hide the fixed bottom navigation or update route content height.

3. **Hide app bottom navigation by moving it fully offscreen and disabling pointer events.**

   - Decision: Reuse the established offscreen behavior pattern (`transform: translateY(calc(100% + 2px))`, `pointer-events: none`) for keyboard-active state.
   - Rationale: The existing `nav-compressed` state already defines an accepted visual contract for hiding the bottom navigation without transparency artifacts. Reusing it avoids a second hiding style.
   - Alternative considered: `display: none`. This avoids visibility but can create abrupt reflow and makes transitions less predictable.

4. **During keyboard-active state, do not subtract bottom navigation height from the Atom root content.**

   - Decision: Root AI content height should switch from a `100dvh - bottom-nav-height` formula to a visual-viewport formula that does not reserve bottom navigation space while the nav is hidden.
   - Rationale: The user explicitly wants the keyboard to reach the previous bottom-navigation upper edge instead of exposing old page background. Reserving `--mobile-bottom-nav-height` during keyboard-open state produces exactly the wrong gap.
   - Alternative considered: keep reserving nav height but hide nav visually. That preserves a blank nav-sized band and fails the requested behavior.

5. **Keep route identity stable while chrome changes.**

   - Decision: The `/ai` route remains the `ai` root route with the Atom tab identity. Only the transient keyboard chrome changes.
   - Rationale: History, new-chat, route matching, and bottom-tab active state should continue to behave consistently before and after focusing the composer.

6. **Shift the empty welcome inside the chat stream, not as a fixed overlay.**

   - Decision: When the root Atom assistant is both keyboard-active and empty, keep the Atom welcome group in the chat stream but change its empty-state alignment from centered to top-biased within the visible area above the composer.
   - Rationale: The welcome should remain part of the chat surface and should disappear naturally once messages exist. A fixed overlay would risk covering messages, composer controls, or future root content.
   - Implementation shape: use the existing `root-empty` stream state plus the shell keyboard-active class to apply a keyboard-specific alignment rule. The offset should be driven by a CSS variable derived from the visible viewport, with a conservative CSS fallback, so the welcome can sit in the upper portion of the available stream area on different keyboard heights.
   - Alternative considered: hide the welcome during keyboard-open state. This keeps the composer clean but loses the Gemini-like entry cue the user wants to preserve.

## Risks / Trade-offs

- [Risk] `visualViewport` resize events may fire several times during keyboard animation. -> Mitigation: keep the update cheap: set CSS variables and one boolean state only; avoid layout-heavy DOM measurement loops.
- [Risk] Some desktop browsers and test environments do not expose `visualViewport`. -> Mitigation: fall back to `window.innerHeight`/`100dvh` and keep behavior gated by focused root composer.
- [Risk] Focus can move from the textarea to the send button while the keyboard remains open. -> Mitigation: treat focus inside the root compose form as keyboard-active, not only focus on the textarea.
- [Risk] Hiding bottom navigation while keyboard is open could strand users if focus cannot be dismissed. -> Mitigation: restore navigation on focusout, route changes, Escape/blur-like state changes, and visual viewport return to normal height.
- [Risk] Contextual `/ai/chat` routes already hide bottom navigation; applying root keyboard rules there could create redundant or unstable classes. -> Mitigation: gate the behavior on `isRootRoute && activeRoot === "ai"`.
- [Risk] On very short visual viewports, preserving the full welcome and full composer may still feel cramped. -> Mitigation: allow keyboard-active styling to reduce welcome gap or icon size only if needed, but keep the welcome phrase readable and never place it behind the composer.

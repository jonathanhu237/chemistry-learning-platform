## 1. Shell Keyboard State

- [x] 1.1 Add root-AI composer focus detection in `AuthenticatedAppLayout` using delegated `focusin`/`focusout` handling gated to `isRootRoute && activeRoot === "ai"`.
- [x] 1.2 Add visual viewport tracking that writes a CSS variable such as `--student-visual-viewport-height` from `window.visualViewport.height`, with a safe fallback when `visualViewport` is unavailable.
- [x] 1.3 Derive a keyboard-active shell class only while focus remains inside the root Atom composer and clear it on route changes, composer blur, or viewport restoration.

## 2. Root Layout and Chrome CSS

- [x] 2.1 Add shell CSS for the keyboard-active Atom root that hides `.student-bottom-nav` fully offscreen and disables pointer events without transparency artifacts.
- [x] 2.2 Update root-AI route content height in keyboard-active state to use the visible viewport variable and stop subtracting `--mobile-bottom-nav-height`.
- [x] 2.3 Adjust the root assistant panel/composer keyboard-active spacing so the composer sits directly above the keyboard without exposing raw page background.
- [x] 2.4 Add keyboard-active empty-state styling that shifts the Atom welcome upward within the chat stream while keeping the pictogram and phrase visible above the composer.
- [x] 2.5 Preserve normal closed-keyboard layout, bottom Atom navigation visibility, and the existing Atom root title/welcome/composer design.
- [x] 2.6 Make the root composer transition from empty welcome state to text-entry state, then auto-grow until approximately `61.8%` of the effective chat panel height before switching to internal textarea scrolling.

## 3. Regression Coverage

- [x] 3.1 Add focused component/e2e coverage that simulates root Atom composer focus and verifies keyboard-active shell class, hidden bottom navigation, and visible-viewport CSS variable behavior.
- [x] 3.2 Add coverage that blur or route changes restore normal bottom navigation and preserve chat state/input state.
- [x] 3.3 Add coverage that contextual `/ai/chat` remains a detail route with bottom navigation hidden and without root-only keyboard-active dependencies.
- [x] 3.4 Add coverage that root empty-state Atom welcome remains visible and positioned above the composer during keyboard-active layout.
- [x] 3.5 Extend CSS contract tests or mobile viewport QA scripts to prevent reintroducing bottom-navigation-sized gaps during focused root assistant input.
- [x] 3.6 Add coverage that typed root composer text hides the empty welcome and that long input clamps the composer height before becoming scrollable.

## 4. Validation and Delivery

- [x] 4.1 Run `openspec validate student-ai-keyboard-aware-layout --strict --no-interactive`.
- [x] 4.2 Run `npm run typecheck` in `apps/web-student`.
- [x] 4.3 Run focused student app tests for Atom root chat and keyboard layout behavior.
- [x] 4.4 Run the full student e2e suite and production build.
- [x] 4.5 If implementation is deployed in the current environment, copy the built `dist` into the running student container and verify `/health` plus the new asset hashes.

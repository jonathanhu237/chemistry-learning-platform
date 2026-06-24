## 1. Navigation Contract

- [x] 1.1 Update `StudentBottomNav` markup and accessibility hooks for compact ordinary tabs and the centered Atom brand control.
- [x] 1.2 Preserve the existing five root route ids, order, route targets, and active-root derivation.

## 2. Compact Visual System

- [x] 2.1 Reduce the shared mobile bottom-navigation height token and keep bottom spacing formulas token-driven.
- [x] 2.2 Restyle `.student-bottom-nav` so ordinary root destinations are text-forward and selected quietly.
- [x] 2.3 Restyle the centered Atom destination as an in-bar green rounded rectangle/squircle with a white Atom icon.
- [x] 2.4 Preserve safe-area padding, touch targets, focus-visible styling, scroll-hide behavior, and Atom keyboard-active hiding.
- [x] 2.5 Add a distinct inactive Atom visual state so only the active `ai` root uses the solid green/white treatment.
- [x] 2.6 Remove the inactive Atom border and rely on a shallow green background for non-active emphasis.
- [x] 2.7 Slightly enlarge the centered Atom control so it reads more clearly as the primary root entry without increasing the compact bar height.

## 3. Verification

- [x] 3.1 Update student shell contract tests for the compact token and Atom-centered visual contract.
- [x] 3.2 Update authenticated student E2E expectations so route order, Atom identity, detail hidden-navigation, and keyboard behavior remain covered.
- [x] 3.3 Run focused `web-student` tests for role boundaries and authenticated app navigation.
- [x] 3.4 Re-run focused verification and update the running `web-student` container artifacts.

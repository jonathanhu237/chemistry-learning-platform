## Context

The authenticated student H5 shell already exposes five root destinations through `StudentBottomNav`: home, learn, ai/Atom, assessment, and profile. The current navigation is a fixed `68px` icon-plus-label bar backed by the shared `--mobile-bottom-nav-height` token. Root learning and Atom pages also derive route-content heights from this token, and the Atom root composer hides the bottom navigation while the soft keyboard is active.

The requested redesign is visual and layout-oriented: make the bottom navigation shorter and more like a Xiaohongshu-style root bar, while using the chemistry product's green Atom identity instead of a red publish action. It must not change route ownership, detail-route hidden-navigation rules, or contextual `/ai/chat` behavior.

## Goals / Non-Goals

**Goals:**
- Reduce the root bottom navigation height through the shared mobile token so pages gain vertical space consistently.
- Make ordinary root destinations quiet text-first controls with a compact selected state.
- Make the centered Atom destination a branded rounded rectangle/squircle whose inactive state stays visually primary but distinct from the active solid-green state.
- Preserve route order, accessibility, safe-area handling, touch usability, keyboard-aware Atom composer behavior, and root/detail navigation semantics.
- Update regression tests so the new visual contract is protected.

**Non-Goals:**
- Do not add, remove, or rename student root routes.
- Do not turn Atom into a floating action button that protrudes outside the bottom bar.
- Do not introduce a new mobile UI library or image asset.
- Do not redesign individual root page content.
- Do not change backend APIs, authentication, or assessment/assistant data behavior.

## Decisions

1. **Use the shared bottom-nav token as the height source of truth.**
   - Set `--mobile-bottom-nav-height` to a compact value and leave all route-content calculations tied to it.
   - Rationale: root pages, learning root, and Atom root already depend on this token, so updating it keeps the spacing model coherent.
   - Alternative considered: only visually shrink `.student-bottom-nav` while leaving the token at `68px`. Rejected because it would waste invisible reserved space and make the visual bar and layout contract disagree.

2. **Keep five equal grid columns, but style Atom as the only primary control.**
   - Ordinary tabs remain in the same root order and occupy equal columns.
   - Atom's button content becomes a centered rounded rectangular/squircle mark, keeping the route entry in the navigation flow instead of floating above it.
   - The inactive Atom mark uses a soft green-tinted surface with green icon/border; the active Atom mark uses the solid product green with white icon.
   - Rationale: the user wants the Xiaohongshu-like center emphasis without increasing total bar height or creating overlay collision risk.
   - Alternative considered: a protruding floating Atom button. Rejected for this iteration because it would complicate safe-area, keyboard, and scroll-hide interactions.

3. **Make ordinary root destinations text-first.**
   - Hide ordinary icon visuals from the compact bar and rely on Chinese labels for the four non-Atom roots.
   - Rationale: the user's stated target is "普通的都是矮纯字"; removing the icon row is what lets the bar become materially shorter.
   - Alternative considered: keep smaller icons above text. Rejected because it only modestly reduces height and keeps the current visual density.

4. **Preserve accessibility through button labels and route data.**
   - Keep text labels in the DOM for all root destinations.
   - Atom keeps an accessible label while the visible control can be icon-only.
   - Rationale: compact visual treatment should not make the navigation ambiguous for assistive technology or tests.

## Risks / Trade-offs

- [Risk] Atom becomes less self-explanatory if only the icon is visible. → Mitigation: keep `aria-label`/button name and route tests asserting the Atom label remains present in the nav item.
- [Risk] Reducing nav height could expose overlap in root pages that assumed the old 68px value. → Mitigation: update the shared token and run focused route/navigation tests plus visual checks across supported phone widths.
- [Risk] Hiding ordinary icons could reduce glanceability for first-time users. → Mitigation: use clear labels, strong active text treatment, and keep Atom's brand icon as the single visual anchor.
- [Risk] The Atom root keyboard layout could regress because it hides/restores bottom navigation. → Mitigation: keep existing keyboard-active selectors and run the focused Atom keyboard E2E test.

## Migration Plan

1. Update `StudentBottomNav` markup only where needed for accessibility and styling hooks.
2. Update mobile tokens and bottom navigation CSS.
3. Update contract/E2E tests to assert the compact Atom-centered contract.
4. Run focused `web-student` tests. Rollback is limited to restoring the old token/CSS and related test expectations.

## Open Questions

- None for this implementation. Future visual QA may tune the exact green control width or corner radius after phone preview.

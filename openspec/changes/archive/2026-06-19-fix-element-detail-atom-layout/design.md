## Context

The element detail page reuses `LearningAtomModelCard` to show an atom model plus selected-element facts. On phone viewports the card is single-column and renders correctly. On wide desktop preview widths, `.atom-model-layout` switches to two columns and uses stretched grid alignment. The right facts column can be taller than the intended model stage, so the left visual column stretches; `AtomViewerZdog` observes that enlarged shell and resizes the canvas to a tall rectangle. The atom is then centered in a much taller canvas and appears visually displaced.

The student frontend is a phone-first H5 / mini-program-style surface. A wide desktop browser is a development preview, not a separate desktop layout target.

## Goals / Non-Goals

**Goals:**

- Keep the element detail atom model centered and readable on phone viewports and wide desktop previews.
- Preserve touch-first controls and the detail-page bottom-navigation-hidden route behavior.
- Prevent facts or teaching cue content from stretching the atom viewer stage.
- Add a repeatable regression check that catches abnormal atom canvas geometry outside the current phone-only QA widths.

**Non-Goals:**

- Redesign the atom renderer, Zdog drawing model, chemistry data, or element fact content.
- Reintroduce desktop-specific student layouts.
- Fix unrelated console errors from browser extensions or auth backend failures.

## Decisions

1. Preserve phone-first composition for the atom model card.

   The element detail page should not gain a separate desktop two-column behavior just because a developer opens it in a wide browser. The layout may use available width, but the model stage must remain bounded like a phone H5 component. This aligns with the existing mobile design-system contract that desktop preview is not a second student product.

2. Decouple model stage height from fact column height.

   The atom viewer container should be sized by its own intended visual ratio or bounded height, not by the tallest sibling in a grid row. CSS alignment should avoid stretch-driven height inflation, and the viewer stage should have stable height constraints that `ResizeObserver` can trust.

3. Add explicit geometry assertions to QA.

   Existing atom QA checks that the canvas exists, is large enough, and is nonblank. It does not fail when the canvas is excessively tall. Add a wide preview case and assert that the atom viewer height remains within an expected ratio or max bound for the element detail route.

## Risks / Trade-offs

- Wide preview may show a narrower or more vertical card than a desktop dashboard would. This is acceptable because the student H5 surface is phone-first.
- A strict geometry threshold could become noisy if future design intentionally changes the model stage. Keep the threshold tied to abnormal stretch, not exact pixel art.
- Facts still need to remain readable when long localized labels or values are present. Use wrapping and content flow rather than a two-column layout that can distort the model.

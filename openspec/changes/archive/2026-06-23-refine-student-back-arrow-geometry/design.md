## Context

Student H5 second-level pages currently use visually inconsistent back arrows:

- ordinary detail pages use `PageBar` with Lucide `ArrowLeft`;
- the point-video player injects a separate SVG string into an ArtPlayer layer and uses a React fallback for empty-video state;
- unified search has its own `ArrowLeft` usage.

The previous pass made these arrows larger, but the glyph geometry is still wrong for the desired mature mobile reference:

- the arrow head reads too tall vertically;
- the horizontal tail is too short;
- the stroke is slightly too heavy;
- the left whitespace is too large in the current student page screenshots.

Reference measurements gathered before this change:

- Standalone reference arrow image:
  - white connected-component bounding box: about `37px x 32px`;
  - width/height ratio: about `1.16`;
  - longest center row spans the full arrow width, confirming the long-tail visual.
- X/Twitter top-bar reference:
  - image width: `884px`;
  - arrow left edge: `49px`;
  - arrow left-edge ratio: `5.54%` of image width;
  - arrow-to-title gap: about `44px`;
  - arrow component bounding box: about `38px x 32px`.
- Current student screenshot sample:
  - image width: `406px`;
  - current detected arrow component left edge: about `36px`;
  - current left-edge ratio: about `8.87%`.

For a `406px`-wide student preview, matching the reference ratio gives a target first-visible-arrow left edge of about `22.5px`. That is `62.5%` of the current `36px`, aligning with the user direction to reduce the left whitespace to about `60%` of the current value.

## Goals / Non-Goals

**Goals:**

- Create one shared student H5 second-level back arrow geometry source.
- Draw the arrow as SVG vector lines, not as a cropped bitmap or embedded screenshot.
- Use a visually longer and flatter arrow than Lucide's default `ArrowLeft`.
- Slightly reduce stroke weight while keeping mobile readability.
- Keep phone-safe hit areas while moving the visible glyph/affordance left to match the measured reference ratio.
- Apply the same glyph and placement rules to:
  - normal second-level `PageBar` routes,
  - point-video player chrome,
  - point-video empty state,
  - unified search/detail-style back control,
  - any other existing student second-level back arrow found during implementation.
- Add regression coverage for source sharing, geometry constants, and placement values.

**Non-Goals:**

- Do not change route-stack behavior, source-aware back logic, or browser-history semantics.
- Do not redesign the point-video player layout, controls, or ArtPlayer configuration beyond its back arrow.
- Do not add a mobile UI component library or icon dependency.
- Do not alter backend APIs, media binding, chemistry rendering, or teacher preview data behavior.
- Do not shrink the accessible/touchable area below the mobile hit-target contract just to move the visible arrow.

## Decisions

### Decision: Use a shared hand-authored SVG geometry instead of Lucide ArrowLeft

Lucide's `ArrowLeft` is convenient but its default path is close to a square visual box: the head spans too much vertical height and the tail ends too early. The target reference reads as a flatter, longer arrow.

Implementation should introduce a shared module such as `apps/web-student/src/shared/mobile/BackArrowIcon.tsx` or equivalent. It should export:

- a React component for JSX usage;
- a raw SVG string or helper for ArtPlayer HTML-layer injection.

Both exports must derive from the same geometry constants or same source string so future tuning does not fork the arrow shape.

Alternative considered: keep Lucide and use CSS transforms. This was rejected because scaling X/Y and stroke values around Lucide's path still preserves the short-tail/square-head character and creates separate tuning per usage.

Alternative considered: crop or embed the reference arrow. This was rejected because the user explicitly wants the line-drawn SVG geometry derived from analysis, not a bitmap copy.

### Decision: Use measured geometry as a tuning target, not a pixel-perfect copy

The implementation should start from a `24x24` SVG viewBox so sizing remains familiar. A candidate vector is:

```svg
<svg viewBox="0 0 24 24" aria-hidden="true">
  <path d="M20.8 12H4.6" />
  <path d="M10.9 5.8 4.6 12l6.3 6.2" />
</svg>
```

Recommended attributes:

- `fill="none"`
- `stroke="currentColor"`
- `stroke-width="2.1"` or `2.15`
- `stroke-linecap="butt"` to prevent the horizontal tail from protruding past the arrow joint and creating the square burr seen with `square` caps
- `stroke-linejoin="miter"` or equivalent crisp join

The important geometry contract is:

- left point near `x=4.5-4.8`;
- tail right endpoint near `x=20.5-21`;
- wing top and bottom roughly within `y=5.8-18.2`;
- rendered visual is wider than Lucide's default and not taller;
- stroke is visibly lighter than the previous `2.4`.

These coordinates are starting values, not a prohibition on minor tuning after screenshot QA. Any tuning must keep the shared source and measured goals intact.

### Decision: Preserve 44px hit targets while moving the visible arrow left

The user feedback is about visible whitespace and glyph proportions, not a desire for tiny touch targets. The mobile design system should keep a `44px` class hit target where practical, then adjust either:

- page/container margin,
- grid column placement,
- button transform/negative offset,
- or player layer left offset

so the first visible arrow pixel aligns with the measured target. For a roughly `406px` preview, the target left edge is about `22-23px`; for common phone widths from `360px` to `430px`, the target band is approximately `20-24px`, allowing safe-area differences.

Final adopted placement values after phone-preview tuning:

- normal `PageBar` detail headers keep a `44px` tappable icon button but use a `38px` grid column and `4px` title gap so the title sits about one Chinese character away from the arrow;
- family/catalog detail pagebars use `margin-left: 12px` inside the widened frame;
- normal `PageBar` icon buttons use `transform: translateX(-8px)`;
- unified search back controls use `transform: translateX(-8px)`;
- point-video playable chrome uses `margin: 8px 0 0 10px`;
- point-video empty-state back controls use `left: 10px`.

These values replace the intermediate tuning values (`-12px`, `8px`, and the wider `44px + 8px` pagebar text spacing) because the intermediate version overcorrected leftward and left too much title gap in the real phone preview.

Alternative considered: reduce the button width from `44px`. This was rejected because it would regress touch ergonomics.

### Decision: Treat all non-tab/detail back arrows as one affordance family

All second-level student pages should read as the same back affordance family even when the implementation host differs. A video player back arrow may appear inside player chrome instead of a page header, but the glyph geometry and apparent left spacing should still match the shared mobile standard.

This does not mean every page must show the same header layout. The point-video page intentionally keeps the page header removed so long video titles do not push the video frame. It only means the back glyph itself is shared and aligned to the same visual rule.

### Decision: Verify with source guards and screenshot-friendly criteria

Regression coverage should include:

- `PageBar`, search back, and point-video back no longer directly render Lucide `ArrowLeft` for the second-level glyph;
- ArtPlayer's injected SVG uses the shared helper/string;
- the old `18px` video back left offset and overly-large pagebar left whitespace do not return;
- the shared glyph exposes or contains the expected viewBox/stroke/path constants;
- existing student tests still pass.

If practical, visual QA should include a screenshot or connected-component measurement at one representative viewport to confirm the arrow left edge is near the target band and that the arrow bbox is wider than it is tall.

## Risks / Trade-offs

- Shared SVG string and React component drift over time -> Derive both from one helper/module and add a regression test that checks the point-video layer imports/uses the shared source.
- Moving the visible glyph left could make touch feel too close to the screen edge -> Preserve the `44px` hit target and keep the visible left edge in the measured reference band rather than flush to the edge.
- Crisp linecaps may look too harsh against the chemistry UI -> Use `butt` caps for the current standard because they remove the visible joint burr; keep visual QA available for future tuning while preserving the longer-tail/flatter geometry.
- Existing tests may assert old `44px` grid/offset details -> Update tests so they protect the intended visual contract, not the outdated implementation values.
- Browser/WebView rendering of SVG strokes can vary slightly -> Use tolerant visual criteria and source-level geometry guards instead of relying only on exact pixel counts.

## Migration Plan

1. Add the shared back-arrow module and migrate React usage.
2. Migrate the ArtPlayer injected back button to the shared raw SVG helper.
3. Adjust left placement for PageBar, unified search, point-video chrome, and empty-video state.
4. Add or update tests that preserve shared-source usage and geometry/placement constants.
5. Run student-web typecheck, tests, e2e, and build.
6. Refresh the student container and verify health/external asset serving if implementation is requested.

Rollback is straightforward: restore the previous Lucide/inline SVG usages and placement values. No data migration is involved.

## Open Questions

- Final linecap choice should be confirmed visually after the first implementation screenshot: `square`/`butt` likely matches X better, while `round` may blend more softly with the existing chemistry UI.
- If a future page uses a dark or image-backed header, it should still use the same glyph geometry but may tune color and shadow for contrast.

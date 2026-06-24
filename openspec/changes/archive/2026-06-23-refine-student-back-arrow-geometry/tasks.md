## 1. Shared Arrow Geometry

- [x] 1.1 Audit student-web for all second-level back arrow usages, including `PageBar`, point-video player chrome, point-video empty state, unified search, and any remaining direct `ArrowLeft` imports used as route back controls.
- [x] 1.2 Add a shared student mobile back-arrow module that defines the hand-authored SVG geometry once and exports both a React component and an ArtPlayer-safe raw SVG/helper.
- [x] 1.3 Implement the initial line-drawn SVG from the design target: `24x24` viewBox, longer tail near `x=20.5-21`, lowered head height, and lighter stroke around `2.1-2.15`.
- [x] 1.4 Keep the shared module bitmap-free: do not embed, crop, or trace the reference screenshots.

## 2. Usage Migration And Placement

- [x] 2.1 Replace `PageBar` detail-header `ArrowLeft` usage with the shared back-arrow component while preserving the existing `onBack` behavior and accessible label.
- [x] 2.2 Replace unified search back icon usage with the shared back-arrow component while preserving search form behavior and route return behavior.
- [x] 2.3 Replace point-video ArtPlayer injected SVG and empty-state React icon with the shared back-arrow source while preserving chrome-only visibility for playable videos and visible fallback navigation for empty videos.
- [x] 2.4 Adjust normal detail page/PageBar spacing so the visible arrow left edge moves toward the measured reference target instead of keeping the previous wide-left-padding look.
- [x] 2.5 Adjust unified search spacing to match the same second-level back-arrow left-spacing standard.
- [x] 2.6 Adjust point-video player back offsets, including playable chrome and empty state, so the visible arrow left edge is roughly `60%` of the previous left whitespace and remains visually related to non-video detail pages.
- [x] 2.7 Preserve phone-safe hit targets, preferably the existing `44px` control area, while moving only the visible glyph/control placement.

## 3. Regression Coverage

- [x] 3.1 Update source-level tests to verify `PageBar`, unified search, and point-video player use the shared arrow source rather than independent copied SVG paths or direct Lucide-only geometry.
- [x] 3.2 Add or update tests that guard the shared SVG geometry constants: `24x24` viewBox family, lighter stroke, longer tail, and lower-height head.
- [x] 3.3 Add or update tests that guard placement values so the old excessive video-player offset and equivalent wide-left-padding behavior do not return.
- [x] 3.4 Confirm route-stack tests still cover source-aware return behavior and that the visual arrow migration does not change detail route role semantics.

## 4. Verification And Delivery

- [x] 4.1 Run student-web typecheck.
- [x] 4.2 Run focused student-web regression tests covering role boundaries, route/detail behavior, and point-video detail behavior.
- [x] 4.3 Run the full student-web test suite and e2e suite.
- [x] 4.4 Run a production build for `apps/web-student`.
- [x] 4.5 Perform screenshot or connected-component visual QA on at least one representative phone/preview width to confirm the arrow is flatter, longer-tailed, lighter, and closer to the measured left-spacing target.
- [x] 4.6 Refresh the student container with the new build output and verify container health plus externally served JS/CSS asset names.

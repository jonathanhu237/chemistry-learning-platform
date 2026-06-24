## Context

The student H5 home page now behaves as the experiment-video discovery root. Its top chrome contains the institutional logo/search row plus a horizontal recommendation topic rail, and the feed below is a native vertically scrolling video stream.

The previous experiment tried to make the header consume exactly its own height before normal feed scrolling continued. That model requires active gesture interception, synthetic scroll replay, nested-scroll coordination, or CSS Scroll-Driven Animation fallback branching. In mobile browsers and WebViews this is too fragile and can feel janky, especially when videos, sticky browser chrome, and bottom navigation are present.

The product decision is to standardize on option 2: the same quick-return pattern already used by the app navigation. The home header is visible by default, compresses when the student scrolls down into the feed, and restores when the student scrolls upward or returns near the top.

## Goals / Non-Goals

**Goals:**

- Treat the home logo/search row and recommendation tag rail as one header unit.
- Use the existing root-scroll direction state to compress and restore the home header.
- Keep the video feed as the native document scroll surface.
- Keep the implementation lightweight: passive scroll observation, thresholded state changes, and CSS transforms/transitions.
- Preserve root-tab identity, bottom navigation behavior, and the second-level video-library search route.

**Non-Goals:**

- Do not implement exact title-height scroll consumption before feed scrolling.
- Do not depend on CSS Scroll-Driven Animations for this behavior.
- Do not add a nested internal scroll container for the home feed.
- Do not finalize recommendation ranking, Elasticsearch-backed topic filtering, or per-topic feed results in this change.
- Do not change backend APIs or search index documents.

## Decisions

### Use root quick-return state for the home header

The authenticated shell already tracks scroll direction and toggles a compressed root-navigation state. Home header collapse shall use that same state family instead of a separate title-progress value.

When the user scrolls down past a configured threshold, the shell may add a compressed class to the root shell. When the user scrolls upward beyond a small reverse threshold, or when scroll position returns near the top, the shell removes that class. CSS owns the visual movement of the header.

Alternative considered: a header-height state machine that prevents default scrolling until the title is fully hidden or shown. Rejected because it requires active touch/wheel handling, touches every gesture frame, and performs poorly in mobile WebViews.

### Make the home header a single unit

The `StudentAppHeader` should support a main row and a `below` region. On the home root, the main row renders the SYSU logo plus video-library search action, and the `below` region renders the recommendation topic rail. The compressed state applies to the whole header so the rail never behaves as an independent sticky strip.

Alternative considered: keeping the rail inside `HomeRootPage` above the feed. Rejected because the user's product model treats the rail as part of the title/header, and it must collapse and restore with that header.

### Keep the feed scroll native

The home feed remains in the normal document flow. The implementation must not install active `touchmove` or wheel listeners that call `preventDefault` for header behavior, must not call `window.scrollBy` as a synthetic replay loop, and must not drive React state from raw per-pixel gesture deltas.

Alternative considered: a nested feed scroller under a fixed header. Rejected because it complicates bottom navigation, browser back/restore, video visibility detection, and WebView keyboard/browser-chrome behavior.

### Scope the behavior to home root chrome

The quick-return header is only for the home root. Other root tabs keep their current header behavior unless a future change explicitly opts them in. Detail routes, including video-library search and point video detail, remain governed by route-stack/detail-page chrome rules.

Alternative considered: applying the same collapsible top header to every root route now. Rejected because AI and learning pages have different surface constraints and should not inherit a video-feed-specific interaction without separate design review.

## Risks / Trade-offs

- [Risk] Option 2 does not produce the exact physical "scroll title height first" feel. -> Mitigation: it is simpler, consistent with the existing navigation model, and avoids scroll jank on target WebViews.
- [Risk] Header compression could leave a transient visual gap if CSS flow and transforms are mismatched. -> Mitigation: test at 360px, 390px, and 430px phone widths and tune header spacing/gaps in the shell styles.
- [Risk] Topic tags may look like filters before real filtering exists. -> Mitigation: this change only requires active-state selection; data filtering and ranking require a future search/feed spec.
- [Risk] Scroll thresholds may feel too eager or too slow on real devices. -> Mitigation: keep thresholds centralized with the existing navigation logic so they can be tuned without introducing another scroll engine.

## Migration Plan

1. Remove any home-header implementation that depends on CSS Scroll-Driven Animations, active gesture interception, synthetic scroll replay, or title-progress state.
2. Reuse the existing root `navCompressed` style/state family for the home header, scoped to `.root-home`.
3. Keep the home topic rail inside `StudentAppHeader` as the `below` content.
4. Verify `apps/web-student` build and hot-update the `web-student` container for phone preview.
5. Rollback path: remove the `.root-home.nav-compressed` header transform and keep the header statically visible while preserving the tag rail markup.

## Open Questions

- Exact feed filtering semantics for topic tags are deferred. The current requirement is only default `推荐` selection and visible active-state switching.
- Final scroll thresholds may be tuned after manual phone/WebView preview, but the mechanism must remain option 2.

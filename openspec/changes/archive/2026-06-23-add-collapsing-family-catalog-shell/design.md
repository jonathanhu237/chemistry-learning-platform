## Context

The student H5 learning route currently has the raw ingredients for the desired experience:

- `ChapterStudyPage` renders the selected profile's element chips and selected-element card through `LearningHomePanel`, then renders the chapter catalog through `CatalogChapterPanel`.
- `CatalogDirectoryPage` renders child catalog nodes through `CatalogDirectoryPanel`, but it loses the family element context because it is a separate route that only knows the catalog node.
- The selected-element card is useful, but it is visually too tall for a phone catalog browser. It makes the catalog feel secondary even though the catalog tree is the main learning path.

The desired product model is a family-scoped catalog browser. A page such as `17族（卤素）` is not an intermediate "choose chapter" page; it is the catalog tree surface for that family/chapter. The top area provides chemistry context, and the lower area is the file-browser-like catalog list.

## Goals / Non-Goals

**Goals:**

- Give the selected family/chapter page a polished expanded context header inspired by Spotify / Apple Music detail pages.
- Collapse that context into a slim sticky element rail once the student scrolls into the catalog list, preserving context without blocking the catalog.
- Keep the selected family element context visible when opening child catalog directories from the same chapter.
- Ensure the catalog list is visible and usable early in the first phone viewport.
- Keep the implementation within student H5 route/component boundaries and reuse existing backend endpoints.

**Non-Goals:**

- Do not create a new backend API for the first version.
- Do not redesign point detail, video playback, AI chat, assessment, or teacher pages.
- Do not replace the element detail route; full atom/fact exploration remains a separate detail page.
- Do not introduce a third-party animation or gesture dependency for this layout.
- Do not turn the family page into an `元素 / 目录` tab split; both context and catalog must be visible in one vertical flow.

## Decisions

### Decision: Introduce a family catalog shell component

Create a route-level student H5 shell for family catalog browsing. It owns the selected profile fetch, selected element state, compact/collapsed header state, and catalog navigation callbacks. It can render either the chapter root catalog or a specific directory's children as the body.

Rationale: this keeps the family context and catalog browser together. It also avoids duplicating element header logic in `ChapterStudyPage` and `CatalogDirectoryPage`.

Alternative considered: keep `LearningHomePanel` and `CatalogDirectoryPanel` as separate sibling pages and pass more props. Rejected because the user-facing mental model is one catalog browser shell, not separate element and directory pages.

### Decision: Use a CSS sticky compact header with scroll-derived state

The expanded header is normal content near the top of the detail page. A compact header uses `position: sticky` below the page bar and becomes visually active when the catalog body crosses a small threshold. A lightweight scroll listener or `IntersectionObserver` can toggle a class such as `is-collapsed`.

Rationale: this mirrors Spotify / Apple Music style detail pages while staying native to the browser. It avoids expensive per-frame mouse or gesture logic.

Alternative considered: complex animated scroll transforms driven by `requestAnimationFrame`. Rejected for the first version because the value is mostly spatial, not cinematic, and the H5 WebView must stay stable.

### Decision: Compress the element context into an element rail plus one-line focus copy

The expanded header should show:

- Horizontal element rail with mini element tiles.
- Selected element name, one or two compact focus/relevance lines, and up to three compact tags.
- A small inline `元素详情 >` affordance for the full element route.

The old large selected-element tile and full-width CTA are removed from the catalog surface.

Rationale: the element context becomes useful orientation rather than a competing detail card. The catalog body becomes visible sooner.

### Decision: Make secondary page chrome X-like and left aligned

Detail pages use a plain left arrow and left-aligned title, without the previous square button background or centered-title spacer. The family title such as `17族（卤素）` belongs in this detail page chrome, so the family context header does not repeat it.

Rationale: this saves the first vertical layer and matches familiar social/content app navigation patterns where `← 标题` is compact and immediately readable.

### Decision: Limit the expanded rail to five visible element tiles

The expanded family header treats the element rail like a modern app shortcut row: at most five tiles are visible per row, and any additional elements continue horizontally with native overflow scrolling. The collapsed state becomes an even slimmer symbol rail.

Rationale: families such as halogens have around five to six entries. A fixed five-slot rail keeps the top context predictable while avoiding wrapping that would push the catalog below the first viewport.

### Decision: Separate the catalog into a lower sheet workspace

The family page should read as two vertical regions: an upper element-context region and a lower catalog-browser sheet. The sheet owns the browser header, tappable breadcrumb navigation, catalog rows, vertical list scrolling, and a low-emphasis end marker.

Rationale: the user mental model is "element context above, learning directory below." A sheet boundary makes the catalog feel like its own browser workspace instead of another card below the element card. Search is no longer a pinned bottom field; it is a compact tool in the browser header that opens the unified search page for the current catalog scope.

### Decision: Use row-style catalog entries inside the sheet

Catalog entries inside the family sheet should render as compact list rows with a small icon, title/summary/meta, and chevron. The old floating card styling remains acceptable for non-family standalone contexts, but the family shell should prioritize dense scanning.

Rationale: the catalog behaves like a file browser. Rows let more learning entries appear earlier and reduce nested-card heaviness.

### Decision: Keep the catalog footer inside the scrollable list

The catalog end marker is a list footer, not a fixed overlay. It summarizes only non-zero visible entries for the current catalog layer: `当前共m目录`, `当前共n实验`, or `当前共m目录，n实验`. Here `实验` means student-visible point nodes, regardless of whether media has actually been uploaded. When both counts are zero, the footer is not rendered.

Rationale: this is a finite catalog, not an infinite-loading feed. A content footer avoids covering rows or adding another fixed control layer. Short lists should place the footer at the bottom of the row-list viewport; long lists should show it only after the student scrolls to the end.

### Decision: Make the sheet height chain explicit

The lower sheet uses a single catalog-browser row that fills available height. The browser then splits into an auto header and a `minmax(0, 1fr)` row-list viewport. Historical invisible spacer nodes such as `family-catalog-sheet-edge` must not own a grid row.

Rationale: footer placement depends on the row list receiving real remaining height. If the browser falls into an `auto` grid row, the footer can only align to content height and leaves unused blank space below it.

### Decision: Directory navigation preserves profile context via existing search params

When a directory opens from the family shell, navigation keeps `profileId`, `chapterId`, and `catalogPath`. `CatalogDirectoryPage` uses `profileId` to render the same family shell, while direct directory URLs without profile context continue to render the plain directory page.

Rationale: this preserves durable catalog routes and does not require a new route path. Direct links remain robust.

### Decision: Catalog panels expose body rendering without owning page chrome

`CatalogChapterPanel` / `CatalogDirectoryPanel` should either gain shell-friendly variants or be decomposed into smaller catalog-body components. The family shell owns the high-level page chrome; catalog panels own loading/error/empty/body behavior.

Rationale: avoids nested cards and duplicated headers. It keeps catalog logic reusable while allowing the page to feel like one unified browser.

## Risks / Trade-offs

- [Risk] Sticky header height can collide with the existing PageBar. -> Mitigation: define one CSS variable for detail top offset and test on 360-430px phone widths.
- [Risk] Scroll state can feel jumpy. -> Mitigation: collapse only after the catalog body reaches the top threshold; transitions must be short and opacity/height based, not delayed.
- [Risk] Direct catalog URLs may lack profile context. -> Mitigation: preserve the existing plain directory route behavior for missing `profileId`.
- [Risk] The compact header can still be too tall. -> Mitigation: cap expanded header height and line-clamp focus/relevance copy; the compact header must fit within roughly one control row.
- [Risk] Element rail could overflow on families with many elements. -> Mitigation: make it horizontally scrollable with snap/overflow cues and no hidden required controls.
- [Risk] The catalog footer can drift above the phone bottom if an ancestor grid row collapses to content height. -> Mitigation: use a single filled sheet row, `min-height: 0` on all `1fr` ancestors, and browser-level geometry QA for short and long lists.

## Migration Plan

1. Add the OpenSpec requirements and tasks for the family catalog shell.
2. Refactor student H5 learning components so the compact element rail/header can be reused by chapter and directory routes.
3. Update chapter and directory routes to use the shell when a profile context exists.
4. Update styles and tests for expanded/collapsed header, catalog visibility, toolbar search entry, and catalog footer geometry.
5. Run student typecheck/e2e, catalog-footer geometry QA, and OpenSpec validation.

Rollback is a normal code revert. No database migration or seed data migration is required.

## Open Questions

- Whether a future version should add a chemistry-specific trend line between element tiles, such as `氧化性递减`, after the first collapsed-header version feels stable.

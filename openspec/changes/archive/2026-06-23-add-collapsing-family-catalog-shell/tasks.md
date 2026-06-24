## 1. Family Shell Structure

- [x] 1.1 Add a reusable student H5 family catalog shell component that owns selected profile loading, selected element state, and shared catalog navigation callbacks.
- [x] 1.2 Refactor the existing compact element context from the chapter learning page into shell-friendly expanded and compact header sections.
- [x] 1.3 Preserve the existing element detail route behavior from the compact header affordance.

## 2. Catalog Body Integration

- [x] 2.1 Adapt chapter-root catalog rendering so it can appear as the family shell body without a duplicate large panel header.
- [x] 2.2 Adapt catalog-directory rendering so routes with `profileId` render inside the family shell and routes without `profileId` keep the standalone directory fallback.
- [x] 2.3 Preserve `profileId`, `chapterId`, `catalogPath`, and selected `elementSymbol` when navigating between catalog directories and point detail.

## 3. Collapsing Header Interaction

- [x] 3.1 Implement scroll-threshold or intersection-based collapsed state for the family context header.
- [x] 3.2 Add mobile-first styles for expanded header, compact sticky header, horizontal element rail, and catalog-first spacing.
- [x] 3.3 Ensure the compact header stays below the detail page bar and does not overlap catalog rows on 360px-430px phone viewports.

## 4. Verification

- [x] 4.1 Update student H5 tests for family shell rendering, directory context preservation, and point navigation search context.
- [x] 4.2 Update mobile viewport QA expectations or screenshots for the compact header and catalog discoverability.
- [x] 4.3 Run OpenSpec validation plus relevant student typecheck/e2e checks.

## 5. Lightweight Header Refinement

- [x] 5.1 Align detail page chrome with an X-like `← 标题` layout: plain arrow, left title, tighter vertical spacing.
- [x] 5.2 Remove duplicate family title/subtitle from the family context header; the page bar owns the title.
- [x] 5.3 Limit the expanded element rail to five visible tiles with horizontal overflow for larger families.
- [x] 5.4 Replace the large selected-element CTA with an inline `元素详情 >` action beside the selected element name.
- [x] 5.5 Remove the `当前观察元素` label and use a subtle divider plus compact focus/relevance copy and tags.

## 6. Fixed Viewport Directory Sheet

- [x] 6.1 Lock the family catalog page to a fixed viewport and move vertical scrolling into the lower catalog row list without a pinned bottom search field.
- [x] 6.2 Move catalog search into the browser header action that opens the unified search page with current profile/chapter/source context.
- [x] 6.3 Render the finite catalog end marker as list content with non-zero `目录` / `实验` counts.
- [x] 6.4 Add browser geometry QA for short-list footer bottom alignment and long-list footer-at-end behavior.

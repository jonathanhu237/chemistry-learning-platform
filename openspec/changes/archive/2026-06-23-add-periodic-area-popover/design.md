## Context

The student `/learn` root currently renders `LearningEntryPanel`, which fetches the student learning payload and renders `PeriodicTable`. `PeriodicTable` receives `onSelectArea(areaId)` and every area legend button or element cell calls it. `LearnRootPage` then translates that callback into `navigateToLearningArea(...)`, so the student leaves the periodic-table entry and lands on `/learn/area/$areaId`, where `LearningAreaChapterList` renders the short filtered chapter list.

That selected-area page is useful as a durable fallback URL, but it is weak as the primary phone interaction because the periodic table is already the fixed selector. The desired interaction is closer to ChatGPT's plus menu: tap a stable control, show a temporary anchored menu, then choose the concrete destination. Unlike ChatGPT's fixed plus button, the anchor can be any area legend button or element cell, so the placement must respond to the tapped element and avoid viewport clipping.

The current student app is React + Vite with phone-first CSS and bottom navigation on root routes. This change adds `@floating-ui/react` only to `apps/web-student` and keeps the implementation local to the student learning entry.

## Goals / Non-Goals

**Goals:**

- Keep `/learn` as the primary periodic-table selection surface.
- Show the selected area's chapter/family choices in an anchored popover on the same page.
- Ensure the popover is fixed-positioned or portaled so it never participates in document flow and never stretches the current screen.
- Make the popover collision-aware: flip away from blocked edges, shift inside the viewport, and clamp its height to visible space.
- Preserve direct navigation to the real chapter/family learning route when a list row is selected.
- Keep `/learn/area/$areaId` as a compatibility fallback for direct URLs and history.
- Preserve touch-first behavior, outside-tap dismissal, Escape dismissal, focus safety, and screen-reader labels.

**Non-Goals:**

- Do not redesign the chapter detail, element detail, catalog directory, or point detail routes.
- Do not remove the selected-area route in this change.
- Do not introduce a broad mobile UI component library.
- Do not replace the periodic table renderer with a third-party table component.
- Do not make the popover a bottom sheet by default on normal supported phone viewports.

## Decisions

### Decision: Use Floating UI for anchored placement

Use `@floating-ui/react` with `useFloating`, `offset`, `flip`, `shift`, `size`, `autoUpdate`, `useClick`, `useDismiss`, `useRole`, and `FloatingFocusManager` where appropriate.

Rationale: the hard part is not drawing the card; it is keeping it attached to many possible anchors while avoiding clipping during scroll, resize, browser chrome changes, and different phone widths. Floating UI already provides this collision and lifecycle behavior.

Alternative considered: manually call `getBoundingClientRect()` and compute `top/left`. Rejected because it would duplicate collision, resize, scroll, and edge handling and would be easy to regress.

### Decision: Make the popover a transient root overlay, not inline content

The popover will render through a fixed-position floating layer using Floating UI's computed styles. It will not be inserted inside the periodic card's grid layout or inside the normal page flow.

Rationale: the user's explicit constraint is that the bubble must not stretch the current screen. Rendering in normal flow would resize the periodic table panel or increase page height. A fixed floating layer keeps the root layout stable.

Alternative considered: render an inline accordion below the table. Rejected because it would recreate the "root becomes list page" problem and push content vertically.

### Decision: Pass the clicked element as the reference anchor

Change the periodic-table callback shape from `onSelectArea(areaId)` to an anchor-aware payload such as `onSelectArea(areaId, triggerElement)`. Area legend buttons and element cells will pass `event.currentTarget`.

Rationale: the popover must respond to the actual tapped control. Using the element itself lets Floating UI follow the target during scroll and gives assistive technology a natural controller relationship.

Alternative considered: pass only pointer coordinates. Rejected because coordinate-only anchors do not update as naturally during layout shifts and do not preserve control relationships.

### Decision: Reuse the chapter filtering model, but adapt list chrome for popover

Reuse the existing `profileAreaIds(profile).includes(selectedArea)` filtering. Extract or extend the list rendering so the selected-area route can keep the full-page panel while the popover uses compact row chrome.

Rationale: this keeps the learning data contract unchanged and avoids duplicating area membership rules.

Alternative considered: fetch area-specific chapter data only after each tap. Rejected because `LearningEntryPanel` already has the page payload and the list is small.

### Decision: Chapter selection closes the popover and pushes the chapter detail route

Selecting a row closes the popover and calls `navigateToChapter(...)`. The selected-area route is bypassed for normal root interactions.

Rationale: the popover replaces only the intermediate selector page. Chapter learning remains a route-level detail task with bottom navigation hidden.

Alternative considered: row selection navigates to `/learn/area/$areaId` first. Rejected because it preserves the unnecessary intermediate page.

### Decision: Normal phone viewports must show the full area list

At 360x780, 390x844, and 430x932 CSS pixel viewports, the p-area list and hydrogen list must fit inside the viewport without clipping or page stretch. The popover width will be clamped to the viewport, and its height will be constrained by Floating UI `size()` middleware.

If a nonstandard viewport has too little height, the popover may scroll internally or later degrade to a bottom sheet, but the supported mobile QA target is a complete, visible list.

## Risks / Trade-offs

- [Risk] `@floating-ui/react` adds a frontend dependency. -> Mitigation: scope it to `apps/web-student`, use a narrow API surface, and keep the selected-area fallback route.
- [Risk] Popover placement may conflict with root bottom navigation or safe areas. -> Mitigation: use fixed positioning, viewport padding, CSS safe-area spacing, and QA at required phone sizes.
- [Risk] Opening from tiny element cells can produce awkward anchor geometry. -> Mitigation: use a minimum popover width and `shift` so the card reads as anchored but remains legible.
- [Risk] Tests currently expect clicking an area to navigate to `/learn/area/$areaId`. -> Mitigation: update tests to expect an in-place popover and chapter navigation from its rows; keep direct selected-area route tests where route fallback is important.
- [Risk] The popover could obscure the recommendation card. -> Mitigation: treat the popover as a transient selector; outside tap closes it, and it should prefer placement near the selected table/legend control.

## Migration Plan

1. Add `@floating-ui/react` to `apps/web-student`.
2. Introduce an anchored learning area popover component or route-local overlay inside `LearningEntryPanel`.
3. Update `PeriodicTable` to pass the trigger element to the selection callback.
4. Update `LearnRootPage` so root area selection opens the popover, while row selection still navigates to chapter detail.
5. Keep `LearningAreaPage` and `navigateToLearningArea` unchanged for compatibility.
6. Update CSS for compact popover rows, fixed overlay z-index, viewport-contained dimensions, and touch targets.
7. Update tests and mobile QA expectations for the new root interaction.

Rollback is straightforward: restore `LearnRootPage` to navigate on area selection and remove the popover component/dependency. No backend or data migration is involved.

## Open Questions

- Whether future design should add a tiny pointer arrow from the popover back to the tapped cell. The initial implementation can ship without an arrow if placement, contrast, and row clarity are good.
- Whether the selected-area fallback route should eventually be removed after analytics show the popover flow is stable. It should remain in this change.

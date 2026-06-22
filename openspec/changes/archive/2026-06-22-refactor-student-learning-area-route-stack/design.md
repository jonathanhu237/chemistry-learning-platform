## Context

The authenticated student app already uses TanStack Router with five bottom-tab roots and non-tab detail pages. The learning root currently renders the periodic table and, below it, the selected-area chapter list in the same scroll surface. That made area filtering easy, but it blurs the route model: the learning tab becomes both the entry page and the first drilldown page.

The intended H5 flow is a stack:

```text
/learn
  -> /learn/area/$areaId
    -> /chapter/$profileId
      -> /catalog/$nodeId
        -> /point/$nodeId
```

All routes after `/learn` are non-tab pages. They hide the bottom navigation and rely on history/page-back to return to the previous level.

## Goals / Non-Goals

**Goals:**

- Keep `/learn` as a focused periodic-table root entry page.
- Add a durable second-level area route for `p`, `s`, `ds`, `d`, `f`, and the hydrogen/noble-gas learning area.
- Move selected-area chapter cards from the root page into the area route.
- Preserve existing chapter, catalog directory, element detail, point detail, AI, assessment, and feedback route behavior.
- Reuse the existing learning-page payload and profile-to-area helpers instead of adding backend contracts.

**Non-Goals:**

- No backend API, database, seed, or catalog-tree changes.
- No native mini-program rewrite or new routing library.
- No redesign of chapter, catalog directory, or point detail content.
- No new third-level page category; area, chapter, catalog, and point are all non-tab detail routes by role.

## Decisions

### 1. Area Selection Opens A Detail Route

`PeriodicTable` should call a navigation-oriented area selection handler from `/learn`, and the route owner should push a detail route such as `/learn/area/p`.

Rationale: the area page is the first drilldown after the learning tab. Keeping it as a route aligns with the existing mini-program model and gives browser/WebView back a concrete page to return from.

Alternative considered: keep local `selectedArea` on `/learn` and scroll to the chapter list. Rejected because it keeps the root page as a mixed entry/list page and reproduces the current screenshot issue.

### 2. The Area Page Reuses Existing Learning Data

The area route should fetch `getStudentLearningPage(null)` just as the current learning entry does, resolve the recommended profile and selected area, then render only the chapter cards that match the route area id.

Rationale: the backend already returns all profile summaries required for the list. Adding an area-specific endpoint would not change authorization or payload shape enough to justify the extra contract.

Alternative considered: pass the filtered profiles through route state from `/learn`. Rejected because direct area URLs must work without prior in-memory state.

### 3. Split Root And Area Components By Responsibility

The root entry component should render the periodic table only. A new reusable area chapter-list component should render the current area header, recommendation label, empty state, and chapter card navigation.

Rationale: the root page and area detail page have different route roles and chrome. Separate components make tests and future polish easier without duplicating profile filtering logic.

Alternative considered: add a prop to hide the chapter list inside the existing `LearningEntryPanel`. This is smaller but keeps the component's ownership blurry.

### 4. Detail Chrome Remains Route-Driven

The area route should use the existing detail-page frame or equivalent route role so the bottom navigation is hidden. Its back behavior should return to `/learn` when opened from the root and still work for direct URLs.

Rationale: the app already treats non-root routes as detail pages. Area selection should not introduce a custom navigation chrome path.

Alternative considered: make the area page a root sub-view with bottom nav visible. Rejected because the user explicitly wants selected area as a second-level page.

## Risks / Trade-offs

- [Risk] Direct area URLs may load without in-memory learning data. -> Mitigation: fetch the existing learning-page payload in the area page.
- [Risk] Tests that click chapter cards on `/learn` will fail. -> Mitigation: update E2E and mobile QA to navigate `/learn -> /learn/area/:areaId -> /chapter/:profileId`.
- [Risk] The root periodic table may lose visible recommended chapter context. -> Mitigation: keep recommended area cues and learnable/recommended element highlighting on the root table.
- [Risk] Unsupported area ids could crash filtering. -> Mitigation: validate route params against known area ids and render a controlled empty/unavailable area state.

## Migration Plan

1. Add route helpers and a TanStack route for `/learn/area/$areaId`.
2. Refactor the learning entry root so it renders only the periodic table and pushes the area route on area or cell tap.
3. Add the area route page and chapter-list component using existing profile filtering helpers.
4. Update tests and mobile QA expectations for the new route stack.
5. Run focused student tests, typecheck, and OpenSpec validation.

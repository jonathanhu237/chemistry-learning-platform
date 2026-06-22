## Context

The student H5 app now uses TanStack Router with five root tabs and hidden-nav detail pages. The learning root (`/learn`) owns chapter selection/search/entry. The chapter detail route currently still behaves like an older combined surface: it contains a local `ChapterViewSwitcher`, selected element chips, the full atom model, whole-family/common-property blocks, property-section summaries, experiment video/card content, and completion-to-assessment affordances.

The user direction for this change is sharper:

- selecting another chapter is a route/history concern, not a chapter-page action;
- the full atom/model page should become its own detail page;
- the chapter page should show only a simple element description plus experiment content below it;
- the old facts/video capsule switch is unnecessary;
- family-level property blocks and typical-property blocks are not useful in this learning page;
- real experiment cards may render now even if their final detailed content/design is still undecided;
- the chapter-page completion-to-assessment action should not remain.

## Goals / Non-Goals

**Goals:**

- Make the chapter detail page a focused selected-chapter learning entry surface.
- Remove chapter-local A/B switching between facts and experiments.
- Move the full atom model and element fact chips into a dedicated element detail route.
- Keep a lightweight element summary on the chapter page with an obvious entry to element detail.
- Render real experiment cards under the element summary, using existing `chapterExperimentGroupsForProfile` / point card data.
- Preserve hidden bottom navigation on the chapter page, element detail page, and experiment point detail page.
- Preserve contextual AI from chapter detail.

**Non-Goals:**

- Do not redesign the final experiment content experience yet; cards may be provisional.
- Do not add a new experiment root tab or restore an experiment tab.
- Do not add a new backend API for element detail.
- Do not keep the old `性质通识 / 实验视频` capsule as a compatibility path.
- Do not retain chapter-page completion-to-assessment.

## Decisions

### Decision 1: Chapter Page Becomes A Lightweight Entry Surface

The chapter detail route remains the first destination after choosing a chapter/family, but it should no longer render the full encyclopedia-like facts page. It should render:

1. selected chapter/profile context,
2. element chips or another compact selector for the family elements,
3. a selected-element summary card,
4. an element-detail entry action,
5. experiment card entries below.

Rationale: the chapter page becomes easy to scan and no longer competes with the learning root for selection or with the element detail page for deep content.

Alternative considered: keep facts as the default and only move the atom canvas. Rejected because the family/common-property blocks are explicitly not useful for the intended page.

### Decision 2: Element Detail Gets Its Own Route

Add a route such as `/chapter/$profileId/element/$symbol` (exact path may vary if implementation chooses a typed helper, but it must be a concrete detail URL) that renders the full element model page. This page owns:

- `LearningAtomModelCard` or its successor,
- Bohr/electron-shell and orbital controls,
- atomic mass, group/period/block, state, density, electron configuration,
- teaching cue / oxidation-state hint.

The route fetches the learning profile by `profileId`, resolves the element by `symbol`, and falls back gracefully if the symbol is unavailable.

Rationale: full atom-model interaction is a deep task and should not bloat the chapter overview.

Alternative considered: open a modal from the chapter page. Rejected because the app already uses route-stack detail pages and the user specifically wants a page-like second-level experience with native back behavior.

### Decision 3: Experiments Are Always Visible On Chapter Detail

The chapter page should render experiment cards directly below the element summary instead of hiding them behind a capsule switch. It should use real existing experiment card data (`chapterExperimentGroupsForProfile(profile)` and `LearningPointGroupView`-style cards) even if copy/layout is provisional.

Rationale: experiments are the useful next learning action, and rendering real cards now keeps routing/data behavior honest while leaving visual refinement for a later pass.

Alternative considered: show a placeholder block only. Rejected because the data path already exists and real cards are needed to test navigation to experiment point detail.

### Decision 4: Remove Chapter-Level Completion Action

The chapter page and the experiment list area should not show the current finish-learning / start-assessment action. Assessment remains accessible through its root page, and any existing point-detail assessment action can remain unless a later design removes or replaces it.

Rationale: the refocused chapter page is about choosing what to study next, not completing the whole learning flow from a generic page bottom.

Alternative considered: keep completion as a sticky footer. Rejected because it conflicts with the user's requested simplification.

### Decision 5: Remove Stale Route Search State

`chapterView` should stop being a meaningful navigation parameter for chapter pages. Existing callers may temporarily ignore it for compatibility during migration, but the final behavior must not depend on it, and tests should verify that the capsule switch is gone.

Rationale: keeping a hidden `chapterView=facts/experiments` state would recreate the model being removed.

## Risks / Trade-offs

- [Risk] Direct URLs with old `chapterView=experiments` search may no longer restore the old experiments-only view. -> Mitigation: render the same refocused chapter page and keep experiment cards visible without needing a view switch.
- [Risk] The element detail route depends on profile data that may not include the requested symbol. -> Mitigation: show a route-local empty/error state and allow back navigation.
- [Risk] Removing completion-to-assessment from the chapter page may reduce assessment entry visibility. -> Mitigation: assessment remains a first-level tab; point-detail behavior can remain until separately redesigned.
- [Risk] Experiment card visuals are not final. -> Mitigation: scope this change to real data rendering and routing, not final experiment pedagogy/content design.
- [Risk] Existing tests/mobile QA may still expect the capsule switch or old property blocks. -> Mitigation: update tests to assert their removal and cover the new element route.

## Migration Plan

1. Add typed route/search helpers for the element detail route.
2. Split the current facts/model content so the full model renders only in element detail.
3. Replace chapter facts view with a compact element summary and direct experiment list.
4. Remove the chapter view switcher and view-state scroll preservation.
5. Remove chapter-page completion-to-assessment action.
6. Update tests and mobile QA expectations.

Rollback is straightforward: restore the previous `LearningFactsView`/`LearningExperimentsView` switcher and remove the element route. No data migration is involved.

## Open Questions

- Final experiment card content and hierarchy are intentionally unresolved; this change should render real cards first and allow later redesign.
- The exact element detail URL may be adjusted during implementation, but it must remain a real route detail page with hidden bottom navigation.

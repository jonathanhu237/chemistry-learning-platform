## Context

This change builds on `student-element-chapter-learning-composition`. That change established the correct hierarchy:

```text
periodic-table entry
  -> selected family/chapter
    -> within-family element selection
    -> learning content
    -> experiment point detail
    -> post-learning assessment
```

The remaining issue is composition. The current chapter page puts selected-element facts, family common properties, property-section selectors, experiment-point groups, AI, feedback, and finish actions into one vertical phone page. It also asks chemical property sections, such as oxidizing or reducing behavior, to act as the primary grouping mechanism for experiment points. This is not the product's strongest mental model. The product's core learning resource is experiment-point video learning; properties are context, not the required navigation taxonomy for experiments.

Research context to preserve:

- Apple Human Interface Guidelines use segmented controls for switching between a small number of mutually exclusive views in the same context. This maps well to `Facts` vs `Experiments`.
- Material Design tabs organize sibling content views at the same hierarchy level. This supports the idea that A and B are peer views inside one chapter.
- Material bottom navigation is intended for top-level destinations. It is not a good fit for chapter-local A/B switching, especially because this app already has bottom navigation, floating AI, feedback, and finish actions.
- Ionic segment is a similar mobile pattern for switching in-page views.
- WCAG target-size guidance sets a lower bound for touch targets. This app should use phone-native-feeling 44-48px switcher height rather than small desktop tabs.

The target remains React + Vite H5 in a mobile browser or WebView. This is not a native WeChat mini-program package.

## Goals / Non-Goals

**Goals:**

- Split the current chapter learning page into two sibling views:
  - A: element facts and family/common-property learning.
  - B: experiment-point video learning.
- Use an Apple-style sticky segmented control for fast A/B switching on small phone screens.
- Keep the switcher visible or quickly reachable without competing with bottom navigation, AI, feedback, or finish actions.
- Remove the forced property-to-experiment grouping from the primary experiment view.
- Group experiment learning by current chapter, parent experiment, and point.
- Preserve point detail, protected videos, AI context, feedback context, and completion-to-posttest behavior.
- Preserve phone QA at 360, 390, and 430 CSS-pixel widths.

**Non-Goals:**

- Do not introduce Ant Design Mobile, Ionic, Taro, uni-app, React Native, or a native mini-program build chain for this change.
- Do not redesign the teacher/admin console.
- Do not change CI or release workflows.
- Do not remove the explicit student learning seed facts.
- Do not require public reference images or videos for the page to work.
- Do not delete existing `property_sections` seed data; they can still support the facts/common-property view.

## Decisions

### Decision 1: A/B views are chapter-local sibling views

The chapter page should have two local views:

```text
Current chapter header
Element chips
Sticky segmented switcher
  [ Facts ] [ Experiments 6 ]

Facts view:
  selected element facts
  family common properties
  optional reference media
  CTA to experiments

Experiments view:
  chapter experiment groups
  experiment -> point cards
  point detail route
  finish learning / assessment
```

Alternatives considered:

- Keep one long page. This keeps all content visible, but it pushes the experiment task too far down and blurs theory vs task.
- Put A/B in bottom navigation. This conflicts with app-level bottom navigation and floating entries. Bottom navigation should remain for global destinations and primary task actions.
- Use property-section tabs as the A/B navigation. This repeats the current problem by making chemistry properties carry too much navigation meaning.

Chosen behavior:

- A/B is a local segmented switch inside the current chapter.
- The active chapter and selected element stay stable while switching between A and B.
- A/B switching must not navigate back to the periodic-table entry.

### Decision 2: Use a sticky segmented control, not a library dependency

The switcher should be custom-built in the student H5 primitive style. It should visually borrow from iOS segmented controls:

- two equal-width options;
- 44-48px minimum control height;
- clear active background and inactive state;
- rounded capsule container;
- no hover-only affordance;
- accessible `button` or tab semantics;
- `position: sticky` below the chapter context area;
- safe-area aware top offset where applicable;
- z-index below modal/chat/feedback overlays and above scrolling content.

No new mobile component library is needed for a two-option switcher. `antd-mobile`, Ionic, or similar libraries can be revisited later only if the app needs a broader primitive set.

### Decision 3: Facts view owns properties; experiments view owns points

The facts view contains:

- selected element facts;
- family/common-property cards;
- property/trend explanations;
- optional reference media;
- a clear CTA to switch to experiments.

The experiments view contains:

- current chapter/family context in compact form;
- parent experiment groups;
- point cards under each experiment;
- media availability and question count;
- finish learning / assessment action.

`property_sections` remain useful for theory content, but they should not be the primary experiment grouping. This removes the forced "this point belongs to oxidizing/reducing/precipitation" interpretation when the product goal is simply to learn the chapter's experiment points.

### Decision 4: Add an explicit chapter experiment grouping payload

The frontend should not reconstruct the B view from property-filtered `related_groups`. The backend should expose an explicit chapter-level grouping, for example:

```json
{
  "chapter_experiment_groups": [
    {
      "parent_code": "19-1",
      "parent_title": "Halogen experiments",
      "points": [
        {
          "id": "...",
          "code": "19-1-01",
          "title": "...",
          "point_key": "...",
          "point_title": "...",
          "summary": "...",
          "published_video_count": 3,
          "question_count": 30
        }
      ]
    }
  ]
}
```

`related_groups` can remain temporarily for backward compatibility, but the new B page should read from `chapter_experiment_groups`.

### Decision 5: Preserve tab and scroll state where feasible

The page should remember:

- active chapter profile;
- selected element;
- active A/B tab;
- facts scroll position;
- experiments scroll position.

The first implementation can preserve A/B tab and selected element in component route state. Independent scroll retention can be implemented with refs and `window.scrollY`, or with tab-local scroll containers if that fits the existing H5 shell. If scroll preservation becomes fragile, it should degrade by preserving the active tab first.

### Decision 6: Floating entries stay global but context-aware

AI and feedback must remain available when enabled by admin settings, but they must not obscure the sticky segmented switcher or finish action. Their context should include:

- screen: facts or experiments;
- profile/chapter id;
- selected element symbol when present;
- experiment/point context in detail view;
- active tab label.

## Risks / Trade-offs

- [Risk] Sticky controls can overlap content or browser safe areas. Mitigation: reuse mobile tokens for safe-area offsets, z-index, and bottom spacing; verify at 360/390/430 widths.
- [Risk] Two views can hide content that was previously visible on one page. Mitigation: make the segmented switcher highly visible and add an in-content CTA from facts to experiments.
- [Risk] Scroll-position preservation can become complex. Mitigation: preserve active tab first; preserve per-tab scroll where feasible and test with mobile QA.
- [Risk] Adding `chapter_experiment_groups` duplicates some information from `related_groups`. Mitigation: keep it as a clearer API contract for the new B view and deprecate property-driven grouping later.
- [Risk] Users may still expect property filters. Mitigation: property content remains in facts view; experiment learning is grouped by experiment and point because that matches the resource model.

## Migration Plan

1. Add or derive `chapter_experiment_groups` in the student learning payload while keeping existing fields compatible.
2. Recompose `LearningHomePanel` into shared chapter context plus an active `facts | experiments` view.
3. Move selected-element facts, family common properties, and optional reference media into the facts view.
4. Move experiment cards into the experiments view and group by parent experiment/point rather than property section.
5. Update AI and feedback context to include active tab and selected element.
6. Update mobile QA to cover A/B switching, element switching, experiment point cards, point detail, floating entries, and finish action.
7. Run backend tests, production resource validation, student-web typecheck/build, mobile viewport QA, and OpenSpec validation.

Rollback strategy:

- Keep additive API fields backward compatible.
- If the two-tab composition has a regression, the frontend can temporarily return to one-page rendering while the new API fields remain harmless.
- Do not modify protected experiment video resources, question banks, canonical chunks, embeddings, or manually reviewed evidence resources as part of this change.

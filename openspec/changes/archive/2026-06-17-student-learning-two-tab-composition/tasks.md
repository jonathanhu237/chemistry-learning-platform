## 1. Current State And Contract Audit

- [x] 1.1 Trace the current `LearningHomePanel` render path and document which blocks belong to the future facts view versus experiments view.
- [x] 1.2 Trace current backend `related_groups` generation and identify the exact point where property-section filtering drives experiment grouping.
- [x] 1.3 Confirm the current route/state fields needed to preserve `profileId`, `elementSymbol`, `propertyKey` compatibility, point detail return behavior, and posttest handoff.
- [x] 1.4 Identify any tests or mobile QA selectors that assume the old one-page or property-section-driven layout.

## 2. Student Learning Payload

- [x] 2.1 Add a chapter-level experiment grouping contract for the B view, such as `chapter_experiment_groups`, grouped by current chapter parent experiment and point.
- [x] 2.2 Keep existing fields backward compatible while making the new experiments view read from chapter-level groups instead of property-filtered groups.
- [x] 2.3 Update backend schemas and frontend API types for the new chapter experiment group shape.
- [x] 2.4 Ensure profile facts, family common properties, optional reference media, and property sections remain available for the A view.
- [x] 2.5 Add or update backend tests covering payload shape, no-video point behavior, and removal of property section selection as the primary experiment grouping requirement.

## 3. Two-Tab Chapter Composition

- [x] 3.1 Introduce local chapter view state, e.g. `activeChapterView: "facts" | "experiments"`, without changing the selected family/chapter.
- [x] 3.2 Build a reusable student H5 segmented switcher styled like an iOS segmented control using existing mobile primitives/tokens.
- [x] 3.3 Place the segmented switcher as a sticky in-page control under the current chapter context, not in global bottom navigation.
- [x] 3.4 Move selected-element facts, family common properties, property/trend summaries, and optional reference media into the facts view.
- [x] 3.5 Move experiment-point cards into the experiments view and group them by chapter parent experiment and point.
- [x] 3.6 Add an in-content CTA from the facts view to the experiments view so the primary learning task remains discoverable.
- [x] 3.7 Remove or demote property-section buttons from experiment navigation; property sections may remain as facts/common-property content only.

## 4. Mobile Interaction And State

- [x] 4.1 Ensure segmented options have 44-48px phone-appropriate hit areas, clear active state, and readable labels at 360px width.
- [x] 4.2 Preserve selected element and active A/B view across local overlay changes, point detail navigation, and return from point detail.
- [x] 4.3 Preserve independent facts/experiments scroll positions where feasible, or document a safe fallback that preserves active view and chapter context.
- [x] 4.4 Ensure AI, feedback, finish action, sticky switcher, and bottom navigation do not overlap on 360x780, 390x844, and 430x932 viewports.
- [x] 4.5 Keep optional swipe support out of the critical path unless it can be added without interfering with vertical scroll, video controls, or point-card taps.

## 5. Point Detail, AI, Feedback, And Assessment

- [x] 5.1 Ensure selecting a point from the experiments view opens the existing point detail route with profile, experiment, point, selected element, and active view context.
- [x] 5.2 Ensure returning from point detail restores a sensible experiments-view context.
- [x] 5.3 Update AI context metadata to include active chapter view, selected element, and experiment/point context where available.
- [x] 5.4 Update feedback context metadata to include active chapter view, selected element, and experiment/point context where available.
- [x] 5.5 Confirm completing learning from either the chapter page or point detail still starts the existing post-learning assessment flow.

## 6. Verification

- [x] 6.1 Run backend tests or targeted student learning payload tests.
- [x] 6.2 Run `python scripts\validate_production_resources.py`.
- [x] 6.3 Run `npm run typecheck` for `apps/student-web`.
- [x] 6.4 Run `npm run build` for `apps/student-web`.
- [x] 6.5 Update and run mobile viewport QA covering facts-to-experiments switching, experiments-to-facts switching, element switching, point list, point detail, AI entry, feedback entry, and assessment handoff at 360x780, 390x844, and 430x932.
- [x] 6.6 Run `openspec validate student-learning-two-tab-composition --strict`.
- [x] 6.7 Record final manual phone/WebView risks, including sticky switcher behavior and any scroll-position fallback.

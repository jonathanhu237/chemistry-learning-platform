## 1. Route Model

- [x] 1.1 Add a typed element detail route for selected chapter/profile element detail, such as `/chapter/$profileId/element/$symbol`.
- [x] 1.2 Add route helper/search support for opening element detail from chapter detail while preserving source-aware return.
- [x] 1.3 Ensure element detail is classified as a detail route so bottom navigation is hidden.
- [x] 1.4 Remove `chapterView` as a meaningful chapter-page navigation state; callers may pass it temporarily, but final behavior must not depend on it.

## 2. Chapter Detail Refocus

- [x] 2.1 Remove the chapter detail `选章节` header action.
- [x] 2.2 Keep the chapter detail contextual `问 AI` action with chapter context.
- [x] 2.3 Remove `ChapterViewSwitcher` and all `性质通识 / 实验视频` capsule-switch behavior from the chapter page.
- [x] 2.4 Replace the inline full atom-model content with a compact selected-element summary card.
- [x] 2.5 Add a clear element-detail entry action on the compact selected-element summary card.
- [x] 2.6 Remove whole-family/common-property sections such as `全族通性` from the chapter page.
- [x] 2.7 Remove typical-property/property-section blocks such as `族元素的典型性质` from the chapter page.
- [x] 2.8 Remove chapter-page finish-learning/start-assessment actions.

## 3. Element Detail Page

- [x] 3.1 Create an element detail route page under `src/routes/learn`.
- [x] 3.2 Fetch/resolve the current learning profile by `profileId` and resolve the selected element by `symbol`.
- [x] 3.3 Render the full atom/model experience on the element detail page using `LearningAtomModelCard` or a route-specific wrapper.
- [x] 3.4 Provide route-local loading, error, and missing-element states.
- [x] 3.5 Ensure back navigation from element detail restores the chapter page.

## 4. Experiment Entries On Chapter Page

- [x] 4.1 Render real experiment groups/cards below the element summary using existing chapter experiment data.
- [x] 4.2 Keep experiment card clicks opening the existing point detail route.
- [x] 4.3 Preserve profile, point, experiment, and selected element context when opening point detail where available.
- [x] 4.4 Keep experiment card design provisional; do not attempt final experiment pedagogy/content redesign in this change.

## 5. Component Cleanup

- [x] 5.1 Decompose or delete obsolete facts-view code that only supported the removed chapter-local facts page.
- [x] 5.2 Keep reusable element chip, atom model, and experiment card components where they still serve the new route structure.
- [x] 5.3 Remove unused CSS for the capsule switch and removed family/property sections if no longer referenced.
- [x] 5.4 Update route/page ownership so chapter, element detail, and point detail can be optimized independently.

## 6. Tests And QA

- [x] 6.1 Update route tests to assert chapter detail no longer renders `选章节`, the capsule switch, whole-family property cards, or chapter-level assessment completion.
- [x] 6.2 Add tests for opening element detail from chapter page and returning to chapter page.
- [x] 6.3 Add tests that experiment cards render on chapter detail and open existing point detail routes.
- [x] 6.4 Update mobile viewport QA to cover the refocused chapter page and element detail page at 360px, 390px, and 430px widths.
- [x] 6.5 Run student typecheck, tests, build, and relevant mobile QA.

## 7. OpenSpec Validation

- [x] 7.1 Run `openspec validate student-h5-chapter-element-experiment-refocus --strict`.
- [x] 7.2 Confirm modified specs are archive-ready after implementation.

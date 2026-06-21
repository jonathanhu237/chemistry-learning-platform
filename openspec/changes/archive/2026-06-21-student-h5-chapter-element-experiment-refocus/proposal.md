## Why

The chapter detail page currently carries too many responsibilities: it exposes chapter switching, a facts/video capsule switch, a large atom model, whole-family property cards, property sections, experiment entries, and completion-to-assessment actions in one long page. After the route-stack refactor, chapter selection is already owned by the learning root and route history, so the chapter detail page should become a focused learning entry surface instead of a second selector plus full encyclopedia page.

This change refocuses the selected chapter page around two practical actions: inspect the selected element in a dedicated detail page, or open a real experiment card. It removes low-value family/property blocks from the chapter page and keeps contextual AI as the only top action for now.

## What Changes

- Remove the `选章节` action from the chapter detail page; returning to chapter selection is handled by route/history back to the learning root.
- Keep the contextual `问 AI` action on the chapter detail page.
- Remove the `性质通识 / 实验视频` capsule switch from the chapter detail page.
- Replace the current large inline atom model on the chapter page with a lightweight selected-element summary card.
- Add a dedicated element detail route opened from the selected-element summary; this route owns the full atom/model experience.
- Remove whole-family/general-property content from the chapter page, including `全族通性`, family property cards, and typical property-section blocks.
- Render real experiment cards below the element summary on the chapter page using existing experiment data; visual/content details may remain provisional.
- Keep experiment card clicks opening the existing experiment point detail page.
- Remove the chapter-page completion-to-assessment action from this surface; assessment entry remains available through the assessment root and any existing point-detail flow unless separately redesigned.
- Do not add a new backend API or new dependency for this change; reuse the current learning page and experiment detail data.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-learning-flow`: Refocus the chapter detail page around lightweight element summary and real experiment entries, remove local facts/experiments switching, and move full element model content to its own detail route.
- `student-h5-route-stack-navigation`: Add the element detail page to the route-stack/detail-page model and ensure it follows hidden-bottom-nav and source-aware return behavior.

## Impact

- Affected frontend routes:
  - `apps/student-web/src/app/router/*`
  - `apps/student-web/src/routes/learn/*`
- Affected feature components:
  - `apps/student-web/src/features/learning/LearningHomePanel.tsx`
  - `apps/student-web/src/features/learning/LearningFactsView.tsx`
  - `apps/student-web/src/features/learning/LearningExperimentsView.tsx`
  - `apps/student-web/src/features/atom-viewer/LearningAtomModelCard.tsx`
- Affected tests/QA:
  - route tests for chapter page, element detail page, and experiment card navigation
  - mobile viewport QA coverage for the new simplified chapter page and element detail route
- No backend schema or API changes are required for the first implementation.
